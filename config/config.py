import os
import json
from dataclasses import dataclass, asdict, field

class Config():
    __instance = None

    def __init__(self, config_directory:str = '.'):
        if Config.__instance != None:
            raise Exception('Config already created.')
        Config.__instance = self

        print('Initializing Config')

        self.temp_data = {}
        self._config_directory = config_directory
        self._config_filename = 'config.json'
        self._config_filepath = os.path.join(config_directory, self._config_filename)

        if not self._check_config_exists():
            self._create_config()
            print('\t- Created config at', self._config_filepath)
        else:
            print('\t- Reading config from', self._config_filepath)

        self._load_config()
        print('\t- Loaded')
    

    @staticmethod
    def get_instance():
        if Config.__instance == None:
            raise Exception('Config haven\'t been initialized.')
        return Config.__instance

    def _check_config_exists(self):
        files = os.listdir(self._config_directory)
        return self._config_filename in files

    def _create_config(self):
        with open(self._config_filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(_ConfigData()), f, indent=4)

    def _load_config(self) -> dict:
        with open(self._config_filepath, 'r', encoding='utf-8') as f:
            try:
                d = json.load(f)
                _ConfigData.validate_config_data(d)
                self.data = _ConfigData(**d)
            except json.decoder.JSONDecodeError:
                print('\tconfig: JSON Decode Error. config.json is not a valid json file.')
                self.prompt_config_refresh()
            except InvalidConfigData:
                pass


    def _validate_config(self):
        # for k, v in self.data.items():
        pass

    def save_config(self):
        with open(self._config_filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.data), f, indent=4)

    def prompt_config_refresh(self):
        ans = ''
        while ans not in ['y', 'n']:
            ans = input('\tOverwrite config.json with default config? (y/n): ').lower()

        if ans == 'y':
            self._create_config()
            return self._load_config()
        else:
            exit('\tInvalid config.json. Exiting.')

@dataclass
class _GameConfigData():
    # export_path               : str = '_Extracted'
    frame_analysis_parent_path: str = ''

    # predefined_texture_names: list[str] = field(
    #     default_factory= lambda: [
    #         'Diffuse',
    #         'NormalMap',
    #         'LightMap',
    #         'StockingMap',
    #         'Expressionmap',
    #         'Shadow',
    #     ]
    # )

@dataclass
class _ConfigData():
    first_launch: bool = True
    active_game: str = 'zzz'
    targeted_analysis_enabled: bool = False
    game: dict[str, _GameConfigData] = field(
        default_factory= lambda: {
            'zzz': _GameConfigData(),
            'hsr': _GameConfigData(),
            'gi' : _GameConfigData(),
        }
    )

    @staticmethod
    def validate_config_data(d: dict):
        # TODO
        # Defaulted 3 required keys missing from .json 
        # Validate values for certain keys
        # raise InvalidConfigData()
        pass

class InvalidConfigData(Exception):
    def __init__(self, msg):
        super.__init__(msg)
