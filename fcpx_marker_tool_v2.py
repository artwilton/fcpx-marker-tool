"""
This script takes FCPX .xml files as an input and prints chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode

class Library:

    def __init__(self, name):
        pass

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

class Clip:

    def __init__(self, name, offset, asset_id_ref, duration, start):
        self.name = name
        self.offset = offset
        self.asset_id_ref = asset_id_ref
        self.duration = duration
        self.start = start

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

    def __init__(self):
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