import os
from pathlib import Path

import tkinter as tk
from tkinter import filedialog
from tkinter.font import Font

from backend.config.Config import Config

from .data import Page
from .state import State
from .xtk.FlatImageButton import FlatImageButton


class AddressFrame(tk.Frame):
    def __init__(self, parent, target: Page, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent

        self._state = State.get_instance()
        self.terminal = self._state.get_terminal()

        self.font = Font(family='Arial', size=20, weight='bold')
        self.grid_columnconfigure(0, weight=1)

        self.target = target
        self.path: str = ''
        self.path_text = ''

        self.create_widgets()
        self.load_latest_frame_analysis()
    
    def refresh_path_text(self):
        if not self.path: return
        self.path_text = get_trunc_path(self.path, self.font, self.folder_path_label.winfo_width())
        self.folder_path_label.config(text=self.path_text)

    def create_widgets(self):
        self.folder_path_label = tk.Label(self, text='Select Frame Analysis Folder', fg='#555', anchor='w', font=self.font)
        self.folder_path_label.bind('<Configure>', lambda _: self.refresh_path_text())

        img = tk.PhotoImage(file=Path('./resources/images/buttons/folder_open.32.png').absolute())
        pick_folder_btn = FlatImageButton(self, width=40, height=40, img_width=32, img_height=32, bg='#3fb76b', image=img)
        pick_folder_btn.bind('<Button-1>', lambda _: self.handle_frame_dump_pick())

        img = tk.PhotoImage(file=Path('./resources/images/buttons/history.32.png').absolute())
        pick_latest_dump_btn = FlatImageButton(self, width=40, height=40, img_width=32, img_height=32, bg='#244eb9', image=img)
        pick_latest_dump_btn.bind('<Button-1>', lambda _: self.load_latest_frame_analysis())

        self.folder_path_label .grid(row=0, column=0, sticky='nsew')
        pick_latest_dump_btn   .grid(row=0, column=1, sticky='nsew')
        pick_folder_btn        .grid(row=0, column=2, sticky='nsew')

    def set_path(self, text: str):
        self.path = str(Path(text).resolve())
        self.terminal.print('Set frame analysis path: <PATH>{}</PATH>'.format(str(self.path)))
        self.terminal.print()
        
        self.refresh_path_text()
        self.parent.on_address_change(text=self.path)

    def handle_frame_dump_pick(self):
        path = filedialog.askdirectory(mustexist=True, title='Select Frame Analysis Folder')
        if path:
            self.set_path(path)

    def load_latest_frame_analysis(self):
        saved_path = Config.get_instance().data.game[self.target.value].frame_analysis_parent_path
        if not saved_path:
            return
        frame_analysis_parent_path = Path(saved_path)
        if not frame_analysis_parent_path.exists():
            return

        self.terminal.print('Looking for latest frame analysis in <PATH>{}</PATH>'.format(str(frame_analysis_parent_path)))
        frame_analysis_paths = sorted(
            [
                f for f in frame_analysis_parent_path.iterdir()
                if 'FrameAnalysis' in f.name
                and (f/'log.txt').exists()
            ], key=os.path.getctime
        )
        if len(frame_analysis_paths) > 0:
            self.set_path(str(frame_analysis_paths[-1]))
        else:
            self.set_path(saved_path)

        return

# Maybe just a bit overkill
def get_trunc_path(s: str, font: Font, max_width: int):
    if (font.measure(s) <= max_width):
        return s

    # The font isnt changing so I can just hard code
    # the width of '...\' = font.measure('...\\') = 32px
    while 32 + font.measure(s) > max_width:
        try: s = s.split('\\', maxsplit=1)[1]
        except IndexError: break

    return '...\\' + s
