from dataclasses import dataclass, field, asdict, is_dataclass
from pathlib import Path

default_extract_path = str(Path('.', '_Extracted').absolute())

GAME_NAME = {
    'zzz': 'Zenless Zone Zero',
    'hsr': 'Honkai: Star Rail',
    'gi' : 'Genshin Impact',
    'hi3': 'Honkai Impact 3rd',
}

@dataclass
class _TargetedConfigOptionData():
    force_dump_dds : bool = False
    dump_rt        : bool = True
    symlink        : bool = False
    share_dupes    : bool = False

@dataclass
class _GameConfigOptionData():
    clean_extract_folder: bool = True
    open_extract_folder : bool = True
    delete_frame_analysis : bool = False

@dataclass
class _GameConfigData():
    frame_analysis_parent_path: str = ''
    extract_path              : str = default_extract_path
    game_options     :     _GameConfigOptionData = field(default_factory=lambda:     _GameConfigOptionData())
    targeted_options : _TargetedConfigOptionData = field(default_factory=lambda: _TargetedConfigOptionData())

    def __post_init__(self):
        if not is_dataclass(self.game_options):
            self.game_options     =     _GameConfigOptionData(**self.game_options)
            self.targeted_options = _TargetedConfigOptionData(**self.targeted_options)

@dataclass
class ConfigData():
    active_game: str = 'zzz'
    targeted_analysis_enabled: bool = False
    game: dict[str, _GameConfigData] = field(
        default_factory= lambda: {
            'zzz': _GameConfigData(),
            'hsr': _GameConfigData(),
            'gi' : _GameConfigData(),
            'hi3' : _GameConfigData(),
        }
    )
    def __post_init__(self):
        for k in self.game:
            if not is_dataclass(self.game[k]):
                self.game[k] = _GameConfigData(**self.game[k])

    @staticmethod
    def validate_config_data(d: dict):
        '''
            This method will check if all keys are present and
            add if needed add those keys with default values. 
            Unrecognized and deprecated keys will be removed.
            The value is not validated.
        '''
        default_config_data = asdict(ConfigData())

        _validate_helper(d, default_config_data, [],       {'active_game', 'targeted_analysis_enabled', 'game'})
        _validate_helper(d, default_config_data, ['game'], {'zzz', 'hsr', 'gi', 'hi3'})
        for g in GAME_NAME:
            _validate_helper(d, default_config_data, ['game', g], {'extract_path', 'frame_analysis_parent_path', 'game_options', 'targeted_options'})
            _validate_helper(d, default_config_data, ['game', g, 'game_options'], {'clean_extract_folder', 'open_extract_folder', 'delete_frame_analysis'})
            _validate_helper(d, default_config_data, ['game', g, 'targeted_options'], {'force_dump_dds', 'dump_rt', 'symlink', 'share_dupes'})
            

def _validate_helper(d: dict, dd: dict, path: list[str], keys_to_be_added: set[str]):
        for p in path:
            d  = d[p]
            dd = dd[p]

        keys_to_be_removed = []
        for k in d:
            if k in keys_to_be_added:
                keys_to_be_added.remove(k)
            else:
                keys_to_be_removed.append(k)
        for k in keys_to_be_removed:
            print('\t- Removed unrecognized/deprecated key "{}/{}"'.format('/'.join(path), k))
            del d[k]
        for k in keys_to_be_added:
            print('\t- Added missing key "{}/{}"'.format('/'.join(path), k))
            d[k] = dd[k]
