from timecode import Timecode

class TimecodeInfo:

    def __init__(self, frame_rate, start, duration, non_drop_frame=True, offset=None, rational_start=None, rational_duration=None):
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps.
        self.start = start # int representing start frame number
        self.duration = duration # int for total amount of frames
        self.non_drop_frame = non_drop_frame # Boolean, True for NDF and False for DF
        self.offset = offset # int representing start frame within a timeline, optional because usually only clips have this property
        self._timecode = Timecode(frame_rate, frames=(start + 1), force_non_drop_frame=non_drop_frame)
        # rational_start and rational_duration are optional but can be used to store the original rational number info
        self.rational_start = rational_start
        self.rational_duration = rational_duration

    @property
    def frame_rate_number(self):
        return self._timecode.framerate

    @property
    def frame_rate_tuple(self):
        # method that will return a rational number tuple version regardless of how TimecodeInfo class is instantiated
        # for now it just returns frame_rate because the FCPX parser assigns frame_rate as a tuple
        return self.frame_rate

    @property
    def rational_start(self):
        return self._rational_start

    @rational_start.setter
    def rational_start(self, value):
        if (value is not None) and (type(value) is tuple):
            self._rational_start = value
        elif value is not None:
            raise ValueError("rational_start must be a tuple containting integers ex: (24000, 1001)")
        else:
            self._rational_start = (self.frame_rate_tuple[0], int(self.start * self.frame_rate_tuple[1]))

    @property
    def rational_duration(self):
        return self._rational_duration

    @rational_duration.setter
    def rational_duration(self, value):
        if (value is not None) and (type(value) is tuple):
            self._rational_duration = value
        elif value is not None:
            raise ValueError("rational_duration must be a tuple containting integers ex: (24000, 1001)")
        else:
            self._rational_duration = (self.frame_rate_tuple[0], int(self.duration * self.frame_rate_tuple[1]))

    @property
    def standard_timecode(self):
        return str(self._timecode)

    @property
    def fractional_timecode(self):
        self._timecode.set_fractional(True)
        fractional_output = str(self._timecode)
        self._timecode.set_fractional(False) #unset fractional timecode after grabbing output
        return fractional_output

    @property
    def format(self):
        if self.non_drop_frame:
            return 'NDF'
        else:
            return 'DF'