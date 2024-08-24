from pathlib import Path

from .structs import BufferType
from frame_analysis.structs import Component

from .buffer_utilities import extract_from_txt


class FrameAnalysisException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__(self, message, *args, **kwargs)
        self.message = message

class FileAnalysis():
    def __init__(self, frame_analysis_path: Path):
        self.frame_analysis_path = frame_analysis_path
        self.files: list[Path] = [f for f in frame_analysis_path.iterdir() if f.suffix in ['.txt']]

    def extract(self, extract_component: Component, component_hash: str, component_hash_type: str = None) -> None:
        if not component_hash_type:
            component_hash_type = self.guess_hash_type(component_hash)
            if not component_hash_type:
                raise Exception('Failed to find hash "{}" in FrameAnalysis folder files.'.format(component_hash))
            if component_hash_type not in [BufferType.IB, BufferType.Draw_VB]:
                raise Exception('Unsupported')

        self.set_relevant_ids (extract_component, component_hash, component_hash_type)
        self.set_draw_data    (extract_component)
        self.set_prepose_data (extract_component)
        # self.set_shapekey_data(extract_component)

    def guess_hash_type(self, target_hash):
        for file in self.files:
            if f'-ib={target_hash}' in file.name:
                return BufferType.IB
            if f'-vb0={target_hash}' in file.name:
                return BufferType.Draw_VB
        return None

    def set_relevant_ids(self, component: Component, component_hash, component_hash_type):
        if   component_hash_type == BufferType.Draw_VB: s = 'vb0'
        elif component_hash_type == BufferType.IB     : s = 'ib'
        else: raise Exception()

        component.ids = [get_draw_id(f.name) for f in self.files if f'-{s}={component_hash}' in f.name]
        if len(component.ids) == 0:
            raise Exception('Failed to find hash "{}" in FrameAnalysis files.'.format(component_hash))

    def set_draw_data(self, component: Component):
        largest_texcoord_filepath = None
        largest_position_filepath = None
        texcoord_largest_count = -1
        position_largest_count = -1
        object_indices: list[str] = []
        ib_filepaths : list[Path] = []

        for id in component.ids:
            id_files = [f for f in self.files if f.name.startswith(id)]

            ib_filepath = [f for f in id_files if '-ib=' in f.name][0]
            ib_first_index = extract_from_txt('first index', ib_filepath)
            if ib_first_index == -1:
                print('\tWarning: Invalid IB file: ' + ib_filepath.name)
                print('\tSkipping ID {} for "{}"'.format(id, component.name))
                continue

            if ib_first_index in object_indices:
                component.index_ids[ib_first_index].append(id)
                continue
            component.index_ids[ib_first_index] = [id]

            texcoord_vb_candidate = [f for f in id_files if "-vb1=" in f.name]
            if len(texcoord_vb_candidate) == 1:
                texcoord_vb_candidate = texcoord_vb_candidate[0]
                texcoord_count = extract_from_txt('vertex count', texcoord_vb_candidate)
                if texcoord_count > texcoord_largest_count:
                    texcoord_largest_count = texcoord_count
                    largest_texcoord_filepath = texcoord_vb_candidate

            position_vb_candidate = [f for f in id_files if "-vb0=" in f.name]
            if len(position_vb_candidate) == 1:
                position_vb_candidate = position_vb_candidate[0]
                position_count = extract_from_txt('vertex count', position_vb_candidate)
                if position_count > position_largest_count:
                    position_largest_count = position_count
                    largest_position_filepath = position_vb_candidate

            object_indices.append(ib_first_index)
            ib_filepaths  .append(ib_filepath)

        component.backup_position_path = largest_position_filepath
        component.backup_texcoord_path = largest_texcoord_filepath
        component.ib_paths = [
            ib_filepath for ib_filepath, _ in sorted(
                zip(ib_filepaths, object_indices),
                key=lambda item: item[1]
            )
        ]
        component.object_indices = sorted(object_indices)
        component.ib_hash        = get_resource_hash(component.ib_paths[0].name)
        component.draw_hash      = get_resource_hash(component.backup_position_path.name)

    def set_prepose_data(self, component: Component):

        root_vs_hashes = {
            "e8425f64cfb887cd": "ZZZ/HSR: Up to 4VGs/Vertex",
            "a0b21a8e787c5a98": "ZZZ/HSR: Up to 2VGs/Vertex",
            "9684c4091fc9e35a": "ZZZ/HSR: Up to 1VGs/Vertex",
            "653c63ba4a73ca8b": "     GI: Up to 4VGS/Vertex"
        }

        pose_ids = set()
        for file_path in self.files:
            for root_vs_hash in root_vs_hashes:
                if root_vs_hash in file_path.name:
                    pose_ids.add(get_draw_id(file_path.name))
                    continue

        if len(pose_ids) == 0:
            print('No pose calls found.')
            return
        if not component.backup_texcoord_path:
            print('\tComponent {} ({})'.format(component.name, component.ib_hash))
            print('\t\tCannot identify posing data with no texcoord hash')
            return

        any_pose_id = next(iter(pose_ids))
        no_vb2 = 0 == len([
            file_path for file_path in self.files
            if file_path.name.startswith(any_pose_id)
            and '-vb2' in file_path.name
        ])
        if no_vb2 : texcoord_size = extract_from_txt('vertex count', component.backup_texcoord_path)
        else      : texcoord_hash = get_resource_hash(component.backup_texcoord_path.name)


        for pose_id in pose_ids:
            id_file_paths = [file_path for file_path in self.files if file_path.name.startswith(pose_id)]
            
            if no_vb2:
                position_path = [file_path for file_path in id_file_paths if '-vb0' in file_path.name][0]
                blend_path    = [file_path for file_path in id_file_paths if '-vb1' in file_path.name][0]

                if texcoord_size == extract_from_txt('vertex count', position_path):
                    component.position_path = position_path
                    component.blend_path    = blend_path

                    print('\tComponent {} ({})'.format(component.name, component.ib_hash))
                    print('\t\tFound position data file path: ' + component.position_path.name)
                    print('\t\tFound blend    data file path: ' + component.blend_path.name)
                    return

            else:
                position_path = [file_path for file_path in id_file_paths if '-vb0' in file_path.name][0]
                texcoord_path = [file_path for file_path in id_file_paths if '-vb1' in file_path.name][0]
                blend_path    = [file_path for file_path in id_file_paths if '-vb2' in file_path.name][0]

                if texcoord_hash in texcoord_path.name:
                    component.position_path = position_path
                    component.texcoord_path = texcoord_path
                    component.blend_path    = blend_path

                    print('\tComponent {} ({})'.format(component.name, component.ib_hash))
                    print('\t\tFound position data file path: ' + component.position_path.name)
                    print('\t\tFound texcoord data file path: ' + component.texcoord_path.name)
                    print('\t\tFound blend    data file path: ' + component.blend_path.name)
                    return
        
        return


def get_draw_id(filename: str) -> str:
    return filename.split('-')[0]


def get_resource_hash(filename: str) -> str:
    # 000044-ib=5a4c1ef3-vs=274b0b210859d9dc-ps=804069b9174bb779.txt
    # 000047-vb0=8cc1262b-vs=274b0b210859d9dc-ps=f681234a84795646.txt
    # 000047-ps-t7=!S!=028c9a7f-vs=274b0b210859d9dc-ps=f681234a84795646.dds
    return filename.split("-vs=")[0].split("=")[-1]
