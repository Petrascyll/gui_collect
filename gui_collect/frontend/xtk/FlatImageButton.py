import tkinter as tk
from ..style import brighter

from .Tooltip import Tooltip

class FlatImageButton(tk.Canvas):
    def __init__(self, parent, image, img_width, img_height, width, height, value=None, tooltip_text='', key='', dual_state=False, active_bg='', *args, **kwargs):
        tk.Canvas.__init__(self, parent, width=width, height=height, cursor='hand2', relief='flat', highlightthickness=0, *args, **kwargs)

        self.key   = key
        self.value = value

        if dual_state:
            self.def_bg  = self['bg'] if 'bg' in kwargs else '#111'
            self.active_bg = active_bg
            if self.value: self.config(bg=self.active_bg)
            self.bind('<Button-1>', add='+', func=self.toggle)

        self.set_image(image, img_width, img_height, width, height)
        if 'bg' in kwargs: self.refresh()

        if tooltip_text:
            Tooltip(self, text=tooltip_text, bg='#FFF')

    def set_image(self, image, img_width, img_height, width, height):
        self.image = image
        padx = (width - img_width) // 2
        pady = (height - img_height) // 2
        self.delete('all')
        self.create_image(padx, pady, anchor='nw', image=self.image)

    def refresh(self):
        self.config(cursor='hand2')
        default_color = self['bg']
        hover_over_color = brighter(default_color)

        self.bind('<Enter>', add='+', func=lambda e: e.widget.config(bg=hover_over_color))
        self.bind('<Leave>', add='+', func=lambda e: e.widget.config(bg=default_color))

    def disable(self):
        self.config(cursor='left_ptr')
        self.unbind('<Enter>')
        self.unbind('<Leave>')

    def get(self):
        return self.value

    def toggle(self, _):
        if self.value: self.config(bg=self.def_bg)
        else: self.config(bg=self.active_bg)
        self.value = not self.value
        self.refresh()
