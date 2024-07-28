import time
from pathlib import Path
import os
import subprocess

import tkinter as tk

import frame_analysis.frame_analysis

from .xtk.FlatButton import FlatButton
from .xtk.EntryWithPlaceholder import EntryWithPlaceholder
from .xtk.InputComponentList import InputComponentList
from .style import darker, APP_STYLE

# from frame_analysis.frame_analysis import FrameAnalysis, FrameAnalysisException
from frame_analysis import frame_analysis
from frame_analysis.buffer_utilities import is_valid_hash

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class ExtractForm(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):

        self.export_name = EntryWithPlaceholder(
            self,
            placeholder='Export Name', color='#555',
            width=32,
            font=('Arial', '24', 'bold'),
            bg='#333', relief='flat'
        )
        self.export_name.pack(pady=(20, 10))

        self.input_component_list = InputComponentList(self)
        self.input_component_list.pack(fill='x')


        img = tk.PhotoImage(file=Path('./resources/images/icons/Corin.png').absolute())
        zzz = FlatButton(self, width=72, height=72, img_width=64, img_height=64, bg=darker(darker('#a1a98b')), image=img)
        zzz.bind('<Button-1>', lambda _: self.start_extraction())
        zzz.pack()

    def collect_input(self):
        export_name = self.export_name.get()
        ib_hashes = []
        component_names = []
        path = self.parent.address_frame.path

        input_components_data = self.input_component_list.get_data()
        for input_component_data in input_components_data:
            h = input_component_data.input_component_entry_data.hash
            n = input_component_data.input_component_entry_data.name

            if not is_valid_hash(h):
                print('Invalid hash: {}'.format(h))
                return None, None, None, None

            ib_hashes.append(h)
            component_names.append(n)

        # Ellen ----
        # export_name     = 'Ellen'
        # ib_hashes       = ['7f89a2b3', '9c7fac5a', 'a72cfb34', '569f47ac']
        # component_names = ['Hair'    , 'Head'    , 'Body',       'Weapon']

        # # Casual Ellen ----
        # export_name     = 'CasualEllen'
        # ib_hashes       = ['4450d7e1', 'c306ef25', '61320025',   '8bbdab33']
        # component_names = ['Hair'    , 'Head'    , 'UpperBody', 'LowerBody']
        # ----------

        return export_name, ib_hashes, component_names, path

    def start_extraction(self):
        export_name, ib_hashes, component_names, path = self.collect_input()
        if not export_name:     return
        if len(ib_hashes) == 0: return

        try:
            extracted_components = frame_analysis.extract(path, ib_hashes, component_names)
        except frame_analysis.FrameAnalysisException as X:
            print(X.message)
            print('Frame Analysis Failed!')
            return
        
        skip_textures = False
        if not skip_textures:
            self.parent.show_texture_picker()
            self.parent.texture_picker.load(export_name, extracted_components, callback=self.finish_extraction)
        else:
            self.finish_extraction(export_name, extracted_components)

    def finish_extraction(self, export_name, extracted_components, collected_textures=None):
        try:
            frame_analysis.export(export_name, extracted_components, collected_textures)
            subprocess.run([FILEBROWSER_PATH, Path('_Extracted', export_name)])
            print('Extraction done')
            # print('Extraction done {:.3}s'.format(time.time() - st))
        except frame_analysis.FrameAnalysisException as X:
            print(X.message)
            print('Frame Analysis Failed!')
            return

    def get_ib_hashes(self):
        ib_hashes = []
        for ib_hash_entry in self.ib_hash_entries:
            ib_hash = ib_hash_entry.get()
            if len(ib_hash) != 8:
                print('Invalid IB hash:', ib_hash)
                return
            
            try: int(ib_hash, 16)
            except:
                print('Invalid IB hash:', ib_hash)
                return

            ib_hashes.append(ib_hash)
        
        return ib_hashes
