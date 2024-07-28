from pathlib import Path

import tkinter as tk


class Checkbox(tk.Canvas):
    # https://www.tcl.tk/man/tcl8.6/TkCmd/checkbutton.htm
    def __init__(self, parent, active=False, *args, **kwargs):
        tk.Canvas.__init__(self, parent)
        self.config(relief='flat', cursor='hand2', borderwidth=0, highlightthickness=0)
        self.config(*args, **kwargs)

        self.border = tk.PhotoImage(file=Path('./resources/images/buttons/checkbutton_border.32.png'))
        self.core   = tk.PhotoImage(file=Path('./resources/images/buttons/checkbutton_core.18.32.png'))
 
        self.border_id = self.create_image(0, 0, anchor='nw', image=self.border)
        self.core_id   = self.create_image(0, 0, anchor='nw', image=self.core, state='hidden')

        self._active = False
        if active:
            self.toggle()

        self.bind('<Button-1>', lambda _: self.toggle())

    def toggle(self):
        if self._active:
            self._active = False
            self.itemconfigure(self.core_id, state='hidden')
        else:
            self._active = True
            self.itemconfigure(self.core_id, state='normal')

class LabeledCheckbox(tk.Frame):
    def __init__(self, parent, text, font, initial_state=False, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(bg=self.parent['bg'])
        self.config(*args, **kwargs)

        self.label    = tk.Label(self, text=text, font=font, fg='#e8eaed', bg=self['bg'], cursor='hand2')
        self.checkbox = Checkbox(self, active=initial_state, bg=self['bg'], width=32, height=32)

        self.label.bind('<Button-1>', lambda _: self.checkbox.toggle())

        self.label    .grid(row=0, column=1)
        self.checkbox .grid(row=0, column=0)

    def invoke(self):
        self.checkbox.toggle()
