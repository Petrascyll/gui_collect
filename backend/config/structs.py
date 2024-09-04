from dataclasses import dataclass, field


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
class ConfigData():
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