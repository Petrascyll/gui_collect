import re
import tkinter as tk

from pathlib import Path

from backend.config.Config import Config

from frontend.install_connector_window import open_install_connector_window

from ..state import State
from ..xtk.ScrollableFrame import ScrollableFrame
from ..xtk.CompactCheckbox import CompactCheckbox
from ..xtk.FlatButton import FlatButton
from ..xtk.PathPicker import PathPicker
from ..style import brighter, darker



class SettingsPage(ScrollableFrame):
    def __init__(self, parent, *args, **kwargs):
        ScrollableFrame.__init__(self, parent, padx=16, pady=16, bg='#111', scrollbar_pad_x=(8, 0))
        self.config(bg='#111')
        self.config(*args, **kwargs)
        self.parent = parent

        self.state    = State.get_instance()
        self.cfg      = Config.get_instance()
        self.terminal = self.state.get_terminal()
        self.targeted_analysis_linker_buttons = []

        self.create_widgets()

    def create_widgets(self):
        def create_section_header(text: str, accent_color='#CCC', pady=(0, 0)):
            header = tk.Label(self.interior, text=text, font=('Arial', 20), fg=accent_color, bg=self['bg'], anchor='w')
            header_border = tk.Frame(self.interior, bg=accent_color, height=2)
            header.pack(fill='x', pady=(pady[0], 0))
            header_border.pack(fill='x', pady=(0, pady[1]))

        def create_3dm_path_path_picker(game: str, accent_color):
            frame = tk.Frame(self.interior, bg=self['bg'])
            frame.pack(fill='x')

            lbl = tk.Label(frame, text='3dmigoto Path:', font=('Arial', 16), fg='#CCC', bg=self['bg'], relief='flat')
            pp = PathPicker(
                frame,
                cfg_key_path=['game', game, 'frame_analysis_parent_path'],
                editable=True,
                editable_label_text='Change',
                is_valid=lambda path: (path/'d3dx.ini').exists(),
                terminal=self.terminal,
                bg=frame['bg'],
                text_fg=darker(accent_color),
                hover_text_fg=accent_color,
                button_bg=darker(accent_color),
            )

            frame.grid_columnconfigure(index=0, weight=0)
            frame.grid_columnconfigure(index=1, weight=1)
            lbl.grid(row=0, column=0, sticky='nsew', padx=(0, 0))
            pp.grid(row=0, column=1, sticky='nsew')

        def create_checkbox(text: str, *, cfg_key_path: list[str], pady=(0, 0), callback=None, accent_color='#CCC'):
            def handle_change(new_value: bool):
                self.cfg.set_config_key_value(self.terminal, cfg_key_path, new_value)
                if callback:
                    callback(new_value)

            checkbox = CompactCheckbox(
                self.interior, height=30, bg=self['bg'], active_bg=accent_color,
                on_change=handle_change,
                active=self.cfg.get_config_key_value(cfg_key_path),
                flip=True, fill=True,
                text=text,
            )
            checkbox.pack(padx=(0, 0), pady=pady, fill='x', anchor='nw')

        def create_button(text, game, enabled_state_cfg_key_path: list[str], accent_color='#CCC', pady=(0, 0), ):
            button = FlatButton(
                self.interior,
                text=text, justify='left', anchor='w', font=('Arial', 16),
                bg=self['bg'], hover_bg='#222', fg=accent_color, hover_fg='#FFF',
                disabled_fg='#555',
                on_click=lambda _, game: install_targeted_analysis_connection(game),
                on_click_kwargs={'game': game},
                is_active=self.cfg.get_config_key_value(enabled_state_cfg_key_path),
            )
            button.pack(padx=(0, 0), ipadx=0, pady=pady, fill='x', anchor='nw')

            self.cfg.register_config_update_handler(enabled_state_cfg_key_path, lambda new_value: button.enable() if new_value else button.disable())

        def install_targeted_analysis_connection(game):
            root_path = self.cfg.get_config_key_value(['game', game, 'frame_analysis_parent_path'])

            if (
                not root_path
                or not (Path(root_path)/'d3dx.ini').exists()
                or not (Path(root_path)/'mods').exists()
            ):
                self.terminal.print('<ERROR>Set a valid 3dmigoto path for the connector .ini to be installed in first. It must contain a d3dx.ini file and a mods folder.</ERROR>')
                return
    
            ret = open_install_connector_window(self.winfo_toplevel(), Path(root_path, 'mods'))
            if ret == 0:
                self.terminal.print('Installed connector .ini for {}!'.format(game))
            elif ret == 1:
                self.terminal.print('Canceled connector .ini installation for {}!'.format(game))
            else:
                self.terminal.print('<ERROR>Failed to install connector .ini for {}!</ERROR>'.format(game))

        create_section_header('General Settings', pady=(0, 8))
        create_checkbox('Enable Targeted Frame Analysis', cfg_key_path=['targeted_analysis_enabled'], callback=lambda _: self.state.refresh_all_extract_forms())

        create_section_header('ZZZ Settings', '#e2751e', pady=(8, 8))
        create_3dm_path_path_picker('zzz', '#e2751e')
        create_button('Install connector .ini. Required for gui_collect targeted analysis to work.', game='zzz', enabled_state_cfg_key_path=['targeted_analysis_enabled'], pady=(4, 0))
        create_checkbox('Reverse applied shapekeys. Requires `dump_cb` in d3dx.ini analyse_options or targeted analysis.', cfg_key_path=['reverse_shapekeys_zzz'], accent_color='#e2751e', pady=(4, 0))

        create_section_header('HSR Settings', '#7a6ce0', pady=(8, 8))
        create_3dm_path_path_picker('hsr', '#7a6ce0')
        create_button('Install connector .ini. Required for gui_collect targeted analysis to work.', game='hsr', enabled_state_cfg_key_path=['targeted_analysis_enabled'], pady=(4, 0))
        create_checkbox('Reverse applied shapekeys. Requires `dump_cb` in d3dx.ini analyse_options or targeted analysis.', cfg_key_path=['reverse_shapekeys_hsr'], accent_color='#7a6ce0', pady=(4, 0))

        create_section_header('GI Settings', '#5fb970', pady=(8, 8))
        create_3dm_path_path_picker('gi', '#5fb970')
        create_button('Install connector .ini. Required for gui_collect targeted analysis to work.', game='gi', enabled_state_cfg_key_path=['targeted_analysis_enabled'], pady=(4, 0))

        create_section_header('HI3 Settings', '#c660cf', pady=(8, 8))
        create_3dm_path_path_picker('hi3', '#c660cf')
        create_button('Install connector .ini. Required for gui_collect targeted analysis to work.', game='hi3', enabled_state_cfg_key_path=['targeted_analysis_enabled'], pady=(4, 0))
