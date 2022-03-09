from pathlib import Path
from common import helpers
from common.projectclasses import ProjectFile, Resource, Timeline, Clip, Container
from common.timecodeinfo import TimecodeInfo
from fcpx_marker_tool.common.helpers import frame_rate_to_tuple

class FCPXParser:

    def __init__(self, xml_root):
        self.xml_root = xml_root

    # PROJECT FILE
    def _create_project_file(self):
        try:
            library = self.xml_root.find('library')
        except:
            print("'library' element not found")

        path = library.get('location')
        name = Path(path).name
        project_file = ProjectFile(name, path)

        return project_file

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
            
    def _create_timecode_info(self, frame_rate, start, duration, non_drop_frame=True, offset=None):
        start = helpers.get_number_of_frames(start, frame_rate)
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

    def _handle_clip_creation(self, clip_element, event_clip=False):
        name, start, duration, offset = helpers.get_attributes(clip_element, 'name', 'start', 'duration', 'offset')
        type = clip_element.tag
        
        if event_clip:
            frame_rate, non_drop_frame, resource_id = self._get_event_clip_format_info(clip_element)
        else:
            frame_rate, non_drop_frame, resource_id = self._get_timeline_clip_format_info(clip_element)

        timecode_info = self._create_timecode_info(frame_rate, start, duration, non_drop_frame, offset)

        return Clip(name, type, timecode_info, resource_id)

    def _get_event_clip_format_info(self, clip_element):
        format = clip_element.get('format')
        resource_id = clip_element.get('ref')

        if format:
            frame_rate = self._frame_rate_from_format(format)
            non_drop_frame = clip_element.get('tcFormat')
        elif resource_id:
            frame_rate, non_drop_frame = self._parse_ref_info(resource_id)
        elif resource_id is None:
            resource_id = clip_element.get('./ref')
            frame_rate, non_drop_frame = self._parse_ref_info(resource_id)
            
        return frame_rate, non_drop_frame, resource_id

    def _get_timeline_clip_format_info(self, clip_element):
        pass

    def _parse_ref_info(self, resource_id):
        # "ref" will refer to a Resource. Find the matching Resource, grab the frame rate and tcformat from there.
        pass

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
        name = timeline_element.get('name')
        sequence = timeline_element.find('./sequence')
        start, duration, format, non_drop_frame = helpers.get_attributes(sequence, 'tcStart','duration', 'format', 'tcFormat')
        frame_rate = self._frame_rate_from_format(format)
        timecode_info = self._create_timecode_info(frame_rate, start, duration, non_drop_frame)
        
        timeline = Timeline(name, timecode_info)

        # .iter() through the rest of the timeline, have function responsible for filtering clip metadata handling based on clip type
        # I can then either iterate through all of the gathered clips to grab markers, or figure out a way to handle it as I'm iterating through each line

        return timeline

    def parse_xml(self):
        project_file = self._create_project_file()
        self._create_resources(project_file)
        self._create_containers(project_file)

        # return project_file

        resources = project_file.resources
        for resource in resources:
            print(f"{resource.name}, {resource.id}, {resource.timecode_info.frame_rate}")