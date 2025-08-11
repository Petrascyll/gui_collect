import struct
import threading
from dataclasses import dataclass, field
from pathlib import Path
from os.path import getsize
from frontend.state import State

from backend.utils.texture_utils.texdiag_helper import get_texdiag_info


class Texture():
    def __init__(
            self, filepath: Path, *,
            texture_slot:str, texture_hash:str, texture_format:str=None,
            contamination:str, extension:str
        ):
        self.path: Path = filepath

        self.slot         : str = texture_slot
        self.hash         : str = texture_hash
        self.contamination: str = contamination
        self.extension    : str = extension

        self._read_lock      = threading.Lock()
        self._read_thread    = None
        self._read_callbacks = []
        self._width : int = None
        self._height: int = None

        self._format: str = None if not texture_format else texture_format
        self._read_format_lock      = threading.Lock()
        self._read_format_thread    = None
        self._read_format_callbacks = []

        self._pow_2 = None
        self._size  = None

    def async_read_format(self, callback=None, *, blocking=False):
        if not callback and not blocking:
            raise Exception()

        if self._format:
            if callback: return callback()
            return

        def run_in_thread():
            try:
                texdiag_info = get_texdiag_info(str(self.path.absolute()))
                _format = texdiag_info['format']
                # might as well set _width and _height to cause
                # async_read_width_height to return immediately
                # if [blocking] async_read_format has been called
                # before it
                _width  = int(texdiag_info['width'])
                _height = int(texdiag_info['height'])
            except ZeroDivisionError:
                _format = '???'
                _width  = 1
                _height = 1

            self._read_format_lock.acquire()
            self._read_format_thread = None
            self._format = _format
            self._width  = _width
            self._height = _height
            callbacks = [*self._read_format_callbacks]
            self._read_format_callbacks = []
            self._read_format_lock.release()

            for callback in callbacks:
                callback()

        self._read_format_lock.acquire()
        if self._format:
            self._read_format_lock.release()
            if callback: return callback()
            return

        if not self._read_format_thread:
            if callback: self._read_format_callbacks.append(callback)
            self._read_format_thread = threading.Thread(target=run_in_thread, args=())
            self._read_format_thread.start()
        self._read_format_lock.release()

        if callback is None:
            self._read_format_thread.join()
            return

    def async_read_width_height(self, callback=None, *, blocking=False):
        if not callback and not blocking:
            raise Exception()

        if self._width and self._height:
            if callback: return callback(self._width, self._height)
            return self._width, self._height
        if self.extension not in ['jpg', 'dds']:
            print(f'Reading width/height from {str(self.path.name)} is unsupported.')
            if callback: callback(1, 1)
            return 1, 1

        def run_in_thread():
            try:
                _width, _height = read_width_height(self.path)
            except:
                print(f'Failed to read width/height from {str(self.path.name)}.')
                _width, _height = 1, 1
            
            self._read_lock.acquire()
            self._read_thread = None
            self._width, self._height = _width, _height
            callbacks = [*self._read_callbacks]
            self._read_callbacks = []
            self._read_lock.release()

            for callback in callbacks:
                callback(self._width, self._height)

        self._read_lock.acquire()
        if self._width and self._height:
            self._read_lock.release()
            if callback: return callback(self._width, self._height)
            return self._width, self._height

        if not self._read_thread:
            if callback: self._read_callbacks.append(callback)
            self._read_thread = threading.Thread(target=run_in_thread, args=())
            self._read_thread.start()
        self._read_lock.release()
        
        if callback is None:
            self._read_thread.join()
            return self._width, self._height

    def is_contaminated(self):
        return self.contamination is not None

    def is_power_of_two(self):
        if not self._width or not self._height:
            raise Exception('Texture has not been read yet!')
        if self._pow_2 is not None: return self._pow_2

        self._pow_2 = is_power_of_two(self._width) and is_power_of_two(self._height)
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


