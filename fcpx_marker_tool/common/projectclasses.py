from fractions import Fraction
from timecode import Timecode
from typing import NamedTuple

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

class TimecodeInfo:

    def __init__(self, frame_rate, start, duration, offset=0, non_drop_frame=True):
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps.
        self.start = TimecodeFormat(frame_rate, start, non_drop_frame) # Start time for video/audio element
        self.duration = TimecodeFormat(frame_rate, duration, non_drop_frame) # Total length of time for video/audio element
        self.offset = TimecodeFormat(frame_rate, offset, non_drop_frame) # Start time within a timeline, default is 0 since not everything has an offset
        self.non_drop_frame = non_drop_frame # Boolean, True for NDF and False for DF
        # start, duration, and offset can be set with an int (frames) or tuple (rational time).

    @property
    def frame_rate(self):
        # return frame rate as tuple of ints, ex: (30000, 1001)
        # need to create a setter that ensures frame_rate gets set as a tuple, but for now the FCPX parser already does this by default
        return self._frame_rate

    @frame_rate.setter
    def frame_rate(self, value):
        self._frame_rate = value

    @property
    def frame_rate_string(self):
        # return SMPTE standard frame rate as a string, ex: '29.97'
        return Timecode(self._frame_rate).framerate

    @property
    def format(self):
        if self.non_drop_frame:
            return 'NDF'
        else:
            return 'DF'

class RationalTime(NamedTuple):
    numerator: int
    denominator: int

    @property
    def as_frame(self, frame_rate):
        frame = int((self.numerator * frame_rate[0]) / (self.denominator * frame_rate[1]))
        return frame

    @property
    def as_fraction(self):
        return Fraction(*self)

    @property
    def as_timecode(self, frame_rate, non_drop_frame=True):
        return self._create_timecode_obj(frame_rate, non_drop_frame).tc_to_string

    @property
    def as_fractional_timecode(self, frame_rate, non_drop_frame=True):
        self._create_timecode_obj(frame_rate, non_drop_frame).set_fractional(True)
        fractional_output = self.tc_to_string(*self.frames_to_tc(self.frames))
        return fractional_output

    def _create_timecode_obj(self, frame_rate, non_drop_frame):
        return Timecode(frame_rate, frames=self.as_frame + 1, force_non_drop_frame=non_drop_frame)

class TimecodeFormat(Timecode):

    def __init__(self, frame_rate, time_value, non_drop_frame=True):
        self._frame_rate = frame_rate
        self.frame, self.rational_tuple = self._time_value_helper(time_value)
        super().__init__(frame_rate, frames=self.frame + 1, force_non_drop_frame=non_drop_frame)

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, value):
        if isinstance(value, int):
            self._frame = value
            self.frames = self.frame + 1
        else:
            raise ValueError("frame must be an int")

    @property
    def rational_tuple(self):
        return self._rational_tuple

    @rational_tuple.setter
    def rational_tuple(self, value):
        if isinstance(value, tuple):
            self._rational_tuple = value
        elif isinstance(value, Fraction):
            self._rational_tuple = (value.numerator, value.denominator)
        else:
            raise ValueError("rational_tuple must be set as a Tuple or a Fraction")

    @property
    def rational_fraction(self):
        return Fraction(*self.rational_tuple)

    @property
    def standard_timecode(self):
        # returns standard format timecode as string, copied from Timecode __repr__
        return self.tc_to_string(*self.frames_to_tc(self.frames))

    @property
    def fractional_timecode(self):
        self.set_fractional(True)
        fractional_output = self.tc_to_string(*self.frames_to_tc(self.frames))
        self.set_fractional(False) #unset fractional timecode after grabbing output
        return fractional_output

    @classmethod
    def get_number_of_frames(cls, rational_time_tuple, frame_rate_tuple):
        number_of_frames = int((rational_time_tuple[0] * frame_rate_tuple[0]) / (rational_time_tuple[1] * frame_rate_tuple[1]))

        return number_of_frames

    def _time_value_helper(self, time_value):

        if isinstance(time_value, int):
            int_value = time_value
            rational_value = (time_value * self._frame_rate[1], self._frame_rate[0])
        elif isinstance(time_value, tuple):
            int_value = self.get_number_of_frames(time_value, self._frame_rate)
            rational_value = time_value
        else:
            raise ValueError("start, duration, and offset values must be set as either an integer or rational tuple")

        return int_value, rational_value