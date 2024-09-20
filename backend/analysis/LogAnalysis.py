import re
import time
from pathlib import Path

from backend.utils.buffer_utils.structs import BufferType
from frontend.state import State

from .structs import Component


class LogAnalysis():

    def __init__(self, frame_analysis_path: Path):
        self.frame_analysis_path = frame_analysis_path
        self.log_data = parse_frame_analysis_log_file(self.frame_analysis_path / 'log.txt')

        self.terminal = State.get_instance().get_terminal()


    def extract(self, extract_component: Component, component_hash: str, component_hash_type: str = None) -> None:
        st = time.time()
        if not component_hash_type:
            component_hash_type = self.guess_hash_type(component_hash)
            if not component_hash_type:
                self.terminal.print('<ERROR>ERROR: Failed to find hash "{}" in FrameAnalysis log file.</ERROR>'.format(component_hash))
                raise ZeroDivisionError()
            if component_hash_type not in [BufferType.IB, BufferType.Draw_VB]:
                self.terminal.print('<ERROR>ERROR: Hash "{}" is neither an IB nor a Draw hash.</ERROR>'.format(component_hash))
                raise ZeroDivisionError()

        self.set_relevant_ids (extract_component, component_hash, component_hash_type)
        self.set_draw_data    (extract_component)
        self.set_prepose_data (extract_component)
        # self.set_shapekey_data(extract_component)

        self.check_analysis (extract_component)
        self.terminal.print('Log Based Extraction Done: {:.6}s'.format(time.time() - st))


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
        object_indices: list[int] = []
        ib_filepaths  : list[Path] = []

        backup_position_paths: list[Path] = []
        backup_texcoord_paths: list[Path] = []

        for id in component.ids:
            vs_hash = self.get_vertex_shader_hash(id)
            ps_hash = self.get_pixel_shader_hash(id)
            ib_hash = self.get_ib_hash(id)

            ib_first_index = self.get_ib_first_index(id)

            if ib_first_index not in object_indices:
                component.index_ids[ib_first_index] = [id]
                ib_filepath = self.compile_ib_filepath(id, ib_hash, vs_hash, ps_hash)
                if not ib_filepath.exists():
                    self.terminal.print(f'<ERROR>ERROR:</ERROR> <PATH>{ib_filepath.name}</PATH><ERROR> does not exist in the frame analysis folder.</ERROR>')
                    self.terminal.print('Your `analyse_options` [Hunting] 3dm key is missing required values.', timestamp=False)
                    raise BufferError()

                ib_filepaths  .append(ib_filepath)
                object_indices.append(ib_first_index)
            else:
                component.index_ids[ib_first_index].append(id)

            if draw_hash := self.get_vb_hash(id, 0):
                backup_position_path = self.compile_vb_filepath(id, draw_hash, 0, vs_hash, ps_hash)
                if backup_position_path.exists():
                    backup_position_paths.append(backup_position_path)

            if texcoord_hash := self.get_vb_hash(id, 1):
                backup_texcoord_path = self.compile_vb_filepath(id, texcoord_hash, 1, vs_hash, ps_hash)
                if backup_texcoord_path.exists():
                    backup_texcoord_paths.append(backup_texcoord_path)

        component.backup_position_paths = backup_position_paths
        component.backup_texcoord_paths = backup_texcoord_paths

        component.ib_paths = [
            ib_filepath for ib_filepath, _ in sorted(
                zip(ib_filepaths, object_indices),
                key=lambda item: item[1]
            )
        ]
        component.object_indices = sorted(object_indices)
        component.ib_hash        = self.get_ib_hash(component.ids[0])
        component.draw_hash      = self.get_vb_hash(component.ids[0], 0)
        component.texcoord_hash  = self.get_vb_hash(component.ids[0], 1)

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

        # Yunli weapon is posed twice for some reason?
        # if len(pose_ids) != 1: raise Exception()

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

            if buffer_type == BufferType.Position_VB:
                component.root_vs_hash  = vs_hash
                component.position_hash = buffer_hash
                component.position_path = buffer_path
            elif buffer_type == BufferType.Texcoord_VB:
                component.texcoord_hash = buffer_hash
                component.texcoord_path = buffer_path
            elif buffer_type == BufferType.Blend_VB:
                component.blend_hash = buffer_hash
                component.blend_path = buffer_path

    def check_analysis(self, component: Component):

        # Check required .txt and .buf files exist in frame analysis folder
        txt_paths: dict[str, Path] = {
            'Position Data': component.position_path,
            'Blend Data'   : component.blend_path,
            'Texcoord Data': component.texcoord_path,
            'Backup Position Data': component.backup_position_paths[0] if component.backup_position_paths else None,
            'Backup Texcoord Data': component.backup_texcoord_paths[0] if component.backup_texcoord_paths else None,
        }
        for k, txt_path in txt_paths.items():
            if not txt_path: continue

            buf_path = txt_path.with_suffix('.buf')
            
            missing_path: Path = None
            if not txt_path.exists(): missing_path = txt_path
            if not buf_path.exists(): missing_path = buf_path
            if missing_path:
                self.terminal.print(f'<ERROR>{k}: </ERROR><PATH>{missing_path.name}</PATH><ERROR> does not exist in the frame analysis folder.</ERROR>')
                self.terminal.print('Make sure to include `buf` in addition to `txt` in your `analyse_options` [Hunting] 3dm key.', timestamp=False)
                self.terminal.print('If you\'re performing targeted dumps, also check your targeted .ini is correctly targeting the model.', timestamp=False)
                raise BufferError()
        
        return

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
        if str(slot) in self.log_data[draw_id]['IASetVertexBuffers']:
            return self.log_data[draw_id]['IASetVertexBuffers'][str(slot)]
        return ''

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
                    # assert(keyword not in log_data[draw_id])
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
    State.get_instance().get_terminal().print('Read {} in {:.3}s'.format(log_path.parent.name + '\\' + log_path.name, time.time() - st))
    
    return log_data
