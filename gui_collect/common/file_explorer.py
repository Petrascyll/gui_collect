import logging
import platform
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_SYSTEM = platform.system()


def open_folder(path) -> None:
    path = Path(path)
    try:
        if _SYSTEM == "Windows":
            subprocess.run(["explorer", str(path)])
        elif _SYSTEM == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        logger.exception("Failed to open folder: <PATH>%s</PATH>", path)


_LINUX_SELECT_COMMANDS = {
    "nautilus"  : ["--select"],
    "dolphin"   : ["--select"],
    "nemo"      : [],
    "pcmanfm-qt": ["--select"],
}


def reveal_file(path) -> None:
    path = Path(path)
    try:
        if _SYSTEM == "Windows":
            subprocess.run(["explorer", "/select,", str(path)])
        elif _SYSTEM == "Darwin":
            subprocess.run(["open", "-R", str(path)])
        else:
            _reveal_file_linux(path)
    except Exception:
        logger.exception("Failed to reveal file: <PATH>%s</PATH>", path)


def _reveal_file_linux(path: Path) -> None:
    for exe_name, extra_args in _LINUX_SELECT_COMMANDS.items():
        exe = shutil.which(exe_name)
        if exe:
            subprocess.run([exe, *extra_args, str(path)])
            return

    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        subprocess.run([xdg_open, str(path.parent)])
    else:
        logger.warning(
            "No usable file manager found to reveal: <PATH>%s</PATH>", path
        )
