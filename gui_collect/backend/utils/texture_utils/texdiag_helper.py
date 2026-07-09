import re
import subprocess
from pathlib import Path

from PIL import Image

from gui_collect.common.file_explorer import _SYSTEM

# Structure of each line is 'keyword = value'
LINE_PATTERN = re.compile(r"^(.*?)\s*=\s*(.*?)$")


def get_texdiag_info(filepath: str):
    if _SYSTEM == "Windows":
        return process_exe(filepath)
    else:
        return process_PIL(filepath)


def process_PIL(filepath: str):
    """
    - Opens the input texture filepath with Pillow and reads its dimensions
      and pixel format.
    - Returns a dict with the same shape `texdiag info` output was parsed
      into, though only the keys actually consumed elsewhere are populated:
    ### Populated dict keys:
    * width
    * height
    * format
    """
    with Image.open(filepath) as img:
        try:
            width, height = img.size

            # DdsImageFile exposes ".pixel_format" for compressed DDS data (e.g. "BC7");
            # fall back to the PIL image mode (e.g. "RGBA") for uncompressed DDS data and other formats like jpg
            pixel_format = getattr(img, "pixel_format", None) or img.mode

            return {
                "width" : str(width),
                "height": str(height),
                "format": pixel_format,
            }
        except Exception as e:
            raise ZeroDivisionError() from e


def process_exe(filepath: str):
    """
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
    """
    completed_process = subprocess.run(
        [str(Path("modules", "texdiag.exe")), "info", "-nologo", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if completed_process.returncode != 0:
        raise ZeroDivisionError()

    out = completed_process.stdout
    try:
        out = out.decode("utf-8").strip()

    # I am not entirely sure why the decode fails, but I suspect its
    # related to the usage of non-english characters in the user name
    # or a non-english language being the language of the computer
    # causing the shell to use odd characters
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xce in position 9: invalid continuation byte
    except UnicodeDecodeError:
        out = out.decode("latin-1").strip()

    # Split each line, and discard the first.
    out = [l.strip() for l in out.splitlines()][1:]

    info = {}
    for line in out:
        m = LINE_PATTERN.match(line)
        info[m.group(1)] = m.group(2)

    return info
