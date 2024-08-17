import tkinter as tk

from .xtk.ScrollableFrame import ScrollableFrame
from .texture_grid_item import TextureGridItem


class TextureGrid(tk.Frame):
    def __init__(self, parent, get_ref, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)

        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.active_frame = ScrollableFrame(self, bg='#111')
        self.active_frame.grid(row=0, column=0, sticky='nsew')

        self.parent = parent
        self.grid_items = []
        self.get_ref = get_ref

        self.component_index = -1
        self.first_index     = -1

    def load(self, component_index, first_index, component):
        self.first_index     = first_index
        self.component_index = component_index

        self.textures = component.texture_data[first_index]

        temp_frame = ScrollableFrame(self, bg='#111')
        temp_frame.lower()
        temp_frame.grid(row=0, column=0, sticky='nsew')

        self.create_widgets(temp_frame)
        self.grid_widgets()

        temp_frame.bind("<Configure>", self._on_frame_configure)
        temp_frame.update_idletasks()
        temp_frame.after_idle(self.post_load, temp_frame)
    
    def post_load(self, temp_frame):
        self.active_frame.lower()
        self.active_frame.destroy()

        self.active_frame = temp_frame
        self.active_frame.tkraise()

    def unload(self):
        self.active_frame.lower()
        self.active_frame.destroy()

        self.active_frame = ScrollableFrame(self, bg='#111')
        self.active_frame.grid(row=0, column=0, sticky='nsew')
        self.active_frame.tkraise()

        self.textures  = None


    def create_widgets(self, scrollable_frame):
        self.grid_items = []
        for texture in self.textures:

            texture_grid_item = TextureGridItem(
                scrollable_frame.interior,
                texture, width=256, height=256,
                get_ref=lambda: self.get_ref(self.component_index, self.first_index)
            )
            self.grid_items.append(texture_grid_item)

    def grid_widgets(self):

        padding_style = 'centered'
        pady = (4, 0)
        min_padx = 4

        # 272 is the width of a single grid item
        # 14  is the width of the scrollbar
        for column_count in range(1, 6):
            empty_space = self.winfo_width() - (272 * column_count) - 14
            min_empty_space = ((column_count - 1) * min_padx) + min_padx*2
            if min_empty_space <= empty_space <= 272 + min_empty_space:
                break
        else:
            empty_space = min_empty_space

        first = 0
        last = column_count - 1

        if padding_style == 'even':
            # Even x padding on all items
            # ex: [----X----X----X----]
            padding = empty_space // (column_count + 1)
            for i, item in enumerate(self.grid_items):
                row    = i // column_count
                column = i %  column_count

                if   column == first: padx = (padding   , padding//2)
                elif column == last : padx = (padding//2, padding)
                else: padx = (padding//2, padding//2)
                item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=pady)

        elif padding_style == 'centered':
            # Centered middle items
            # ex: [------X--X--X------]
            padding = (empty_space - ((column_count - 1) * min_padx))//2
            for i, item in enumerate(self.grid_items):
                row    = i // column_count
                column = i %  column_count
                if   column == first: padx = (padding    , min_padx//2)
                elif column == last : padx = (min_padx//2, padding)
                else: padx = (min_padx//2, min_padx//2)
                item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=pady)

        else:
            raise Exception('Coding error')


    def _on_frame_configure(self, e):
        # print(e.widget.winfo_width(), e.widget.winfo_reqwidth())
        self.grid_widgets()
