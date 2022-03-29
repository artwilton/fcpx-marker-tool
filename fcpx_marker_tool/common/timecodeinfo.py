from timecode import Timecode

class TimecodeInfo:

    def __init__(self, frame_rate, start, duration, offset=0, non_drop_frame=True):
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps.
        self.start, self.start_rational = self._time_value_helper(start) # Start time for video/audio element
        self.duration, self.duration_rational = self._time_value_helper(duration) # Total length of time for video/audio element
        self.offset, self.offset_rational = self._time_value_helper(offset) # Start time within a timeline, default is 0 since not everything has an offset
        # start, duration, and offset can be set with an int (frames) or tuple (rational time). Default will be to return an int.
        # Use start_rational, duration_rational, and offset_rational to return a rational tuple as necessary.
        self.non_drop_frame = non_drop_frame # Boolean, True for NDF and False for DF
        self._timecode = Timecode(frame_rate, frames=(self.start + 1), force_non_drop_frame=non_drop_frame)

    @classmethod
    def get_number_of_frames(cls, rational_time_tuple, frame_rate_tuple):
        number_of_frames = int((rational_time_tuple[0] * frame_rate_tuple[0]) / (rational_time_tuple[1] * frame_rate_tuple[1]))

        return number_of_frames

    @property
    def frame_rate_number(self):
        return self._timecode.framerate

    @property
    def frame_rate_tuple(self):
        # method that will return a rational number tuple version regardless of how TimecodeInfo class is instantiated
        # for now it just returns frame_rate because the FCPX parser assigns frame_rate as a tuple
        return self.frame_rate

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

    # update frame_rate and keep _timecode in sync when updating frame_rate in FCPX clips
    def update_frame_rate(self, frame_rate_tuple):
        try:
            self.frame_rate = frame_rate_tuple
            self._timecode.framerate = frame_rate_tuple
        except AttributeError:
            self._timecode = Timecode(frame_rate_tuple, frames=(self.start + 1), force_non_drop_frame=self.non_drop_frame)

    # update start and keep _timecode in sync when re-calculating start frame in FCPX clips, does not re-calculate start_rational
    def update_start_frame(self, start_frame_int):
        try:
            self.start = start_frame_int
            self._timecode.frames=(start_frame_int + 1)
        except AttributeError:
            self._timecode = Timecode(self.frame_rate, frames=(start_frame_int + 1), force_non_drop_frame=self.non_drop_frame)

    def _time_value_helper(self, time_value):

        if isinstance(time_value, int):
            int_value = time_value
            rational_value = (time_value * self.frame_rate_tuple[1], self.frame_rate_tuple[0])
        elif isinstance(time_value, tuple):
            int_value = self.get_number_of_frames(time_value, self.frame_rate_tuple)
            rational_value = time_value
        else:
            raise ValueError("start, duration, and offset values must be set as either an integer or rational tuple")

        return int_value, rational_value