from pathlib import Path
from parsers.xmlparser import XMLParser

class MenuBasedCLI:

    def run_cli(self):
        file_path = self._input_to_path("Enter file: ")
        parser = XMLParser(file_path).create_parser()
        parsed_project_file = parser.parse_xml()
        marker_list = self._multiple_source_check(parsed_project_file)
        if len(marker_list) != 0:
            formatted_marker_list = self._choose_output_format(marker_list)
            self._save_prompt(formatted_marker_list)
        else:
            print("No markers found.")

        return 0

    def _input_to_path(self, message):
        user_input = ""

        while user_input != "exit":
            user_input = input(message)
            # Handle path being wrapped in single quotes
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

    def _multiple_source_check(self, project_file_obj):
        project_root = project_file_obj.root_container

        if len(project_root.children) > 1:
            project_root.print_tree()
            marker_list = self._choose_marker_source(project_root)
        else:
            try:
                # need more accurate method for grabbing single
                marker_list = project_root.children[0].children[0].markers
            except IndexError:
                print("Project contains no valid containers, timelines, or clips")

        return marker_list

    def _choose_marker_source(self, project_root_container):
        # print menu showing directory structure, user input determines clip or timeline to grab marker data from
        pass

    def _choose_output_format(self, marker_list):
        # formatting examples will include "YouTube", "DVD Studio Pro", "Marker Name - Frames", "Marker Name - Fractional Timecode"
        # for now just return marker_list for testing
        return marker_list

    def _save_prompt(self, formatted_marker_list):
        user_input_path = input("Choose a location to save the Marker List, or press 'Enter' to print without saving: ")

        for marker in formatted_marker_list:
            frame_rate = marker.timecode_info.frame_rate
            start = marker.timecode_info.start.as_frame(frame_rate)
            rational_time = marker.timecode_info.start
            print(f"Start: {start} Frame Rate: {frame_rate} Rational: {rational_time}")