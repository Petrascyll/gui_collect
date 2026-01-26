import os
import logging
import subprocess
import tkinter as tk
from tkinter.font import Font
from tkinter import filedialog
from pathlib import Path
from functools import cache

from gui_collect.backend.config.Config import Config

from .FlatImageButton import FlatImageButton
from gui_collect.frontend.style import brighter


logger = logging.getLogger(__name__)
FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class PathPicker(tk.Frame):
    def __init__(
            self, parent, button_bg, value: str=None, cfg_key_path=None,
            callback: callable=None, is_valid: callable=None, pass_self_to_callback=False,
            editable=False, editable_label_text=None,
            text_fg='#999', hover_text_fg='#e8eaed',
            override_open=False,
            font=None,
            dialog_title='Select the location to save the extracted folder',
            dialog_parent=None,
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

        self.override_open = override_open
        self.pass_self_to_callback = pass_self_to_callback
        self.dialog_title  = dialog_title
        self.dialog_parent = dialog_parent
        self.is_valid      = is_valid
        self.editable      = editable
        self.editable_label_text = editable_label_text
        self.callback      = callback
        self.text_fg       = text_fg
        self.hover_text_fg = hover_text_fg
        self.default_bg    = self['bg']
        self.button_bg     = button_bg
        self.font = font or ('Arial', 16)

        self.configure_grid()
        if self.editable and not self.override_open:
            self.create_button()
        self.create_label()
    
    def configure_grid(self):
        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=0)
        if self.editable:
            self.grid_columnconfigure(index=2, weight=0)

        self.grid_rowconfigure(index=0, weight=1)

    def handle_click_change_path(self, event):
        path = filedialog.askdirectory(mustexist=True, title=self.dialog_title, parent=self.dialog_parent)

        if path:
            path = Path(path).absolute()
            if self.is_valid and not self.is_valid(path):
                logger.error("Invalid 3dm path: %s", path)
                return

            str_path = str(path)
            if self.cfg_key_path:
                self.cfg.set_config_key_value(self.cfg_key_path, str_path, is_path=True)
            else:
                self.set_path(str_path)

            if self.callback:
                if self.pass_self_to_callback:
                    self.callback(self, str_path)
                else:
                    self.callback(str_path)

    def create_button(self):
        img = tk.PhotoImage(file=Path('./resources/images/buttons/folder_open.25.png').absolute())
        kwargs = {
            'text': self.editable_label_text,
            'text_dims': (Font(family='Arial', size=16).measure(self.editable_label_text), (4,0), (0,0))
        } if self.editable_label_text else {}

        self.pick_folder_btn = FlatImageButton(self, width=32, height=32, img_width=25, img_height=25,bg=self.button_bg, image=img, **kwargs)
        self.pick_folder_btn.grid(column=2, sticky='nsew')

        self.pick_folder_btn.bind('<Button-1>', self.handle_click_change_path)

    def create_label(self):
        self.path_label = tk.Label(self, fg=self.text_fg, bg=self['bg'], font=Font(font=self.font), cursor='hand2', relief='flat', anchor='w')
        self.path_label.grid(row=0, column=0, sticky='nsew')
        self.set_path_label_text()
        
        def handle_enter(event):
            self.path_label.config(bg=brighter(self.default_bg), fg=self.hover_text_fg)
            if self.label_btn:
                self.label_btn.config(bg=brighter(self.default_bg))
        def handle_leave(event):
            self.path_label.config(bg=self.default_bg, fg=self.text_fg)
            if self.label_btn:
                self.label_btn.config(bg=self.default_bg)

        if not self.override_open:
            handle_click = lambda _: subprocess.run([FILEBROWSER_PATH, self.path])
            img = tk.PhotoImage(file=Path('./resources/images/buttons/open_in_new.32.png').absolute())
            img_dim = (32, 32)
            self.label_btn = FlatImageButton(self, width=32, height=32, img_width=img_dim[0], img_height=img_dim[1], bg=self['bg'], image=img)
            self.label_btn.grid(row=0, column=1)

            self.label_btn.bind('<Button-1>', handle_click)
            self.label_btn.bind('<Enter>', handle_enter)
            self.label_btn.bind('<Leave>', handle_leave)
        else:
            handle_click = self.handle_click_change_path
            self.label_btn = None

        self.path_label.bind('<Button-1>', handle_click)
        self.path_label.bind('<Enter>', handle_enter)
        self.path_label.bind('<Leave>', handle_leave)
        self.path_label.bind('<Configure>', lambda _: self.set_path_label_text())

    def refresh_label_bindings(self):
        self.path_label.config(bg=self.default_bg, fg=self.text_fg)

        self.path_label.unbind('<Enter>')
        self.path_label.unbind('<Leave>')

        self.path_label.bind('<Enter>', lambda _: self.path_label.config(
            bg=brighter(self.default_bg),
            fg=self.hover_text_fg,
        ))
        self.path_label.bind('<Leave>', lambda _: self.path_label.config(
            bg=self.default_bg,
            fg=self.text_fg,
        ))

    def set_path(self, text):
        self.path = Path(text)
        self.set_path_label_text()

    def set_path_label_text(self):
        if not self.path: return
        path_text = get_short_path(str(self.path.absolute()), self.path_label.winfo_width(), self.font)
        self.path_label.config(text=path_text)


@cache
def __measure(text, font):
    font_obj = Font(font=font)
    return font_obj.measure(text)


@cache
def get_short_path(s: str, max_width: int, font):
    font_obj = Font(font=font)
    if (font_obj.measure(s) <= max_width):
        return s

    prefix = '...\\'
    prefix_len = __measure(prefix, font)

    while prefix_len + font_obj.measure(s) > max_width:
        try: s = s.split('\\', maxsplit=1)[1]
        except IndexError: break

    return prefix + s
