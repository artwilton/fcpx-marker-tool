from importlib import resources
from pathlib import Path
import resource
import xml.etree.ElementTree as ET
from timecode import Timecode

#This refactor will be built with the idea of making code more scalable, with future ability to import xml files from more than just FCPX

class TimecodeInfo:

    def __init__(self, id, frame_rate, start, duration, non_drop_frame=False):
        self.id = id # can be anything useful, example is "Format id" for FCPX
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps. 
        self.start = start # int representing start frame
        self.duration = duration # int for total amount of frames
        self.non_drop_frame = non_drop_frame # Boolean, True for NDF and False for DF
        self._timecode = Timecode(frame_rate, frames=(start + 1), force_non_drop_frame=non_drop_frame)
    
    @property
    def frame_rate_number(self):
        return self._timecode.framerate

    @property
    def frame_rate_tuple(self):
        # method that will return a rational number tuple version regardless of how TimecodeInfo class is instantiated
        pass

    @property
    def standard_timecode(self):
        return str(self._timecode)

    @property
    def fractional_timecode(self):
        self._timecode.set_fractional(True)
        fractional_output = str(self._timecode)
        self._timecode.set_fractional(False) #unset fractional timecode after grabbing output
        return fractional_output

    @property
    def format(self):
        if self.non_drop_frame:
            return 'NDF'
        else:
            return 'DF'

class ProjectFile:

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.resources = []
        self.timelines = []

    def add_resource(self, resource):
        self.resources.append(resource)  

    def add_timeline(self, timeline):
        self.timelines.append(timeline)  

class Resource:

    # allows shared characteristics between multiple types of xml imports

    def __init__(self, id, name, path, timecode_info):
        self.id = id
        self.name = name
        self.path = path # for anything that's not a file like compound clips, this can be labeled as something like "internal"
        self.timecode_info = timecode_info # TimecodeInfo class object

class Timeline:

    def __init__(self, name, timecode_info):
        self.name = name
        self.timecode_info = timecode_info
        self.clips = []

    def add_clip(self, clip):
        self.clips.append(clip)

class Clip:

    def __init__(self, name, offset, timecode_info):
        self.name = name
        self.offset = offset
        self.timecode_info = timecode_info
        self.markers = []

    def add_marker(self, marker):
        self.markers.append(marker)

class FCPXParser:

    def __init__(self, xml_root):
        self.xml_root = xml_root
        # print("FCPX Parser", xml_root.tag)

    def _create_resources(self):
        resources = self.xml_root.find('resources')

        for resource in resources.iter():
            print(resource)

    def parse_xml(self):
        resources = self._create_resources()

class FCP7Parser:

    def __init__(self, xml_root):
        self.xml_root = xml_root
        print("FCP7 support will be added in a future version.")

class XMLParser:

    parser_types = {
        "fcpxml": FCPXParser,
        "xmeml": FCP7Parser
    }

    def __init__(self, xml_file):
        self.xml_file = xml_file

    @property
    def xml_file(self):
        return self._xml_file

    @xml_file.setter
    def xml_file(self, value):
        # can add further validations here as necessary
        validated_xml_file = self._fcpx_bundle_check(value)
        self._xml_file = validated_xml_file

    @classmethod
    def get_input(cls, message):
        xml_file = cls._input_to_path(message)
        return cls(xml_file)

    @classmethod
    def _input_to_path(cls, message):
        while True:
            # Grab input, handle path being wrapped in single quotes
            user_input = input(message)
            if user_input.startswith("'") and user_input.endswith("'"):
                user_input = user_input[1:-1]
            # create a Path object from input, remove trailing white spaces
            input_path = Path(user_input.strip())
            #validate file exists
            if not input_path.exists():
                print("Please enter valid file path.")
                continue
            else:
                break
           
        return input_path
    
    def _get_xml_root(self):
        tree = ET.parse(self.xml_file)
        xml_root = tree.getroot()
        return xml_root

    def _choose_parser(self, xml_root):
        xml_type = xml_root.tag

        if xml_type not in self.parser_types:
            raise ValueError(f"XML type '{xml_type}' not recognized")
        parser_type = self.parser_types[xml_type]

        return parser_type

    def _fcpx_bundle_check(self, xml_file):
        if xml_file.suffix == '.fcpxmld' and (xml_file / 'Info.fcpxml').exists():
            xml_file = str(xml_file / 'Info.fcpxml')

        return xml_file

    def create_parser(self):
        xml_root = self._get_xml_root()
        parser_type = self._choose_parser(xml_root)
        parser = parser_type(xml_root)
        return parser

def main():
    xml_parser = XMLParser.get_input("Enter file: ")
    parser = xml_parser.create_parser()
    parsed_xml = parser.parse_xml()
    # tc = TimecodeInfo("12", (30000, 1001),10,10,True )
    # print(tc.standard_timecode, tc.id, tc.frame_rate_number)


if __name__ == "__main__":
    main()