def read_width_height(image_path):
    width, height = -1, -1
    with open(image_path, 'rb', buffering=20) as f:

        magic_dword = bytes.hex(f.read(4))

        # DDS Magic DWORD
        # https://learn.microsoft.com/en-us/windows/win32/direct3ddds/dx-graphics-dds-pguide
        # https://learn.microsoft.com/en-us/windows/win32/direct3ddds/dds-header
        if magic_dword == '44445320':
            # Size of structure. This member must be set to 124.
            dwSize = struct.unpack('<I', f.read(4))[0]
            if dwSize != 124:
                raise Exception('\tInvalid DDS File. Invalid structure size.')

            # Flags to indicate which members contain valid data.
            dwFlags = int.from_bytes(f.read(4), byteorder='little')
            
            # Required in every .dds file.
            DDSD_CAPS_FLAG   = (dwFlags & 0x1) >> 0
            DDSD_HEIGHT_FLAG = (dwFlags & 0x2) >> 1
            DDSD_WIDTH_FLAG  = (dwFlags & 0x4) >> 2
            if not(DDSD_CAPS_FLAG & DDSD_HEIGHT_FLAG & DDSD_WIDTH_FLAG):
                raise Exception('\tInvalid DDS File. Invalid flags.')
            
            height, width = struct.unpack('<II', f.read(8))
        
        # JPG Magic DWORD 
        # https://github.com/scardine/image_size
        # yoinked from `get_image_size.py` [MIT License]
        elif magic_dword == 'ffd8ffe0':
            f.seek(0)
            f.read(2)
            b = f.read(1)
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF):
                    b = f.read(1)
                while (ord(b) == 0xFF):
                    b = f.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    f.read(3)
                    h, w = struct.unpack(">HH", f.read(4))
                    break
                else:
                    f.read(int(struct.unpack(">H", f.read(2))[0]) - 2)
                b = f.read(1)
            width, height = int(w), int(h)

        # Unknown DWORD
        else:
            # TODO
            raise Exception('Unimplemented')

    return (width, height)



@dataclass
class ID_Data():
    vs_hash: str = ''
    ps_hash: str = ''
    textures: list[Texture] = field(default_factory=lambda:[])

@dataclass
class Component():
    name: str = ''
    options: dict[str, any] = None

    position_path: Path = None
    blend_path   : Path = None
    texcoord_path: Path = None

    shapekey_buffer_path: Path  = None
    shapekey_buffer_hash: str   = ''
    shapekey_cb_paths   : list[Path] = field(default_factory=lambda:[])
    cs_hash : str = ''
    uav_hash: str = ''

    ids                  : list[str]  = field(default_factory=lambda:[])
    ib_paths             : list[Path] = field(default_factory=lambda:[])
    object_indices       : list[int]  = field(default_factory=lambda:[])
    object_indices_counts: list[int]  = field(default_factory=lambda:[])
    object_classification: list[str]  = field(default_factory=lambda:[])

    backup_position_paths: list[Path] = None
    backup_texcoord_paths: list[Path] = None
    backup_draw_vb2_paths: list[Path] = None

    tex_index_id: dict[int, str]                = field(default_factory=lambda:{})
    draw_data   : dict[int, dict[str, ID_Data]] = field(default_factory=lambda:{})

    root_cs_hash  : str = ''
    pose_cs_hash  : str = ''
    root_vs_hash  : str = ''
    draw_hash     : str = ''
    position_hash : str = ''
    blend_hash    : str = ''
    texcoord_hash : str = ''
    ib_hash       : str = ''

    draw_vb2_hash: str = ''

    def print(self, tabs=0):
        s = [
            # '{}Relevant IDs: {}'        .format('\t'*tabs, self.ids),
            'Index Buffer Paths:',
            *[
                '     {:8} - <PATH>{}</PATH>'.format(first_index, ib_path.name)
                for ib_path, first_index in zip(self.ib_paths, self.object_indices)
            ],
            'Draw VB0 Path: <PATH>{}</PATH>'.format(self.backup_position_paths[0].with_suffix('.buf').name if self.backup_position_paths else ''),
            'Drwa VB1 Path: <PATH>{}</PATH>'.format(self.backup_texcoord_paths[0].with_suffix('.buf').name if self.backup_texcoord_paths else ''),
            'Draw VB2 Path: <PATH>{}</PATH>'.format(self.backup_draw_vb2_paths[0].with_suffix('.buf').name if self.backup_draw_vb2_paths else ''),
            '',
            'Position Path: <PATH>{}</PATH>'.format(self.position_path.with_suffix('.buf').name if self.position_path else ''),
            'Texcoord Path: <PATH>{}</PATH>'.format(self.texcoord_path.with_suffix('.buf').name if self.texcoord_path else ''),
            '   Blend Path: <PATH>{}</PATH>'.format(self.blend_path.with_suffix('.buf').name if self.blend_path else ''),
        ]

        if self.shapekey_buffer_path:
            s.append(
                'Shapekey Path: <PATH>{}</PATH>'.format(self.shapekey_buffer_path.name),
            )

        terminal = State.get_instance().get_terminal()
        for line in s:
            terminal.print(line, timestamp=False)
