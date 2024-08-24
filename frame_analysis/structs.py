from dataclasses import dataclass, field
from enum import Enum, auto

from texture_utilities.Texture import Texture
from pathlib import Path


class BufferType(Enum):
    Position_VB = auto()
    Blend_VB    = auto()
    Texcoord_VB = auto()
    Draw_VB     = auto()
    IB          = auto()


BUFFER_NAME = {
    BufferType.Position_VB : 'Position VB',
    BufferType.Blend_VB    : 'Blend VB',
    BufferType.Texcoord_VB : 'Texcoord VB',
    BufferType.Draw_VB     : 'Draw VB',
    BufferType.IB          : 'IB',
}


@dataclass
class Component():
    name: str = ''
    options: list[dict[str, any]] = None

    position_path: Path = None
    blend_path   : Path = None
    texcoord_path: Path = None

    ids                  : list[str]  = field(default_factory=lambda:[])
    ib_paths             : list[Path] = field(default_factory=lambda:[])
    object_indices       : list[int]  = field(default_factory=lambda:[])
    object_classification: list[str]  = field(default_factory=lambda:[])

    backup_position_path: Path = None
    backup_texcoord_path: Path = None

    index_ids: dict[int, list[str]] = field(default_factory=lambda:{})
    tex_index_id: dict[int, str]    = field(default_factory=lambda:{})

    draw_hash     : str = None
    position_hash : str = None
    blend_hash    : str = None
    texcoord_hash : str = None
    ib_hash       : str = None

    def print(self, tabs=0):
        s = '\n'.join([
            # '{}Relevant IDs: {}'        .format('\t'*tabs, self.ids),
            '{}Index Buffer Paths:'          .format('\t'*tabs),
            *[
                '{}   {:8} - {}'.format('\t'*(tabs+1), first_index, ib_path.name)
                for ib_path, first_index in zip(self.ib_paths, self.object_indices)
            ],
            '{}Backup Position Path: {}'.format('\t'*tabs, self.backup_position_path.name if self.backup_position_path else ''),
            '{}Backup Texcoord Path: {}'.format('\t'*tabs, self.backup_texcoord_path.name if self.backup_texcoord_path else ''),
            '',
            '{} Position Path: {}'.format('\t'*tabs, self.position_path.name if self.position_path else ''),
            '{} Texcoord Path: {}'.format('\t'*tabs, self.texcoord_path.name if self.texcoord_path else ''),
            '{}    Blend Path: {}   '.format('\t'*tabs, self.blend_path.name if self.blend_path else ''),
        ])
        print(s)
