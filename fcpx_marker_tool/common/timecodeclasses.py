from fractions import Fraction
from typing import NamedTuple
from timecode import Timecode

class TimecodeInfo:

    def __init__(self, frame_rate, start, duration, offset=0, non_drop_frame=True):
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps.
        self.start = start # Start time for video/audio element
        self.duration = duration # Total length of time for video/audio element
        self.offset = offset # Start time within a timeline, default is 0 since not everything has an offset
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
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = RationalTime(self._check_for_tuple(value))

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = RationalTime(self._check_for_tuple(value))

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = RationalTime(self._check_for_tuple(value))

    @property
    def format(self):
        if self.non_drop_frame:
            return 'NDF'
        else:
            return 'DF'

    def _check_for_tuple(self, time_value):

        if isinstance(time_value, int):
            rational_value = (time_value * self._frame_rate[1], self._frame_rate[0])
        elif isinstance(time_value, tuple):
            rational_value = time_value
        else:
            raise ValueError("start, duration, and offset values must be set as either an integer or rational tuple")

        return rational_value

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

# TEMP CLASS FOR REFERENCE
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