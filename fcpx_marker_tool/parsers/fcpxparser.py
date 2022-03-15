from pathlib import Path
import resource
from common import helpers
from common.projectclasses import ProjectFile, Resource, Timeline, Clip, Container
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
                frame_rate = self._frame_rate_from_format(format)
                timecode_info = self._create_timecode_info(frame_rate, start, duration, non_drop_frame)
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
            frame_rate = (6000, 100)
        else:
            frame_rate = format_element.get('frameDuration')
            frame_rate = helpers.frame_rate_to_tuple(frame_rate, reverse=True)

        return frame_rate

    def _frame_rate_from_format(self, format):
        format_element = self.xml_root.find(f"./resources/format/[@id='{format}']")
        frame_rate = self._undefined_format_check(format_element)
        
        return frame_rate
            
    def _create_timecode_info(self, frame_rate, start, duration, non_drop_frame=True, offset=None, conformed_frame_rate=None):
        if conformed_frame_rate is None:
            start = helpers.get_number_of_frames(start, frame_rate)
        else:
            start = helpers.get_number_of_frames(start, conformed_frame_rate)
            
        duration = helpers.get_number_of_frames(duration, frame_rate)

        timecode_info = TimecodeInfo(frame_rate, start, duration, non_drop_frame, offset)

        return timecode_info

    # EVENTS
    def _parse_event(self, event):
        # parse clip and project elements, return an array of Clip and Timeline objects
        event_children = []
        for event_child in event:
            event_children.append(self._filter_event_children(event_child))
        return event_children
    
    def _filter_event_children(self, event_child):
        if event_child.tag.endswith('clip'):
            event_child = self._handle_clip_creation(event_child, event_clip=True)
        elif event_child.tag == 'project':
            event_child = self._create_timeline(event_child)

        return event_child

    def _handle_clip_creation(self, clip_element, timeline_frame_rate=None, timeline_ndf=None, event_clip=False):
        name, start, duration, offset = helpers.get_attributes(clip_element, 'start', 'name', 'duration', 'offset')
        type = clip_element.tag
        resource_id = self._get_resource_id(clip_element)
        
        if event_clip:
            frame_rate, non_drop_frame = self._get_event_clip_format_info(clip_element, resource_id)
            conformed_frame_rate = None
        else:
            frame_rate = timeline_frame_rate
            non_drop_frame = timeline_ndf
            conformed_frame_rate = self._get_timeline_clip_format_info(clip_element)

        timecode_info = self._create_timecode_info(frame_rate, start, duration, non_drop_frame, offset, conformed_frame_rate)

        # create clip, then create markers

        return Clip(name, type, timecode_info, resource_id)

    def _get_event_clip_format_info(self, clip_element, resource_id):
        format = clip_element.get('format')

        if format:
            frame_rate = self._frame_rate_from_format(format)
            non_drop_frame = clip_element.get('tcFormat')
        else:
            frame_rate, non_drop_frame = self._parse_ref_info(resource_id)
            
        return frame_rate, non_drop_frame

    def _get_timeline_clip_format_info(self, clip_element):
        conform_rate = clip_element.find('./conform-rate')

        if conform_rate is None:
           conformed_frame_rate = None
        elif conform_rate.get('scaleEnabled') != 0 or conform_rate.get('scaleEnabled') is None:
            source_frame_rate = conform_rate.get('srcFrameRate')
            conformed_frame_rate = self._parse_conformed_frame_rate(source_frame_rate)

        return conformed_frame_rate

    def _parse_conformed_frame_rate(self, source_frame_rate):
        # Matches up values based on Apple's documentation:
        # https://developer.apple.com/documentation/professional_video_applications/fcpxml_reference/story_elements/conform-rate

        conformed_frame_rate = ''

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

        clips_list = self._create_timeline_clip_list(timeline_element)

        # Grab metadata, create timeline instance
        name = timeline_element.get('name')
        sequence = timeline_element.find('./sequence')
        start, duration, format, non_drop_frame = helpers.get_attributes(sequence, 'tcStart','duration', 'format', 'tcFormat')
        frame_rate = self._frame_rate_from_format(format)
        timecode_info = self._create_timecode_info(frame_rate, start, duration, non_drop_frame)
        
        timeline = Timeline(name, timecode_info)


        # creating timeline clips:
        for clip in clips_list:
            parsed_clip = self._handle_clip_creation(clip, frame_rate, non_drop_frame)
            Timeline.add_clip(parsed_clip)

        return timeline

    def _create_timeline_clip_list(self, timeline_element):

        spine_element = timeline_element.find('./sequence/spine')
        primary_clips = self._get_primary_clips(spine_element)
        full_clips_list = self._get_connected_clips(primary_clips)

        return full_clips_list

    def _get_primary_clips(self, spine_element):
        primary_clips = []
        
        for clip in spine_element.iterfind('./'):
            parsed_clip = self._check_for_audition(clip)
            primary_clips.append(parsed_clip)
        
        return primary_clips

    def _get_connected_clips(self, primary_clips_list):
        full_clips_list = primary_clips_list

        for index, clip in enumerate(primary_clips_list):
            connected_clips = [self._check_for_audition(clip) for clip in clip.iterfind('./[@lane]')]
            full_clips_list[index:index] = connected_clips
            # use index slicing here
            # https://realpython.com/lessons/indexing-and-slicing/
            # ex: list1 = [1, 2, 3] and list2 = [4, 5, 6]
            # list1[1:1] = list2 would be [1, 4, 5, 6, 2, 3]
            # starting at index 1 remove up to but not including index 1, then insert list2
        
        return full_clips_list

    def _check_for_audition(self, clip_element):
        if clip_element.tag == 'audition':
            offset = clip_element.get('offset')
            lane = clip_element.get('lane')

            updated_clip = clip_element.find('./')
            updated_clip.set('offset', offset)
            if lane is not None:
                updated_clip.set('lane', lane)
                
            return updated_clip
        else:
            return clip_element

    def parse_xml(self):
        self._create_resources(self.project_file)
        self._create_containers(self.project_file)

        # return project_file

        resources = self.project_file.resources
        for resource in resources:
            print(f"{resource.name}, {resource.id}, {resource.timecode_info.frame_rate}")