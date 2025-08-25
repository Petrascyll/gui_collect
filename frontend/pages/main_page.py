from enum import Enum
import tkinter as tk
from pathlib import Path

from backend.config.Config import Config

from ..data import Page
from ..extract_form import ExtractForm
from ..texture_picker import TexturePicker


class MainPage(tk.Frame):
    def __init__(self, parent, variant: Page, *args, **kwargs):
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
        self.extract_form   = ExtractForm(self, self.variant)
        self.texture_picker = TexturePicker(self)
        self.texture_picker.lower()

    def grid_widgets(self):
        self.extract_form   .grid(column=0, row=1, sticky='nsew')
        self.texture_picker .grid(column=0, row=0, rowspan=2, sticky='nsew')
        

    def show_texture_picker(self):
        self.texture_picker.tkraise()

    def hide_texture_picker(self):
        self.texture_picker.lower()
