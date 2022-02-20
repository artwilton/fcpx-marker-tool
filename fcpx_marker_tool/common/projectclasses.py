class ProjectFile:

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.resources = []
        self.timelines = []

    def add_resource(self, resource):
        self.resources.append(resource)  

    def add_timeline(self, timeline):
        self.timelines.append(timeline)

class Resource:
    """Allows for shared characteristics between multiple types of xml imports"""
    
    def __init__(self, id, name, path, timecode_info):
        self.id = id
        self.name = name
        self.path = path # for anything that's not a file like compound clips, this can be labeled as something like "internal"
        self.timecode_info = timecode_info # TimecodeInfo class object

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
                level += 1
                cls._recursive_container(child, level)
            else:
                print(f"{'------' * level}{child}")

class Timeline:

    def __init__(self, name, timecode_info):
        self.name = name
        self.timecode_info = timecode_info
        self.clips = []

    def add_clip(self, clip):
        self.clips.append(clip)

class Clip:

    def __init__(self, name, type, timecode_info):
        self.name = name
        self.type = type
        self.timecode_info = timecode_info
        self.markers = []

    def add_marker(self, marker):
        self.markers.append(marker)

class Marker:

    def __init__(self):
        pass