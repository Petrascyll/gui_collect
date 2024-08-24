import re
import time
from pathlib import Path

from .structs import BufferType
from .structs import Component


class LogAnalysis():

    def __init__(self, frame_analysis_path: Path):
        self.frame_analysis_path = frame_analysis_path
        self.log_data = parse_frame_analysis_log_file(self.frame_analysis_path / 'log.txt')


    def extract(self, extract_component: Component, component_hash: str, component_hash_type: str = None) -> None:
        if not component_hash_type:
            component_hash_type = self.guess_hash_type(component_hash)
            if not component_hash_type:
                raise Exception('Failed to find hash "{}" in FrameAnalysis log file.'.format(component_hash))
            if component_hash_type not in [BufferType.IB, BufferType.Draw_VB]:
                raise Exception('Unsupported')

        self.set_relevant_ids (extract_component, component_hash, component_hash_type)
        self.set_draw_data    (extract_component)
        self.set_prepose_data (extract_component)
        # self.set_shapekey_data(extract_component)


    def guess_hash_type(self, target_hash):
        for id in self.log_data:
            if 'IASetIndexBuffer' in self.log_data[id] and self.log_data[id]['IASetIndexBuffer'] == target_hash:
                return BufferType.IB
            if (
                'IASetVertexBuffers' in self.log_data[id]
                and '0' in self.log_data[id]['IASetVertexBuffers']
                and self.log_data[id]['IASetVertexBuffers']['0'] == target_hash
            ):
                return BufferType.Draw_VB
        return None

    def get_relevant_ids(self, target_hash, target_hash_type: BufferType):
        if target_hash_type == BufferType.IB:
            return [
                id for id in self.log_data
                if 'IASetIndexBuffer' in self.log_data[id]
                and self.log_data[id]['IASetIndexBuffer'] == target_hash
            ]
        elif target_hash_type == BufferType.Draw_VB:
            return [
                id for id in self.log_data
                if 'IASetVertexBuffers' in self.log_data[id]
                and '0' in self.log_data[id]['IASetVertexBuffers']
                and self.log_data[id]['IASetVertexBuffers']['0'] == target_hash
            ]
        else:
            raise Exception()

    def set_relevant_ids(self, component: Component, component_hash, component_hash_type):
        component.ids = self.get_relevant_ids(component_hash, component_hash_type)
        if len(component.ids) == 0:
            raise Exception('Invalid input hash {}'.format(component_hash))

    def set_draw_data(self, component: Component):
        largest_texcoord_filepath = None
        largest_position_filepath = None
        highest_ib_first_index    = -1
        object_indices: list[str] = []
        ib_filepaths : list[Path] = []

        for id in component.ids:
            vs_hash = self.get_vertex_shader_hash(id)
            ps_hash = self.get_pixel_shader_hash(id)
            ib_hash = self.get_ib_hash(id)

            ib_first_index = self.get_ib_first_index(id)
            # ib_index_count = self.get_ib_index_count(id)
            if ib_first_index in object_indices:
                component.index_ids[ib_first_index].append(id)
                continue
            component.index_ids[ib_first_index] = [id]

            ib_filepath = self.compile_ib_filepath(id, ib_hash, vs_hash, ps_hash)
            if not ib_filepath.exists(): raise Exception()

            if int(ib_first_index) > highest_ib_first_index:
                highest_ib_first_index = int(ib_first_index)
                largest_position_filepath = self.compile_vb_filepath(id, self.get_vb_hash(id, 0), 0, vs_hash, ps_hash)
                largest_texcoord_filepath = self.compile_vb_filepath(id, self.get_vb_hash(id, 1), 1, vs_hash, ps_hash)
                if not largest_position_filepath.exists(): raise Exception()
                if not largest_texcoord_filepath.exists(): raise Exception()

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
        component.ib_hash        = self.get_ib_hash(component.ids[0])
        component.draw_hash      = self.get_vb_hash(component.ids[0], 0)

    def set_prepose_data(self, component: Component):
        if not component.draw_hash:
            return

        pose_ids = [
            id for id in self.log_data
            if 'SOSetTargets' in self.log_data[id]
            and '0' in self.log_data[id]['SOSetTargets']
            and self.log_data[id]['SOSetTargets']['0'] == component.draw_hash
        ]
        if not pose_ids: return
        if len(pose_ids) != 1: raise Exception()

        pose_id = pose_ids[0]
        vs_hash = self.get_vertex_shader_hash(pose_id)
        assert('IASetVertexBuffers' in self.log_data[pose_id])

        prepose_buffer_count = len(self.log_data[pose_id]['IASetVertexBuffers'])
        if   prepose_buffer_count == 2: prepose_data = (['0', '1'],      [BufferType.Position_VB, BufferType.Blend_VB])
        elif prepose_buffer_count == 3: prepose_data = (['0', '1', '2'], [BufferType.Position_VB, BufferType.Texcoord_VB, BufferType.Blend_VB])
        else: raise Exception()

        for slot, buffer_type in zip(*prepose_data):
            buffer_hash = self.log_data[pose_id]['IASetVertexBuffers'][slot]
            buffer_path = self.compile_vb_filepath(pose_id, buffer_hash, slot, vs_hash, ext='.txt')
            assert(buffer_path.exists())

            if buffer_type == BufferType.Position_VB:
                component.position_hash = buffer_hash
                component.position_path = buffer_path
            elif buffer_type == BufferType.Texcoord_VB:
                component.texcoord_hash = buffer_hash
                component.texcoord_path = buffer_path
            elif buffer_type == BufferType.Blend_VB:
                component.blend_hash = buffer_hash
                component.blend_path = buffer_path

    def compile_vb_filepath(self, draw_id, vb_hash, slot, vs_hash, ps_hash=None, ext='.txt'):
        resources = [(f'vb{slot}', vb_hash), ('vs', vs_hash)]
        if ps_hash: resources.append(('ps', ps_hash))
        return self.compile_filepath(draw_id, resources, ext)

    def compile_ib_filepath(self, draw_id, ib_hash, vs_hash, ps_hash, ext='.txt'):
        resources = [(f'ib', ib_hash), ('vs', vs_hash)]
        if ps_hash: resources.append(('ps', ps_hash))
        return self.compile_filepath(draw_id, resources, ext)

    def compile_filepath(self, draw_id, resources: list[tuple[str,str]], ext='.txt'):
        filename = '{}-{}{}'.format(
            draw_id,
            '-'.join([f'{resource}={resource_hash}' for resource, resource_hash in resources]),
            ext
        )

        return Path(self.frame_analysis_path, filename)

    def get_prev_draw_id(self, draw_id: str):
        draw_id = int(draw_id)
        if draw_id == 1: raise Exception()
        return str(draw_id - 1).zfill(6)
    
    def get_vertex_shader_hash(self, draw_id: str):
        while 'VSSetShader' not in self.log_data[draw_id]:
            draw_id = self.get_prev_draw_id(draw_id)
        return self.log_data[draw_id]['VSSetShader']

    def get_pixel_shader_hash(self, draw_id: str):
        while 'PSSetShader' not in self.log_data[draw_id]:
            draw_id = self.get_prev_draw_id(draw_id)
        return self.log_data[draw_id]['PSSetShader']

    def get_vb_hash(self, draw_id: str, slot: int):
        return self.log_data[draw_id]['IASetVertexBuffers'][str(slot)]

    def get_ib_hash(self, draw_id: str):
        return self.log_data[draw_id]['IASetIndexBuffer']

    def get_ib_index_count(self, draw_id: str) -> int:
        if 'DrawIndexedInstanced' in self.log_data[draw_id]: return int(self.log_data[draw_id]['DrawIndexedInstanced']['IndexCountPerInstance'])
        elif 'DrawIndexed' in self.log_data[draw_id]: return int(self.log_data[draw_id]['DrawIndexed']['IndexCount'])
        else:
            print(self.log_data[draw_id])
            raise Exception()

    def get_ib_first_index(self, draw_id: str) -> int:
        if 'DrawIndexedInstanced' in self.log_data[draw_id]: return int(self.log_data[draw_id]['DrawIndexedInstanced']['StartIndexLocation'])
        elif 'DrawIndexed' in self.log_data[draw_id]: return int(self.log_data[draw_id]['DrawIndexed']['StartIndexLocation'])
        else:
            print(self.log_data[draw_id])
            raise Exception()


