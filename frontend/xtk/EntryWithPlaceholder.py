import tkinter as tk

class EntryWithPlaceholder(tk.Entry):
    def __init__(self, parent, placeholder='', color='grey', *args, **kwargs):
        super().__init__(parent)
        self.config(*args, **kwargs)
        self.config(insertbackground='grey', fg='#e8eaed', bg='#333', relief='flat')

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        if not self['text']:
            self.put_placeholder()

        self.bind("<FocusIn>", self.focus_in)
        self.bind("<FocusOut>", self.focus_out)

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def focus_in(self, e):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def focus_out(self, e):
        if not self.get():
            self.put_placeholder()

    def get(self):
        s = super().get()
        if s == self.placeholder:
            return ''
        return s
