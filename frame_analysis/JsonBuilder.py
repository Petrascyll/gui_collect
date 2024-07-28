from dataclasses import dataclass, field, asdict

from .buffer_utilities import parse_buffer_file_name


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
    
    texture_hashes: list[list[tuple[str]]] = field(default_factory=lambda:[[]])


class JsonBuilder():
    def __init__(self):
        self.out = []

    def build(self) -> list[dict]:
        return self.out

    def add_component(self, component, textures=None):
        j = self.jsonify_component(component, textures)
        self.out.append(asdict(j))

    def jsonify_component(self, component, textures=None):
        json_component = JsonComponent(component_name=component.name)

        draw_hash = parse_buffer_file_name(component.backup_position_path.name)[2]
        ib_hash   = parse_buffer_file_name(component.ib_paths[0].name)[2]

        json_component.draw_vb = draw_hash
        json_component.ib      = ib_hash

        if component.position_path:
            parsed = parse_buffer_file_name(component.position_path.name)
            position_hash = parsed[2]
            root_vs_hash  = parsed[4]['vs']
            json_component.root_vs     = root_vs_hash
            json_component.position_vb = position_hash
        else:
            json_component.position_vb = draw_hash

        texcoord_path = component.texcoord_path if component.texcoord_path else component.backup_texcoord_path            
        if texcoord_path:
            texcoord_hash = parse_buffer_file_name(texcoord_path.name)[2]
            json_component.texcoord_vb = texcoord_hash

        if component.blend_path:
            blend_hash = parse_buffer_file_name(component.blend_path.name)[2]
            json_component.blend_vb = blend_hash

        json_component.object_indexes = sorted([int(d) for d in component.object_indices])
        json_component.object_classifications = component.object_classification[:len(component.object_indices)]

        if textures:
            json_component.texture_hashes = [
                [
                    [
                        texture_type,
                        saved_texture.real_path.suffix,
                        saved_texture.hash
                    ]
                    for (saved_texture, texture_type) in textures[first_index]
                ]
                for first_index in textures
            ]

        return json_component
    