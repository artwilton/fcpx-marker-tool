from pathlib import Path
from common import helpers
from common.projectclasses import ProjectFile, Resource, Timeline, Clip
from common.timecodeinfo import TimecodeInfo

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
            if not resource.tag == 'format':
                id, name, path, start, duration, format, non_drop_frame = self._filter_resource_type(resource)
                timecode_info = self._create_timecode_info(format, start, duration, non_drop_frame)
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
        non_drop_frame = False # asset resources don't contain info about NDF or DF, so just assume False
         
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
            
    def _create_timecode_info(self, format, start, duration, non_drop_frame):
        format_element = self.xml_root.find(f"./resources/format/[@id='{format}']")
        format_id, frame_rate = helpers.get_attributes(format_element, 'id', 'frameDuration')
        frame_rate = helpers.frame_rate_to_tuple(frame_rate, reverse=True)
        start = helpers.get_number_of_frames(start, frame_rate)
        duration = helpers.get_number_of_frames(duration, frame_rate)

        timecode_info = TimecodeInfo(format_id, frame_rate, start, duration, non_drop_frame=non_drop_frame)

        return timecode_info

    # TIMELINES
    def _create_timelines(self, project_file):
        try:
            timelines = self.xml_root.findall('./library/event/project')
        except:
            print("'project' element not found")

        for timeline in timelines:
            name = timeline.get('name')
            sequence = timeline.find('./sequence')
            start, duration, format, non_drop_frame = helpers.get_attributes(sequence, 'tcStart','duration', 'format', 'tcFormat')
            timecode_info = self._create_timecode_info(format, start, duration, non_drop_frame)
            project_file.add_timeline(Timeline(name, timecode_info))

        return timelines

    def parse_xml(self):
        project_file = self._create_project_file()
        self._create_resources(project_file)
        timelines = self._create_timelines(project_file)

        print(timelines)

        # resources = project_file.resources
        # for resource in resources:
        #     print(resource.timecode_info.standard_timecode)