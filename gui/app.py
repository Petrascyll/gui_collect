import tkinter as tk
import tkinter.ttk as ttk

from .pages.main_page import MainPageT

from .style import APP_STYLE
from .sidebar import Sidebar
from .main import Main
from .state import State

from config.config import Config

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self)
        self.config(*args, **kwargs)
        self.config(background=APP_STYLE['app_background'])

        self.cfg = Config.get_instance().data
        self.state = State()

        self.title('GUI Collect')
        self.geometry('1650x800')
        # self.geometry('800x800')
        self.configure_style()
        self.configure_grid()
        self.create_widgets()
        self.grid_widgets()

        self.bind_class('Frame', '<Button-1>', lambda e: e.widget.focus_set())

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        last_active_page = self.cfg.active_game
        active_page = MainPageT[last_active_page] if last_active_page else MainPageT.zzz

        self.sidebar = Sidebar(parent=self, active_page=active_page)
        self.main    =    Main(parent=self, active_page=active_page)

    def grid_widgets(self):
        self.sidebar.grid(column=0, row=0, sticky='nsew')
        self.main   .grid(column=1, row=0, sticky='nsew')

    def change_main_page(self, target_page: MainPageT):
        self.main.change_page(target_page)
        self.cfg.active_game = target_page.value

    def configure_style(self):
        # styling tk.Scrollbar via parameters didn't work
        # even though the docs claim that its valid...
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.layout(
            'no_arrows.Vertical.TScrollbar', 
            [
                (
                    'Vertical.Scrollbar.trough',
                    {
                        'children': [
                            (
                                'Vertical.Scrollbar.thumb',
                                {
                                    'expand': '1',
                                    'sticky': 'nswe'
                                }
                            )
                        ],
                    'sticky': 'ns'
                    }
                )
            ]
        )
        
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', '#333')]
        )
        self.style.configure("Vertical.TScrollbar",
            gripcount=0,
            background="#222",
            
            lightcolor="#222",
            darkcolor ="#222",

            bordercolor="#111",
            
            arrowcolor="#222",
            troughcolor="#0D0D0D",
        )
