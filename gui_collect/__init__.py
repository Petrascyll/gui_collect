import logging
import tempfile
import tkinter as tk
import tkinter.ttk as ttk

from gui_collect.common import get_terminal_logging_handler

from gui_collect.frontend.style import APP_STYLE
from gui_collect.frontend.Terminal import Terminal
from gui_collect.frontend.sidebar import Sidebar
from gui_collect.frontend.main import Main
from gui_collect.frontend.state import State

from gui_collect.backend.config.Config import Config
from gui_collect.backend.analysis import targeted_analysis
from gui_collect.backend.utils.texture_utils.TextureManager import TextureManager


logger = logging.getLogger()


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self)
        self.config(*args, **kwargs)
        self.config(background=APP_STYLE['app_background'])
        self.state = State()

        version = '1.3.0'
        self.title(f'GUI Collect v{version}')
        self.geometry('1368x840')
        # self.geometry('1650x800')
        self.configure_style()
        self.configure_grid()
        self.create_widgets()
        self.grid_widgets()

        self.bind_class('Frame', '<Button-1>', lambda e: e.widget.focus_set())

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self   .grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        self.mt_paned_window = tk.PanedWindow(self, orient=tk.VERTICAL, opaqueresize=True, showhandle=False, sashwidth=4, bd=0, relief='flat', bg='#444')

        self.terminal = Terminal(parent=self.mt_paned_window)
        logger.addHandler(get_terminal_logging_handler(self.terminal.print))

        self.main     =     Main(parent=self.mt_paned_window, active_page=self.state.active_page)
        self.sidebar  =  Sidebar(parent=self, active_page=self.state.active_page)

        self.mt_paned_window.add(self.main)
        self.mt_paned_window.add(self.terminal)

    def grid_widgets(self):
        self.sidebar        .grid(column=0, row=0, sticky='nsew')
        self.mt_paned_window.grid(column=1, row=0, sticky='nsew')

        self.update()
        self.after_idle(lambda: self.mt_paned_window.sash_place(0, 0, int(self.winfo_height() * 0.75)))

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

            bordercolor="#222",
            
            arrowcolor="#222",
            troughcolor="#0D0D0D",
        )



def main():
    print('3dmigoto GUI collect script')
    cfg = Config()

    if cfg.data.debugging is True:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logger.setLevel(logging_level)

    targeted_analysis.clear(emit_log=False)
    with tempfile.TemporaryDirectory() as temp_dir:
        cfg.temp_data['temp_dir'] = temp_dir
        app = App()
        TextureManager(temp_dir)

        app.mainloop()
    cfg.save_config()
    targeted_analysis.clear(emit_log=False)
