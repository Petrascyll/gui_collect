import os
from pathlib import Path

import tkinter as tk
from tkinter import filedialog
from tkinter.font import Font

from .data import Page
from .state import State
from config.config import Config
from .xtk.FlatImageButton import FlatImageButton


class AddressFrame(tk.Frame):
    def __init__(self, parent, target: Page, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent

        self._state = State.get_instance()
        
        self.font = Font(family='Arial', size=20, weight='bold')
        self.address_max_width = 400
        self.target = target
        self.path: str = ''
        
        self.create_widgets()
        self.load_latest_frame_analysis()
    
    def create_widgets(self):
        self.folder_path_label = tk.Label(self, text='Select Frame Analysis Folder', fg='#555', font=self.font)
        if self.path:
            self.folder_path_label.config(text=self.path)

        img = tk.PhotoImage(file=Path('./resources/images/buttons/folder_open.256.png').absolute()).subsample(8)
        pick_folder_btn = FlatImageButton(self, width=40, height=40, img_width=32, img_height=32, bg='#3fb76b', image=img)
        pick_folder_btn.bind('<Button-1>', lambda _: self.handle_frame_dump_pick())

        img = tk.PhotoImage(file=Path('./resources/images/buttons/history.256.png').absolute()).subsample(8)
        pick_latest_dump_btn = FlatImageButton(self, width=40, height=40, img_width=32, img_height=32, bg='#244eb9', image=img)
        pick_latest_dump_btn.bind('<Button-1>', lambda _: self.load_latest_frame_analysis())

        # img = tk.PhotoImage(file=Path('./resources/images/buttons/close.256.png').absolute()).subsample(8)
        # close_btn = FlatButton(self, width=40, height=40, img_width=32, img_height=32, bg='#b92424', image=img)
        # close_btn.bind('<Button-1>', self.handle_address_close)

        self.folder_path_label .pack(side='left')
        pick_folder_btn        .pack(side='right', padx=0, pady=0)
        pick_latest_dump_btn   .pack(side='right', padx=0, pady=0)
        # close_btn              .pack(side='right', padx=0, pady=0)

    # def set_label_text(self, text: str, max_chars:int=None):
    #     # path = str(Path(text).resolve())
    #     path = text
    #     width = self.font.measure(self.path)
    #     i = 0
    #     j = len(path)
    #     # Binary search to find the maximum number of characters that still fits within
    #     # our width requirement :teriderp:
    #     while width > self.address_max_width:
    #         i = i + (j-i)//2
    #         trimmed_path = path[-i:]
    #         trimmed_width = self.font.measure(trimmed_path)
    #         if trimmed_width > self.address_max_width:
    #             continue
    #         else:
    #             j = i
    #             i = i + (j-i)//2
    #             trimmed_path = path[-i:]

    #     self.folder_path_label.config(text=path)

    def set_path(self, text: str):
        self.path = str(Path(text).resolve())
        print('Set frame analysis path: {}'.format(str(self.path)))
        
        self.folder_path_label.config(text=self.path)
        self.parent.on_address_change(text=self.path)

    def handle_frame_dump_pick(self):
        path = filedialog.askdirectory(mustexist=True, title='Select Frame Analysis Folder')
        if path:
            self.set_path(path)

    def handle_address_close(self, e):
        path = self.folder_path_label['text']

        if not path or 'FrameAnalysis' not in path:
            self.folder_path_label.config(text='Select Frame Analysis Folder')
            self.path = ''
            return

        path = Path(path)
        while 'FrameAnalysis' not in path.name:
            path = path.parent

        self.set_path(path.parent.absolute())

    def load_latest_frame_analysis(self):
        saved_path = Config.get_instance().data.game[self.target.value]['frame_analysis_parent_path']
        if not saved_path:
            return
        frame_analysis_parent_path = Path(saved_path)
        if not frame_analysis_parent_path.exists():
            return

        print('Looking for latest frame analysis in {}'.format(str(frame_analysis_parent_path)))
        frame_analysis_paths = sorted(
            [
                f for f in frame_analysis_parent_path.iterdir()
                if 'FrameAnalysis' in f.name
                and (f/'log.txt').exists()
            ], key=os.path.getctime
        )
        if len(frame_analysis_paths) > 0:
            self.set_path(str(frame_analysis_paths[-1]))

        return
