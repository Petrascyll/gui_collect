from pathlib import Path
from frame_analysis.buffer_utilities import parse_buffer_file_name


class Texture():
    def __init__(self, filepath: Path, texture_usage):

        self.path = filepath

        _, resource, resource_hash, resource_contaminated, _ = parse_buffer_file_name(filepath.name)
        self.hash         = resource_hash
        self.slot         = resource.split('ps-t')[1]
        self.contaminated = resource_contaminated

        assert(self.hash in texture_usage)

        self.width  = int(texture_usage[self.hash]['width'])
        self.height = int(texture_usage[self.hash]['height'])
        self.format : str = texture_usage[self.hash]['format']

        self._pow_2 = None

    def is_power_of_two(self):
        if self._pow_2 is not None: return self._pow_2
        self._pow_2 = is_power_of_two(self.width) and is_power_of_two(self.height)
        return self._pow_2

def is_power_of_two(n):
   return (n != 0) and (n & (n-1) == 0)
