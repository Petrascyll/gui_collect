from pathlib import Path
import re
from enum import Enum

from .structs import Component

from backend.analysis.structs import Texture


class TextureAnalysis():
    F = Enum('FILTER', 'ONLY_POW_2 MIN_SIZE MIN_WIDTH MIN_HEIGHT')
    def __init__(self, frame_analysis_path: Path):
        self.frame_analysis_path = frame_analysis_path
        self.texture_filepaths: list[Path] = [f for f in frame_analysis_path.iterdir() if f.suffix in ['.dds', '.jpg']]

        p = re.compile(r'<Register orig_hash=([a-f0-9]{8}) type=Texture2D width=(\d*?) height=(\d*?) .*? format="(.*?)"')
        self.texture_usage = {
            hash: {'width' : w, 'height': h, 'format': f}
            for (hash, w, h, f) in p.findall((self.frame_analysis_path/'ShaderUsage.txt').read_text(encoding='utf-8'))
        }

        self.cached_textures: dict[str, list[Texture]] = {}
        self.filters = {
            self.F.ONLY_POW_2: {
                'active': True,
            },
            self.F.MIN_SIZE:  {
                'active': True,
                'value': 64 * 1024,
            },
            self.F.MIN_WIDTH: {
                'active': True,
                'value': 256
            },
            self.F.MIN_HEIGHT: {
                'active': True,
                'value': 256
            },
        }

    def set_preferred_texture_id(self, component: Component, game):
        for first_index in component.index_ids:
            ids = component.index_ids[first_index]
            for id in ids:
                if game == 'gi' and int(id) < 10: continue

                no_o0 = 0 == len([
                    f for f in self.texture_filepaths
                    if f.name.startswith(f'{id}-o0')
                    and f.suffix in ['.dds', '.jpg']
                ])
                if game != 'gi' and no_o0: continue

                component.tex_index_id[first_index] = id
                break

            else:
                component.tex_index_id[first_index] = ids[0]

    # def get_default_filers(self) -> dict[F, dict[str, any]]:
    #     return {}

    def get_textures(self, draw_id: str):
        if draw_id not in self.cached_textures:
            self.cached_textures[draw_id] = sorted([
                    Texture(f, self.texture_usage)
                    for f in self.texture_filepaths
                    if f.name.startswith(f'{draw_id}-ps-t')
                    and f.suffix in ['.dds', '.jpg']
                ],
                # Sort Textures by slot numerically to avoid 0 -> 1 -> 10 -> 2 -> 3
                key=lambda texture: texture.slot
            )

        filtered_textures = [
            tex
            for tex in self.cached_textures[draw_id]
            # if  (self.filters[self.F.ONLY_POW_2]['active'] and tex.is_power_of_two())
            # and (self.filters[self.F.MIN_SIZE  ]['active'] and tex.get_size() >= self.filters[self.F.MIN_SIZE  ]['value'])
            # and (self.filters[self.F.MIN_WIDTH ]['active'] and tex.width      >= self.filters[self.F.MIN_WIDTH ]['value'])
            # and (self.filters[self.F.MIN_HEIGHT]['active'] and tex.height     >= self.filters[self.F.MIN_HEIGHT]['value'])
        ]
        return filtered_textures
