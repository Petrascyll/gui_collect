from pathlib import Path
import os
import time
import traceback
import subprocess

import tkinter as tk

from .xtk.FlatButton import FlatButton
from .xtk.Checkbox import LabeledCheckbox
from .xtk.EntryWithPlaceholder import EntryWithPlaceholder
from .xtk.InputComponentList import InputComponentFrameList
from .state import State

from backend.config.Config import Config
from backend.analysis.FrameAnalysis import FrameAnalysis
from backend.utils import is_valid_hash
from backend.analysis import targeted_analysis

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class ExtractForm(tk.Frame):
    def __init__(self, parent, variant, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent
        self.variant = variant
        
        self.cfg = Config.get_instance()
        self.state = State.get_instance()
        self.state.register_extract_form(self)

        self.terminal = self.state.get_terminal()

        self.configure_grid()
        self.create_widgets()
        self.grid_widgets()

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=0)
        self   .grid_rowconfigure(1, weight=0)
        self   .grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

    def create_widgets(self):
        self.component_options_frame = tk.Frame(self, bg='#222', width=600)
        self.extract_options_frame   = tk.Frame(self, bg='#222', padx=16, pady=16)
        self.targeted_dump           = tk.Frame(self, bg='#222', padx=16, pady=16)
        self.extract_frame           = tk.Frame(self, bg='#111')

        self.input_component_list = InputComponentFrameList(self.component_options_frame)
        self.input_component_list.pack(anchor='w', fill='x')

        self.extract_name = EntryWithPlaceholder(
            self.extract_options_frame, placeholder='Extract Name',
            color='#555', font=('Arial', '24', 'bold'),
            bg='#333', relief='flat', width=32
        )
        self.extract_name.pack(fill='x', pady=(0, 12))
        checkbox_0 = LabeledCheckbox(self.extract_options_frame, disabled=True, initial_state=False, font=('Arial', 20, 'bold'), text='Clean Extracted Folder')
        checkbox_1 = LabeledCheckbox(self.extract_options_frame, disabled=True, initial_state=False, font=('Arial', 20, 'bold'), text='Skip All Textures')
        checkbox_2 = LabeledCheckbox(self.extract_options_frame, disabled=True, initial_state=True,  font=('Arial', 20, 'bold'), text='Skip Small Textures')
        checkbox_3 = LabeledCheckbox(self.extract_options_frame, disabled=True, initial_state=True,  font=('Arial', 20, 'bold'), text='Open Extracted Folder after Completion')
        checkbox_0.pack(side='top', pady=(4, 0), anchor='w')
        checkbox_1.pack(side='top', pady=(4, 0), anchor='w')
        checkbox_2.pack(side='top', pady=(4, 0), anchor='w')
        checkbox_3.pack(side='top', pady=(4, 0), anchor='w')

        targeted_dump_frame_title = tk.Label(self.targeted_dump, text='Targeted Frame Analysis', bg='#222', fg='#555', anchor='center', font=('Arial', '20', 'bold'))
        targeted_dump_frame_title.pack(fill='x', pady=(0, 8))

        clear_targeted_button = FlatButton(self.targeted_dump, text='Clear', bg='#0A0', hover_bg='#F00')
        clear_targeted_button.bind('<Button-1>', lambda _: self.clear_targeted_dump_ini())
        clear_targeted_button.pack(side='left', ipadx=16, ipady=16)

        generate_targeted_button = FlatButton(self.targeted_dump, text='Generate', bg='#0A0', hover_bg='#F00')
        generate_targeted_button.bind('<Button-1>', lambda _: self.generated_targeted_dump_ini())
        generate_targeted_button.pack(side='right', ipadx=16, ipady=16)

        extract_button = FlatButton(self.extract_frame, text='Extract', bg='#A00', hover_bg='#F00')
        extract_button.bind('<Button-1>', lambda _: self.start_extraction())
        extract_button.pack(fill='x', side='bottom', anchor='e', ipadx=16, ipady=16)

    def grid_forget_widgets(self):
        for child in self.winfo_children():
            child.grid_forget()
            # print('Forgot {}'.format(child))

    def grid_widgets(self):
        self.component_options_frame .grid(column=0, row=0, padx=(16, 0), pady=16, sticky='nsew', rowspan=3)
        self.extract_options_frame   .grid(column=1, row=0, padx=16, pady=(16, 0), sticky='nsew')
        if self.cfg.data.targeted_analysis_enabled:
            self.targeted_dump.grid(column=1, row=1, padx=16, pady=(16, 0), sticky='nsew')
            self.extract_frame.grid(column=1, row=2, padx=16, pady=16, sticky='nsew')
        else:
            self.extract_frame.grid(column=1, row=1, rowspan=2, padx=16, pady=16, sticky='nsew')

    def collect_input(self, skip_collect_nothing=True):
        path = Path(self.parent.address_frame.path)
        extract_name = self.extract_name.get().strip().replace(' ', '')

        input_component_hashes   = []
        input_component_names    = []
        input_components_options = []
        for input_component in self.input_component_list.get():
            if not input_component.hash: continue
            if not is_valid_hash(input_component.hash):
                self.terminal.print('<ERROR>Invalid hash: {}</ERROR>'.format(input_component.hash))
                return None, None, None, None, None
            
            # Don't include components with none of the collect options enabled
            if skip_collect_nothing:
                collect_nothing = all(option_value is False for option_value in input_component.options.values())
                if collect_nothing: continue

            input_component_hashes  .append(input_component.hash)
            input_component_names   .append(input_component.name)
            input_components_options.append(input_component.options)

        return extract_name, input_component_hashes, input_component_names, input_components_options, path

    def generated_targeted_dump_ini(self):
        extract_name, input_component_hashes, input_component_names, _, path = self.collect_input(skip_collect_nothing=False)
        if not input_component_hashes:
            self.terminal.print('<ERROR>Targeted Ini Generation Aborted! No valid hashes provided.</ERROR>')
            self.terminal.print()
            return

        d3dx_path = path.parent
        if not (d3dx_path/'d3dx.ini').exists():
            d3dx_path = None

        targeted_analysis.generate(extract_name, input_component_hashes, input_component_names, d3dx_path, self.terminal)

    def clear_targeted_dump_ini(self):
        targeted_analysis.clear(self.terminal)

    def start_extraction(self):
        st = time.time()

        extract_name, input_component_hashes, input_component_names, input_components_options, path = self.collect_input()
        if not input_component_hashes:
            self.terminal.print('<ERROR>Frame Analysis Aborted! No valid hashes provided.</ERROR>')
            self.terminal.print()
            return
        if not extract_name:
            self.terminal.print('<ERROR>Frame Analysis Aborted! You must provided a name for the extracted model.</ERROR>')
            self.terminal.print()
            return
        if not (path/'log.txt').exists():
            self.terminal.print('<ERROR>Frame Analysis Aborted! Invalid frame analysis path: "{}".</ERROR>'.format(str(path)))
            self.terminal.print()
            return

        frame_analysis = FrameAnalysis(path)
        self.state.set_var(State.K.FRAME_ANALYSIS, frame_analysis)
        extracted_components = frame_analysis.extract(input_component_hashes, input_component_names, input_components_options, game=self.variant.value)
        if extracted_components is None:
            self.terminal.print('<ERROR>Frame Analysis Failed!</ERROR>')
            self.terminal.print()
            return

        # Create list with indices of components that need their textures to be selected in the texture picker
        # The other components should not show up in the texture picker, but should still be exported
        textures_component_idx = [
            idx for idx, extracted_component in enumerate(extracted_components)
            if extracted_component.options['collect_texture_data'] or extracted_component.options['collect_texture_hashes']
        ]

        if len(textures_component_idx) > 0:
            self.state.lock_sidebar()
            self.parent.texture_picker.load(extract_name, extracted_components, textures_component_idx, finish_extraction_callback=self.finish_extraction)
            self.parent.texture_picker.focus_set()
            self.update_idletasks()
            self.parent.show_texture_picker()
            self.update_idletasks()
        else:
            self.finish_extraction(extract_name, extracted_components)

        self.terminal.print('Ready {:.3}s'.format(time.time() - st))

    def finish_extraction(self, extract_name, extracted_components, collected_textures=None):
        try:
            frame_analysis = self.state.get_var(State.K.FRAME_ANALYSIS)
            frame_analysis.export(extract_name, extracted_components, collected_textures, game=self.variant.value)
            self.state.del_var(State.K.FRAME_ANALYSIS)

            extract_dir = Path('_Extracted', extract_name)

            self.terminal.print(f'Opening <PATH>{extract_dir.absolute()}</PATH> with File Explorer')
            self.terminal.print()

            subprocess.run([FILEBROWSER_PATH, extract_dir])
        except Exception as X:
            self.terminal.print(f'<ERROR>{X}</ERROR>')
            self.terminal.print(f'<ERROR>{traceback.format_exc()}</ERROR>')
            self.terminal.print('<ERROR>Frame Analysis Failed!</ERROR>')

        self.state.unlock_sidebar()

    def cancel_extraction(self):
        self.terminal.print('<WARNING>Frame Analysis Canceled.</WARNING>')
        self.state.unlock_sidebar()
