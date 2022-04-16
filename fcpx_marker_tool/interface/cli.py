from pathlib import Path
from parsers.xmlparser import XMLParser

class MenuBasedCLI:

    def run_cli(self):
        file_path = self._input_to_path("Enter file: ")
        parser = XMLParser(file_path).create_parser()
        parsed_project_file = parser.parse_xml()
        marker_source = self._multiple_source_check(parsed_project_file)
        if len(marker_source.markers) != 0:
            formatted_marker_list = self._choose_output_format(marker_source.markers)
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

        if len(project_file_obj.items) > 1:
            project_file_obj.print_nested_items()
            marker_source = self._choose_marker_source(project_file_obj)
        else:
            try:
                marker_source = project_file_obj.items[0]
            except IndexError:
                print("Project contains no valid timelines, or clips")

        return marker_source

    def _choose_marker_source(self, project_file_obj):
        message = "There is more than one timeline or clip present in this file, select an item to parse: "
        while True:
            user_input = int(input(message))

            if user_input == 'exit':
                raise SystemExit(0)
            elif not isinstance(user_input, int):
                message = "Enter a valid item number from the list to continue: "
                raise ValueError("Value must be an integer")
            else:
                try:
                    project_item = project_file_obj.items[user_input]
                    break
                except IndexError:
                    print("Invalid item number")

        return project_item

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