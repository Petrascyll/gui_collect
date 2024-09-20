from enum import Enum, auto

from backend.config.Config import Config

from .data import Page


class State():
    '''
    Global state management for certain global-ish widgets
    because I'm tired of drilling args and methods through
    multiple nested levels
    '''
    __instance = None
    K = Enum('K', 'FRAME_ANALYSIS F_ARIAL16')

    def __init__(self):
        if State.__instance != None:
            raise Exception('State has already been intialized.')
        State.__instance = self

        self._cfg = Config.get_instance().data
        self.registered = {}

        self.active_page = Page[self._cfg.active_game] if self._cfg.active_game else Page.zzz
        self._active_page_callbacks = []

        self.sidebar  = None
        self.terminal = None
        self.extract_forms = []

    @staticmethod
    def get_instance():
        if State.__instance == None:
            raise Exception('State hasn\'t been initialized.')
        return State.__instance

    def register_sidebar(self, sidebar):
        if self.sidebar:
            raise Exception('Sidebar has already been registered')
        self.sidebar = sidebar

    def register_terminal(self, terminal):
        if self.terminal:
            raise Exception('Terminal has already been registered')
        self.terminal = terminal

    def get_terminal(self):
        return self.terminal

    def lock_sidebar(self):
        if not self.sidebar:
            raise Exception('Sidebar not registered')
        self.sidebar.lock()

    def unlock_sidebar(self):
        if not self.sidebar:
            raise Exception('Sidebar not registered')
        self.sidebar.unlock()

    def register_extract_form(self, extract_form):
        self.extract_forms.append(extract_form)
    
    def refresh_all_extract_forms(self):
        # print('Refreshing {}'.format(self.extract_forms))
        for extract_form in self.extract_forms:
            extract_form.grid_forget_widgets()
            extract_form.grid_widgets()

    def update_active_page(self, active_page: Page):
        self.active_page = active_page
        self._cfg.active_game = active_page.value
        for callback in self._active_page_callbacks:
            callback(active_page)
        
    def subscribe_active_page_updates(self, callback):
        self._active_page_callbacks.append(callback)
    
    def set_var(self, key, value):
        self.registered[key] = value
    
    def get_var(self, key):
        return self.registered[key]
    
    def del_var(self, key):
        del self.registered[key]

    def has_var(self, key):
        return key in self.registered
