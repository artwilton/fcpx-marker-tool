import copy
from fractions import Fraction
from pathlib import Path
from common.projectclasses import ProjectFile, Resource, Timeline, Clip, Container, Marker, TimecodeInfo, TimecodeFormat

class FCPXParser:

    def __init__(self, xml_root):
        self.xml_root = xml_root
        self._project_file = self._create_project_file()

    # PROJECT FILE
    @property
    def project_file(self):
        return self._project_file

    def _create_project_file(self):
        name, path = self._get_project_info()
        return ProjectFile(name, path)

    def _get_project_info(self):
        try:
            library = self.xml_root.find('library')
        except:
            print("'library' element not found")

        path = library.get('location')
        name = Path(path).name

        return name, path

    # RESOURCES
    def _create_resources(self, project_file):
        try:
            resources = self.xml_root.find('resources')
        except:
            print("'resources' element not found")

        for resource in resources:
            if resource.tag == 'asset' or resource.tag == 'media':
                id, name, path, start, duration, format, non_drop_frame = self._filter_resource_type(resource)
                frame_rate_tuple, interlaced = self._frame_info_from_format(format)
                timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, offset=0, non_drop_frame=non_drop_frame)
                project_file.add_resource(Resource(id, name, path, timecode_info, interlaced))

    def _filter_resource_type(self, resource):
        if resource.tag == 'asset':
            resource = self._handle_asset_resource(resource)
        elif resource.tag == 'media':
            resource = self._handle_media_resource(resource)

        return resource

    def _handle_asset_resource(self, resource):
        id, name, start, duration, format = self._get_attributes(resource, 'id', 'name', 'start', 'duration', 'format')
        path = resource.find('./media-rep').get('src')
        non_drop_frame = True # asset resources don't contain info about NDF or DF, so just assume NDF
         
        return id, name, path, start, duration, format, non_drop_frame

    def _handle_media_resource(self, resource):
        id, name = self._get_attributes(resource, 'id', 'name')
        path = 'N/A'
        start, duration, format, non_drop_frame = self._filter_media_child_element(resource)

        return id, name, path, start, duration, format, non_drop_frame

    def _filter_media_child_element(self, resource):
        child_element = resource.find('./')
        start, format, non_drop_frame = self._get_attributes(child_element, 'tcStart', 'format', 'tcFormat')

        if child_element.tag == 'multicam':
            duration = 0 # Multicam duration is not listed, can create logic later to determine this if necessary
        else:
            duration = child_element.get('duration')

        return start, duration, format, non_drop_frame

    def _undefined_format_check(self, format_element):
        # audio only resources don't have format tags, image resources have format tags that point to "FFVideoFormatRateUndefined"
        # FCPX assumes 60fps or 6000/100 for these resources when dealing with frame rates
        if format_element is None or format_element.get('name') == "FFVideoFormatRateUndefined":
            frame_rate_tuple = (6000, 100)
        else:
            frame_rate = format_element.get('frameDuration')
            frame_rate_tuple = self._parse_frame_info(frame_rate, reverse=True)

        return frame_rate_tuple

    def _frame_info_from_format(self, format):
        format_element = self.xml_root.find(f"./resources/format/[@id='{format}']")
        frame_rate_tuple = self._undefined_format_check(format_element)
        interlaced = self._interlaced_info_from_format(format_element)

        return frame_rate_tuple, interlaced

    def _interlaced_info_from_format(self, format_element):
        if format_element is None:
            return False
        else:
            interlaced_check = format_element.get('fieldOrder')
            
        if (interlaced_check == "upper first") or (interlaced_check == "lower first"):
            interlaced = True
        else:
            interlaced = False

        return interlaced

    def _create_timecode_info(self, frame_rate, start, duration, offset, non_drop_frame=True, conformed_frame_rate=None):
        
        start_tuple = self._parse_frame_info(start)
        duration_tuple = self._parse_frame_info(duration)
        offset_tuple = self._parse_frame_info(offset)

        timecode_info = TimecodeInfo(frame_rate, start_tuple, duration_tuple, offset_tuple, non_drop_frame)

        if conformed_frame_rate is not None:
            updated_frame = TimecodeFormat.get_number_of_frames(start_tuple, conformed_frame_rate)
            timecode_info.update_start_frame(updated_frame)
        
        return timecode_info

    # EVENTS
    def _parse_event(self, event):
        # parse clip and project elements, return an array of Clip and Timeline objects
        event_children = []
        for event_child in event:
            event_children.append(self._parse_event_children(event_child))
        return event_children
    
    def _parse_event_children(self, event_child):
        if event_child.tag.endswith('clip'):
            parsed_event_child = self._handle_clip_and_marker_creation(event_child)
            # self._add_markers_to_clip(event_child, parsed_event_child)
        elif event_child.tag == 'project':
            parsed_event_child = self._create_timeline(event_child)

        return parsed_event_child

    def _format_conformed_frame_rate(self, timeline_frame_rate_string, timeline_interlaced):
        if timeline_interlaced:
            timeline_frame_rate_string += 'i'
        else:
            timeline_frame_rate_string += 'p'
        
        return timeline_frame_rate_string

    def _validate_resource(self, resource_id):
        resource_element = self.xml_root.find(f"./resources/*[@id='{resource_id}']")

        if (resource_element is not None) and (resource_element.tag in {'media', 'asset'}):
            return resource_id
        else:
            return None

    def _handle_clip_and_marker_creation(self, clip_element, timeline_obj=None):
        name, start, duration, offset, type, resource_id = self._get_common_clip_info(clip_element)
        frame_rate_tuple, non_drop_frame, interlaced = self._get_clip_format_info(clip_element, resource_id, timeline_obj)

        if timeline_obj is not None:
            timeline_frame_rate_string = timeline_obj.timecode_info.frame_rate_string
            timeline_frame_rate_tuple = timeline_obj.timecode_info.frame_rate
            timeline_interlaced = timeline_obj.interlaced
            conformed_frame_rate = self._conform_rate_check(clip_element, timeline_frame_rate_tuple, timeline_frame_rate_string, timeline_interlaced)
            timecode_info = self._create_timecode_info(timeline_frame_rate_tuple, start, duration, offset, non_drop_frame, conformed_frame_rate)
            timecode_info.update_frame_rate(frame_rate_tuple) # set frame_rate back to Clip frame rate after using Timeline frame rate for calculating start time
        else:
            timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, offset, non_drop_frame)
            conformed_frame_rate = None

        clip_obj = Clip(name, type, timecode_info, interlaced, resource_id)
        self._add_markers_to_clip(clip_element, clip_obj, conformed_frame_rate)

        return clip_obj

    def _get_common_clip_info(self, clip_element):
        name, start, duration, offset = self._get_attributes(clip_element, 'name', 'start', 'duration', 'offset')
        type = clip_element.tag
        resource_id = self._get_resource_id(clip_element)
        resource_id = self._validate_resource(resource_id)

        return  name, start, duration, offset, type, resource_id

    def _get_clip_format_info(self, clip_element, resource_id, timeline_obj=None):
        format = clip_element.get('format')

        if format:
            frame_rate_tuple, interlaced = self._frame_info_from_format(format)
            non_drop_frame = clip_element.get('tcFormat')
        elif resource_id is not None:
            frame_rate_tuple, non_drop_frame, interlaced = self._parse_ref_info(resource_id)
        else:
            frame_rate_tuple = timeline_obj.timecode_info.frame_rate
            non_drop_frame = timeline_obj.timecode_info.non_drop_frame
            interlaced = timeline_obj.interlaced
            
        return frame_rate_tuple, non_drop_frame, interlaced

    def _conform_rate_check(self, clip_element, timeline_frame_rate_tuple, timeline_frame_rate_string, timeline_interlaced):
        conform_rate = clip_element.find('./conform-rate')

        if conform_rate is not None and conform_rate.get('scaleEnabled') != "0":
            source_frame_rate = conform_rate.get('srcFrameRate')
            timeline_frame_rate_formatted = self._format_conformed_frame_rate(timeline_frame_rate_string, timeline_interlaced)
            conformed_frame_rate = self._parse_conformed_frame_rate(timeline_frame_rate_formatted, source_frame_rate)
        else:
            conformed_frame_rate = timeline_frame_rate_tuple

        return conformed_frame_rate

    def _parse_conformed_frame_rate(self, timeline_frame_rate, source_frame_rate):
        # Matches up values based on Apple's documentation:
        # https://developer.apple.com/documentation/professional_video_applications/fcpxml_reference/story_elements/conform-rate

        CONFORM_RATE_DICTIONARY = {
            # timeline_frame_rate: {source_frame_rate: conformed_frame_rate}
            '23.98p': {'24': (2400, 100), '25': (2500, 100), '50': (2500, 100)},
            '24p': {'23.98': (24000, 1001), '25': (2500, 100), '50': (2500, 100)},
            '25p': {'23.98': (24000, 1001), '24': (2400, 100)},
            '29.97p': {'30': (3000, 100), '60': (3000, 100)},
            '30p': {'29.97': (30000, 1001), '59.94': (30000, 1001)},
            '50p': {'23.98': (48000, 1001), '24': (4800, 100)},
            '59.94p': {'30': (6000, 100), '60': (6000, 100)},
            '60p': {'29.97': (60000, 1001), '59.94': (60000, 1001)},
            '25i': {'23.98': (48000, 1001), '24': (4800, 100)},
            '29.97i': {'30': (6000, 100), '60': (6000, 100)}
        }

        timeline_frame_rate_match = CONFORM_RATE_DICTIONARY.get(timeline_frame_rate)

        if timeline_frame_rate_match is not None:
            conformed_frame_rate = timeline_frame_rate_match.get(source_frame_rate)
        else:
            conformed_frame_rate = timeline_frame_rate

        return conformed_frame_rate

    def _get_resource_id(self, clip_element):
        resource_id = clip_element.get('ref')

        if resource_id is None:
            # resource_id will be None if element is a 'gap' or 'sync-clip' so just return early
            if clip_element.tag == 'gap' or clip_element.tag == 'sync-clip':
                return resource_id

            # Find the first child that is not a <conform-rate> element
            clip_children = clip_element.findall('./')
            if clip_children[0].tag != 'conform-rate':
                clip_child = clip_children[0]
            else:
                clip_child = clip_children[1]

            # Grab 'ref' based on if a clip is a 'video' element or a 'gap' with a nested 'audio' element
            if clip_child.tag == 'video':
                resource_id = clip_child.get('ref')
            elif clip_child.tag == 'gap' and clip_child.find('./audio/[@ref]'):
                resource_id = clip_child.find('./audio').get('ref')

        return resource_id

    def _parse_ref_info(self, resource_id):
        # Find Resource with an id matching 'ref', grab the frame rate and tcformat from there.
        for resource in self.project_file.resources:
            if resource.id == resource_id:
                frame_rate = resource.timecode_info.frame_rate
                non_drop_frame = resource.timecode_info.non_drop_frame
                interlaced = resource.interlaced
                break

        return frame_rate, non_drop_frame, interlaced

    def _parse_non_drop_frame(self, timecode_format):
        # easiest to make anything that isn't 'DF' True, since 'NDF' is most common and this will catch if timecode_format is None
        if timecode_format == 'DF':
            return False
        else:
            return True

    # CONTAINERS
    def _create_containers(self, project_file):
        events = self.xml_root.findall('./library/event')

        for event in events:
            event_children = self._parse_event(event)
            event_container = Container(event.get("name"), event_children)
            project_file.root_container.add_child(event_container)

    # TIMELINES
    def _create_timeline(self, timeline_element):
        # Grab metadata, create timeline instance
        name, timecode_info, interlaced = self._get_timeline_info(timeline_element)
        timeline_obj = Timeline(name, timecode_info, interlaced)
        self._handle_timeline_clip_creation(timeline_element, timeline_obj)

        return timeline_obj

    def _get_timeline_info(self, timeline_element):
        name = timeline_element.get('name')
        sequence_element = timeline_element.find('./sequence')
        start, duration, format, non_drop_frame = self._get_attributes(sequence_element, 'tcStart','duration', 'format', 'tcFormat')
        frame_rate_tuple, interlaced = self._frame_info_from_format(format)
        timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, offset=0, non_drop_frame=non_drop_frame)

        return name, timecode_info, interlaced

    def _add_clips_and_markers_to_timeline(self, timeline_obj, primary_clip, connected_clip=None):
        if connected_clip:
            connected, primary = connected_clip.timecode_info, primary_clip.timecode_info
            connected.offset = connected.offset + primary.offset - primary.start
            connected_fraction = Fraction(*connected.offset_rational) + (Fraction(*primary.offset_rational) - Fraction(*primary.start_rational))
            connected.offset_rational = (connected_fraction.numerator, connected_fraction.denominator)
            clip_obj = connected_clip

        else:
            clip_obj = primary_clip

        timeline_obj.add_clip(clip_obj)
        self._add_markers_to_timeline(timeline_obj, clip_obj)

    def _handle_timeline_clip_creation(self, timeline_element, timeline_obj):

        primary_clips = timeline_element.iterfind('./sequence/spine/')
        primary_clips_formatted = [self._check_for_audition(clip) for clip in primary_clips]

        for primary_clip in primary_clips_formatted:
            primary_clip_obj = self._handle_clip_and_marker_creation(primary_clip, timeline_obj)
            self._add_clips_and_markers_to_timeline(timeline_obj, primary_clip_obj)

            for connected_clip in primary_clip.iterfind('*[@lane]'):
                connected_clip_formatted = self._check_for_audition(connected_clip)
                connected_clip_obj = self._handle_clip_and_marker_creation(connected_clip_formatted, timeline_obj)
                self._add_clips_and_markers_to_timeline(timeline_obj, primary_clip_obj, connected_clip_obj)

    def _check_for_audition(self, clip_element):
        if clip_element.tag == 'audition':
            offset, lane = self._get_attributes(clip_element, 'offset', 'lane')
            updated_clip = clip_element.find('./')
            
            updated_clip.set('offset', offset)
            if lane is not None:
                updated_clip.set('lane', lane)
                
            return updated_clip
        else:
            return clip_element

    def _add_markers_to_clip(self, clip_element, clip_obj, conformed_frame_rate=None):
        for child_element in clip_element.iterfind('./'):
            if child_element.tag.endswith('marker'):
                marker = self._create_marker(child_element, clip_obj, conformed_frame_rate)
                clip_obj.add_marker(marker)

    def _create_marker(self, marker_element, clip_obj, conformed_frame_rate=None):
        frame_rate_tuple, non_drop_frame = clip_obj.timecode_info.frame_rate, clip_obj.timecode_info.non_drop_frame
        start, duration, name, completed, offset = self._get_attributes(marker_element, 'start', 'duration', 'value', 'completed', 'offset')

        if completed is not None:
            completed = bool(int(completed))
            marker_type = "to-do"
        else:
            marker_type = marker_element.tag
        
        timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, offset, non_drop_frame, conformed_frame_rate)

        return Marker(name, marker_type, timecode_info, completed)

    def _add_markers_to_timeline(self, timeline_obj, clip_obj):
        for marker in clip_obj.markers:
            marker_start_frame = marker.timecode_info.start
            clip_time = clip_obj.timecode_info
            clip_start_frame, clip_offset_frame = clip_time.start, clip_time.offset
            marker_timeline_start_frame = (marker_start_frame - clip_start_frame) + clip_offset_frame
            # compare rational time values for accuracy
            clip_start_fraction, clip_offset_fraction, clip_duration_fraction = Fraction(*clip_time.start_rational), Fraction(*clip_time.offset_rational), Fraction(*clip_time.duration_rational)
            clip_end_fraction = clip_offset_fraction + clip_duration_fraction
            marker_start_fraction = Fraction(*marker.timecode_info.start_rational)
            marker_timeline_start_fraction = (marker_start_fraction - clip_start_fraction) + clip_offset_fraction

            if (marker_timeline_start_fraction >= clip_offset_fraction) and (marker_timeline_start_fraction < clip_end_fraction):
                timeline_marker = copy.deepcopy(marker)
                timeline_marker.timecode_info.update_start_frame(marker_timeline_start_frame)
                timeline_marker.timecode_info.start_rational = (marker_timeline_start_fraction.numerator, marker_timeline_start_fraction.denominator)
                timeline_marker.timecode_info.update_frame_rate(timeline_obj.timecode_info.frame_rate)
                timeline_obj.add_marker(timeline_marker)


    # HELPERS
    def _parse_frame_info(self, frame_info, reverse=False):
        # Preps frame info for timecode module, ex: the string "1001/30000s" becomes a tuple (30000, 1001) if reverse=True, while a string "10s" becomes (10,1)

        # Handle typical ways that frame 0 is represented and return early. "0s" and None will be common in FCPX
        if frame_info in {"0s", "0", 0, None}:
            return (0,1)

        frame_info_string = frame_info.replace("s", "")

        if "/" in frame_info_string:
            frame_info_tuple = tuple(map(int, frame_info_string.split("/")))
            
        else:
            try:
                frame_info_tuple = (int(frame_info_string), 1)
            except ValueError:
                raise ValueError("start, duration, and offset values must be set as either an integer or rational tuple")

        return (frame_info_tuple[1], frame_info_tuple[0]) if reverse else frame_info_tuple

    def _get_attributes(self, element, *args):
        attribute_value = [element.get(arg) for arg in args]
        return attribute_value

    def parse_xml(self):
        self._create_resources(self.project_file)
        self._create_containers(self.project_file)

        return self.project_file