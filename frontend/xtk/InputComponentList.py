import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

from .EntryWithPlaceholder import EntryWithPlaceholder
from .FlatImageButton import FlatImageButton


@dataclass
class InputComponent():
    hash: str
    name: str
    options: dict[str, any]

class InputComponentFrameList(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(bg=self.parent['bg'])
        self.config(*args, **kwargs)
        self.create_widgets()

    def create_widgets(self):
        self.input_component_frames: list[InputComponentFrame] = []
        for _ in range(4):
            self.add_input_component_frame()

    def get(self) -> list[InputComponent]:
        return [input_component_frame.get() for input_component_frame in self.input_component_frames]
    
    def hash_key_release(self, e, i):
        c = len(self.input_component_frames)
        if i == c - 1:
            s = e.widget.get()
            if not s: return
            self.add_input_component_frame()
        return

    def add_input_component_frame(self):
        i = len(self.input_component_frames)
        self.input_component_frames.append(InputComponentFrame(self, index=i))
        pady = (16, 4) if i == 0 else (4, 4) 
        self.input_component_frames[-1].pack(side='top', padx=16, anchor='w', fill='x', pady=pady)

        self.input_component_frames[-1].component_hash_entry.bind(
            '<KeyRelease>',
            lambda e: self.hash_key_release(e, i)
        )


class InputComponentFrame(tk.Frame):
    def __init__(self, parent, index, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(bg=self.parent['bg'])
        self.config(*args, **kwargs)

        self.index = index

        self.configure_grid()
        self.create_widgets()

    def create_widgets(self):
        self.component_hash_entry = EntryWithPlaceholder(
            self,
            placeholder='IB Hash', color='#555',
            width=16,
            font=('Arial', '20', 'bold')
        )
        self.component_name_entry = EntryWithPlaceholder(
            self,
            placeholder='Component Name', color='#555',
            width=16,
            font=('Arial', '20', 'bold')
        )
        self.component_options_frame = tk.Frame(self, bg=self['bg'])

        self.component_hash_entry   .grid(row=0, column=0, pady=(0,1), sticky='nsew')
        self.component_name_entry   .grid(row=1, column=0, pady=(1,0), sticky='nsew')
        self.component_options_frame.grid(row=0, column=1, rowspan=2,  sticky='nsew', padx=(2,0))

        # TODO stop being lazy and hard coding colors
        variant_value = self.parent.parent.master.variant.value
        if variant_value   == 'hsr': active_bg = '#7a6ce0'
        elif variant_value == 'zzz': active_bg = '#e2751e'
        elif variant_value ==  'gi': active_bg = '#5fb970'
        elif variant_value == 'hi3': active_bg = '#c660cf'

        boolean_options = [
            ('collect_model_data',     True, tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'cube.inverted.74.png')), 'Collect model data. Model data will be extracted to the output folder.',),
            ('collect_model_hashes',   True, tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'hash.inverted.74.png')), 'Collect model hashes. Model hashes will be written to the hash.json in the output folder.',),
            ('collect_texture_data',   True, tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'dds.inverted.74.png')),  'Collect texture data. Texture data will be copied to the output folder.',),
            ('collect_texture_hashes', True, tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'hash.inverted.74.png')), 'Collect texture hashes. Texture hashes will be written to the hash.json in the output folder.',),
        ]

        for i, (option_key, initial_value, img, option_text) in enumerate(boolean_options):
            checkbox = FlatImageButton(
                self.component_options_frame,
                image=img, dual_state=True, key=option_key, value=initial_value,
                bg='#222', active_bg=active_bg, tooltip_text=option_text,
                img_width=74, img_height=74, width=74, height=74
            )

            padx = (0,0) if i != 1 else (0,2)
            checkbox.pack(anchor='nw', padx=padx, side='left')



    def configure_grid(self):
        self   .rowconfigure(0, weight=1)
        self   .rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

    def get(self):
        return InputComponent(
            hash = self.component_hash_entry.get().strip(),
            name = self.component_name_entry.get().strip().replace(' ', ''),
            options = {
                option_widget.key: option_widget.get()
                for option_widget in self.component_options_frame.winfo_children()
            }
        )

    def key_release(self, event):
        s = self.component_hash_entry.get()
        if s: self.parent.parent.add_input_component()

