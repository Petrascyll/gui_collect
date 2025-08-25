import os
import json
from dataclasses import asdict
from typing import Callable

from .structs import ConfigData
from .exceptions import InvalidConfigData


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

        self.config_key_callbacks: dict[str, list[Callable]] = {}

    def set_config_key_value(self, terminal, key_path: list[str], value, is_path=False, echo=True):
        d = self.data
        for i, key in enumerate(key_path):
            if i == len(key_path) - 1:
                if type(d) is dict: d[key] = value
                else: d.__setattr__(key, value)

            if type(d) is dict: d = d[key]
            else: d = d.__getattribute__(key)

        self.trigger_callbacks(key_path, value)

        if echo:
            if is_path: value = '<PATH>{}</PATH>'.format(value)
            terminal.print('Set Config: {} = {}'.format('/' + '/'.join(key_path), value))

    def trigger_callbacks(self, key_path: list[str], value, skip_callback=None):
        key_path = '/' + '/'.join(key_path)
        if key_path in self.config_key_callbacks:
            for callback in self.config_key_callbacks[key_path]:
                if skip_callback == callback: continue
                callback(value)

    def get_config_key_value(self, key_path: list[str]):
        d = self.data
        for key in key_path:
            if type(d) is dict: d = d[key]
            else: d = d.__getattribute__(key)
        return d

    def register_config_update_handler(self, key_path: list[str], callback: Callable):
        key_path = '/' + '/'.join(key_path)
        if key_path not in self.config_key_callbacks:
            self.config_key_callbacks[key_path] = []
        self.config_key_callbacks[key_path].append(callback)


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
            json.dump(asdict(ConfigData()), f, indent=4)

    def _load_config(self) -> dict:
        with open(self._config_filepath, 'r', encoding='utf-8') as f:
            try:
                d = json.load(f)
                ConfigData.validate_config_data(d)
                self.data = ConfigData(**d)
            except json.decoder.JSONDecodeError:
                print('\tconfig: JSON Decode Error. config.json is not a valid json file.')
                self.prompt_config_refresh()
            except InvalidConfigData:
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
