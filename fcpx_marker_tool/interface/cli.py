from pathlib import Path
from parsers.xmlparser import XMLParser
from common.formatting import OutputFormat, DirectoryTree

class MenuBasedCLI:

    def run_cli(self):
        file_path = self._input_to_path("Enter file: ")
        parser = XMLParser(file_path).create_parser()
        parsed_project_file = parser.parse_xml()
        marker_source = self._multiple_source_check(parsed_project_file)
        if len(marker_source.markers) != 0:
            output_format = self._choose_output_format()
            formatted_marker_list = self._format_marker_list(marker_source.markers, output_format)
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
            DirectoryTree(project_file_obj.items).print_tree()
            marker_source = self._choose_marker_source(project_file_obj)
        else:
            try:
                marker_source = project_file_obj.items[0]
            except IndexError:
                print("Project contains no valid timelines, or clips")

        return marker_source

    def _choose_marker_source(self, project_file_obj):
        message = "More than one timeline or clip was found. Select an item to parse by entering an option number: "
        return self._menu_selection_template(message, project_file_obj.items)
  
    def _choose_output_format(self):
        message = "Select an output format by entering an option number: "
        choices_list = list(OutputFormat.FORMAT_OPTIONS.keys())
        output_format = self._menu_selection_template(message, choices_list, print_choices=True)
        return output_format

    def _format_marker_list(self, marker_list, output_format):
        formatted_marker_list = []

        for marker in marker_list:
            marker_string = OutputFormat(marker, output_format).formatted
            formatted_marker_list.append(marker_string)

        return formatted_marker_list

    def _menu_selection_template(self, message, choices_list, print_choices=False):
        while True:
            if print_choices:
                for index, value in enumerate(choices_list):
                    print(f"{index}. {value}")
            user_input = input(message)
    
            if user_input == 'exit':
                raise SystemExit(0)
            else:
                try:
                    user_input = int(user_input)
                except ValueError:
                    print()
                    message = "Selection must be an integer.\nEnter a valid item choice from the list to continue: "
                    continue

            try:
                user_selection = choices_list[user_input]
                break
            except IndexError:
                print("Invalid item choice")
                message = "Enter a valid item choice from the list to continue: "

        return user_selection

    def _save_prompt(self, formatted_marker_list):
        user_input_path = input("Choose a location to save the Marker List, or press 'Enter' to print without saving: ")

        for marker in formatted_marker_list:
            print(marker)