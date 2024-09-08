import tkinter as tk

from .state import State
from .style import APP_STYLE
from .data import Page
from .pages.main_page import MainPage
from .pages.settings_page import SettingsPage

class Main(tk.Frame):
    def __init__(self, parent, active_page: Page, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent

        self._state = State.get_instance()
        self._state.subscribe_active_page_updates(callback=lambda active_page: self.change_page(active_page))

        self.config(bg=APP_STYLE['app_background'])
        self.active_page = active_page

        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.grid_widgets()

    def create_widgets(self):
        self.pages: dict[Page, tk.Widget] = {
            Page.zzz      : MainPage(parent=self, variant=Page.zzz),
            Page.hsr      : MainPage(parent=self, variant=Page.hsr),
            Page.gi       : MainPage(parent=self, variant=Page.gi),
            Page.settings : SettingsPage(parent=self)
        }

    def grid_widgets(self):
        self.pages[self.active_page].grid(row=0, column=0, sticky='nsew')

    def change_page(self, page: Page):
        self.pages[self.active_page].tkraise()
        self.pages[page].lower()
        self.pages[page].grid(row=0, column=0, sticky='nsew')

        self.update_idletasks()
        self.pages[self.active_page].grid_forget()
        self.pages[page].tkraise()

        self.active_page = page
