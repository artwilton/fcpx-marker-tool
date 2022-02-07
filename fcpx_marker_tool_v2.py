"""
This script takes FCPX .xml files as an input and prints chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode

# will refactor this into a defaults module
ALLOWED_RESOURCE_TYPES = ["format", "media", "asset"]
ALLOWED_CLIP_TYPES = ["clip", "asset-clip", "sync-clip", "mc-clip", "ref-clip", "gap"]
ALLOWED_MARKER_TYPES = ["marker", "to_do_marker", "chapter_marker"]

class Library:

    def __init__(self, file_path):
        self.file_path = file_path
        self.resources = []
        self.timelines = []

class Resource:

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
        if value not in ALLOWED_RESOURCE_TYPES:
            raise ValueError(f"Resource type must be one of the following: {ALLOWED_RESOURCE_TYPES}")
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

class Clip:

    def __init__(self, name, type, offset, duration, start, asset_id_ref=None):
        self.name = name
        self.type = type
        self.offset = offset
        self.duration = duration
        self.start = start
        self.asset_id_ref = asset_id_ref
        self.markers = []

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in ALLOWED_CLIP_TYPES:
            raise ValueError(f"Clip type must be one of the following: {ALLOWED_CLIP_TYPES}")
        self._type = value

class Marker:

    def __init__(self, start, duration, value, type, completed=None):
        self.start = start
        self.duration = duration
        self.value = value
        self.type = type
        self.completed = completed

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in ALLOWED_MARKER_TYPES:
            raise ValueError(f"Marker type must be one of the following: {ALLOWED_MARKER_TYPES}")
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
    # In future iterations creating an ABC for different Parsers might be beneficial here

    def _get_xml_root(self, xml_file):
        tree = ET.parse(xml_file)
        xml_root = tree.getroot()
        return xml_root

    def __init__(self, xml_file):
        self.xml_file = xml_file
        self._xml_root = self._get_xml_root(xml_file)

    # Library Parsing
    def _get_library_element(self):
        library = self._xml_root.find("./library")
        file_path = library.get("location")
        return file_path

    def _create_library(self):
        file_path = self._get_library_element()
        return Library(file_path)

    # Resource Parsing
    def _get_resource_elements(self):
        resources = self._xml_root.find("./resources")
        return resources

    def _create_resources(self, library):
        resources = self._get_resource_elements()

        for resource in resources:
            id = resource.get("id")
            name = resource.get("name")
            type = resource.tag
            frame_rate = resource.get("frameDuration", default=None)

            library.resources.append(Resource(id, name, type, frame_rate=frame_rate))

    # Timeline Parsing
    def _get_timeline_elements(self):
        timelines = self._xml_root.findall(".//project")

        return timelines

    def _create_timelines(self, library):
        timelines = self._get_timeline_elements()

        for timeline in timelines:
            _sequence = timeline.find("sequence")

            name = timeline.get("name")
            start_frame = _sequence.get("tcStart")
            duration = _sequence.get("duration")
            timecode_format = _sequence.get("tcFormat")
            frame_rate = _sequence.get("frameDuration")
            
            library.timelines.append(Timeline(name, start_frame, duration, timecode_format, frame_rate))

    # Clip Parsing
    def _get_clip_elements(self, timeline_root):

        #use list comprehension to grab all clip elements that can possibly have markers on them
        #inlcuding clips that don't have Markers for scalability, for example if a user wants to see percentege of clips that have Markers, etc.
        clips = [clip for clip in timeline_root.iter() if str(clip.tag) in ALLOWED_CLIP_TYPES]
        
        return clips

    def _create_clips(self, timelines):

        all_clips = []

        # to avoid nested loops the solution will most likely be having a Timeline object be responsible for creating its own clips, and to follow that pattern with other classes.

        for timeline in timelines:
            #for each timeline, only find clips that belong to it
            timeline_root = self._xml_root.find(f".//project/[@name='{timeline.name}']")
            clips = self._get_clip_elements(timeline_root)
            all_clips.extend(clips)

            for clip in clips:
                name = clip.get("name")
                type = clip.tag
                offset = clip.get("offset")
                duration = clip.get("duration")
                start = clip.get("start")
                asset_id_ref = clip.get("", default=None) #some asset types like gaps don't have a "ref" attribute, will add better handling for this in future versions
            
                timeline.clips.append(Clip(name, type, offset, duration, start, asset_id_ref=asset_id_ref))

        return all_clips

    def _get_marker_elements(self, clip):
        markers = [marker for marker in clip.iter() if str(marker.tag).endswith('marker')]

        return markers

    def _create_markers(self, all_clips, library):
        for clip in all_clips:
            markers = self._get_marker_elements(clip)

            # again need to change design pattern here to avoid nested loops
            for marker in markers:
                start = marker.get("start")
                value = marker.get("value")
                type = marker.tag
                completed = marker.get("completed", default=None)
                clip.markers.append(Marker(self, start, value, type, completed))

    def parse_xml(self):
        library = self._create_library()
        self._create_resources(library)
        self._create_timelines(library)
        all_clips = self._create_clips(library.timelines)
        self._create_markers(all_clips, library)
        print(len(all_clips))

class TimecodeHelpers:

    def __init__(self):
        pass

class Interface:

    def __init__(self):
        pass

def main():
    xml_file = input("Enter xml file path: ").strip()
    xml_parser = XMLParser(xml_file)
    xml_parser.parse_xml()

if __name__ == "__main__":
    main()