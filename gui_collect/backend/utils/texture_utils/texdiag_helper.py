import re
import subprocess
from pathlib import Path


import os

# Structure of each line is 'keyword = value'
LINE_PATTERN = re.compile(r"^(.*?)\s*=\s*(.*?)$")


def get_texdiag_info(filepath: str):
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
    if os.name != "nt":
        completed_process = subprocess.run(
            ["file", "-b", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if completed_process.returncode != 0:
            raise ZeroDivisionError()

        out = completed_process.stdout.strip()
        match = re.search(r"Microsoft DirectDraw Surface \(DDS\):\s*(\d+)\s*x\s*(\d+),\s*(.*)", out)
        if not match:
            raise ZeroDivisionError()

        width = match.group(1)
        height = match.group(2)
        format_detail = match.group(3)

        fmt = "???"
        if "DXGI format:" in format_detail:
            fmt = format_detail.split("DXGI format:", 1)[1].strip()
        elif "compressed using" in format_detail:
            fmt = format_detail.split("compressed using", 1)[1].strip()
        else:
            fmt = format_detail.strip()

        return {
            "width": width,
            "height": height,
            "format": fmt,
            "depth": "1",
            "mipLevels": "1",
            "arraySize": "1",
            "dimension": "2D",
            "alpha mode": "unknown",
            "images": "1",
            "pixel size": "unknown"
        }

    completed_process = subprocess.run(
        [str(Path("modules", "texdiag.exe")), "info", "-nologo", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

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
