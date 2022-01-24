"""
This script takes FCPX .xml files as an input and prints chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode

class Library:

    def __init__(self, file_path):
        self.file_path = file_path
        self.resources = []
        self.timelines = []

class Resource:

    allowed_types = ["format", "media", "asset"]

    def __init__(self, id, name, type, frame_rate=None):
        self.id = id
        self.name = name
        self.type = type
        self.frame_rate = frame_rate

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in Resource.allowed_types:
            raise ValueError(f"Resource type must be one of the following: {Resource.allowed_types}")
        self._type = value

    @property
    def frame_rate(self):
        return self._frame_rate

    @frame_rate.setter
    def frame_rate(self, value):
        if (self.type == "format") and (value is None):
            raise ValueError(f"Resources with the 'format' type must have a frame rate")
        self._frame_rate = value

class Timeline:
    
    def __init__(self, name, start_frame, duration, timecode_format, frame_rate):
        self.name = name
        self.start_frame = start_frame
        self.duration = duration
        self.timecode_format = timecode_format
        self.frame_rate = frame_rate
        self.clips = []

    def add_clip(self, name, offset, asset_id_ref, duration, start):
        self.clips.append(Clip(name, offset, asset_id_ref, duration, start))

class Clip:

    def __init__(self, name, offset, asset_id_ref, duration, start):
        self.name = name
        self.offset = offset
        self.asset_id_ref = asset_id_ref
        self.duration = duration
        self.start = start
        self.markers = []

    def add_marker(self, start, value, type, completed=None):
        self.markers.append(Marker(self, start, value, type, completed))

class Marker:

    allowed_types = ["marker", "to_do_marker", "chapter_marker"]

    def __init__(self, start, value, type, completed=None):
        self.start = start
        self.value = value
        self.type = type
        self.completed = completed

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in Marker.allowed_types:
            raise ValueError(f"Marker type must be one of the following: {Marker.allowed_types}")
        self._type = value

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        if (self.type == "to_do_marker") and (value is None):
            raise ValueError(f"To Do Markers must have a completed status set to 'True' or 'False'")
        elif (self.type != "to_do_marker") and (value is not None):
            raise ValueError(f"Only To Do Markers can have a completed status'")
        self._completed = value

class XMLParser:

    def _get_xml_root(self, xml_file):
        tree = ET.parse(xml_file)
        xml_root = tree.getroot()
        return xml_root

    def __init__(self, xml_file):
        self.xml_file = xml_file
        self._xml_root = self._get_xml_root(xml_file)

    # Library Parsing
    def _get_library_info(self):
        library = self._xml_root.find("./library")
        file_path = library.get("location")
        return file_path

    def _create_library(self):
        file_path = self._get_library_info()
        return Library(file_path)

    # Resource Parsing
    def _get_resource_info(self):
        resources = self._xml_root.find("./resources")
        return resources

    def _create_resources(self, library):
        resources = self._get_resource_info()

        for resource in resources:
            id = resource.get("id")
            name = resource.get("name")
            type = resource.tag
            frame_rate = resource.get("frameDuration", default=None)

            library.resources.append(Resource(id, name, type, frame_rate=frame_rate))

    # Timeline Parsing
    def _get_timeline_info(self):
        timelines = self._xml_root.findall("./project")
        return timelines

    def _create_timelines(self, library):
        timelines = self._get_timeline_info()

        for timeline in timelines:
            _sequence = timeline.find("sequence")

            name = timeline.get("name")
            start_frame = _sequence.get("tcStart")
            duration = _sequence.get("duration")
            timecode_format = _sequence.get("tcFormat")
            frame_rate = _sequence.get("frameDuration")
            
            library.timelines.append(Timeline(name, start_frame, duration, timecode_format, frame_rate))

    def _get_clip_info(self):
        pass

    def _create_clips(self, timelines):
        pass

    def parse_xml(self):
        library = self._create_library()
        self._create_resources(library)
        self._create_timelines(library)
        self._create_clips(library.timelines)
        #call other functions to actually generate objects
        pass

class TimecodeHelpers:

    def __init__(self):
        pass

class Interface:

    def __init__(self):
        pass

def main():
    print("main")

if __name__ == "main":
    main()