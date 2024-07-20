import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field


from .buffer_utilities import extract_from_txt, collect_buffer_data, merge_buffers, handle_no_weight_blend
from .JsonBuilder import JsonBuilder

@dataclass
class Component():
    name: str = ''

    position_path: Path = None
    blend_path   : Path = None
    texcoord_path: Path = None

    ids                  : list[str]  = field(default_factory=lambda:[])
    ib_paths             : list[Path] = field(default_factory=lambda:[])
    object_indices       : list[str]  = field(default_factory=lambda:[])
    object_classification: list[str]  = field(default_factory=lambda:[])
    
    backup_position_path = None
    backup_texcoord_path = None

    texture_data: dict[int, list[Path]] = field(default_factory=lambda:{})

    # For debugging only for now, optimize later 
    def __str__(self):
        s = ''
        s += 'IDs: {}\n'.format(self.ids)
        s += 'Object Indices: {}\n'.format(self.object_indices)
        s += 'Backup Position Path: {}\n'.format(self.backup_position_path.name)
        s += 'Backup Texcoord Path: {}\n'.format(self.backup_texcoord_path.name)
        s += 'IBs:\n'
        for ib_path in self.ib_paths:
            s += '\t{}\n'.format(ib_path.name)

        s += 'Texture Data:\n'
        for first_index in self.texture_data:
            s += '\n'.join(['\t' + f.name for f in self.texture_data[first_index]]) + '\n\n'

        s += 'Position Path: {}\n'.format(self.position_path.name)
        s += 'Texcoord Path: {}\n'.format(self.texcoord_path.name)
        s += 'Blend Path: {}\n'   .format(self.blend_path.name)

        return s + '\n'


class FrameAnalysisException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__(self, message, *args, **kwargs)
        self.message = message


# class FrameAnalysis():
#     def __init__(self, frame_analysis_path, export_name: str, ib_hashes: tuple[str], component_names: tuple[str]):
#         self.frame_analysis_path = frame_analysis_path
#         self.ib_hashes           = ib_hashes
#         self.export_name         = export_name
#         self.component_names     = component_names

def extract(frame_analysis_path, ib_hashes, component_names) -> list[Component]:
    print(frame_analysis_path)

    path = Path(frame_analysis_path)
    files: list[Path] = [f for f in path.iterdir() if f.suffix in ['.txt', '.dds', '.jpg']]
    
    if 'FrameAnalysis' not in path.name:
        raise FrameAnalysisException('Invalid frame analysis path: "{}"'.format(frame_analysis_path))

    components: list[Component] = []
    for component_name in component_names:
        c = Component()
        c.name = component_name
        c.object_classification = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        components.append(c)

    set_relevant_ids (components, files, ib_hashes)
    set_relevant_data(components, files)
    set_unposed_data (components, files)

    return components

def export(export_name, components: list[Component], collected_textures = None):
    json_builder = JsonBuilder()
    for i, component in enumerate(components):
        textures = None
        if collected_textures:
            textures = collected_textures[i]

        json_builder.add_component(component, textures)

        position, position_format = collect_buffer_data(component.position_path)
        blend,    blend_format    = collect_buffer_data(component.blend_path)
        texcoord, texcoord_format = collect_buffer_data(component.texcoord_path)

        handle_no_weight_blend(blend, blend_format)

        vb_merged = merge_buffers((position, blend, texcoord), (position_format, blend_format, texcoord_format))
        export_component(export_name, component, vb_merged, textures)

    json_out = json.dumps(json_builder.build(), indent=4)
    Path('_Extracted', export_name, 'hash.json').write_text(json_out)


