import tkinter as tk
from frontend.style import brighter


class TextFilter(tk.Label):
    def __init__(self, parent,  callback: callable, *args, active:bool, values: tuple[str], value_labels: tuple[str]=None, initial_value_index: int, **kwargs):
        tk.Label.__init__(self, parent, width=max(len(v) for v in values), bg=parent['bg'], font=('Arial', 16, 'bold'), cursor='hand2')
        self.config(*args, **kwargs)

        self.active = active
        self.active_fg = '#E00'
        self.inactive_fg = '#333'

        if value_labels is None:
            value_labels = values

        self.callback = callback
        self.values = values
        self.value_labels = value_labels

        if self.active:
            self.value_index = initial_value_index
            self.config(fg=self.active_fg, text=value_labels[self.value_index])
        else:
            self.value_index = 0
            self.config(fg=self.inactive_fg, text=value_labels[1])

        self.bind('<Button-1>', self.handle_click)
        self.bind('<Enter>', lambda _: self.config(fg=brighter(self['fg'])))
        self.bind('<Leave>', lambda _: self.config(fg=self.active_fg if self.active else self.inactive_fg))
        
    def handle_click(self, _):
        if self.value_index == len(self.value_labels) - 1:
            self.value_index = 0
            self.active = False
            self.config(fg=self.inactive_fg, text=self.value_labels[1])
        elif self.value_index == 0:
            self.value_index = 1
            self.active = True
            self.config(fg=self.active_fg)
        else:
            self.value_index += 1
            self.config(text=self.value_labels[self.value_index])
        self.callback()

    def get(self, value):
        if not self.active: return True
        return self.values[self.value_index] == value
