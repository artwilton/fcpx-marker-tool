"""
This script takes FCPX .xml files as an input and exports a .txt file containing chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

def get_timeline_info(xml_root):

    library = xml_root.find("./library")
    sequence = library.find(".//sequence")

    # grab format tag that corresponds with the current sequence
    format_number = sequence.get('format')
    format = xml_root.find(f"./resources/format/[@id='{format_number}']")

    timeline_info = {
        "start_frame": sequence.get("tcStart"),
        "timecode_format": sequence.get("tcFormat"),
        "frame_rate": format.get("frameDuration")
    }

    return timeline_info

def split_and_remove_s(rational_time):
    rational_time = rational_time.replace("s", "")
    rational_time = tuple(map(int, rational_time.split("/")))

    return rational_time

def format_time_values(timeline_info):

    start_frame = timeline_info["start_frame"]

    if start_frame == "0s":
        timeline_info["start_frame"] = 0
    else:
        start_frame = split_and_remove_s(start_frame)
        timeline_info["start_frame"] = start_frame

    frame_rate_list = split_and_remove_s(timeline_info["frame_rate"])
    timeline_info["frame_rate"] = frame_rate_list

def grab_clips(xml_root):
    clips_list = []
    clips_with_markers = xml_root.findall(".//chapter-marker/..")

    for clip in clips_with_markers:
        clips_list.append(
            {
            "clip_offset": clip.get("offset"),
            "clip_start": clip.get("start"),
            "chapter_start": clip.find("chapter-marker").get("start"),
            "chapter_name": clip.find("chapter-marker").get("value")
            }
        )

    return clips_list

def main():
    xml_file = input("Enter xml file path: ")
    parsed_xml = parse_xml(xml_file)
    timeline_info = get_timeline_info(parsed_xml)
    format_time_values(timeline_info)
    clips_list = grab_clips(parsed_xml)

    print(timeline_info, clips_list)

if __name__ == "__main__":
    main()