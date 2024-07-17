import os
import re
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass

from .frame_analysis import Component
from .buffer_utilities import parse_buffer_file_name

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


@dataclass
class SavedTexture():
    real_path : Path
    path      : Path
    hash      : str
    size      : int
    width     : int
    height    : int
    _width    : int
    _height   : int
    type      : str
    slot      : str
    is_contaminated: bool


def prepare_textures(components: list[Component], temp_dir: str):
    print('Preparing textures for preview', end='')
    st = time.time()

    processed_hashes       : dict[str, str] = {}
    temp_texture_file_paths: dict[str, SavedTexture] = {}
    skipped_texture_file_paths : list[str]  = []
    map_texture_file_paths : dict[str, str] = {}

    for component in components:
        for component_part_texture_data in component.texture_data.values():
            for texture_file_path in component_part_texture_data:

                print('.', end='', flush=True)

                texture_name      = texture_file_path.name
                temp_texture_name = texture_file_path.with_suffix('.png').name

                temp_texture_file_path = Path(temp_dir, temp_texture_name)
                # if temp_texture_file_path.exists():
                #     print('-', end='', flush=True)
                #     # print('Skipping already converted texture ', texture_file_path.name)
                #     continue

                filesize = os.path.getsize(texture_file_path)
                _, texture, texture_hash, is_contaminated, _ = parse_buffer_file_name(texture_name)
                if (
                    texture_hash in processed_hashes
                    and filesize > 128 * 1024 and not is_contaminated
                ):
                    print(',', end='', flush=True)
                    # print('Skipping duplicate texture ', texture_file_path.name)
                    original_texture_file_path = processed_hashes[texture_hash]
                    map_texture_file_paths[texture_file_path.name] = original_texture_file_path
                    continue

                if filesize < 64 * 1024:
                    print('_', end='', flush=True)
                    skipped_texture_file_paths.append(texture_file_path.name)
                    continue

                info = get_texdiag_info(texture_file_path)
                if not info:
                    print('x', end='', flush=True)
                    # print('Failed to analyze {}'.format(texture_name))
                    skipped_texture_file_paths.append(texture_file_path.name)
                    continue
                
                original_width  = int(info['width'])
                original_height = int(info['height'])
                width, height = get_max_fit(original_width, original_height, 256)

                result = create_temp_texture(texture_file_path, temp_dir, width, height)
                if result == 1:
                    print('x', end='', flush=True)
                    # print('Failed to convert {}'.format(texture_name))
                    skipped_texture_file_paths.append(texture_file_path.name)
                    continue

                if not is_contaminated:
                    processed_hashes[texture_hash] = texture_file_path.name
        
                temp_texture_file_paths[texture_file_path.name] = SavedTexture(
                    real_path = texture_file_path,
                    path      = temp_texture_file_path,
                    hash      = texture_hash,
                    _width    = width,
                    _height   = height,
                    size      = filesize,
                    width     = original_width,
                    height    = original_height,
                    type      = info['format'],
                    slot      = texture.split('-t')[1],
                    is_contaminated = is_contaminated
                )
    
    print('\nTextures ready ({:.3}s)'.format(time.time() - st))
    # subprocess.run([FILEBROWSER_PATH, Path(temp_dir)])

    return (
        temp_texture_file_paths,
        skipped_texture_file_paths,
        map_texture_file_paths
    )



def get_texdiag_info(filepath: str):
    '''
    - Executes `texdiag info` on the input texture filepath.
    - Parses the stdout result and returns it as a dict.\n
    ### All dict keys:
    * width
    * height
    * depth
    * mipLevels
    * arraySize
    * format
    * dimension
    * alpha mode
    * images
    * pixel size
    '''
    completed_process = subprocess.run(
        [
            str(Path('modules', 'texdiag.exe')),
            "info",
            "-nologo",
            filepath
        ],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )

    if completed_process.returncode != 0:
        return {}

    out = completed_process.stdout.decode('utf-8').strip()

    # Split each line, and discard the first.
    out = [l.strip() for l in out.splitlines()][1:]

    # Structure of each line is 'keyword = value'.
    pattern = re.compile(r'^(.*?)\s*=\s*(.*?)$')

    info = {}
    for line in out:
        m = re.match(pattern, line)
        info[m.group(1)] = m.group(2)

    return info

def create_temp_texture(texture_file_path, temp_dir, width, height):
    result = subprocess.run(
        [
            str(Path('modules', 'texconv.exe')),
            texture_file_path,
            "-y",               # ovewrite existing
            "-sepalpha", 		# useful if we're resizing in this step
            "-swizzle", "rgb1", # Set alpha channel to 1
            "-m", "1", 			# Remove mip aps
            "-w", str(width),
            "-h", str(height),
            "-ft", "png",
            "-o", temp_dir
        ],
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL,
    )
    return result.returncode

def get_max_fit(width, height, max_side):
    '''
        Get the max width and height that fit within max_side
        while maintaining the original aspect ratio
    '''

    ratio = max_side / max(width, height)

    new_width  = width * ratio
    new_height = height * ratio

    return new_width, new_height


