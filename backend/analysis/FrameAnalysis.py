import os
import json
import time
import shutil
import traceback
import subprocess

from pathlib import Path

from backend.utils.buffer_utils.buffer_reader import get_buffer_elements
from backend.utils.buffer_utils.buffer_encoder import merge_buffers, handle_no_weight_blend
from backend.utils.buffer_utils.buffer_decoder import collect_binary_buffer_data
from backend.utils.buffer_utils.exceptions import InvalidTextBufferException
from backend.utils.buffer_utils.structs import BufferElement, POSITION_FMT, BLEND_4VGX_FMT, BLEND_2VGX_FMT, BLEND_1VGX_FMT

from backend.config.Config import Config

from .LogAnalysis import LogAnalysis
from .JsonBuilder import JsonBuilder
from .structs     import Component

from frontend.state import State

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class FrameAnalysis():
    def __init__(self, frame_analysis_path: Path):
        self.terminal     = State.get_instance().get_terminal()
        self.path         = frame_analysis_path
        self.log_analysis = LogAnalysis(self.path)
        self.cfg          = Config.get_instance().data

        self.terminal.print(f'Starting Frame Analysis: <PATH>{frame_analysis_path}</PATH>\n')

    def extract(self, input_component_hashes, input_component_names, input_components_options, game='zzz', reverse_shapekeys=False) -> list[Component]:
        components: list[Component] = []
        for name, target_hash, options in zip(input_component_names, input_component_hashes, input_components_options):
            c = Component(name=name, options=options)

            self.terminal.print('Extracting model data of [{}]{}'.format(target_hash, f' - {name}' if name else ''))
            try:
                self.log_analysis.extract(c, target_hash, game=game, reverse_shapekeys=reverse_shapekeys)
                c.print()
            except BufferError:
                self.terminal.print('<ERROR>Log Analysis Failed!</ERROR>')
                return
            except ZeroDivisionError:
                self.terminal.print('<ERROR>Log Analysis Failed!</ERROR>')
                return
            except Exception as X:
                self.terminal.print('<ERROR>Log Analysis Failed: {}</ERROR>'.format(X))
                self.terminal.print(f'<ERROR>{traceback.format_exc()}</ERROR>')
                return

            components.append(c)
        
        if game != 'gi' or (game == 'gi' and any(len(c.object_indices) > 4 for c in components)):
            for c in components:
                c.object_classification = [
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                    'U', 'V', 'W', 'X', 'Y', 'Z',
                    'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1',
                    'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1',
                    'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1',
                ]
        else:
            for c in components:
                c.object_classification = ['Head', 'Body', 'Dress', 'Extra']

        return components


    def get_position_data(self, buffer_paths: list[Path], shapekey_args={}):
        if len(buffer_paths) == 0: return None, None

        buffer_stride   = 40
        buffer_elements = POSITION_FMT

        if txt_buffer_paths := [p for p in buffer_paths if p.suffix != '.buf']:
            try:
                buffer_stride, buffer_elements = get_buffer_elements(txt_buffer_paths)
            except InvalidTextBufferException:
                self.terminal.print(f'<WARNING>WARNING: SKIPPING Invalid TEXCOORD text buffer!</WARNING>')
                for p in buffer_paths:
                    self.terminal.print(f'<WARNING>{p.name}</WARNING>', timestamp=False)
        
        buffer_path    = buffer_paths[0].with_suffix('.buf')
        buffer_formats = [element.Format for element in buffer_elements]
        buffer         = collect_binary_buffer_data(buffer_path, buffer_formats, buffer_stride, self.terminal, **shapekey_args)

        return buffer, buffer_elements

    def get_blend_data(self, buffer_paths: list[Path], expected_vertex_count: int):
        if len(buffer_paths) == 0: return None, None

        for buffer_stride, buffer_elements in [(32, BLEND_4VGX_FMT), (16, BLEND_2VGX_FMT), (4, BLEND_1VGX_FMT)]:
            buffer_path    = buffer_paths[0].with_suffix('.buf')
            buffer_formats = [element.Format for element in buffer_elements]
            buffer         = collect_binary_buffer_data(buffer_path, buffer_formats, buffer_stride, self.terminal)

            if len(buffer) == expected_vertex_count:
                break

        buffer, buffer_elements = handle_no_weight_blend(buffer, buffer_elements)

        return buffer, buffer_elements

    def get_texcoord_data(self, buffer_paths: list[Path]):
        if len(buffer_paths) == 0: return None, None

        try:
            buffer_stride, buffer_elements = get_buffer_elements(buffer_paths)
        except InvalidTextBufferException:
            self.terminal.print(f'<WARNING>WARNING: SKIPPING Invalid TEXCOORD text buffer!</WARNING>')
            for p in buffer_paths:
                self.terminal.print(f'<WARNING>{p.name}</WARNING>', timestamp=False)
            return None, None
        else:
            buffer_path    = buffer_paths[0].with_suffix('.buf')
            buffer_formats = [element.Format for element in buffer_elements]
            buffer         = collect_binary_buffer_data(buffer_path, buffer_formats, buffer_stride, self.terminal)

            return buffer, buffer_elements
    

    def export(self, export_name, components: list[Component], textures = None, *, game: str):
        json_builder = JsonBuilder()

        extract_path = Path(self.cfg.game[game].extract_path, export_name)
        if self.cfg.game[game].game_options.clean_extract_folder:
            if extract_path.exists(): shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True, exist_ok=True)

        st = time.time()

        for i, component in enumerate(components):
            self.terminal.print(f'Exporting [{component.ib_hash}] - {component.name}')
            self.terminal.print((
                    f'collect_model_data = {component.options["collect_model_data"]}, '
                    f'collect_model_hashes = {component.options["collect_model_hashes"]} '
                ), timestamp=False
            )
            self.terminal.print((
                    f'collect_texture_data = {component.options["collect_texture_data"]}, '
                    f'collect_texture_hashes = {component.options["collect_texture_hashes"]}'
                ), timestamp=False
            )

            if component.options['collect_model_hashes'] or component.options['collect_texture_hashes']:
                json_builder.add_component(component, textures[i] if textures else None, game)

            if component.options['collect_model_data']:
                buffers  = []
                elements = []

                position_paths = [component.position_path] if component.position_path else component.backup_position_paths
                blend_paths    = [component.blend_path]    if component.blend_path    else []
                texcoord_paths = [component.texcoord_path] if component.texcoord_path else component.backup_texcoord_paths

                position_data, position_elements = self.get_position_data(position_paths, {
                        'shapekey_buffer_path': component.shapekey_buffer_path,
                        'shapekey_cb_paths':    component.shapekey_cb_paths
                    } if component.shapekey_buffer_path and component.shapekey_cb_paths else {}
                )
                blend_data, blend_elements       = self.get_blend_data(blend_paths, len(position_data))
                texcoord_data, texcoord_elements = self.get_texcoord_data(texcoord_paths)

                if not position_data:
                    json_builder.components[-1].__setattr__(f'position_vb', '')
                if not blend_data:
                    json_builder.components[-1].__setattr__(f'blend_vb', '')
                if not texcoord_data:
                    json_builder.components[-1].__setattr__(f'texcoord_vb', '')

                if position_data: buffers .append(position_data)
                if blend_data   : buffers .append(blend_data)
                if texcoord_data: buffers .append(texcoord_data)
            
                if position_elements: elements.append(position_elements)
                if blend_elements   : elements.append(blend_elements)
                if texcoord_elements: elements.append(texcoord_elements)

                self.terminal.print(f'Constructing combined buffer for [{component.ib_hash}] - {component.name}')
                vb_merged = merge_buffers(buffers, elements) if buffers else None
            
            if component.options['collect_texture_data'] and  textures: _export_component_textures(export_name, extract_path, component, textures[i])
            if component.options['collect_model_data']   and vb_merged:  _export_component_buffers(export_name, extract_path, component, vb_merged)

        json_out = json.dumps(json_builder.build(), indent=4)
        (extract_path / 'hash.json').write_text(json_out)

        self.terminal.print('Export done: {:.3}s'.format(time.time() - st))

        if self.cfg.game[game].game_options.delete_frame_analysis:
            shutil.rmtree(self.path)
            self.terminal.print('Deleted frame analysis <PATH>{}</PATH>'.format(str(self.path.absolute())))

        if self.cfg.game[game].game_options.open_extract_folder:
            subprocess.run([FILEBROWSER_PATH, extract_path])
            self.terminal.print(f'Opening <PATH>{extract_path.absolute()}</PATH> with File Explorer')


