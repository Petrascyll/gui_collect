from dataclasses import dataclass, field
from pathlib import Path
from os.path import getsize

from backend.utils import is_valid_hash
from backend.utils.buffer_utils.buffer_encoder import parse_buffer_file_name

from frontend.state import State


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

    backup_position_paths: list[Path] = None
    backup_texcoord_paths: list[Path] = None

    index_ids: dict[int, list[str]] = field(default_factory=lambda:{})
    tex_index_id: dict[int, str]    = field(default_factory=lambda:{})

    root_vs_hash  : str = ''
    draw_hash     : str = ''
    position_hash : str = ''
    blend_hash    : str = ''
    texcoord_hash : str = ''
    ib_hash       : str = ''

    def print(self, tabs=0):
        s = [
            # '{}Relevant IDs: {}'        .format('\t'*tabs, self.ids),
            'Index Buffer Paths:',
            *[
                '     {:8} - <PATH>{}</PATH>'.format(first_index, ib_path.name)
                for ib_path, first_index in zip(self.ib_paths, self.object_indices)
            ],
            'Backup Position Path: <PATH>{}</PATH>'.format(self.backup_position_paths[0].with_suffix('.buf').name if self.backup_position_paths else ''),
            'Backup Texcoord Path: <PATH>{}</PATH>'.format(self.backup_texcoord_paths[0].with_suffix('.buf').name if self.backup_texcoord_paths else ''),
            '',
            'Position Path: <PATH>{}</PATH>'.format(self.position_path.with_suffix('.buf').name if self.position_path else ''),
            'Texcoord Path: <PATH>{}</PATH>'.format(self.texcoord_path.with_suffix('.buf').name if self.texcoord_path else ''),
            '   Blend Path: <PATH>{}</PATH>'.format(self.blend_path.with_suffix('.buf').name if self.blend_path else ''),
        ]

        terminal = State.get_instance().get_terminal()
        for line in s:
            terminal.print(line, timestamp=False)



class Texture():
    def __init__(self, filepath: Path, texture_usage):

        self.path = filepath

        _, resource, resource_hash, resource_contamination, _ = parse_buffer_file_name(filepath.name)

        if is_valid_hash(resource_hash, 8):
            self.hash          = resource_hash
            self.contamination = resource_contamination
            self.slot          = int(resource.split('ps-t')[1].split('-')[0])

            if self.hash not in texture_usage:
                State.get_instance().get_terminal().print(f'<ERROR>Failed to find texture hash {self.hash} in ShaderUsage.txt</ERROR>')
                raise Exception()

            self.width  = int(texture_usage[self.hash]['width'])
            self.height = int(texture_usage[self.hash]['height'])
            self.format : str = texture_usage[self.hash]['format']

        else:
            self.hash          = '???'
            self.contamination = None
            self.slot          = int(resource.split('ps-t')[1].split('-')[0])

            self.width  = 1
            self.height = 1
            self.format = '???'

        self._pow_2 = None
        self._size  = None

    def is_contaminated(self):
        return self.contamination is not None

    def is_power_of_two(self):
        if self._pow_2 is not None: return self._pow_2
        self._pow_2 = is_power_of_two(self.width) and is_power_of_two(self.height)
        return self._pow_2

    def get_size(self):
        '''
            returns size of file in bytes
        '''
        if self._size is not None: return self._size
        self._size = getsize(self.path)
        return self._size


def is_power_of_two(n):
   return (n != 0) and (n & (n-1) == 0)
