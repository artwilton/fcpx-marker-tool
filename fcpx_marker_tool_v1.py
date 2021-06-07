"""
This script takes FCPX .xml files as an input and exports a .txt file containing chapter marker info
"""

import xml.etree.ElementTree as ET

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

def grab_chapter_markers(xml_root):
    chapter_markers = xml_root.findall(".//chapter-marker/..")
    # print(chapter_markers)
    for clip in chapter_markers:
        print(clip.tag, clip.attrib, clip.find("chapter-marker").attrib)

def main():
    xml_file = input('Enter xml file path: ')
    parsed_xml = parse_xml(xml_file)
    grab_chapter_markers(parsed_xml)

if __name__ == "__main__":
    main()