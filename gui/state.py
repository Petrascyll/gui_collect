

class State():
    '''
    Global state management for certain global-ish widgets
    because I'm tired of drilling args and methods through
    multiple nested levels
    '''
    __instance = None

    def __init__(self):
        if State.__instance != None:
            raise Exception('State has already been intialized.')
        State.__instance = self

        self.sidebar = None
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
