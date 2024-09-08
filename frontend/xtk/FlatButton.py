import tkinter as tk


class FlatButton(tk.Label):
    def __init__(self, parent, hover_bg, *args, **kwargs):
        tk.Label.__init__(self, parent)
        self.parent = parent
        self.config(fg='#e8eaed', font=('Arial', 18, 'bold'), cursor='hand2')
        self.config(*args, **kwargs)

        bg = self['bg']

        self.bind('<Enter>', lambda e: e.widget.config(bg=hover_bg))
        self.bind('<Leave>', lambda e: e.widget.config(bg=bg))