def export_component(export_name: str, component: Component, vb_merged, textures=None):
    object_classification = component.object_classification

    for i, ib_path in enumerate(component.ib_paths):
        prefix = export_name + component.name + object_classification[i]
        vb0_file_name = '{}-vb0={}.txt'.format(prefix, get_resource_hash(component.position_path.name))
        ib_file_name  = '{}-ib={}.txt' .format(prefix, get_resource_hash(ib_path.name))

        vb0_file_path = Path('_Extracted', export_name, vb0_file_name)
        vb0_file_path.parent.mkdir(parents=True, exist_ok=True)
        vb0_file_path.write_text(vb_merged)

        ib_file_path = Path('_Extracted', export_name, ib_file_name)
        ib_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ib_path, ib_file_path)

    if textures:
        for i, first_index in enumerate(textures):
            base_texture_file_name = '{}{}{}'.format(export_name, component.name, object_classification[i])
            for (saved_texture, texture_type) in textures[first_index]:
                texture_file_name = base_texture_file_name + texture_type + saved_texture.real_path.suffix
                shutil.copyfile(saved_texture.real_path, Path('_Extracted', export_name, texture_file_name))


def set_unposed_data(components: list[Component], file_paths: list[Path]):
    print('Collecting unposed data')

    root_vs_hashes = {
        "e8425f64cfb887cd": "ZZZ/HSR: Up to 4VGs/Vertex",
        "a0b21a8e787c5a98": "ZZZ/HSR: Up to 2VGs/Vertex",
        "9684c4091fc9e35a": "ZZZ/HSR: Up to 1VGs/Vertex",
        "653c63ba4a73ca8b": "     GI: Up to 4VGS/Vertex"
    }

    pose_ids = set()
    for file_path in file_paths:
        for root_vs_hash in root_vs_hashes:
            if root_vs_hash in file_path.name:
                pose_ids.add(get_draw_id(file_path.name))
                continue

    if len(pose_ids) == 0:
        raise FrameAnalysisException('No pose calls found.')

    in_progress_components = [*components]

    for pose_id in pose_ids:
        id_file_paths = [file_path for file_path in file_paths if file_path.name.startswith(pose_id)]
        
        vb0_path = [file_path for file_path in id_file_paths if '-vb0' in file_path.name][0]
        vb1_path = [file_path for file_path in id_file_paths if '-vb1' in file_path.name][0]
        vb2_path = [file_path for file_path in id_file_paths if '-vb2' in file_path.name][0]

        for component in in_progress_components:
            texcoord_hash = get_resource_hash(component.backup_texcoord_path.name)
            if texcoord_hash in vb1_path.name:
                component.position_path = vb0_path
                component.texcoord_path = vb1_path
                component.blend_path    = vb2_path

                print('\tComponent {} ({})'.format(component.name, get_resource_hash(component.ib_paths[0].name)))
                print('\t\tFound position data file path: ' + vb0_path.name)
                print('\t\tFound texcoord data file path: ' + vb1_path.name)
                print('\t\tFound blend    data file path: ' + vb2_path.name)
                print()

                in_progress_components.remove(component)
                continue

    if len(in_progress_components) != 0:
        raise FrameAnalysisException('Failed to find unposed data for {} ({})'.format(
            in_progress_components[0].name,
            get_resource_hash(in_progress_components[0].ib_paths[0].name),
        ))
    
    return


def set_relevant_ids(components: list[Component], files: list[Path], ib_hashes: tuple[str]):
    for i, ib_hash in enumerate(ib_hashes):
        component_ids = [get_draw_id(f.name) for f in files if f'-ib={ib_hash}' in f.name]

        if len(component_ids) == 0:
            raise FrameAnalysisException(message='Failed to find IB hash "' + ib_hash + '" in frame analysis folder.')

        ids_with_textures = []
        for id in component_ids:
            no_render_target = len([f for f in files if f'{id}-o0=' in f.name]) == 0
            if no_render_target:
                continue
            ids_with_textures.append(id)

        components[i].ids = ids_with_textures


# def set_texture_data(components: list[Component], files: list[Path]):
#     for component in components:
#         component.texture_data = [
#             [f for f in files if f.name.startswith(f'{id}-ps-t') and f.suffix in ['.dds', '.jpg']]
#             for id in component.ids
#         ]


