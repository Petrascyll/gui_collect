from dataclasses import dataclass, field, asdict

from .buffer_utilities import parse_buffer_file_name
from .structs import Component

@dataclass
class JsonComponent():
    component_name : str = ''
    root_vs        : str = ''
    draw_vb        : str = ''
    position_vb    : str = ''
    blend_vb       : str = ''
    texcoord_vb    : str = ''
    ib             : str = ''
    
    object_indexes        : list[int] = field(default_factory=lambda:[])
    object_classifications: list[str] = field(default_factory=lambda:[])
    
    texture_hashes: list[list[tuple[str]]] = field(default_factory=lambda:[])


class JsonBuilder():
    def __init__(self):
        self.out = []

    def build(self) -> list[dict]:
        return self.out

    def add_component(self, component: Component, textures=None, game='zzz'):
        j = self.jsonify_component(component, textures, game)
        self.out.append(asdict(j))

    def jsonify_component(self, component: Component, textures=None, game='zzz'):
        json_component = JsonComponent(component_name=component.name)

        json_component.texture_hashes = [
            [
                [
                    texture_type,
                    texture.path.suffix,
                    texture.hash
                ]
                for (texture, texture_type) in textures[first_index]
            ]
            for first_index in textures
        ] if textures else [[] for _ in component.object_indices]
        
        json_component.object_indexes         = component.object_indices
        json_component.object_classifications = component.object_classification[:len(component.object_indices)]
        if game != 'zzz' and ('textures_only' in component.options and component.options['textures_only']):
            return json_component

        json_component.ib                     = parse_buffer_file_name(component.ib_paths[0].name)[2] if component.ib_paths else ''
        if game == 'zzz' and ('textures_only' in component.options and component.options['textures_only']):
            return json_component

        json_component.draw_vb = parse_buffer_file_name(component.backup_position_path.name)[2] if component.backup_position_path else ''

        if component.position_path:
            parsed = parse_buffer_file_name(component.position_path.name)
            json_component.root_vs     = parsed[4]['vs']
            json_component.position_vb = parsed[2]
        elif component.backup_position_path:
            json_component.position_vb = json_component.draw_vb

        texcoord_path = component.texcoord_path if component.texcoord_path else component.backup_texcoord_path            
        if texcoord_path:
            texcoord_hash = parse_buffer_file_name(texcoord_path.name)[2]
            json_component.texcoord_vb = texcoord_hash

        if component.blend_path:
            blend_hash = parse_buffer_file_name(component.blend_path.name)[2]
            json_component.blend_vb = blend_hash

        return json_component
