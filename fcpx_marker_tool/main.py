from parsers.xmlparser import XMLParser

def main():
    xml_parser = XMLParser.get_input("Enter file: ")
    parser = xml_parser.create_parser()
    parsed_xml = parser.parse_xml()
    # tc = TimecodeInfo("12", (30000, 1001),10,10,True )
    # print(tc.standard_timecode, tc.id, tc.frame_rate_number)

if __name__ == "__main__":
    main()