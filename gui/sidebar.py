import tkinter as tk
from pathlib import Path

from .pages.main_page import MainPageT
from .style import APP_STYLE, brighter, darker
from .xtk.FlatButton import FlatButton

sidebar_button_style = {
    'width': 72,
    'height': 72,
    'img_width': 64,
    'img_height': 64,
}

class Sidebar(tk.Frame):
    def __init__(self, parent, active_page: MainPageT, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(
            bg=APP_STYLE['sidebar_background'],
            padx=0, pady=0, relief=tk.FLAT,
        )
        self.parent = parent
        self.active_page = active_page

        self.create_widgets()
        self.configure_buttons_bg()

    def create_widgets(self):
        self.buttons = {}

        bg_color = '#e2751e'
        img = tk.PhotoImage(file=Path('./resources/images/icons/Corin.png'))
        b = FlatButton(self, bg=bg_color, image=img, **sidebar_button_style)
        b.bind('<Button-1>', lambda _: self.handle_button_click(MainPageT.zzz))
        b.pack()
        self.buttons[MainPageT.zzz] = (b, bg_color)

        # bg_color = '#7a6ce0'
        # img = tk.PhotoImage(file=Path('./resources/images/icons/Fofo.png'))
        # b = FlatButton(self, bg=bg_color, image=img, **sidebar_button_style)
        # b.bind('<Button-1>', lambda _: self.handle_button_click(MainPageT.hsr))
        # b.pack()
        # self.buttons[MainPageT.hsr] = (b, bg_color)

        # bg_color = '#5fb970'
        # img = tk.PhotoImage(file=Path('./resources/images/icons/Sucrose.64.png'))
        # b = FlatButton(self, bg=bg_color, image=img, **sidebar_button_style)
        # b.bind('<Button-1>', lambda _: self.handle_button_click(MainPageT.gi))
        # b.pack()
        # self.buttons[MainPageT.gi] = (b, bg_color)

        # bg_color = '#AAA'
        # img = tk.PhotoImage(file=Path('./resources/images/buttons/settings.1.256.png')).subsample(4)
        # b = FlatButton(self, bg=bg_color, image=img, **sidebar_button_style)
        # b.bind('<Button-1>', lambda _: self.handle_button_click(MainPageT.settings))
        # b.pack(side='bottom')
        # self.buttons[MainPageT.settings] = (b, bg_color)

    def configure_buttons_bg(self):
        active_accent = self.buttons[self.active_page][1]
        for page, (button, _) in self.buttons.items():
            if page == self.active_page:
                button.config(bg=darker(darker(active_accent)))
                self.config(bg=active_accent)
            else:
                button.config(bg=active_accent)
            
            button.refresh_bg_binds()

    def handle_button_click(self, page: MainPageT):
        if page == self.active_page: return
        self.parent.change_main_page(page)
        self.active_page = page
        self.configure_buttons_bg()
