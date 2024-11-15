import tkinter as tk

from frontend.style import brighter, darker

from .Tooltip import Tooltip

class CompactCheckbox(tk.Canvas):
    def __init__(self, parent, *args, text, active=False, on_change: callable, active_bg, tooltip_text='', **kwargs):
        tk.Canvas.__init__(self, parent)
        self.config(bg='#222', relief='flat', cursor='hand2', borderwidth=0, highlightthickness=0)
        self.config(*args, **kwargs)

        self.active = active
        self.active_bg = active_bg
        self.on_change = on_change

        h  = int(self['height'])
        bt = h // 7 # border_thickness
        g  = 3      # core/border gap

        self.border_id = self.create_rectangle(0, 0, h, h, outline='', fill=active_bg)
        self.inner_bg  = self.create_rectangle(bt, bt, h-bt, h-bt, outline='', fill=self['bg'])
        self.core_id   = self.create_rectangle(bt+g, bt+g, h-bt-g, h-bt-g, outline='', fill=active_bg)
        if not self.active:
            self.itemconfig(self.core_id, fill=self['bg'])
        self.text_id = self.create_text(h+4, h//2, anchor='w', text=text, font=('Arial', 16), fill='#CCC')

        self.bind('<Button-1>', self.handle_click)
        self.bind('<Enter>', self.handle_enter)
        self.bind('<Leave>', self.handle_leave)

        if tooltip_text:
            Tooltip(self, text=tooltip_text, bg='#FFF')

    def handle_click(self, _):
        self.active = not self.active
        if self.active:
            self.itemconfig(self.core_id, fill=self.active_bg)
        else:
            self.itemconfig(self.core_id, fill=self['bg'])
        self.on_change(self.active)

    def handle_enter(self, _):
        self.itemconfig(self.text_id, fill='#FFF')
        if self.active:
            self.itemconfig(self.core_id, fill=brighter(self.active_bg))
        else:
            self.itemconfig(self.core_id, fill=brighter(self['bg']))

    def handle_leave(self, _):
        self.itemconfig(self.text_id, fill='#CCC')
        if self.active:
            self.itemconfig(self.core_id, fill=self.active_bg)
        else:
            self.itemconfig(self.core_id, fill=self['bg'])
