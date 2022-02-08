from pathlib import Path
from common import helpers
from common.projectclasses import ProjectFile, Resource, Timeline, Clip
from common.timecodeinfo import TimecodeInfo


class FCPXParser:

    def __init__(self, xml_root):
        self.xml_root = xml_root

    def _create_project_file(self):
        try:
            library = self.xml_root.find('library')
        except:
            print("'library' element not found")

        path = library.get('location')
        name = Path(path).name
        project_file = ProjectFile(name, path)

        return project_file

    def _create_project_resources(self, project_file):
        try:
            resources = self.xml_root.find('resources')
        except:
            print("'resources' element not found")

        for resource in resources:
            id, name, path, start, duration, format, non_drop_frame = self._filter_resource_type(resource)
            timecode_info = self._create_resource_timecode_info(resources, format, start, duration, non_drop_frame)
            project_file.add_resource(Resource(id, name, path, timecode_info))

    def _filter_resource_type(self, resource):
        if resource.tag == 'asset':
            resource = self._handle_asset_resource(resource)
        elif resource.tag == 'media':
            resource = self._handle_media_resource(resource)

        return resource

    def _handle_asset_resource(self, resource):
        id = resource.get('id')
        name = resource.get('name')
        start = resource.get('start')
        duration = resource.get('duration')
        format = resource.get('format')
        path = resource.get(f"./format/[@id='{format}']")
        non_drop_frame = False # asset resources don't contain info about NDF or DF, so just assume False
         
        return id, name, path, start, duration, format, non_drop_frame

    def _handle_media_resource(self, resource):
        id = resource.get('id')
        name = resource.get('name')
        path = 'N/A'
        start, duration, format, non_drop_frame = self._filter_media_child_element(resource)   

        return id, name, path, start, duration, format, non_drop_frame

    def _filter_media_child_element(self, resource):
        child_element = resource.find('./')
        start = child_element.get('tcStart')
        format = child_element.get('format')
        non_drop_frame = child_element.get('tcFormat')

        if child_element.tag == 'multicam':
            duration = 0 # Multicam duration is not listed, can create logic later to determine this if necessary
        else:
            duration = child_element.get('')

        return start, duration, format, non_drop_frame
            
    def _create_resource_timecode_info(self, resource, format, start, duration, non_drop_frame):
        format_element = resource.find(f"./resources/format/[@id='{format}']")
        format_id = format_element.get('id')
        frame_rate = format_element.get('frameDuration')
        duration = helpers.frame_rate_to_tuple(duration)

        timecode_info = TimecodeInfo(format_id, frame_rate, start, duration, non_drop_frame=non_drop_frame)

        return timecode_info

    def parse_xml(self):
        project_file = self._create_project_file()
        self._create_project_resources(project_file)

        resources = project_file.resources
        print(resources)