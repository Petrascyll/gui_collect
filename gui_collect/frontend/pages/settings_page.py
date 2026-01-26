import re
import logging
import tkinter as tk

from pathlib import Path
from typing import Literal, TypeAlias


from gui_collect.frontend.install_connector_window import open_install_connector_window
from gui_collect.backend.config.Config import Config
from ..state import State
from ..xtk.ScrollableFrame import ScrollableFrame
from ..xtk.CompactCheckbox import CompactCheckbox
from ..xtk.FlatButton import FlatButton
from ..xtk.PathPicker import PathPicker
from ..style import brighter, darker


logger = logging.getLogger(__name__)


class SettingsPage(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, padx=16, pady=16, bg='#111')
        self.config(bg='#111')
        self.config(*args, **kwargs)
        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self.game_buttons_frame = tk.Frame(self, bg=self['bg'])
        self.header_border      = tk.Frame(self, bg='#CCC', height=2)
        self.settings_router    = SettingsRouter(self, initial_tab='general')

        self.tabs = {}
        self.cur_tab = 'general'

        def change_tab(e):
            new_tab_btn, new_tab = e.widget, e.widget.tab
            cur_tab_btn = self.tabs[self.cur_tab]
            self.cur_tab = new_tab
            cur_tab_btn.toggle()
            new_tab_btn.toggle()

            self.settings_router.route(new_tab)
            self.header_border.config(bg=new_tab_btn['bg'])
            logger.info('<GAME>%s</GAME> Settings', new_tab_btn.name)

        class _FlatButton(FlatButton):
            def __init__(self, *args, accent, tab, name, **kwargs):
                self.accent = accent
                self.tab = tab
                self.name = name
                super().__init__(*args, **kwargs)

            def enable(_self):
                _self.is_active = True
                _self.update_args(
                    new_bg=_self.accent, new_hover_bg=_self.accent,
                    new_fg=self['bg'], new_hover_fg=self['bg'],
                )

            def disable(_self):
                _self.is_active = False
                _self.update_args(
                    new_bg=darker(darker(darker(darker(_self.accent)))), new_hover_bg=_self.accent,
                    new_fg=self['bg'], new_hover_fg=self['bg'],
                )

        for i, (game_id, full_game_name, accent) in enumerate([
            ('General', 'General',           '#CCCCCC'),
            ('HI3',     'Honkai Impact 3',   '#c660cf'),
            ('GI',      'Genshin Impact',    '#5fb970'),
            ('HSR',     'Honkai: Star Rail', '#7a6ce0'),
            ('ZZZ',     'Zenless Zone Zero', '#e2751e'),
        ]):
            width = 8     if i == 0 else 6
            side = 'left' if i == 0 else 'right'
            padx = 0      if i == 0 else (16, 0)
            bg = accent   if i == 0 else darker(darker(darker(darker(accent))))

            tab_btn = _FlatButton(
                self.game_buttons_frame, text=game_id,
                fg=self['bg'],
                bg=bg, hover_bg=accent,
                width=width, padx=16, pady=4, font=('Arial', 20),
                is_active=game_id.lower() == self.cur_tab,

                accent=accent,
                tab=game_id.lower(),
                name=full_game_name,
            )
            tab_btn.bind('<Button-1>', change_tab)
            tab_btn.pack(side=side, padx=padx)

            self.tabs[tab_btn.tab] = tab_btn

        self.game_buttons_frame.grid(row=0, column=0, sticky='nsew', pady=0)
        self.header_border.grid(row=1, column=0, sticky='nsew', pady=(8, 8))
        self.settings_router.grid(row=2, column=0, sticky='nsew')


tab_type: TypeAlias = Literal['general', 'zzz', 'hsr', 'gi', 'hi3']


