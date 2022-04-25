from pathlib import Path
from fcpx_marker_tool.parsers.xmlparser import XMLParser
from fcpx_marker_tool.common import filemanagement

class MenuBasedCLI:

    def run_cli(self):
        file_path = self._input_to_path("Enter file: ")
        parser = XMLParser(file_path).create_parser()
        parsed_project_file = parser.parse_xml()
        marker_source = self._multiple_source_check(parsed_project_file)
        if len(marker_source.markers) != 0:
            output_formatting = self._choose_output_formatting()
            formatted_marker_list = self._format_marker_list(marker_source.markers, output_formatting)
            self._format_and_save_file(formatted_marker_list)
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
            filemanagement.DirectoryTree(project_file_obj.items).print_tree()
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
  
    def _choose_output_formatting(self):
        message = "Select an output format by entering an option number: "
        choices_list = list(filemanagement.OutputFormatting.FORMATTING_OPTIONS.keys())
        output_formatting = self._menu_selection_template(message, choices_list, print_choices=True)
        return output_formatting

    def _format_marker_list(self, marker_list, output_formatting):
        formatted_marker_list = []

        for marker in marker_list:
            marker_string = filemanagement.OutputFormatting(marker, output_formatting).formatted
            formatted_marker_list.append(marker_string)

        return formatted_marker_list

    def _menu_selection_template(self, message, choices_list, print_choices=False):
        while True:
            if print_choices:
                for index, value in enumerate(choices_list):
                    print(f"{index + 1}. {value}")
                print_choices=False

            user_input = input(message)
    
            if user_input == 'exit':
                raise SystemExit(0)
            else:
                try:
                    user_input = int(user_input)
                except ValueError:
                    message = "Selection must be an integer.\nEnter a valid item choice from the list to continue: "
                    continue
            
            if user_input > 0:
                try:
                    user_selection = choices_list[user_input - 1]
                    break
                except IndexError:
                    message = "Enter a valid item choice from the list to continue: "
                    print("Error: Invalid item choice")
            else:
                print("Error: Invalid item choice, selection must be an integer greater than 0")

        return user_selection

    def _choose_output_formatting(self):
        message = "Select an output format by entering an option number: "
        choices_list = list(filemanagement.OutputFormatting.FORMATTING_OPTIONS.keys())
        output_formatting = self._menu_selection_template(message, choices_list, print_choices=True)
        return output_formatting

    def _format_and_save_file(self, formatted_marker_list):
        message = "Select a file export type by entering an option number: "
        choices_list = list(filemanagement.OutputFile.FILE_FORMAT_OPTIONS.keys())
        file_format = self._menu_selection_template(message, choices_list, print_choices=True)

        if file_format != "Print":
            output_file_path = input("Enter a file path to save the Marker List: ")
            filemanagement.OutputFile(formatted_marker_list, file_format, output_file_path)
        else:
            filemanagement.OutputFile(formatted_marker_list, file_format)