def _export_component_buffers(export_name: str, path: Path, component: Component, vb_merged):
    object_classification = component.object_classification

    # Instead of writing the same vb0 text file multiple times,
    # write it once, and copy and rename it to spread it across
    # the rest of the component's parts. Copying seems faster
    # than writing
    main_vb0_file_path = None

    for i, ib_path in enumerate(component.ib_paths):
        prefix = export_name + component.name + object_classification[i]
        vb0_file_name = '{}-vb0={}.txt'.format(prefix, component.position_hash if component.position_hash else component.draw_hash)
        ib_file_name  = '{}-ib={}.txt' .format(prefix, component.ib_hash)

        vb0_file_path = (path/vb0_file_name)
        if not main_vb0_file_path:
            vb0_file_path.write_text(vb_merged)
            main_vb0_file_path = vb0_file_path
        else:
            shutil.copyfile(main_vb0_file_path, vb0_file_path)

        ib_file_path = (path/ib_file_name)
        shutil.copyfile(ib_path, ib_file_path)


def _export_component_textures(export_name: str, path: Path, component: Component, textures):
    object_classification = component.object_classification
    for i, first_index in enumerate(textures):
        base_texture_file_name = '{}{}{}'.format(export_name, component.name, object_classification[i])
        for (texture, texture_type) in textures[first_index]:
            texture_file_name = base_texture_file_name + texture_type + texture.path.suffix
            shutil.copyfile(texture.path, (path/texture_file_name))