def parse_frame_analysis_log_file(log_path):
    st = time.time()
    log_data = {}

    with open(log_path, encoding='utf-8') as log_file:
        log_file.readline()  # skip first line

        while line := log_file.readline():
            if m := re.match(r'\d{6}', line):
                draw_id = m.group()
                if draw_id not in log_data:
                    log_data[draw_id] = {}

                if line[7:15] == '3DMigoto':
                    continue

                keyword = line[7:].split('(', maxsplit=1)[0]
                if keyword in [
                    'IASetVertexBuffers', 'CopyResource', 'SOSetTargets',
                    'CSSetUnorderedAccessViews', 'CSSetShaderResources',
                    'CSSetConstantBuffers'
                ]:
                    if keyword not in log_data[draw_id]:
                        log_data[draw_id][keyword] = {}

                    pos  = log_file.tell()
                    line = log_file.readline()
                    while s := re.match(r'^\s*(.*):(?: view=0x.*?)? resource=.*? hash=(.*)$', line):
                        assert(s.group(1) not in log_data[draw_id][keyword])
                        log_data[draw_id][keyword][s.group(1)] = s.group(2)
                        pos  = log_file.tell()
                        line = log_file.readline()
                    log_file.seek(pos)
                
                elif keyword in ['IASetIndexBuffer', 'PSSetShader', 'VSSetShader', 'CSSetShader']:
                    hash_match = re.search(r'hash=([a-f0-9]+)', line)
                    if not hash_match: continue
                    assert(keyword not in log_data[draw_id])
                    log_data[draw_id][keyword] = hash_match.group(1)
                
                elif keyword in ['DrawIndexedInstanced', 'DrawIndexed']:
                    args = re.findall(r'\b([a-z]+):(.+?\b)', line.split('(')[1].split(')')[0], flags=re.IGNORECASE)
                    assert(keyword not in log_data[draw_id])
                    log_data[draw_id][keyword] = {
                        arg[0]: arg[1]
                        for arg in args
                    }
                
                elif keyword in ['ClearRenderTargetView']:
                    log_data[draw_id] = {}

            else:
                continue
    print('Read {} in {:.3}s'.format(log_path.parent.name + '\\' + log_path.name, time.time() - st))
    
    return log_data
