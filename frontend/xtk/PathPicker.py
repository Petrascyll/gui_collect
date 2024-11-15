import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from .FlatImageButton import FlatImageButton
from frontend.style import brighter


FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class PathPicker(tk.Frame):
    def __init__(self, parent, value: str, callback: callable, button_bg, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)

        self.path       = Path(value)
        self.path_text  = get_short_path(self.path)
        self.callback   = callback
        self.default_bg = self['bg']
        self.button_bg  = button_bg

        if self.callback:
            self.create_button()
        self.create_label()

    def create_button(self):
        img = tk.PhotoImage(file=Path('./resources/images/buttons/folder_open.25.png').absolute())
        self.pick_folder_btn = FlatImageButton(self, width=32, height=32, img_width=25, img_height=25, bg=self.button_bg, image=img)
        self.pick_folder_btn.pack(side='right')
        
        def handle_click(event):
            path = filedialog.askdirectory(mustexist=True, title='Select the location to save the extracted folder')
            if path: self.set_path(path)

        self.pick_folder_btn.bind('<Button-1>', handle_click)

    def create_label(self):
        self.path_label = tk.Label(self, text=self.path_text, fg='#999', bg=self['bg'], font=('Arial', '16'), cursor='hand2', relief='flat', anchor='w')
        self.path_label.pack(side='left', fill='both', expand=True)
        
        img = tk.PhotoImage(file=Path('./resources/images/buttons/open_in_new.32.png').absolute())
        self.open_folder_btn = FlatImageButton(self, width=32, height=32, img_width=32, img_height=32, bg=self['bg'], image=img)
        self.open_folder_btn.pack(side='left')
        
        def handle_click(event):
            subprocess.run([FILEBROWSER_PATH, self.path])
        def handle_enter(event):
            self.path_label.config(bg=brighter(self.default_bg), fg='#e8eaed')
            self.open_folder_btn.config(bg=brighter(self.default_bg))
        def handle_leave(event):
            self.path_label.config(bg=self.default_bg, fg='#999')
            self.open_folder_btn.config(bg=self.default_bg)

        self.open_folder_btn.bind('<Button-1>', handle_click)
        self.open_folder_btn.bind('<Enter>', handle_enter)
        self.open_folder_btn.bind('<Leave>', handle_leave)

        self.path_label.bind('<Button-1>', handle_click)
        self.path_label.bind('<Enter>', handle_enter)
        self.path_label.bind('<Leave>', handle_leave)
        
    def set_path(self, path):
        self.path = Path(path)
        self.path_text = get_short_path(self.path)

        self.path_label.config(text=self.path_text)
        self.callback(str(self.path.absolute()))

def get_short_path(path: Path, max_width: int = 50):
    s = str(path.absolute())
    if len(s) <= max_width:
        return s

    while len(s) + 4 > max_width:
        s = s.split('\\', maxsplit=1)[1]

    return '...\\' + s
