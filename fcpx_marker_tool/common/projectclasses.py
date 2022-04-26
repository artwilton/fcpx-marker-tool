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

class Resource:
    """Allows for shared characteristics between multiple types of xml imports"""
    
    def __init__(self, id, name, file_path, timecode_info, interlaced=False):
        self.id = id
        self.name = name
        self.file_path = file_path # for anything that's not a file like compound clips, this can be labeled as something like "internal"
        self.timecode_info = timecode_info # TimecodeInfo class object
        self.interlaced = interlaced # boolean, True for progressive and False for interlaced

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