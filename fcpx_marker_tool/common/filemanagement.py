import sys

class OutputFormatting:

    def __init__(self, item, formatting_option=None):
        self.item = item
        if self.item.timecode_info.conform_rate_check:
            self.frame_rate = self.item.timecode_info.conformed_frame_rate
        else:
            self.frame_rate = self.item.timecode_info.frame_rate
        if formatting_option is not None:
            self.formatted = self.set_formatting(formatting_option)

    def youtube(self):
        # need to implement specific checks here:
            # First chapter must start with 00:00.
            # There must be at least three timestamps listed in ascending order.
            # The minimum length for video chapters is 10 seconds.
            # https://support.google.com/youtube/answer/9884579
        timecode = self.item.timecode_info.start.as_hr_min_sec(self.frame_rate, self.item.timecode_info.non_drop_frame)
        return f"{timecode} {self.item.name}"
        
    def dvd_studio_pro(self):
        # need to check for first chapter starting at 00:00:00:00 here
        timecode = self.item.timecode_info.start.as_timecode(self.frame_rate, self.item.timecode_info.non_drop_frame)
        return f"{timecode} {self.item.name}"

    def name_frames(self):
        frame_number = self.item.timecode_info.start.as_frame(self.frame_rate)
        return f"{self.item.name} - {frame_number}"

    def name_fractional_timecode(self):
        fractional_timecode = self.item.timecode_info.start.as_fractional_timecode(self.frame_rate, self.item.timecode_info.non_drop_frame)
        return f"{self.item.name} - {fractional_timecode}"

    FORMATTING_OPTIONS = {
    "Youtube": youtube,
    "DVD Studio Pro": dvd_studio_pro,
    "Marker Name - Frames": name_frames,
    "Marker Name - Fractional Timecode": name_fractional_timecode
    }

    def set_formatting(self, formatting_option):
        try:
            return self.FORMATTING_OPTIONS[formatting_option](self)
        except KeyError:
            print("Invalid format option")

class OutputFile:

    def __init__(self, item_list, file_format, output_file_path=sys.stdout):
        self.item_list = item_list
        self.output_file_path = output_file_path
        self.file_format = file_format

    def _save_file(self):
        with self.output_file_path as output_file:
            for item in self.item_list:
                print(item, file=output_file)

    def print_to_stdout(self):
        if not self.output_file_path == sys.stdout:
            self.output_file_path = sys.stdout
        self._save_file()

    def text_file(self):
        # add more path validations in the future
        if not self.output_file_path.endswith(".txt"):
            self.output_file_path += ".txt"
        self.output_file_path = open(self.output_file_path, "w", encoding="UTF-8")
        self._save_file()

    FILE_FORMAT_OPTIONS = {
    "Print": print_to_stdout,
    "Text file": text_file
    }

    @property
    def file_format(self):
        return self._file_format

    @file_format.setter
    def file_format(self, file_format_option):
        try:
            self._file_format = self.FILE_FORMAT_OPTIONS[file_format_option](self)
        except KeyError:
            print("Invalid format option")

class DirectoryTree:

    def __init__(self, item_list, file_path=False):
        self.item_list = item_list #must be a list containing item objects that all have a valid project_path or file_path
        self.nested_items = self._get_nested_items(file_path=file_path)

    def print_tree(self):
        item_list = []
        self._recursive_parse_nested_items(self.nested_items, item_list)

        print(".")
        for item in item_list:
            print(item)

    def _get_nested_items(self, file_path=False):
        # returns a dictionary of items nested based on their project path, the key for each item object will be its index number in self.items
        # ex: {'Folder': {1: <item_obj_1>, 2: <item_obj_2>, 'Subfolder': {3: <item_obj_3>}}}
        nested_items_dict = {}

        def set_nested_keys(dictionary, keys, value):
            for key in keys[:-1]:
                dictionary = dictionary.setdefault(key, {})
            dictionary[keys[-1]] = value

        for index, item in enumerate(self.item_list):
            if file_path:
                parts = [*item.file_path.parts, index]
            else:
                parts = [*item.project_path.parts, index]
            set_nested_keys(nested_items_dict, parts, item)

        return nested_items_dict

    def _recursive_parse_nested_items(self, dictionary, item_list, level=0, prefix=""):
        directory_count = len(dictionary)

        for index, (key, value) in enumerate(dictionary.items()):
            connector = "├──" if index != directory_count - 1 else "└──"

            if isinstance(value, dict):
                prefix = "│" if index != directory_count - 1 else " "
                item_list.append(f"{'   ' * level}{connector} {key}")
                self._recursive_parse_nested_items(value, item_list, level+1, prefix)
            else:
                item_list.append(f"{'   ' * int(level/2)}{prefix}{'   ' * int(level/2)}{connector} [{key+1}] {value.name}")