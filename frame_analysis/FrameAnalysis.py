import json
import time
import shutil

from pathlib import Path

from .LogAnalysis     import LogAnalysis
from .FileAnalysis    import FileAnalysis
from .TextureAnalysis import TextureAnalysis

from .structs import Component
from .JsonBuilder import JsonBuilder
from .buffer_utilities import collect_buffer_data, extract_from_txt, merge_buffers, handle_no_weight_blend


class FrameAnalysis():
    def __init__(self, frame_analysis_path: Path):
        print(frame_analysis_path)

        self.path = frame_analysis_path
        self.log_analysis     =     LogAnalysis(self.path)
        self.file_analysis    =    FileAnalysis(self.path)
        self.texture_analysis = TextureAnalysis(self.path)

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
                'U', 'V', 'W', 'X', 'Y', 'Z'
            ] if game != 'gi' else ['Head', 'Body', 'Dress', 'Extra']
            
            print('\tExtracting model data of [{}]{}'.format(target_hash, f' - {name}' if name else ''))
            try:
                self.log_analysis.extract(c, target_hash)
                self.check_extraction_sanity(c)
                c.print(tabs=2)
            except Exception as X:
                print('\t\tLog Analysis  Failed [{}] - {}'.format(target_hash, X))
                try:
                    self.file_analysis.extract(c, target_hash)
                    self.check_extraction_sanity(c)
                    c.print(tabs=2)
                except Exception as X:
                    print('\t\tFile Analysis Failed [{}] - {}'.format(target_hash, X))
                    return

            self.texture_analysis.set_preferred_texture_id(c, game)
            components.append(c)
        return components

    @staticmethod
    def check_extraction_sanity(component: Component):
        st = time.time()
        paths = (
            component.backup_position_path,
            component.backup_texcoord_path,
            component.position_path,
            component.texcoord_path,
            component.blend_path
        )
        vcount = None
        for path in paths:
            if not vcount: vcount = extract_from_txt('vertex count', path)
            if path: assert(vcount == extract_from_txt('vertex count', path))
        print('\t\tSanity Checks Done: {:.6}s'.format(time.time() - st))

    @staticmethod
    def export(export_name, components: list[Component], textures = None, game='zzz'):
        json_builder = JsonBuilder()

        extract_path = Path('_Extracted', export_name)
        # if extract_path.exists(): shutil.rmtree(extract_path) # TODO Should be optional
        extract_path.mkdir(parents=True, exist_ok=True)

        for i, component in enumerate(components):
            json_builder.add_component(component, textures[i] if textures else None, game)

            if 'textures_only' in component.options and component.options['textures_only']:
                vb_merged = None
            else: 
                buffers = []
                formats = []
                if component.position_path or component.backup_position_path:
                    position, position_format = collect_buffer_data(component.position_path if component.position_path else component.backup_position_path)
                    buffers.append(position)
                    formats.append(position_format)
                
                if component.blend_path:
                    blend, blend_format = collect_buffer_data(component.blend_path)
                    handle_no_weight_blend(blend, blend_format)
                    buffers.append(blend)
                    formats.append(blend_format)
                
                if component.texcoord_path or component.backup_texcoord_path:
                    texcoord, texcoord_format = collect_buffer_data(component.texcoord_path if component.texcoord_path else component.backup_texcoord_path)
                    buffers.append(texcoord)
                    formats.append(texcoord_format)

                vb_merged = merge_buffers(buffers, formats)
            
            if textures : _export_component_textures(export_name, component, textures[i])
            if vb_merged: _export_component_buffers(export_name, component, vb_merged)

        json_out = json.dumps(json_builder.build(), indent=4)
        Path('_Extracted', export_name, 'hash.json').write_text(json_out)


def _export_component_buffers(export_name: str, component: Component, vb_merged):
    object_classification = component.object_classification

    for i, ib_path in enumerate(component.ib_paths):
        prefix = export_name + component.name + object_classification[i]
        vb0_file_name = '{}-vb0={}.txt'.format(prefix, component.position_hash if component.position_hash else component.draw_hash)
        ib_file_name  = '{}-ib={}.txt' .format(prefix, component.ib_hash)

        vb0_file_path = Path('_Extracted', export_name, vb0_file_name)
        vb0_file_path.write_text(vb_merged)

        ib_file_path = Path('_Extracted', export_name, ib_file_name)
        shutil.copyfile(ib_path, ib_file_path)


def _export_component_textures(export_name: str, component: Component, textures):
    object_classification = component.object_classification
    for i, first_index in enumerate(textures):
        base_texture_file_name = '{}{}{}'.format(export_name, component.name, object_classification[i])
        for (texture, texture_type) in textures[first_index]:
            texture_file_name = base_texture_file_name + texture_type + texture.path.suffix
            shutil.copyfile(texture.path, Path('_Extracted', export_name, texture_file_name))
