import xml.etree.ElementTree as ET

from fcpx_marker_tool.parsers.fcpxparser import FCPXParser
from fcpx_marker_tool.parsers.fcp7parser import FCP7Parser

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