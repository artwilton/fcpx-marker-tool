"""
This script takes FCPX .xml files as an input and exports a .txt file containing chapter marker info
"""

import xml.etree.ElementTree as ET
from timecode import Timecode
import timecode

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

def format_frame_rate(frame_rate):
    # Preps framerate for timecode module, ex: the string "1001/30000s" becomes a tuple (30000, 1001)
    frame_rate = split_and_remove_s(frame_rate)
    frame_rate = (frame_rate[1], frame_rate[0])

    return frame_rate

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

def get_number_of_frames(rational_time_value, frame_rate):

    if rational_time_value == "0s" or rational_time_value is None:
        return 0

    rational_time_tuple = split_and_remove_s(rational_time_value)

    number_of_frames = (rational_time_tuple[0] * frame_rate[0]) / (rational_time_tuple[1] * frame_rate[1])

    return number_of_frames

def grab_marker_start_time(clip, timeline_info, frame_rate):

    timeline_starting_frame = get_number_of_frames(timeline_info["start_frame"], frame_rate)
    clip_offset = get_number_of_frames(clip["clip_offset"], frame_rate)
    chapter_start = get_number_of_frames(clip['chapter_start'], frame_rate)
    clip_start = get_number_of_frames(clip['clip_start'], frame_rate)

    chapter_marker_timeline_frame = int((chapter_start - clip_start) + clip_offset + timeline_starting_frame)

    return chapter_marker_timeline_frame

def frames_to_timecode(frame_count, frame_rate):

    #adding 1 here because timecode module needs the amount of frames here, not a 0 based frame number
    frame_count += 1
    timecode_value = Timecode(frame_rate, frames=frame_count)

    return timecode_value

def check_for_NDF(timeline_info):
    # sometimes the framerate will be stored as something like "3003/90000s" instead of "1001/30000s"
    # so this function checks to see if there is any possibility of a match for 29.97 or 59.94 no matter how the framerate is stored

    frame_rate = format_frame_rate(timeline_info["frame_rate"])
    timecode_format = timeline_info["timecode_format"]

    check_5994 = (frame_rate[0] % 60000 + frame_rate[1] % 1001)
    check_2997 = (frame_rate[0] % 30000 + frame_rate[1] % 1001)

    if (check_5994 == 0) and (timecode_format == "NDF"):
        frame_rate = (60, 1)
    elif (check_2997 == 0) and (timecode_format == "NDF"):
        frame_rate = (3000, 100)

    return frame_rate

def generate_output(clips_list, timeline_info):

    for clip in clips_list:
        frame_rate = check_for_NDF(timeline_info)
        # frame_rate = format_frame_rate(timeline_info["frame_rate"]) 
        marker_frame = grab_marker_start_time(clip, timeline_info, frame_rate)
        marker_timecode = frames_to_timecode(marker_frame, frame_rate)
        print(marker_timecode)

def main():
    xml_file = input("Enter xml file path: ")
    parsed_xml = parse_xml(xml_file)
    timeline_info = get_timeline_info(parsed_xml)
    clips_list = grab_clips(parsed_xml)
    generate_output(clips_list, timeline_info)

if __name__ == "__main__":
    main()