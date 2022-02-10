def split_and_remove_s(rational_time_string):
    rational_time_string = rational_time_string.replace("s", "")
    #Handles rational time represented as fractions or whole numbers, FCPX rounds down rational numbers when possible
    if "/" in rational_time_string:
        rational_time_tuple = tuple(map(int, rational_time_string.split("/")))
    else:
        rational_time_tuple = (int(rational_time_string), 1)

    return rational_time_tuple

def frame_rate_to_tuple(frame_rate, reverse=False):
# Preps framerate for timecode module, ex: the string "1001/30000s" becomes a tuple (30000, 1001) when reverse is True
    frame_rate = split_and_remove_s(frame_rate)

    if reverse:
        frame_rate = (frame_rate[1], frame_rate[0])
    else:
        frame_rate = (frame_rate[0], frame_rate[1])

    return frame_rate

def get_number_of_frames(rational_time_string, frame_rate_tuple):
    # Handle typical ways that frame 0 is represented and return early. "0s" and None will be common in FCPX, "0" in FCP7
    if rational_time_string in {"0s", "0", 0, None}:
        return 0

    rational_time_tuple = split_and_remove_s(rational_time_string)
    number_of_frames = int((rational_time_tuple[0] * frame_rate_tuple[0]) / (rational_time_tuple[1] * frame_rate_tuple[1]))

    return number_of_frames