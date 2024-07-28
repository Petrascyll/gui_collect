import tkinter as tk

from .InputComponent import InputComponent, InputComponentData


class InputComponentList(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(*args, **kwargs, bg=self.parent['bg'])
        self.create_widgets()

    def create_widgets(self):
        self.components: list[InputComponent] = []
        for _ in range(3):
            self.add_input_component()

    def get_data(self):
        data: list[InputComponentData] = []
        for component in self.components:
            d = component.get_data()
            if not d.input_component_entry_data.hash:
                continue
            data.append(d)

        return data
    
    def hash_key_release(self, e, i):
        c = len(self.components)
        if i == c - 1:
            s = e.widget.get()
            if not s: return
            self.add_input_component()
        return

    def add_input_component(self):
        i = len(self.components)
        self.components.append(InputComponent(self, index=i))
        self.components[-1].pack(side='top', pady=4)

        self.components[-1].component_entry.component_hash.bind(
            '<KeyRelease>',
            lambda e: self.hash_key_release(e, i)
        )

