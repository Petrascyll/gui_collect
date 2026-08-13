import os
import re
import subprocess
from pathlib import Path


# Structure of each line is 'keyword = value'
LINE_PATTERN = re.compile(r"^(.*?)\s*=\s*(.*?)$")


def get_texdiag_info(filepath: str):
    """
    - Executes `texdiag info` on the input texture filepath.
    - Uses `file -b` instead of `texdiag info` on linux.
    - Parses the stdout result and returns it as a dict.
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
        [str(Path("modules", "texdiag.exe")), "info", "-nologo", filepath] if os.name == 'nt' else ["file", "-b", filepath],
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

    info = {}
    if os.name == 'nt':
        # Split each line, and discard the first.
        out = [l.strip() for l in out.splitlines()][1:]

        for line in out:
            m = LINE_PATTERN.match(line)
            info[m.group(1)] = m.group(2)
    else:
        outlist = out.replace(" ","").split(',')
        dimensions = outlist[0].split(':')[1].split('x')

        info['format'] = outlist[-1].split(':')[-1]
        info['width'] = dimensions[0]
        info['height'] = dimensions[1]

    return info
