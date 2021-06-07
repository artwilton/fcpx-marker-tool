"""
This script takes FCPX .xml files as an input and exports a .txt file containing chapter marker info
"""

import xml.etree.ElementTree as ET

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    print(root)

def main():
    xml_file = input('Enter xml file path: ')
    parse_xml(xml_file)

if __name__ == "__main__":
    main()