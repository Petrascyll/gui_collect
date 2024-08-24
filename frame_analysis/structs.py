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

    # For debugging only for now, optimize later 
    def __str__(self):
        s = ''
        s += 'IDs: {}\n'.format(self.ids)
        s += 'Object Indices: {}\n'.format(self.object_indices)
        s += 'Backup Position Path: {}\n'.format(self.backup_position_path.name)
        s += 'Backup Texcoord Path: {}\n'.format(self.backup_texcoord_path.name)
        s += 'IBs:\n'
        for ib_path in self.ib_paths:
            s += '\t{}\n'.format(ib_path.name)

        s += 'Position Path: {}\n'.format(self.position_path.name)
        s += 'Texcoord Path: {}\n'.format(self.texcoord_path.name)
        s += 'Blend Path: {}\n'   .format(self.blend_path.name)

        return s + '\n'