def set_relevant_data(components: list[Component], files: list[Path]):
    '''
        - Index Buffer
        - Backup Positional Data
        - Backup Texcoord Data
    '''
    print('Collecting data from relevant ids')

    for component in components:

        texcoord_vb_path = None
        position_vb_path = None
        texcoord_largest_count = -1
        position_largest_count = -1

        for id in component.ids:
            id_files = [f for f in files if f.name.startswith(id)]

            ib_path = [f for f in id_files if '-ib=' in f.name][0]
            first_index = extract_from_txt('first index', ib_path)
            if first_index == -1:
                print('\tWarning: Invalid IB file: ' + ib_path.name)
                print('\tSkipping ID {} for "{}"'.format(id, component.name))
                continue

            if first_index in component.object_indices:
                continue

            component      .ib_paths.append(ib_path)
            component.object_indices.append(first_index)
            component.texture_data[first_index] = [
                f for f in id_files
                if f.name.startswith(f'{id}-ps-t')
                and f.suffix in ['.dds', '.jpg']
            ]

            texcoord_vb_candidate = [f for f in id_files if "-vb1=" in f.name]
            if len(texcoord_vb_candidate) == 1:
                texcoord_vb_candidate = texcoord_vb_candidate[0]
                texcoord_count = extract_from_txt('vertex count', texcoord_vb_candidate)
                if texcoord_count > texcoord_largest_count:
                    texcoord_largest_count = texcoord_count
                    texcoord_vb_path = texcoord_vb_candidate

            position_vb_candidate = [f for f in id_files if "-vb0=" in f.name]
            if len(position_vb_candidate) == 1:
                position_vb_candidate = position_vb_candidate[0]
                position_count = extract_from_txt('vertex count', position_vb_candidate)
                if position_count > position_largest_count:
                    position_largest_count = position_count
                    position_vb_path = position_vb_candidate

        component.backup_position_path = position_vb_path
        component.backup_texcoord_path = texcoord_vb_path

        print('\tComponent {} ({})'.format(component.name, get_resource_hash(component.ib_paths[0].name)))
        print('\t\tIB Data:')
        for i, object_index in enumerate(component.object_indices):
            print('\t\t\t{}\t{}'.format(object_index, component.ib_paths[i].name))
        print('\t\tBackup position data file path: ' + position_vb_path.name)
        print('\t\tBackup texcoord data file path: ' + texcoord_vb_path.name)
        print()
    
    return


def get_draw_id(name: str) -> str:
    return name.split('-')[0]

def get_resource_hash(name: str) -> str:
    # 000044-ib=5a4c1ef3-vs=274b0b210859d9dc-ps=804069b9174bb779.txt
    # 000047-vb0=8cc1262b-vs=274b0b210859d9dc-ps=f681234a84795646.txt
    # 000047-ps-t7=!S!=028c9a7f-vs=274b0b210859d9dc-ps=f681234a84795646.dds
    return name.split("-vs=")[0].split("=")[-1]

    # No headers
    # def extract_buf(self):
    #     print(self.frame_analysis_path)

    #     path = Path(self.frame_analysis_path)
    #     log_path = path / 'log.txt'
    #     log = log_path.read_text(encoding='utf-8')

    #     ia_set_index_buffer_pattern = re.compile(r'(\d{6}) IASetIndexBuffer\(pIndexBuffer:0x([A-F0-9]+), Format:(\d+), Offset:(\d+)\) hash='+self.ib_hashes[1].lower())
    #     ia_set_index_buffer_groups = re.findall(ia_set_index_buffer_pattern, log)

    #     relevant_draw_ids = [g[0] for g in ia_set_index_buffer_groups]
    #     ib_formats = set(g[2] for g in ia_set_index_buffer_groups)
    #     if len(ib_formats) > 1: raise Exception()
    #     ib_format = ib_formats.pop()

    #     # find index buffer offsets
    #     # 000052 DrawIndexed(IndexCount:46683, StartIndexLocation:0, BaseVertexLocation:0)
    #     draw_indexed_pattern = re.compile(r'(\d{6}) DrawIndexed\(IndexCount:(\d+), StartIndexLocation:(\d+), BaseVertexLocation:(\d+)\)')
    #     draw_indexed_groups = re.findall(draw_indexed_pattern, log)

    #     my_draw_indexed_groups = [d for d in draw_indexed_groups if d[0] in relevant_draw_ids]

    #     print(relevant_draw_ids, ib_format)
    #     print(my_draw_indexed_groups)
    #     exit()
