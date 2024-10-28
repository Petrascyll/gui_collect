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

        self.bind("<Key>", _onKeyRelease)
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

# https://stackoverflow.com/questions/40946919/python-tkinter-copy-paste-not-working-with-other-languages
def _onKeyRelease(event):
    ctrl = (event.state & 0x4) != 0
    if ctrl:
        if event.keycode==65 and event.keysym.lower() != "a":
            event.widget.event_generate("<<SelectAll>>")
        elif event.keycode==67 and event.keysym.lower() != "c":
            event.widget.event_generate("<<Copy>>")
        elif event.keycode==88 and event.keysym.lower() != "x": 
            event.widget.event_generate("<<Cut>>")
        elif event.keycode==86 and event.keysym.lower() != "v": 
            event.widget.event_generate("<<Paste>>")
