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