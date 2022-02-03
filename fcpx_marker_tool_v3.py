import xml.etree.ElementTree as ET
from timecode import Timecode

#This refactor will be built with the idea of making code more scalable, with future ability to import xml files from more than just FCPX

class TimecodeInfo:

    def __init__(self, id, frame_rate, start, duration, non_drop_frame):
        self.id = id # can be anything useful, example is "Format id" for FCPX
        self.frame_rate = frame_rate # can be rational string like '30000/1001', rational tuple (30000, 1001), int 30, or float 29.97
        # as notated in the Timecode module, frame_rate should be one of ['23.976', '23.98', '24', '25', '29.97', '30', '50', '59.94', '60', 'NUMERATOR/DENOMINATOR', ms'] where "ms" is equal to 1000 fps. 
        self.start = start # int representing start frame
        self.duration = duration # int for total amount of frames
        self.non_drop_frame = non_drop_frame # Boolean, True for NDF and False for DF
        self._timecode = Timecode(frame_rate, frames=(start + 1), force_non_drop_frame=non_drop_frame)
    
    @property
    def frame_rate_number(self):
        return self._timecode.framerate

    @property
    def frame_rate_tuple(self):
        # method that will return a rational number tuple version regardless of how TimecodeInfo class is instantiated
        pass

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

class Resource:

    # allows shared characteristics between multiple types of xml imports

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

def main():
    tc = TimecodeInfo("12", (30000, 1001),10,10,True )
    print(tc.standard_timecode, tc.id, tc.frame_rate_number)

if __name__ == "__main__":
    main()