import tkinter as tk
from tkinter import filedialog
from tkinter.font import Font

from pathlib import Path

from config.config import Config
from ..state import State
from ..xtk.Checkbox import LabeledCheckbox
from ..xtk.FlatImageButton import FlatImageButton

class SettingsPage(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, padx=16, pady=16)
        self.config(bg='#111')
        self.config(*args, **kwargs)
        self.parent = parent

        self.state = State.get_instance()
        self.cfg   = Config.get_instance()

        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text='Warning: only enable advanced features if you know what you\'re doing!', anchor='center', fg='#FD5', bg=self['bg'], font=('Arial', 20, 'bold'))
        header.pack(pady=(0, 8), fill='x')

        enable_targeted_checkbox = LabeledCheckbox(self, 'Targeted Frame Analysis (Advanced)', ('Arial', 18, 'bold'), initial_state=self.cfg.data.targeted_analysis_enabled)
        enable_targeted_checkbox.on_toggle(lambda v: self.update_cfg('targeted_analysis_enabled', v))
        enable_targeted_checkbox.pack(padx=(8, 0), anchor='nw')
    

    def update_cfg(self, key, value):
        print('Set {} to {}'.format(key, value))
        self.cfg.data.__setattr__(key, value)
        self.state.refresh_all_extract_forms()

