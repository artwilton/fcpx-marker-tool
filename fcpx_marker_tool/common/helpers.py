def split_and_remove_s(rational_time_string):
        rational_time_string = rational_time_string.replace("s", "")
        rational_time_tuple = tuple(map(int, rational_time_string.split("/")))

        return rational_time_tuple

def frame_rate_to_tuple(frame_rate):
# Preps framerate for timecode module, ex: the string "1001/30000s" becomes a tuple (30000, 1001)
    frame_rate = split_and_remove_s(frame_rate)
    frame_rate = (frame_rate[1], frame_rate[0])

    return frame_rate