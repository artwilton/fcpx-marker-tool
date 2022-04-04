from numbers import Rational
from parsers.xmlparser import XMLParser

def main():
    xml_parser = XMLParser.get_input("Enter file: ")
    parser = xml_parser.create_parser()
    parsed_xml = parser.parse_xml()
    # tc = TimecodeInfo("12", (30000, 1001),10,10,True )
    # print(tc.standard_timecode, tc.id, tc.frame_rate_number)
    for marker in parsed_xml.root_container.children[0].children[0].markers:
        frame_rate = marker.timecode_info.frame_rate
        start = marker.timecode_info.start.as_frame(frame_rate)
        rational_time = marker.timecode_info.start
        print(f"Start: {start} Frame Rate: {frame_rate} Rational: {rational_time}")

    print('')

if __name__ == "__main__":
    main()