import xml.etree.ElementTree as ET
from timecode import Timecode

#This refactor will be built with the idea of making code more scalable, with future ability to import xml files from more than just FCPX

class TimecodeInfo():

    def __init__(self, id, frame_rate, start, duration, format):
        self.id = id # can be anything useful, example is "Format id" for FCPX
        self.frame_rate = frame_rate # use Timecode module methods to grab this
        self.start = start # int representing start frame (use Timecode module methods to grab this)
        self.duration = duration # int for amount of frames
        self.format = format # NDF or DF
    
    @property
    def frame_rate(self):
        return self._frame_rate

    @frame_rate.setter
    def frame_rate(self, value):
        self._frame_rate = value