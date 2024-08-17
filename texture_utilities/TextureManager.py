import subprocess
import threading
from pathlib import Path

from .Texture import Texture


class TextureManager():
    __instance = None

    temp_dir_filepath    = None
    ready_temp_filenames = set()

    callbacks: dict[str, list] = {}
    callbacks_lock = threading.Lock()

    def __init__(self, temp_dir: str):
        if TextureManager.__instance != None:
            raise Exception('TextureManager already created.')
        TextureManager.__instance = self
        self.temp_dir_filepath = Path(temp_dir)
        # subprocess.run([FILEBROWSER_PATH, Path(temp_dir)])

    @staticmethod
    def get_instance():
        if TextureManager.__instance == None:
            raise Exception('TextureManager hasn\'t been initialized.')
        return TextureManager.__instance

    def popen_and_call(self, temp_filepath: Path, width, height, popen_args):

        def run_in_thread(temp_filepath: Path, width, height, popen_args):
            proc = subprocess.Popen(
                popen_args,
                stdout = subprocess.DEVNULL,
                stderr = subprocess.DEVNULL,
            )
            proc.wait()

            self.callbacks_lock.acquire(blocking=True)

            self.ready_temp_filenames.add(temp_filepath.name)
            callbacks = [*self.callbacks[temp_filepath.name]]
            del self.callbacks[temp_filepath.name]

            self.callbacks_lock.release()

            for callback in callbacks:
                callback(temp_filepath, width, height)

        thread = threading.Thread(target=run_in_thread, args=(temp_filepath, width, height, popen_args))
        thread.start()
        return thread


    def get_image(self, texture: Texture, max_width, callback):
        temp_filepath = self.temp_dir_filepath / '{}.{}.png'.format(texture.path.with_suffix('').name, max_width)
        width, height = get_max_fit(texture.width, texture.height, max_width)

        if temp_filepath.name in self.ready_temp_filenames:
            callback(temp_filepath, width, height)
        else:
            self.callbacks_lock.acquire(blocking=True)

            # Check again if the texture already exists after we acquire the lock
            # in case the texture being requested is the same as the one that was
            # holding the lock
            if temp_filepath.name in self.ready_temp_filenames:
                callback(temp_filepath, width, height)
            # Checking if the temp filepath alone exists is not enough to guarantee that
            # its safe to use as texconv may still be in the middle of writing to it
            # if temp_filepath.exists() and temp_filepath.name not in self.callbacks:
            #     self.callbacks_lock.release()
            #     callback(temp_filepath, width, height)

            else:
                if temp_filepath.name in self.callbacks:
                    self.callbacks[temp_filepath.name].append(callback)
                    self.callbacks_lock.release()
                else:
                    self.callbacks[temp_filepath.name] = [callback]
                    popen_args = get_popen_args(texture.path, self.temp_dir_filepath, max_width, width, height)
                    self.popen_and_call(temp_filepath, width, height, popen_args)
                    self.callbacks_lock.release()
        return


def get_popen_args(texture_filepath, temp_dir_filepath, max_width, width, height):
    return [
        str(Path('modules', 'texconv.exe').absolute()),
        str(texture_filepath.absolute()),
        "-y",                   # ovewrite existing
        "-sx", f'.{max_width}', # Text string to attach to the end of the resulting texture's name
        "-sepalpha",            # useful if we're resizing in this step
        "-swizzle", "rgb1",     # Set alpha channel to 1
        "-m", "1",              # No mip maps
        "-if", "POINT",         # Image filter used for resizing
        "-w", str(width),
        "-h", str(height),
        "-ft", "png",
        "-o", str(temp_dir_filepath.absolute())
    ]


def get_max_fit(width, height, max_side):
    '''
        Get the max width and height that fit within max_side
        while maintaining the original aspect ratio
    '''

    ratio = max_side / max(width, height)

    new_width  = width * ratio
    new_height = height * ratio

    return new_width, new_height
