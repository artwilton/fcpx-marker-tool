import copy
from pathlib import Path
from common import helpers
from common.projectclasses import ProjectFile, Resource, Timeline, Clip, Container, Marker
from common.timecodeinfo import TimecodeInfo

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
                frame_rate_tuple = self._frame_rate_tuple_from_format(format)
                timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, non_drop_frame)
                project_file.add_resource(Resource(id, name, path, timecode_info))

    def _filter_resource_type(self, resource):
        if resource.tag == 'asset':
            resource = self._handle_asset_resource(resource)
        elif resource.tag == 'media':
            resource = self._handle_media_resource(resource)

        return resource

    def _handle_asset_resource(self, resource):
        id, name, start, duration, format = helpers.get_attributes(resource, 'id', 'name', 'start', 'duration', 'format')
        path = resource.find('./media-rep').get('src')
        non_drop_frame = True # asset resources don't contain info about NDF or DF, so just assume NDF
         
        return id, name, path, start, duration, format, non_drop_frame

    def _handle_media_resource(self, resource):
        id, name = helpers.get_attributes(resource, 'id', 'name')
        path = 'N/A'
        start, duration, format, non_drop_frame = self._filter_media_child_element(resource)

        return id, name, path, start, duration, format, non_drop_frame

    def _filter_media_child_element(self, resource):
        child_element = resource.find('./')
        start, format, non_drop_frame = helpers.get_attributes(child_element, 'tcStart', 'format', 'tcFormat')

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
            frame_rate_tuple = helpers.frame_rate_to_tuple(frame_rate, reverse=True)

        return frame_rate_tuple

    def _frame_rate_tuple_from_format(self, format):
        format_element = self.xml_root.find(f"./resources/format/[@id='{format}']")
        frame_rate_tuple = self._undefined_format_check(format_element)
        
        return frame_rate_tuple
            
    def _create_timecode_info(self, frame_rate_tuple, start, duration, non_drop_frame=True, offset=None, conformed_frame_rate_tuple=None):
        if conformed_frame_rate_tuple is None:
            start = helpers.get_number_of_frames(start, frame_rate_tuple)
        else:
            start = helpers.get_number_of_frames(start, conformed_frame_rate_tuple)
            
        duration = helpers.get_number_of_frames(duration, frame_rate_tuple)
        offset = helpers.get_number_of_frames(offset, frame_rate_tuple)

        timecode_info = TimecodeInfo(frame_rate_tuple, start, duration, non_drop_frame, offset)

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
            parsed_event_child = self._handle_clip_and_marker_creation(event_child, event_clip=True)
        elif event_child.tag == 'project':
            parsed_event_child = self._create_timeline(event_child)

        return parsed_event_child

    def _handle_clip_and_marker_creation(self, clip_element, timeline_obj=None, event_clip=False):
        if event_clip:
            clip_obj = self._create_event_clip(clip_element)
            conformed_frame_rate_tuple = None
        else:
            timeline_frame_rate_tuple, timeline_ndf = timeline_obj.timecode_info.frame_rate_tuple, timeline_obj.timecode_info.non_drop_frame
            conformed_frame_rate_tuple = self._conform_rate_check(clip_element, timeline_obj.timecode_info.frame_rate_number)
            clip_obj = self._create_timeline_clip(clip_element, timeline_frame_rate_tuple, timeline_ndf, conformed_frame_rate_tuple)
            
        self._add_markers_to_clip(clip_element, clip_obj, conformed_frame_rate_tuple)

        return clip_obj

    def _create_event_clip(self, clip_element):
        name, start, duration, offset, type, resource_id = self._get_common_clip_info(clip_element)
        frame_rate_tuple, non_drop_frame = self._get_event_clip_format_info(clip_element, resource_id)
        timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, non_drop_frame, offset)

        clip_obj = Clip(name, type, timecode_info, resource_id)

        return clip_obj

    def _create_timeline_clip(self, clip_element, timeline_frame_rate, timeline_ndf, conformed_frame_rate_tuple=None):
        name, start, duration, offset, type, resource_id = self._get_common_clip_info(clip_element)
        timecode_info = self._create_timecode_info(timeline_frame_rate, start, duration, timeline_ndf, offset, conformed_frame_rate_tuple)

        clip_obj = Clip(name, type, timecode_info, resource_id)

        return clip_obj


    def _get_common_clip_info(self, clip_element):
        name, start, duration, offset = helpers.get_attributes(clip_element, 'name', 'start', 'duration', 'offset')
        type = clip_element.tag
        resource_id = self._get_resource_id(clip_element)

        return  name, start, duration, offset, type, resource_id

    def _get_event_clip_format_info(self, clip_element, resource_id):
        format = clip_element.get('format')

        if format:
            frame_rate = self._frame_rate_tuple_from_format(format)
            non_drop_frame = clip_element.get('tcFormat')
        else:
            frame_rate, non_drop_frame = self._parse_ref_info(resource_id)
            
        return frame_rate, non_drop_frame

    def _conform_rate_check(self, clip_element, timeline_frame_rate_number):
        conform_rate = clip_element.find('./conform-rate')

        if conform_rate is not None and conform_rate.get('scaleEnabled') != "0":
            source_frame_rate = conform_rate.get('srcFrameRate')
            conformed_frame_rate = self._parse_conformed_frame_rate(timeline_frame_rate_number, source_frame_rate)
        else:
            conformed_frame_rate = None

        return conformed_frame_rate

    def _parse_conformed_frame_rate(self, timeline_frame_rate_number, source_frame_rate):
        # Matches up values based on Apple's documentation:
        # https://developer.apple.com/documentation/professional_video_applications/fcpxml_reference/story_elements/conform-rate

        # making fps 25 for testing purposes until completed
        # conformed_frame_rate = '25'
        conformed_frame_rate = self._conform_rate_lookup(timeline_frame_rate_number, source_frame_rate)
        conformed_frame_rate_tuple = helpers.frame_rate_to_tuple(conformed_frame_rate)

        return conformed_frame_rate_tuple

    def _conform_rate_lookup(self, timeline_frame_rate, source_frame_rate):

        CONFORM_RATE_DICTIONARY = {
            # timeline_frame_rate: {source_frame_rate: conformed_frame_rate_tuple}
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
            conformed_frame_rate_tuple = timeline_frame_rate_match.get(source_frame_rate)
        else:
            conformed_frame_rate_tuple = None

        return conformed_frame_rate_tuple

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
                frame_rate = resource.timecode_info.frame_rate_tuple
                non_drop_frame = resource.timecode_info.non_drop_frame
                break

        return frame_rate, non_drop_frame

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
        name, timecode_info = self._get_timeline_info(timeline_element)
        timeline_obj = Timeline(name, timecode_info)
        self._handle_timeline_clip_creation(timeline_element, timeline_obj)

        return timeline_obj

    def _get_timeline_info(self, timeline_element):
        name = timeline_element.get('name')
        sequence_element = timeline_element.find('./sequence')
        start, duration, format, non_drop_frame = helpers.get_attributes(sequence_element, 'tcStart','duration', 'format', 'tcFormat')
        frame_rate_tuple = self._frame_rate_tuple_from_format(format)
        timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, non_drop_frame)

        return name, timecode_info

    def _add_clips_and_markers_to_timeline(self, timeline_obj, primary_clip, connected_clip=None):
        if connected_clip:
            clip_obj = connected_clip
            clip_obj.timecode_info.offset += primary_clip.timecode_info.offset
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
            offset, lane = helpers.get_attributes(clip_element, 'offset', 'lane')
            updated_clip = clip_element.find('./')
            
            updated_clip.set('offset', offset)
            if lane is not None:
                updated_clip.set('lane', lane)
                
            return updated_clip
        else:
            return clip_element

    def _add_markers_to_clip(self, clip_element, clip_obj, conformed_frame_rate_tuple):
        for child_element in clip_element.iterfind('./'):
            if child_element.tag.endswith('marker'):
                marker = self._create_marker(child_element, clip_obj, conformed_frame_rate_tuple)
                clip_obj.add_marker(marker)

    def _create_marker(self, marker_element, clip_obj, conformed_frame_rate_tuple):
        frame_rate_tuple, non_drop_frame = clip_obj.timecode_info.frame_rate_tuple, clip_obj.timecode_info.non_drop_frame
        start, duration, name, completed, offset = helpers.get_attributes(marker_element, 'start', 'duration', 'value', 'completed', 'offset')

        if completed is not None:
            completed = bool(completed)
            marker_type = "to-do"
        else:
            marker_type = marker_element.tag
        
        timecode_info = self._create_timecode_info(frame_rate_tuple, start, duration, non_drop_frame, offset, conformed_frame_rate_tuple)

        return Marker(name, marker_type, timecode_info, completed)

    def _add_markers_to_timeline(self, timeline_obj, clip_obj):
        for marker in clip_obj.markers:
            marker_start = marker.timecode_info.start
            clip_start, clip_offset, clip_duration = clip_obj.timecode_info.start, clip_obj.timecode_info.offset, clip_obj.timecode_info.duration
            clip_end = clip_offset + clip_duration
            marker_timeline_start = (marker_start - clip_start) + clip_offset

            if (marker_timeline_start >= clip_offset) and (marker_timeline_start <= clip_end):
                timeline_marker = copy.deepcopy(marker)
                timeline_marker.timecode_info.start = marker_timeline_start
                timeline_obj.add_marker(timeline_marker)

    def parse_xml(self):
        self._create_resources(self.project_file)
        self._create_containers(self.project_file)

        return self.project_file

        # Tests
        # resources = self.project_file.resources
        # for resource in resources:
        #     print(f"{resource.name}, {resource.id}, {resource.timecode_info.frame_rate}")