import tkinter as tk

from .style import APP_STYLE
from .pages.main_page import MainPage, MainPageT

class Main(tk.Frame):
    def __init__(self, parent, active_page: MainPageT, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#111')
        self.parent = parent

        self.config(bg=APP_STYLE['app_background'])
        self.active_page = active_page

        self.create_widgets()
        self.pack_widgets()

    def create_widgets(self):
        self.pages = {
            MainPageT.zzz      : MainPage(parent=self, variant=MainPageT.zzz),
            MainPageT.hsr      : MainPage(parent=self, variant=MainPageT.hsr),
            MainPageT.gi       : MainPage(parent=self, variant=MainPageT.gi),
            MainPageT.settings : MainPage(parent=self, variant=MainPageT.settings)
        }

    def pack_widgets(self):
        self.pages[self.active_page].pack(fill='both', expand=True)

    def change_page(self, page: MainPageT):
        self.pages[self.active_page].pack_forget()
        self.active_page = page
        self.pack_widgets()
