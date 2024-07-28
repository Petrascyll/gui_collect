from pathlib import Path
import os
import subprocess

import tkinter as tk

import frame_analysis.frame_analysis

from .xtk.FlatButton import FlatButton
from .xtk.Checkbox import LabeledCheckbox
from .xtk.EntryWithPlaceholder import EntryWithPlaceholder
from .xtk.InputComponentList import InputComponentList
from .state import State

from frame_analysis import frame_analysis
from frame_analysis.buffer_utilities import is_valid_hash
from targeted_dump import targeted_dump

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class ExtractForm(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent
        self.configure_grid()
        self.create_widgets()

        self.state = State.get_instance()

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self   .grid_rowconfigure(1, weight=1)
        self   .grid_rowconfigure(2, weight=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        self.component_options_frame = tk.Frame(self, bg='#600')
        self.extract_options_frame   = tk.Frame(self, bg='#060')
        self.targeted_dump           = tk.Frame(self, bg='#006')
        self.extract_frame           = tk.Frame(self, bg='#066')

        self.input_component_list = InputComponentList(self.component_options_frame)
        self.input_component_list.pack(fill='x')

        self.extract_name = EntryWithPlaceholder(
            self.extract_options_frame, placeholder='Export Name',
            color='#555', font=('Arial', '24', 'bold'),
            bg='#333', relief='flat', width=32
        )
        self.extract_name.pack(pady=(20, 10))
        checkbox_0 = LabeledCheckbox(self.extract_options_frame, text='Clean Extracted Folder', initial_state=True, font=('Arial', 20, 'bold'))
        checkbox_1 = LabeledCheckbox(self.extract_options_frame, text='Skip All Textures',      initial_state=False, font=('Arial', 20, 'bold'))
        checkbox_2 = LabeledCheckbox(self.extract_options_frame, text='Skip Small Textures',    initial_state=True, font=('Arial', 20, 'bold'))
        checkbox_3 = LabeledCheckbox(self.extract_options_frame, text='Open Extracted Folder after Completion', initial_state=True, font=('Arial', 20, 'bold'))
        checkbox_0.pack(side='top', anchor='w')
        checkbox_1.pack(side='top', anchor='w')
        checkbox_2.pack(side='top', anchor='w')
        checkbox_3.pack(side='top', anchor='w')

        clear_targeted_button = FlatButton(self.targeted_dump, text='Clear', bg='#0A0', hover_bg='#F00')
        clear_targeted_button.bind('<Button-1>', lambda _: self.clear_targeted_dump_ini())
        clear_targeted_button.pack(side='left', ipadx=16, ipady=16)

        generate_targeted_button = FlatButton(self.targeted_dump, text='Generate', bg='#0A0', hover_bg='#F00')
        generate_targeted_button.bind('<Button-1>', lambda _: self.generated_targeted_dump_ini())
        generate_targeted_button.pack(side='right', ipadx=16, ipady=16)

        extract_button = FlatButton(self.extract_frame, text='Extract', bg='#A00', hover_bg='#F00')
        extract_button.bind('<Button-1>', lambda _: self.start_extraction())
        extract_button.pack(ipadx=16, ipady=16)

        self.component_options_frame .grid(column=0, row=0, padx=(16, 0), pady=16, sticky='nsew', rowspan=3)
        self.extract_options_frame   .grid(column=1, row=0, padx=16, pady=(16, 0), sticky='nsew')
        self.targeted_dump           .grid(column=1, row=1, padx=16, pady=(16, 0), sticky='nsew')
        self.extract_frame           .grid(column=1, row=2, padx=16, pady=16, sticky='nsew')

    def collect_input(self):
        extract_name = self.extract_name.get().strip().replace(' ', '')
        ib_hashes = []
        component_names = []
        path = self.parent.address_frame.path

        input_components_data = self.input_component_list.get_data()
        for input_component_data in input_components_data:
            h = input_component_data.input_component_entry_data.hash.strip()
            n = input_component_data.input_component_entry_data.name.strip().replace(' ', '')

            if not is_valid_hash(h):
                print('Invalid hash: {}'.format(h))
                return None, None, None, None

            ib_hashes.append(h)
            component_names.append(n)

        # return 'Rina', ['2825da1e'], ['Dress'], path
        return extract_name, ib_hashes, component_names, path

    def generated_targeted_dump_ini(self):
        extract_name, ib_hashes, component_names, _ = self.collect_input()
        if not ib_hashes: return
        targeted_dump.generate(extract_name, ib_hashes, component_names)

    def clear_targeted_dump_ini(self):
        targeted_dump.clear()

    def start_extraction(self):
        self.state.lock_sidebar()

        extract_name, ib_hashes, component_names, path = self.collect_input()
        if not extract_name:    return
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
            self.parent.texture_picker.load(extract_name, extracted_components, callback=self.finish_extraction)
        else:
            self.finish_extraction(extract_name, extracted_components)

    def finish_extraction(self, extract_name, extracted_components, collected_textures=None):
        try:
            frame_analysis.export(extract_name, extracted_components, collected_textures)
            subprocess.run([FILEBROWSER_PATH, Path('_Extracted', extract_name)])
            print('Extraction done')
            # print('Extraction done {:.3}s'.format(time.time() - st))
        except frame_analysis.FrameAnalysisException as X:
            print(X.message)
            print('Frame Analysis Failed!')
            return
        self.state.unlock_sidebar()

    def cancel_extraction(self):
        self.state.unlock_sidebar()
