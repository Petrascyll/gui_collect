import tkinter as tk
from ..style import brighter


class FlatImageButton(tk.Canvas):
    def __init__(self, parent, image, img_width, img_height, width, height, *args, **kwargs):
        tk.Canvas.__init__(self, parent, width=width, height=height, cursor='hand2', relief='flat', highlightthickness=0, *args, **kwargs)

        self.image = image
        padx = (width - img_width) // 2
        pady = (height - img_height) // 2
        self.create_image(padx, pady, anchor='nw', image=self.image)

        if 'bg' in kwargs:
            self.refresh()

    def refresh(self):
        self.config(cursor='hand2')
        default_color = self['bg']
        hover_over_color = brighter(default_color)

        self.bind('<Enter>', func=lambda e: e.widget.config(bg=hover_over_color))
        self.bind('<Leave>', func=lambda e: e.widget.config(bg=default_color))

    def disable(self):
        self.config(cursor='left_ptr')
        self.unbind('<Enter>')
        self.unbind('<Leave>')
