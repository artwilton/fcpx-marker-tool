"""
This script takes FCPX .xml files as an input and exports a .txt file containing chapter marker info
"""

import xml.etree.ElementTree as ET

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

def get_timeline_info(xml_root):
    
    sequence = xml_root.find('.//sequence')
    format = xml_root.find('./resources/format')

    timeline_info = {
        'start_frame': sequence.get('tcStart'),
        'timecode_format': sequence.get('tcFormat'),
        'frame_rate': format.get('frameDuration')
    }

    return timeline_info

def grab_clips(xml_root):
    clips_list = []
    clips_with_markers = xml_root.findall(".//chapter-marker/..")

    for clip in clips_with_markers:
        clips_list.append(
            {
            'clip_offset': clip.get('offset'),
            'clip_start': clip.get('start'),
            'chapter_start': clip.find('chapter-marker').get('start'),
            'chapter_name': clip.find('chapter-marker').get('value')
            }
        )

    return clips_list

def main():
    xml_file = input('Enter xml file path: ')
    parsed_xml = parse_xml(xml_file)
    timeline_info = get_timeline_info(parsed_xml)
    clips_list = grab_clips(parsed_xml)

    print(timeline_info)

if __name__ == "__main__":
    main()