import os
from pathlib import Path


from frame_analysis.buffer_utilities import parse_buffer_file_name

class Texture():
    def __init__(self, filepath: Path, texture_usage):

        self.path = filepath

        _, resource, resource_hash, resource_contamination, _ = parse_buffer_file_name(filepath.name)
        self.hash          = resource_hash
        self.contamination = resource_contamination
        self.slot          = int(resource.split('ps-t')[1])

        assert(self.hash in texture_usage)

        self.width  = int(texture_usage[self.hash]['width'])
        self.height = int(texture_usage[self.hash]['height'])
        self.format : str = texture_usage[self.hash]['format']

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
        self._size = os.path.getsize(self.path)
        return self._size

def is_power_of_two(n):
   return (n != 0) and (n & (n-1) == 0)
