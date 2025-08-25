import tkinter as tk
from tkinter.font import Font

from frontend.style import brighter, darker

from .Tooltip import Tooltip

class CompactCheckbox(tk.Canvas):
    def __init__(self, parent, *args, text, active=False, on_change: callable, active_bg, tooltip_text='', flip=False, fill=False, **kwargs):
        tk.Canvas.__init__(self, parent)
        self.config(bg='#222', relief='flat', cursor='hand2', borderwidth=0, highlightthickness=0)
        self.config(*args, **kwargs)

        self.active = active
        self.active_bg = active_bg
        self.on_change = on_change
        self.flip = flip
        self.fill = fill
        self.text = text
        self._first_draw = True

        if not self.fill:
            text_width = Font(family='Arial', size=16).measure(text)
            checkbox_width = int(self['height'])
            text_checkbox_gap = 4
            total_width = text_width + checkbox_width + text_checkbox_gap
            self.draw(total_width)
        else:
            self.draw(1)
            self.bind('<Configure>', self.on_configure)

        self.bind('<Button-1>', self.handle_click)
        self.bind('<Enter>', self.handle_enter)
        self.bind('<Leave>', self.handle_leave)

        if tooltip_text:
            Tooltip(self, text=tooltip_text, bg='#FFF')

    def on_configure(self, event):
        total_width = event.width
        (
            h, bt, g,
            text_x,
            border_x0, border_x1,
            inner_bg_x0, inner_bg_x1,
            core_id_x0, core_id_x1
        ) = self.calc_coords(total_width)

        self.coords(self.border_id, border_x0, 0, border_x1, h)
        self.coords(self.inner_bg, inner_bg_x0, bt, inner_bg_x1, h-bt)
        self.coords(self.core_id, core_id_x0, bt+g, core_id_x1, h-bt-g)

    def calc_coords(self, total_width):
        h  = int(self['height'])
        bt = h // 7 # border_thickness
        g  = 3      # core/border gap
    
        text_x                   = h + 4
        border_x0, border_x1     = 0,    h
        inner_bg_x0, inner_bg_x1 = bt,   h-bt
        core_id_x0, core_id_x1   = bt+g, h-bt-g
        if self.flip:
            text_x = 4
            border_x0, border_x1 = (
                total_width - h + border_x0,
                total_width - h + border_x1
            )
            inner_bg_x0, inner_bg_x1 = (
                total_width - h + inner_bg_x0,
                total_width - h + inner_bg_x1
            )
            core_id_x0, core_id_x1 = (
                total_width - h + core_id_x0,
                total_width - h + core_id_x1,
            )

        return (
            h, bt, g,
            text_x,
            border_x0, border_x1,
            inner_bg_x0, inner_bg_x1,
            core_id_x0, core_id_x1
        )

    def draw(self, total_width):
        (
            h, bt, g,
            text_x,
            border_x0, border_x1,
            inner_bg_x0, inner_bg_x1,
            core_id_x0, core_id_x1
        ) = self.calc_coords(total_width)

        self.text_id   = self.create_text(text_x, h//2, anchor='w', text=self.text, font=('Arial', 16), fill='#CCC')
        self.border_id = self.create_rectangle(border_x0, 0, border_x1, h, outline='', fill=self.active_bg)
        self.inner_bg  = self.create_rectangle(inner_bg_x0, bt, inner_bg_x1, h-bt, outline='', fill=self['bg'])
        self.core_id   = self.create_rectangle(core_id_x0, bt+g, core_id_x1, h-bt-g, outline='', fill=self.active_bg)

        if not self.active:
            self.itemconfig(self.core_id, fill=self['bg'])

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
