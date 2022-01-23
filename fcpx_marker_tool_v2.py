"""
This script takes FCPX .xml files as an input and prints chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode

class Timeline:
    
    def __init__(self, name, start_frame, duration, timecode_format, frame_rate):
        return

class Clip:

    def __init__(self, name, offset, asset_id_ref, duration, start):
        return

class Marker:

    def __init__(self, start, value, type, completed=None):
        return

    # if type == ToDo, add a 'completed' boolean

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

class XMLParser:

    def __init__(self):
        return

class TimecodeHelpers:

    def __init__(self):
        return

class Interface:

    def __init__(self):
        return

def main():
    print("main")

if __name__ == "main":
    main()