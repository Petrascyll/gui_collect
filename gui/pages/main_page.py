from enum import Enum
import tkinter as tk
from pathlib import Path

from ..extract_form import ExtractForm
from ..address_frame import AddressFrame
from ..texture_picker import TexturePicker
from config.config import Config


class MainPageT(Enum):
    zzz = 'zzz'
    hsr = 'hsr'
    gi  = 'gi'
    settings = 'settings'

class MainPage(tk.Frame):
    def __init__(self, parent, variant: MainPageT, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent

        self.variant = variant
        self.texture_picker_visible = False

        self.cfg = Config.get_instance().data
        
        self.configure_grid()
        self.create_widgets()
        self.grid_widgets()

    def configure_grid(self):
        self.columnconfigure(0, weight=1)
        self   .rowconfigure(0, weight=0)
        self   .rowconfigure(1, weight=1)

    def create_widgets(self):
        self.address_frame  =  AddressFrame(self)
        self.extract_form   =   ExtractForm(self)
        self.texture_picker = TexturePicker(self)
        self.texture_picker.lower()

    def grid_widgets(self):
        self.address_frame  .grid(column=0, row=0, sticky='nsew')
        self.extract_form   .grid(column=0, row=1, sticky='nsew')
        self.texture_picker .grid(column=0, row=0, rowspan=2, sticky='nsew')
        
    # def grid_forget_widgets(self):
    #     self .address_frame.grid_forget()
    #     self  .extract_form.grid_forget()
    #     self.texture_picker.grid_forget()

    def show_texture_picker(self):
        self.texture_picker.tkraise()
        # self.texture_picker_visible = True
        # self.grid_forget_widgets()
        # self.grid_widgets()

    def hide_texture_picker(self):
        self.texture_picker.lower()
        # self.texture_picker_visible = False
        # self.grid_forget_widgets()
        # self.grid_widgets()

    def on_address_change(self, text: str):
        # TODO: hard coded to zzz for now
        # Update 3dm parent folder in config when user picks a frame dump
        # path = Path(self.address_frame.path)
        path = Path(text)
        
        # Check if current directory is a frame analysis in which case the parent is 3dm's
        if 'FrameAnalysis' in path.name:
            self.cfg.game['zzz']['frame_analysis_parent_path'] = str(path.parent)
            return

        # Check if the current directory is that of 3dm
        has_d3dx = len([p for p in path.iterdir() if 'd3dx.ini' == p.name]) == 1
        if has_d3dx:
            self.cfg.game['zzz']['frame_analysis_parent_path'] = str(path)
