class ProjectFile:

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.resources = []
        self.root_container = Container(name)

    def add_resource(self, resource):
        self.resources.append(resource)  

    def get_timelines(self):
        timelines = []
        # recursively grab timelines from self.root_container
        return timelines

class Resource:
    """Allows for shared characteristics between multiple types of xml imports"""
    
    def __init__(self, id, name, path, timecode_info, interlaced=False):
        self.id = id
        self.name = name
        self.path = path # for anything that's not a file like compound clips, this can be labeled as something like "internal"
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
                print(f"{'------' * level}{child}")

class Timeline:

    def __init__(self, name, timecode_info, interlaced=False):
        self.name = name
        self.timecode_info = timecode_info
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced
        self.clips = []
        self.markers = []

    def add_clip(self, clip):
        self.clips.append(clip)

    def add_marker(self, marker):
        self.markers.append(marker)

class Clip:

    def __init__(self, name, clip_type, timecode_info, interlaced=False, resource_id=None, track=0):
        self.name = name
        self.clip_type = clip_type
        self.timecode_info = timecode_info
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced
        # resource_id is optional. It isn't necessary for dealing with clips in timelines at a basic level,
        # but it can be helpful for custom workflows where referencing the original timecode information is necessary.
        if resource_id is not None:
            self.resource_id = resource_id
        self.track = track
        self.markers = []

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
            raise ValueError(f"to-do markers must have a completed status set to 'True' or 'False'")
        elif (value is not None) and (isinstance(value, bool) is False):
            raise ValueError(f"completed must be set to True or False")
        self._completed = value