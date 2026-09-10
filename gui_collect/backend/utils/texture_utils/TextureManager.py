import subprocess
import threading
from pathlib import Path
from tkinter import PhotoImage

from gui_collect.common.file_explorer import _SYSTEM

from ...analysis.structs import Texture


class TextureManager:
    __instance = None

    temp_dir_filepath = None

    callbacks: dict[str, list] = {}
    callbacks_lock = threading.Lock()

    cached_images: dict[str, tuple[int, int, PhotoImage]] = {}
    invalid_textures: dict[str, tuple[int, int]] = {}

    def __init__(self, temp_dir: str):
        if TextureManager.__instance != None:
            raise Exception("TextureManager already created.")
        TextureManager.__instance = self
        self.temp_dir_filepath = Path(temp_dir)

        self.no_preview_image = PhotoImage(
            file=str(Path("./resources/images/textures/NoPreview.256.png").absolute())
        )

    @staticmethod
    def get_instance():
        if TextureManager.__instance == None:
            raise Exception("TextureManager hasn't been initialized.")
        return TextureManager.__instance

    def popen_and_call(self, texture: Texture, temp_filepath: Path, max_width: int):

        def run_in_thread(texture: Texture, temp_filepath: Path, max_width: int):
            _width, _height = texture.async_read_width_height(blocking=True)
            width, height = get_max_fit(_width, _height, max_width)

            is_generated = generate_thumbnail(
                texture.path, temp_filepath, width, height, max_width
            )
            image = None
            if is_generated:
                image = PhotoImage(file=str(temp_filepath.absolute()))
            else:
                image = self.no_preview_image
                width, height = 256, 256

            self.callbacks_lock.acquire(blocking=True)

            if is_generated:
                self.cached_images[temp_filepath.name] = (_width, _height, image)
            else:
                self.invalid_textures[temp_filepath.name] = (_width, _height)

            callbacks = [*self.callbacks[temp_filepath.name]]
            del self.callbacks[temp_filepath.name]

            self.callbacks_lock.release()

            for callback in callbacks:
                callback(image, width, height)

        thread = threading.Thread(
            target=run_in_thread, args=(texture, temp_filepath, max_width)
        )
        thread.start()
        return thread

    def get_image(self, texture: Texture, max_width, callback):
        temp_filepath = self.temp_dir_filepath / "{}.{}.png".format(
            texture.path.with_suffix("").name, max_width
        )

        if temp_filepath.name in self.cached_images:
            texture._width, texture._height, img = self.cached_images[
                temp_filepath.name
            ]
            width, height = get_max_fit(texture._width, texture._height, max_width)
            callback(img, width, height)
        elif temp_filepath.name in self.invalid_textures:
            texture._width, texture._height = self.invalid_textures[temp_filepath.name]
            callback(self.no_preview_image, 256, 256)

        else:
            self.callbacks_lock.acquire(blocking=True)

            # Check again if the texture already exists after we acquire the lock
            # in case the texture being requested is the same as the one that was
            # holding the lock
            if temp_filepath.name in self.cached_images:
                texture._width, texture._height, img = self.cached_images[
                    temp_filepath.name
                ]
                width, height = get_max_fit(texture._width, texture._height, max_width)
                callback(img, width, height)
            elif temp_filepath.name in self.invalid_textures:
                texture._width, texture._height = self.invalid_textures[
                    temp_filepath.name
                ]
                callback(self.no_preview_image, 256, 256)
            else:
                if temp_filepath.name in self.callbacks:
                    self.callbacks[temp_filepath.name].append(callback)
                    self.callbacks_lock.release()
                else:
                    self.callbacks[temp_filepath.name] = [callback]
                    self.popen_and_call(texture, temp_filepath, max_width)
                    self.callbacks_lock.release()
        return


def generate_thumbnail(texture_filepath: Path, dest_filepath: Path, width: int, height: int, max_width: int) -> bool:
    try:
        dest_filepath.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        return False

    if _SYSTEM == "Windows":
        return generate_thumbnail_exe(texture_filepath, dest_filepath, width, height, max_width)
    else:
        return generate_thumbnail_PIL(texture_filepath, dest_filepath, width, height)


def generate_thumbnail_PIL(texture_filepath: Path, dest_filepath: Path, width: int, height: int) -> bool:
    from PIL import Image

    try:
        with Image.open(texture_filepath) as img:
            img = img.convert("RGB")
            if img.size != (width, height):
                img = img.resize((width, height), Image.Resampling.NEAREST)
            img.save(dest_filepath, format="PNG")
        return True
    except Exception:
        return False


def generate_thumbnail_exe(texture_filepath: Path, dest_filepath: Path, width: int, height: int, max_width: int) -> bool:
    try:
        completed_process = subprocess.run(
            get_run_args(texture_filepath, dest_filepath.parent, max_width, width, height),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False
    return completed_process.returncode == 0


def get_run_args(texture_filepath: Path, temp_dir_filepath: Path, max_width: int, width: int, height: int):
    return [
        str(Path("modules", "texconv.exe").absolute()),
        str(texture_filepath.absolute()),
        "-y",  # ovewrite existing
        "-sx",
        f".{max_width}",  # Text string to attach to the end of the resulting texture's name
        "-sepalpha",  # useful if we're resizing in this step
        "-swizzle",
        "rgb1",  # Set alpha channel to 1
        "-m",
        "1",  # No mip maps
        "-if",
        "POINT",  # Image filter used for resizing
        "-w",
        str(width),
        "-h",
        str(height),
        "-ft",
        "png",
        "-o",
        str(temp_dir_filepath.absolute()),
    ]


def get_max_fit(width, height, max_side):
    """
    Get the max width and height that fit within max_side
    while maintaining the original aspect ratio
    """

    ratio = max_side / max(width, height)

    new_width = int(width * ratio)
    new_height = int(height * ratio)

    return new_width, new_height