class SettingsRouter(ScrollableFrame):
    def __init__(self, parent, initial_tab: tab_type, *args, **kwargs):
        super().__init__(parent, padx=0, pady=0, bg=parent['bg'], scrollbar_pad_x=(8, 0))

        self.state    = State.get_instance()
        self.cfg      = Config.get_instance()

        self.interior.grid_columnconfigure(0, weight=1)
        self.route(initial_tab)

    def route(self, tab: tab_type):
        children = self.interior.winfo_children()
        for child in children:
            child.grid_forget()
            child.destroy()

        {
            'general': self.create_widgets_general,
            'zzz': self.create_widgets_zzz,
            'hsr': self.create_widgets_hsr,
            'gi': self.create_widgets_gi,
            'hi3': self.create_widgets_hi3,
        }[tab]()

    def create_widgets_general(self):
        self.create_checkbox('Enable Targeted Frame Analysis', cfg_key_path=['targeted_analysis_enabled'], callback=lambda _: self.state.refresh_all_extract_forms(), pady=(0, 8))
        connector_button = ConnectorButton(self.interior, enabled_cfg_path=['targeted_analysis_enabled'], bg='#222', padx=8, pady=8)
        connector_button.grid(sticky='nsew')


    def create_widgets_zzz(self):
        self.create_checkbox('Reverse applied shapekeys. Requires `dump_cb` in d3dx.ini analyse_options or targeted analysis.', cfg_key_path=['reverse_shapekeys_zzz'], accent_color='#e2751e')

    def create_widgets_hsr(self):
        self.create_checkbox('Reverse applied shapekeys. Requires `dump_cb` in d3dx.ini analyse_options or targeted analysis.', cfg_key_path=['reverse_shapekeys_hsr'], accent_color='#7a6ce0')

    def create_widgets_gi(self):
        lbl = tk.Label(self.interior, text='Nothing here...', anchor='w', font=('Arial', 16), fg='#CCC', bg=self['bg'], relief='flat')
        lbl.grid(sticky='nsew')

    def create_widgets_hi3(self):
        lbl = tk.Label(self.interior, text='Nothing here...', anchor='w', font=('Arial', 16), fg='#CCC', bg=self['bg'], relief='flat')
        lbl.grid(sticky='nsew')


    def create_checkbox(self, text: str, *, cfg_key_path: list[str], pady=(0, 0), callback=None, accent_color='#CCC'):
        def handle_change(new_value: bool):
            self.cfg.set_config_key_value(cfg_key_path, new_value)
            if callback:
                callback(new_value)

        frame = tk.Frame(self.interior, bg='#222', padx=8, pady=8)
        frame.grid(sticky='nsew',  pady=pady, column=0)
        frame.grid_columnconfigure(0, weight=1)

        checkbox = CompactCheckbox(
            frame, height=30, bg=frame['bg'], active_bg=accent_color,
            font=('Arial', 16, 'bold'),
            on_change=handle_change,
            active=self.cfg.get_config_key_value(cfg_key_path),
            flip=True, fill=True,
            text=text,
        )
        checkbox.grid(sticky='nsew')

        def handle_enter(_):
            frame.config(bg='#333', cursor='hand2')
            checkbox.config(bg='#333')
            checkbox.handle_enter(_)
        
        def handle_leave(_):
            frame.config(bg='#222', cursor='left_ptr')
            checkbox.config(bg='#222')
            checkbox.handle_leave(_)

        frame   .bind('<Button-1>', checkbox.handle_click)
        frame   .bind('<Enter>', handle_enter)
        checkbox.bind('<Enter>', handle_enter)
        frame   .bind('<Leave>', handle_leave)
        checkbox.bind('<Leave>', handle_leave)


class ConnectorButton(tk.Frame):
    def __init__(self, parent, enabled_cfg_path: list[str], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.cfg = Config.get_instance()

        is_active = self.cfg.get_config_key_value(enabled_cfg_path)
        self.cfg.register_config_update_handler(
            enabled_cfg_path,
            lambda is_active: self.refresh(is_active)
        )
        self.bind('<Destroy>', lambda _: self.cfg.deregister_config_update_handler(enabled_cfg_path))

        self.create_widgets()
        self.grid_widgets()
        self.refresh(is_active=is_active)

    def refresh(self, is_active: bool):
        if is_active is not None:
            self.is_active = is_active

        if self.is_active:
            self.register_events()
            self.lbl_main.config(fg='#CCC')
            self.lbl_extra.config(fg='#CCC')
        else:
            self.deregister_events()
            self.lbl_main.config(fg='#666')
            self.lbl_extra.config(fg='#666')

    def install_targeted_analysis_connection(self):
        ret = open_install_connector_window(self.winfo_toplevel())
        if ret == 0:
            logger.info('Installed connector .ini!')
        elif ret == 1:
            logger.info("Canceled connector .ini installation")
        else:
            logger.error("Failed to install connector .ini!")

    def create_widgets(self):
        kwargs = {'anchor':'w', 'fg':'#CCC', 'bg':self['bg'], 'relief':'flat', 'pady': 0}
        self.lbl_main  = tk.Label(self, text='Install connector .ini', font=('Arial', 16, 'bold'), **kwargs)
        self.lbl_extra = tk.Label(self, text='Required for gui_collect based targeted analysis', font=('Arial', 10), **kwargs)

    def grid_widgets(self):
        self.lbl_main.grid(column=0, sticky='nsew')
        self.lbl_extra.grid(column=0, sticky='nsew')

    def register_events(self):
        def handle_click(_):
            self.install_targeted_analysis_connection()

        def handle_enter(_):
            self.config(bg='#333', cursor='hand2')
            self.lbl_main .config(bg='#333', fg='#FFF')
            self.lbl_extra.config(bg='#333', fg='#FFF')
        
        def handle_leave(_):
            self.config(bg='#222', cursor='left_ptr')
            self.lbl_main .config(bg='#222', fg='#CCC')
            self.lbl_extra.config(bg='#222', fg='#CCC')

        for widget in [self, self.lbl_main, self.lbl_extra]:
            widget.bind('<Button-1>', handle_click)
            widget.bind('<Enter>', handle_enter)
            widget.bind('<Leave>', handle_leave)

    def deregister_events(self):
        for widget in [self, self.lbl_main, self.lbl_extra]:
            widget.unbind('<Button-1>')
            widget.unbind('<Enter>')
            widget.unbind('<Leave>')
