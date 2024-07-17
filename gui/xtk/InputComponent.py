import tkinter as tk
from dataclasses import dataclass

from .EntryWithPlaceholder import EntryWithPlaceholder

@dataclass
class InputComponentEntryData():
    name: str
    hash: str

@dataclass
class InputComponentData():
    input_component_entry_data: InputComponentEntryData


class InputComponent(tk.Frame):
    def __init__(self, parent, index, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent
        self.config(bg='#111')

        self.index = index

        self.configure_grid()
        self.create_widgets()

    def create_widgets(self):
        self.component_entry = _Component_Entry(self)
        self.component_entry.grid(row=0, column=0, sticky='nsew')

        # tk.Label(self, text='1').grid(row=0, column=1, sticky='nsew')
        # tk.Label(self, text='2').grid(row=0, column=2, sticky='nsew')

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

    def get_data(self):
        return InputComponentData(
            input_component_entry_data=self.component_entry.get_data()
        )


class _Component_Entry(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        self.component_hash = EntryWithPlaceholder(
            self,
            placeholder='IB Hash', color='#555',
            width=16,
            font=('Arial', '24', 'bold')
        )
        self.component_name = EntryWithPlaceholder(
            self,
            placeholder='Component Name', color='#555',
            width=16,
            font=('Arial', '24', 'bold')
        )

        self.component_hash.pack(pady=(0,1))
        self.component_name.pack()

    def get_data(self):
        return InputComponentEntryData(
            hash=self.component_hash.get(),
            name=self.component_name.get(),
        )
    
    def key_release(self, event):
        s = self.component_hash.get()
        if s:
            self.parent.parent.add_input_component()
