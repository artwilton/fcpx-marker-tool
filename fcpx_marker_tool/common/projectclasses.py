from pathlib import PurePath

class ProjectFile:

    def __init__(self, name, file_path, project_path=None):
        self.name = name
        self.file_path = file_path
        # project_path is optional because it's assumed it will be the project name, should be the root for clip and timeline project paths
        if project_path is None:
            self.project_path = self.name
        else:
            self.project_path = project_path
        self.resources = []
        self.items = [] # list of clip and/or timeline objects found in project
        self.root_container = Container(name)

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = PurePath(value)

    def add_item(self, item):
        if isinstance(item, (Clip, Timeline)):
            self.items.append(item)
        else:
            raise ValueError("ProjectFile items must be either Clip or Timeline objects")

    def add_resource(self, resource):
        if isinstance(resource, Resource):
            self.resources.append(resource)
        else:
            raise ValueError("Not a valid Resource object")
    
    def get_clips(self):
        return [item for item in self.items if isinstance(item, Clip)]

    def get_timelines(self):
        return [item for item in self.items if isinstance(item, Timeline)]

    def get_nested_items(self, project_items):
        # returns a dictionary of items nested based on their project path, the key for each item object will be its index number in self.items
        # ex: {'Folder': {1: <item_obj_1>, 2: <item_obj_2>, 'Subfolder': {3: <item_obj_3>}}}
        nested_items_dict = {}

        def set_nested_keys(dictionary, keys, value):
            for key in keys[:-1]:
                dictionary = dictionary.setdefault(key, {})
            dictionary[keys[-1]] = value

        for index, item in enumerate(project_items):
            parts = [*item.project_path.parts, index]
            set_nested_keys(nested_items_dict, parts, item)

        return nested_items_dict

    def create_and_print_nested_items(self, dictionary=None):
        item_list = []
        # allows for flexibility of simply calling print_nested_items() from a project file instance, or supplying a different dictionary
        if dictionary is None:
            dictionary = self.get_nested_items(self.items)

        self.recursive_parse_nested_items(dictionary, item_list)

        for item in item_list:
            print(item)

    def recursive_parse_nested_items(self, dictionary, item_list, level=1):

        for key, value in dictionary.items():
            if isinstance(value, dict):
                item_list.append(f"/{'---' * level}{key}")
                self.recursive_parse_nested_items(value, item_list, level + 1)
            else:
                item_list.append(f"{key}{'---' * level}{value.name}")

class Resource:
    """Allows for shared characteristics between multiple types of xml imports"""
    
    def __init__(self, id, name, file_path, timecode_info, interlaced=False):
        self.id = id
        self.name = name
        self.file_path = file_path # for anything that's not a file like compound clips, this can be labeled as something like "internal"
        self.timecode_info = timecode_info # TimecodeInfo class object
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced

class Container:
    """Used for creating a simple directory structure. Container children nodes can be another container, timeline, or clip."""

    def __init__(self, name, children=None):
        self.name = name
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def add_child(self, child):
        self.children.append(child)

    def print_tree(self):
        self._recursive_container(self)

    @classmethod
    def _recursive_container(cls, container, level=1):
        print(f"{'---' * level}{container.name}")

        sorted_container = sorted(container.children, key=lambda child: child.name if child.name else child)

        for child in sorted_container:
            if isinstance(child, cls):
                # level += 1
                cls._recursive_container(child, level + 1)
            else:
                print(f"{'------' * level}{child.name}")

class Timeline:

    def __init__(self, name, timecode_info, project_path, interlaced=False):
        self.name = name
        self.timecode_info = timecode_info
        self.project_path = project_path
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced
        self.clips = []
        self.markers = []

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = value if isinstance(value, PurePath) else PurePath(value)

    def add_clip(self, clip):
        self.clips.append(clip)

    def add_marker(self, marker):
        self.markers.append(marker)

class Clip:

    def __init__(self, name, clip_type, timecode_info, project_path, interlaced=False, resource_id=None, track=0):
        self.name = name
        self.clip_type = clip_type
        self.timecode_info = timecode_info
        self.project_path = project_path
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced
        # resource_id is optional. It isn't necessary for dealing with clips in timelines at a basic level,
        # but it can be helpful for custom workflows where referencing the original timecode information is necessary.
        if resource_id is not None:
            self.resource_id = resource_id
        self.track = track
        self.markers = []

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = value if isinstance(value, PurePath) else PurePath(value)

    def add_marker(self, marker):
        self.markers.append(marker)

class Marker:

    def __init__(self, name, marker_type, timecode_info, completed=None, metadata=None):
        self.name = name
        self.marker_type = marker_type
        self.timecode_info = timecode_info
        self.completed = completed # completed is optional but will be used for FCPX to-do markers and must be a boolean
        # metadata is optional but can be used for things like descriptions.
        if metadata is not None:
            self.metadata = metadata

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        if (self.marker_type == "to-do") and (value is None):
            raise ValueError("to-do markers must have a completed status set to 'True' or 'False'")
        elif (value is not None) and (isinstance(value, bool) is False):
            raise ValueError("completed must be set to True or False")
        self._completed = value