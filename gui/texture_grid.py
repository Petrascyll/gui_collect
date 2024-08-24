import tkinter as tk

from .xtk.ScrollableFrame import ScrollableFrame
from .texture_grid_item import TextureGridItem
from frame_analysis.structs import Component
from .state import State


class TextureGrid(tk.Frame):
    def __init__(self, parent, get_ref, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)

        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.parent = parent
        self.grid_items = []
        self.get_ref = get_ref

        self.component_index = -1
        self.first_index     = -1

        self.frames: dict[int, dict[int, ScrollableFrame]] = {
            # component_index: {
            #   first_index: scrollable_frame
            # }
        }


    def load(self, components: list[Component], component_index, first_index):
        self.component_index = component_index
        self.first_index     = first_index
        frame_analysis = State.get_instance().get_var(State.K.FRAME_ANALYSIS)
        self.grid_refresh()
        
        for i, component in enumerate(components):
            if i not in self.frames: self.frames[i] = {}
            for first_index in component.object_indices:
                frame = ScrollableFrame(self, bg='#111')
                frame.grid(row=0, column=0, sticky='nsew')
                frame.lower()

                textures = frame_analysis.get_textures(component.tex_index_id[first_index])
                self.create_widgets(frame, textures, i, first_index)
                self.grid_widgets(frame)

                self.frames[i][first_index] = frame

        self.frames[self.component_index][self.first_index].bind("<Configure>", self._on_frame_configure)
        self.frames[self.component_index][self.first_index].tkraise()
    
    def set_active_grid(self, component_index, first_index):
        self.frames[self.component_index][self.first_index].lower()
        self.frames[self.component_index][self.first_index].unbind_all("<Configure>")
        self.component_index = component_index
        self.first_index     = first_index
        self.frames[self.component_index][self.first_index]._canvas.yview_moveto(0)
        self.frames[self.component_index][self.first_index].bind("<Configure>", self._on_frame_configure)
        self.frames[self.component_index][self.first_index].tkraise()

    def unload(self):
        for component_index in self.frames:
            for first_index in self.frames[component_index]:
                self.frames[component_index][first_index].destroy()
        self.frames = {}

        self.textures   = None
        self.grid_items = None

    def create_widgets(self, scrollable_frame, textures, component_index, first_index):
        for texture in textures:
            TextureGridItem(
                scrollable_frame.interior,
                texture, width=256, height=256,
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
        # 14  is the width of the scrollbar
        for column_count in range(1, 6):
            empty_space = self.winfo_width() - (272 * column_count) - 14
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
