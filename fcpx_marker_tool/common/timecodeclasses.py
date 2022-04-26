from fractions import Fraction
from typing import NamedTuple
from timecode import Timecode

class TimecodeInfo:

    def __init__(self, frame_rate, start, duration, offset=0, non_drop_frame=True, conformed_frame_rate=None):
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps.
        self.conformed_frame_rate = conformed_frame_rate # Optional, but NLEs like FCPX will sometimes calculate frame number based on a conformed frame rate
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
    def conformed_frame_rate(self):
        # return conformed frame rate as tuple of ints, ex: (30000, 1001)
        # need to create a setter that ensures conformed_frame_rate gets set as a tuple, but for now the FCPX parser already does this by default
        return self._conformed_frame_rate

    @conformed_frame_rate.setter
    def conformed_frame_rate(self, value):
        self._conformed_frame_rate = value

    @property
    def frame_rate_string(self):
        # return SMPTE standard frame rate as a string, ex: '29.97'
        return Timecode(self._frame_rate).framerate
        
    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = RationalTime(*self._check_for_tuple(value))

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = RationalTime(*self._check_for_tuple(value))

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = RationalTime(*self._check_for_tuple(value))

    @property
    def format(self):
        if self.non_drop_frame:
            return 'NDF'
        else:
            return 'DF'

    @property
    def conform_rate_check(self):
        return False if self.conformed_frame_rate is None else True

    def _check_for_tuple(self, time_value):

        frame_rate = self.conformed_frame_rate if self.conform_rate_check else self.frame_rate

        if isinstance(time_value, int):
            rational_value = (time_value * frame_rate[1], frame_rate[0])
        elif isinstance(time_value, tuple):
            rational_value = time_value
        elif isinstance(time_value, Fraction):
            rational_value = (time_value.numerator, time_value.denominator)
        else:
            raise ValueError("start, duration, and offset values must be set as an integer, rational tuple, rational fraction")

        return rational_value

class RationalTime(NamedTuple):
    numerator: int
    denominator: int

    @property
    def as_fraction(self):
        return Fraction(*self)

    def as_frame(self, frame_rate):
        frame = int((self.numerator * frame_rate[0]) / (self.denominator * frame_rate[1]))
        return frame

    def as_timecode(self, frame_rate, non_drop_frame=True):
        timecode_obj = self._create_timecode_obj(frame_rate, non_drop_frame)
        # returns standard format timecode as string, copied from Timecode __repr__
        return timecode_obj.tc_to_string(*timecode_obj.frames_to_tc(timecode_obj.frames))

    def as_fractional_timecode(self, frame_rate, non_drop_frame=True):
        timecode_obj = self._create_timecode_obj(frame_rate, non_drop_frame)
        timecode_obj.set_fractional(True)
        # returns fractional timecode as string, copied from Timecode __repr__
        return timecode_obj.tc_to_string(*timecode_obj.frames_to_tc(timecode_obj.frames))

    def as_hr_min_sec(self, frame_rate, non_drop_frame=True):
        timecode_obj = self._create_timecode_obj(frame_rate, non_drop_frame)
        hr, min, sec = (lambda *args: [str(arg).zfill(2) for arg in args])(timecode_obj.hrs, timecode_obj.mins, timecode_obj.secs)
        return f"{hr + ':' if hr != '00' else ''}{min}:{sec}"

    def _create_timecode_obj(self, frame_rate, non_drop_frame):
        return Timecode(frame_rate, frames=self.as_frame(frame_rate) + 1, force_non_drop_frame=non_drop_frame)