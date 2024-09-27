from dataclasses import dataclass, field, asdict

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

        json_component.texture_hashes         = [[] for _ in component.object_indices]
        json_component.object_indexes         = component.object_indices
        json_component.object_classifications = component.object_classification[:len(component.object_indices)]

        if component.options['collect_texture_hashes']:
            if textures:
                json_component.texture_hashes = [
                    [
                        [texture_type, texture.path.suffix, texture.hash]
                        for (texture, texture_type) in textures[first_index]
                    ] for first_index in textures
                ]
            if game == 'zzz': json_component.ib = component.ib_hash

        if component.options['collect_model_hashes']:
            json_component.ib = component.ib_hash
            json_component.draw_vb = component.draw_hash

            if component.position_path:
                json_component.root_vs     = component.root_vs_hash
                json_component.position_vb = component.position_hash
            elif component.backup_position_paths:
                json_component.position_vb = component.draw_hash

            json_component.texcoord_vb = component.texcoord_hash
            json_component.blend_vb    = component.blend_hash

        return json_component
