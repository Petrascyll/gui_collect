import tkinter as tk
from pathlib import Path

from .data import Page
from .style import APP_STYLE, brighter, darker
from .xtk.FlatImageButton import FlatImageButton
from .xtk.Tooltip import Tooltip
from .state import State

sidebar_button_style = {
    'width': 72,
    'height': 72,
    'img_width': 64,
    'img_height': 64,
}

class Sidebar(tk.Frame):
    def __init__(self, parent, active_page: Page, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(
            bg=APP_STYLE['sidebar_background'],
            padx=0, pady=0, relief=tk.FLAT,
        )
        self.parent = parent
        self.active_page = active_page
        self._locked = False

        self._state = State.get_instance()
        self._state.register_sidebar(self)

        self.create_widgets()
        self.refresh_buttons()

    def create_widgets(self):
        self.buttons = {}

        def add_button(page, bg_color, img_path, tooltip_text, subsample=1, bottom=False):
            img = tk.PhotoImage(file=Path(img_path)).subsample(subsample)
            b = FlatImageButton(self, bg=bg_color, image=img, **sidebar_button_style)
            b.bind('<Button-1>', lambda _: self.handle_button_click(page))
            if bottom:
                b.pack(side='bottom')
            else:
                b.pack()

            tooltip = Tooltip(b, text=tooltip_text, bg='#FFF', waittime=400, wraplength=250)
            b.bind("<Enter>", tooltip.onEnter)
            b.bind("<Leave>", tooltip.onLeave)

            self.buttons[page] = (b, bg_color)

        add_button(page=Page.zzz, bg_color='#e2751e', img_path='./resources/images/icons/Corin.png',   tooltip_text="Collect for Zenless Zone Zero")
        add_button(page=Page.hsr, bg_color='#7a6ce0', img_path='./resources/images/icons/Fofo.png',    tooltip_text="Collect for Honkai: Star Rail")
        add_button(page=Page.gi,  bg_color='#5fb970', img_path='./resources/images/icons/Sucrose.png', tooltip_text="Collect for Genshin Impact")
        add_button(page=Page.hi3, bg_color='#c660cf', img_path='./resources/images/icons/Mobius.png',  tooltip_text="Collect for Honkai Impact 3rd")
        add_button(page=Page.settings, bg_color='#AAA', img_path='./resources/images/buttons/settings.1.64.png', tooltip_text="Settings", bottom=True)

    def refresh_buttons(self):
        active_accent = self.buttons[self.active_page][1]
        for page, (button, _) in self.buttons.items():
            if page == self.active_page:
                button.config(bg=darker(darker(active_accent)))
                self.config(bg=active_accent)
            else:
                button.config(bg=active_accent)
            
            button.refresh()

    def disable_buttons(self):
        active_accent = self.buttons[self.active_page][1]
        self.config(bg=active_accent)
        for _, (button, _) in self.buttons.items():
            button.config(bg=active_accent)
            button.disable()

    def handle_button_click(self, page: Page):
        if self._locked: return
        if page == self.active_page: return

        self._state.update_active_page(page)
        self.active_page = page
        self.refresh_buttons()

    def lock(self):
        self._locked = True
        self.disable_buttons()
    
    def unlock(self):
        self._locked = False
        self.refresh_buttons()
