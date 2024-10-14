from pathlib import Path
import time
import traceback

import tkinter as tk

from .xtk.FlatButton import FlatButton
from .xtk.EntryWithPlaceholder import EntryWithPlaceholder
from .xtk.InputComponentList import InputComponentFrameList
from .xtk.CompactCheckbox import CompactCheckbox
from .xtk.PathPicker import PathPicker
from .state import State

from backend.config.Config import Config
from backend.analysis.FrameAnalysis import FrameAnalysis
from backend.utils import is_valid_hash
from backend.analysis import targeted_analysis


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

        self.create_component_options()
        self.create_extract_options()
        self.create_targeted_options()

        extract_button = FlatButton(self.extract_frame, text='Extract', bg='#A00', hover_bg='#F00')
        extract_button.bind('<Button-1>', lambda _: self.start_extraction())
        extract_button.pack(fill='x', side='bottom', anchor='e', ipadx=16, ipady=16)

    def create_component_options(self):
        self.input_component_list = InputComponentFrameList(self.component_options_frame)
        self.input_component_list.pack(anchor='w', fill='x')

    def create_targeted_options(self):
        targeted_dump_frame_title = tk.Label(self.targeted_dump, text='Targeted Frame Analysis', bg='#222', fg='#555', anchor='center', font=('Arial', '20', 'bold'))
        targeted_dump_frame_title.pack(fill='x', pady=(0, 8))

        clear_targeted_button = FlatButton(self.targeted_dump, text='Clear', bg='#0A0', hover_bg='#F00')
        clear_targeted_button.bind('<Button-1>', lambda _: self.clear_targeted_dump_ini())
        clear_targeted_button.pack(side='left', ipadx=16, ipady=16)

        generate_targeted_button = FlatButton(self.targeted_dump, text='Generate', bg='#0A0', hover_bg='#F00')
        generate_targeted_button.bind('<Button-1>', lambda _: self.generated_targeted_dump_ini())
        generate_targeted_button.pack(side='right', ipadx=16, ipady=16)

    def create_extract_options(self):
        self.extract_name = EntryWithPlaceholder(
            self.extract_options_frame, placeholder='Extract Name',
            color='#555', font=('Arial', '24', 'bold'),
            bg='#333', relief='flat', width=32
        )
        self.extract_name.pack(side='top', fill='x', pady=(0, 2))

        variant_value = self.variant.value
        if variant_value   == 'hsr': active_bg = '#7a6ce0'
        elif variant_value == 'zzz': active_bg = '#e2751e'
        elif variant_value ==  'gi': active_bg = '#5fb970'
        elif variant_value == 'hi3': active_bg = '#c660cf'

        def handle_path_change(newPath: str):
            self.cfg.data.game[self.variant.value].extract_path = newPath
            self.terminal.print('Set Config: /game/extract/{}/extract_path = <PATH>{}</PATH>'.format(self.variant.value, newPath))

        pp = PathPicker(self.extract_options_frame, value=self.cfg.data.game[self.variant.value].extract_path, callback=handle_path_change, bg='#333', button_bg=active_bg)
        pp.pack(side='top', fill='x', pady=(0, 12))

        game_options = self.cfg.data.game[variant_value].game_options
        def handle_change_0(newValue: bool):
            self.terminal.print('Set Config: /game/{}/clean_extract_folder = {}'.format(variant_value, newValue))
            game_options.clean_extract_folder  = newValue
        def handle_change_1(newValue: bool):
            self.terminal.print('Set Config: /game/{}/open_extract_folder = {}'.format(variant_value, newValue))
            game_options.open_extract_folder   = newValue
        def handle_change_2(newValue: bool):
            self.terminal.print('Set Config: /game/{}/delete_frame_analysis = {}'.format(variant_value, newValue))
            game_options.delete_frame_analysis = newValue

        checkbox_0 = CompactCheckbox(self.extract_options_frame, height=30, active_bg=active_bg, active=game_options.clean_extract_folder,  on_change=handle_change_0, text='Clean extracted folder before extraction')
        checkbox_1 = CompactCheckbox(self.extract_options_frame, height=30, active_bg=active_bg, active=game_options.open_extract_folder,   on_change=handle_change_1, text='Open extracted folder after extraction')
        checkbox_2 = CompactCheckbox(self.extract_options_frame, height=30, active_bg=active_bg, active=game_options.delete_frame_analysis, on_change=handle_change_2, text='Delete frame analysis after extraction')
        checkbox_0.pack(side='top', pady=(3, 0), anchor='w', fill='x')
        checkbox_1.pack(side='top', pady=(3, 0), anchor='w', fill='x')
        checkbox_2.pack(side='top', pady=(3, 0), anchor='w', fill='x')



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
            self.terminal.print('Ready {:.3}s'.format(time.time() - st))
        else:
            self.finish_extraction(extract_name, extracted_components)

    def finish_extraction(self, extract_name, extracted_components, collected_textures=None):
        try:
            frame_analysis = self.state.get_var(State.K.FRAME_ANALYSIS)
            frame_analysis.export(extract_name, extracted_components, collected_textures, game=self.variant.value)
            if not frame_analysis.path.exists():
                self.parent.address_frame.load_latest_frame_analysis()
            self.state.del_var(State.K.FRAME_ANALYSIS)

        except Exception as X:
            self.terminal.print(f'<ERROR>{X}</ERROR>')
            self.terminal.print(f'<ERROR>{traceback.format_exc()}</ERROR>')
            self.terminal.print('<ERROR>Frame Analysis Failed!</ERROR>')

        self.state.unlock_sidebar()

    def cancel_extraction(self):
        self.terminal.print('<WARNING>Frame Analysis Canceled.</WARNING>')
        self.state.unlock_sidebar()
