import os
import subprocess
import tkinter as tk
from tkinter.font import Font
from tkinter import filedialog
from pathlib import Path
from functools import cache

from backend.config.Config import Config

from .FlatImageButton import FlatImageButton
from frontend.style import brighter


FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class PathPicker(tk.Frame):
    def __init__(
            self, parent, button_bg, terminal, value: str=None, cfg_key_path=None,
            callback: callable=None, is_valid: callable=None,
            editable=False, editable_label_text=None,
            text_fg='#999', hover_text_fg='#e8eaed',
            *args, **kwargs
        ):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)

        self.cfg_key_path = cfg_key_path
        if self.cfg_key_path:
            self.cfg  = Config.get_instance()
            self.path = Path(self.cfg.get_config_key_value(self.cfg_key_path)).absolute()

            self.cfg.register_config_update_handler(self.cfg_key_path, self.set_path)
        elif value:
            self.path = Path(value).absolute()
        else:
            raise Exception('Programming Error')

        self.is_valid      = is_valid
        self.editable      = editable
        self.editable_label_text = editable_label_text
        self.callback      = callback
        self.text_fg       = text_fg
        self.hover_text_fg = hover_text_fg
        self.default_bg    = self['bg']
        self.button_bg     = button_bg
        self.font_args     = {
            'family': 'Arial',
            'size': 16
        }
        self.terminal = terminal

        self.configure_grid()
        if self.editable:
            self.create_button()
        self.create_label()
    
    def configure_grid(self):
        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=0)
        if self.editable:
            self.grid_columnconfigure(index=2, weight=0)

        self.grid_rowconfigure(index=0, weight=1)

    def create_button(self):
        img = tk.PhotoImage(file=Path('./resources/images/buttons/folder_open.25.png').absolute())
        kwargs = {
            'text': self.editable_label_text,
            'text_dims': (Font(family='Arial', size=16).measure(self.editable_label_text), (4,0), (0,0))
        } if self.editable_label_text else {}

        self.pick_folder_btn = FlatImageButton(self, width=32, height=32, img_width=25, img_height=25,bg=self.button_bg, image=img, **kwargs)
        self.pick_folder_btn.grid(column=2, sticky='nsew')

        def handle_click(event):
            path = filedialog.askdirectory(mustexist=True, title='Select the location to save the extracted folder')
            if path:
                path = Path(path).absolute()
                if self.is_valid and not self.is_valid(path):
                    self.terminal.print('<ERROR>Invalid 3dm path: {}</ERROR>'.format(path))
                    return

                str_path = str(path)
                if self.cfg_key_path:
                    self.cfg.set_config_key_value(self.terminal, self.cfg_key_path, str_path, is_path=True)
                else:
                    self.set_path(str_path)

                if self.callback:
                    self.callback(str_path)

        self.pick_folder_btn.bind('<Button-1>', handle_click)

    def create_label(self):
        self.path_label = tk.Label(self, fg=self.text_fg, bg=self['bg'], font=Font(**self.font_args), cursor='hand2', relief='flat', anchor='w')
        self.path_label.grid(row=0, column=0, sticky='nsew')
        self.set_path_label_text()
        
        img = tk.PhotoImage(file=Path('./resources/images/buttons/open_in_new.32.png').absolute())
        self.open_folder_btn = FlatImageButton(self, width=32, height=32, img_width=32, img_height=32, bg=self['bg'], image=img)
        self.open_folder_btn.grid(row=0, column=1)
        
        def handle_click(event):
            subprocess.run([FILEBROWSER_PATH, self.path])
        def handle_enter(event):
            self.path_label.config(bg=brighter(self.default_bg), fg=self.hover_text_fg)
            self.open_folder_btn.config(bg=brighter(self.default_bg))
        def handle_leave(event):
            self.path_label.config(bg=self.default_bg, fg=self.text_fg)
            self.open_folder_btn.config(bg=self.default_bg)

        self.open_folder_btn.bind('<Button-1>', handle_click)
        self.open_folder_btn.bind('<Enter>', handle_enter)
        self.open_folder_btn.bind('<Leave>', handle_leave)

        self.path_label.bind('<Button-1>', handle_click)
        self.path_label.bind('<Enter>', handle_enter)
        self.path_label.bind('<Leave>', handle_leave)
        self.path_label.bind('<Configure>', lambda _: self.set_path_label_text())

        
    def set_path(self, text):
        self.path = Path(text)
        self.set_path_label_text()

    def set_path_label_text(self):
        if not self.path: return
        path_text = get_short_path(str(self.path.absolute()), self.path_label.winfo_width(), **self.font_args)
        self.path_label.config(text=path_text)


@cache
def __measure(text, **font_args):
    font = Font(**font_args)
    return font.measure(text)


@cache
def get_short_path(s: str, max_width: int, **font_args):
    font = Font(**font_args)
    if (font.measure(s) <= max_width):
        return s

    prefix = '...\\'
    prefix_len = __measure(prefix, **font_args)

    while prefix_len + font.measure(s) > max_width:
        try: s = s.split('\\', maxsplit=1)[1]
        except IndexError: break

    return prefix + s
