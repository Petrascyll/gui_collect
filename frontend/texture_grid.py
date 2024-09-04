import tkinter as tk
from functools import partial

from .xtk.ScrollableFrame import ScrollableFrame
from .texture_grid_item import TextureGridItem
from backend.analysis.structs import Component
from .state import State


class TextureGrid(tk.Frame):
    def __init__(self, parent, get_ref, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs, bg='#111')

        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.parent = parent
        self.get_ref = get_ref

        self.component_index = -1
        self.first_index     = -1

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.id_picker = tk.Frame(self, width=74, bg='#333')
        self.id_picker.grid(row=0, column=0, padx=(1,0), sticky='nsew')
        self.id_picker.pack_propagate(False)

        self.frames: dict[int, dict[int, dict[str, ScrollableFrame]]] = {
            # component_index: {
            #     first_index: {
            #         id: scrollable_frame
            #     },
            #  },
        }


    def load(self, components: list[Component], component_index, first_index):
        self.component_index = component_index
        self.first_index     = first_index
        self.active_id       = components[component_index].tex_index_id[first_index]

        frame_analysis = State.get_instance().get_var(State.K.FRAME_ANALYSIS)
        self.grid_refresh()
        
        for i, component in enumerate(components):
            if i not in self.frames: self.frames[i] = {}
            for first_index in component.object_indices:
                frame = ScrollableFrame(self, bg='#111')
                frame.grid(row=0, column=1, sticky='nsew')
                frame.lower()

                initial_id = component.tex_index_id[first_index]
                textures = frame_analysis.get_textures(initial_id)
                self.create_widgets(frame, textures, i, first_index)
                self.grid_widgets(frame)

                self.frames[i][first_index] = {
                    id: None
                    for id in component.index_ids[first_index]
                }
                self.frames[i][first_index][initial_id] = frame
                self.frames[i][first_index]['active_id'] = initial_id

        self.frames[self.component_index][self.first_index][self.active_id].bind("<Configure>", self._on_frame_configure)
        self.frames[self.component_index][self.first_index][self.active_id].tkraise()
        self.refresh_id_picker(self.component_index, self.first_index)

    def refresh_id_picker(self, component_index: int, first_index: int):
        for child in self.id_picker.winfo_children():
            child.destroy()

        header = tk.Label(self.id_picker, text='ID', font=('Arial', '24', 'bold'))
        header.config(bg='#333', fg='#e8eaed')
        header.pack(side='top', pady='4', anchor='center')

        for id in self.frames[component_index][first_index]:
            if id == 'active_id': continue
            active_id = self.frames[component_index][first_index]['active_id']

            id_label = tk.Label(self.id_picker, text=str(id), cursor='hand2', font=('Arial', '10', 'bold'))
            if id == active_id:
                id_label.config(bg='#A00', fg='#e8eaed')
            else:
                id_label.config(bg='#444', fg='#e8eaed')
                id_label.bind('<Enter>', func=lambda e: e.widget.config(bg='#A00'))
                id_label.bind('<Leave>', func=lambda e: e.widget.config(bg='#444'))
                id_label.bind('<Button-1>', partial(self.set_active_grid_id, component_index, first_index, id))
            id_label.pack(side='top', pady='2', ipady='4', ipadx='8', anchor='center')

    def set_active_grid_id(self, component_index, first_index, id, event):
        if self.frames[component_index][first_index][id] is not None:
            self.frames[component_index][first_index]['active_id'] = id
            self.set_active_grid(component_index, first_index)
            return
        
        frame = ScrollableFrame(self, bg='#111')
        frame.grid(row=0, column=1, sticky='nsew')
        frame.lower()
    
        frame_analysis = State.get_instance().get_var(State.K.FRAME_ANALYSIS)
        self.create_widgets(frame, frame_analysis.get_textures(id), component_index, first_index)
        self.grid_widgets(frame)

        self.frames[component_index][first_index][id] = frame
        self.frames[component_index][first_index]['active_id'] = id
        self.set_active_grid(component_index, first_index)

    def set_active_grid(self, component_index, first_index):
        self.frames[self.component_index][self.first_index][self.active_id].lower()
        self.frames[self.component_index][self.first_index][self.active_id].unbind_all("<Configure>")

        self.component_index = component_index
        self.first_index     = first_index
        self.active_id       = self.frames[component_index][first_index]['active_id']

        self.frames[self.component_index][self.first_index][self.active_id]._canvas.yview_moveto(0)
        self.frames[self.component_index][self.first_index][self.active_id].bind("<Configure>", self._on_frame_configure)
        self.frames[self.component_index][self.first_index][self.active_id].event_generate('<Configure>')
        self.frames[self.component_index][self.first_index][self.active_id].tkraise()
        self.refresh_id_picker(self.component_index, self.first_index)

    def unload(self):
        for component_index in self.frames:
            for first_index in self.frames[component_index]:
                for id in self.frames[component_index][first_index]:
                    if id == 'active_id': continue
                    if self.frames[component_index][first_index][id]:
                        self.frames[component_index][first_index][id].destroy()
        self.frames = {}

    def create_widgets(self, scrollable_frame, textures, component_index, first_index):
        for texture in textures:
            TextureGridItem(
                scrollable_frame.interior,
                texture, width=272, height=328,
                get_ref=lambda: self.get_ref(component_index, first_index)
            )

    def grid_widgets(self, scrollable_frame: ScrollableFrame):
        for i, item in enumerate(scrollable_frame.interior.winfo_children()):
            self.grid_widget(i, item)

    def grid_widget(self, i, item):
        first  = 0
        last   = self.column_count - 1
        row    = i // self.column_count
        column = i %  self.column_count

        if self.padding_style == 'even':
            # Even x padding on all items
            # ex: [----X----X----X----]
            padding = self.empty_space // (self.column_count + 1)
            if   column == first: padx = (padding   , padding//2)
            elif column == last : padx = (padding//2, padding)
            else: padx = (padding//2, padding//2)
            item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=self.pady)

        elif self.padding_style == 'centered':
            # Centered middle items
            # ex: [------X--X--X------]
            padding = (self.empty_space - ((self.column_count - 1) * self.min_padx))//2
            if   column == first: padx = (padding    , self.min_padx//2)
            elif column == last : padx = (self.min_padx//2, padding)
            else: padx = (self.min_padx//2, self.min_padx//2)
            item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=self.pady)

    def grid_refresh(self):
        self.padding_style = 'centered'
        self.pady      = (4, 0)
        self.min_padx  = 4

        # 272 is the width of a single grid item
        # 74  is the width of the id picker
        # 14  is the width of the scrollbar
        for column_count in range(1, 6):
            empty_space = self.winfo_width() - (272 * column_count) - 14 - 74
            min_empty_space = ((column_count - 1) * self.min_padx) + self.min_padx*2
            if min_empty_space <= empty_space <= 272 + min_empty_space:
                break
        else:
            empty_space = min_empty_space

        self.empty_space   = empty_space
        self.column_count  = column_count

    def _on_frame_configure(self, e):
        # print(e.widget.winfo_width(), e.widget.winfo_reqwidth())
        self.grid_refresh()
        self.grid_widgets(e.widget)
