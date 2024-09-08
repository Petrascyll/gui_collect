import tkinter as tk
from dataclasses import dataclass

from .EntryWithPlaceholder import EntryWithPlaceholder
from .Checkbox import LabeledCheckbox


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
        self.input_component_frames[-1].pack(side='top', padx=16, anchor='w', pady=pady)

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
        self   .rowconfigure(0, weight=0)
        self   .rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

    def create_widgets(self):
        self.component_hash_entry = EntryWithPlaceholder(
            self,
            placeholder='IB Hash', color='#555',
            width=16,
            font=('Arial', '24', 'bold')
        )
        self.component_name_entry = EntryWithPlaceholder(
            self,
            placeholder='Component Name', color='#555',
            width=16,
            font=('Arial', '24', 'bold')
        )
        self.component_options_frame = tk.Frame(self, bg=self['bg'])

        self.component_hash_entry   .grid(row=0, column=0, pady=(0,1), sticky='n')
        self.component_name_entry   .grid(row=1, column=0, pady=(0,1), sticky='n')
        self.component_options_frame.grid(row=0, column=1, rowspan=2,  sticky='nsew', padx=4, pady=4)

        # TODO
        boolean_options = [
            ('textures_only', 'Textures Only', False),
        ]
        for option_key, option_text, initial_value in boolean_options:
            checkbox = LabeledCheckbox(self.component_options_frame, text=option_text, font=('Arial', 18, 'bold'), disabled=False, initial_state=initial_value)
            checkbox.key = option_key
            checkbox.pack(pady=(0, 6), anchor='nw')



    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

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
