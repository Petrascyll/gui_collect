import json
import time
import shutil
import traceback

from pathlib import Path

from backend.utils.buffer_utils.buffer_reader import get_buffer_elements
from backend.utils.buffer_utils.buffer_encoder import merge_buffers, handle_no_weight_blend
from backend.utils.buffer_utils.buffer_decoder import collect_binary_buffer_data
from backend.utils.buffer_utils.exceptions import InvalidTextBufferException

from .LogAnalysis     import LogAnalysis
from .TextureAnalysis import TextureAnalysis

from .JsonBuilder import JsonBuilder
from .structs     import Component

from frontend.state import State


class FrameAnalysis():
    def __init__(self, frame_analysis_path: Path):
        self.terminal = State.get_instance().get_terminal()

        self.path = frame_analysis_path
        self.log_analysis     =     LogAnalysis(self.path)
        self.texture_analysis = TextureAnalysis(self.path)

        self.terminal.print(f'Starting Frame Analysis: <PATH>{frame_analysis_path}</PATH>\n')

    def get_textures(self, draw_id):
        # filter = self.texture_analysis.get_default_filter()
        # filter[TextureAnalysis.F.MIN_HEIGHT]['active']
        return self.texture_analysis.get_textures(draw_id)

    def extract(self, input_component_hashes, input_component_names, input_components_options, game='zzz') -> list[Component]:
        components: list[Component] = []
        for name, target_hash, options in zip(input_component_names, input_component_hashes, input_components_options):
            c = Component(name=name, options=options)
            c.object_classification = [
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                'U', 'V', 'W', 'X', 'Y', 'Z',
                'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1',
                'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1',
                'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1',
            ] if game != 'gi' else ['Head', 'Body', 'Dress', 'Extra']
            
            self.terminal.print('Extracting model data of [{}]{}'.format(target_hash, f' - {name}' if name else ''))
            try:
                self.log_analysis.extract(c, target_hash)
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

            self.texture_analysis.set_preferred_texture_id(c, game)
            components.append(c)
        return components


    def export(self, export_name, components: list[Component], textures = None, game='zzz'):
        json_builder = JsonBuilder()

        extract_path = Path('_Extracted', export_name)
        # if extract_path.exists(): shutil.rmtree(extract_path) # TODO Should be optional
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

                merged_buffer_paths = (
                    ('position', [component.position_path] if component.position_path else component.backup_position_paths),
                    ('blend',    [component.blend_path   ] if component.blend_path    else []),
                    ('texcoord', [component.texcoord_path] if component.texcoord_path else component.backup_texcoord_paths),
                )

                for buffer_type, buffer_paths in merged_buffer_paths:
                    if len(buffer_paths) > 0:
                        try:
                            buffer_stride, buffer_elements = get_buffer_elements(buffer_paths)
                        except InvalidTextBufferException:
                            self.terminal.print('<ERROR>ERROR: Invalid text buffer!</ERROR>')
                            return
                        else:
                            buffer_path    = buffer_paths[0].with_suffix('.buf')
                            buffer_formats = [element.Format for element in buffer_elements]
                            buffer         = collect_binary_buffer_data(buffer_path, buffer_formats, buffer_stride)

                            if buffer_type == 'blend':
                                handle_no_weight_blend(buffer, buffer_elements)

                            buffers .append(buffer)
                            elements.append(buffer_elements)
                
                self.terminal.print(f'Constructing combined buffer for [{component.ib_hash}] - {component.name}')
                vb_merged = merge_buffers(buffers, elements) if buffers else None
            
            if component.options['collect_texture_data'] and  textures: _export_component_textures(export_name, component, textures[i])
            if component.options['collect_model_data']   and vb_merged: _export_component_buffers(export_name, component, vb_merged)

        json_out = json.dumps(json_builder.build(), indent=4)
        Path('_Extracted', export_name, 'hash.json').write_text(json_out)

        self.terminal.print('Export done: {:.3}s'.format(time.time() - st))


def _export_component_buffers(export_name: str, component: Component, vb_merged):
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

        vb0_file_path = Path('_Extracted', export_name, vb0_file_name)
        if not main_vb0_file_path:
            vb0_file_path.write_text(vb_merged)
            main_vb0_file_path = vb0_file_path
        else:
            shutil.copyfile(main_vb0_file_path, vb0_file_path)

        ib_file_path = Path('_Extracted', export_name, ib_file_name)
        shutil.copyfile(ib_path, ib_file_path)


def _export_component_textures(export_name: str, component: Component, textures):
    object_classification = component.object_classification
    for i, first_index in enumerate(textures):
        base_texture_file_name = '{}{}{}'.format(export_name, component.name, object_classification[i])
        for (texture, texture_type) in textures[first_index]:
            texture_file_name = base_texture_file_name + texture_type + texture.path.suffix
            shutil.copyfile(texture.path, Path('_Extracted', export_name, texture_file_name))
