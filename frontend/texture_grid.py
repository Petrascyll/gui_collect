import tkinter as tk
from functools import partial
from pathlib import Path

from .xtk.ScrollableFrame   import ScrollableFrame
from .xtk.FlatImageButton   import FlatImageButton
from .xtk.ConditionalFilter import ConditionalFilter
from .xtk.TextFilter        import TextFilter

from .texture_grid_item import TextureGridItem

from backend.analysis.structs import Texture, Component


class TextureGrid(tk.Frame):
    def __init__(self, parent, get_ref, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs, bg='#111')

        self   .grid_rowconfigure(0, weight=0)
        self   .grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        self.parent = parent
        self.get_ref = get_ref

        self.component_index = -1
        self.first_index     = -1

        self.create_id_picker()
        self.create_header()
        self.id_picker.grid(row=0, column=0, rowspan=2, padx=(1,0), sticky='nsew')
        self.header   .grid(row=0, column=1, sticky='nsew', padx=4, pady=4)

        self.frames: dict[int, dict[int, dict[str, ScrollableFrame]]] = {
            # component_index: {
            #     first_index: {
            #         id: scrollable_frame
            #     },
            #  },
        }

    def create_id_picker(self):
        self.id_picker = tk.Frame(self, width=74, bg='#333')
        self.id_picker.pack_propagate(False)

    def create_header(self):
        self.header = tk.Frame(self, bg='#111')
        self.header   .grid_rowconfigure(0, weight=1)
        self.header   .grid_rowconfigure(1, weight=1)
        self.header.grid_columnconfigure(0, weight=1)

        self.vs_label = tk.Label(self.header, text='VS Hash:', fg='#e8eaed', bg='#111', font=('Arial', 10, 'bold'), anchor='w')
        self.ps_label = tk.Label(self.header, text='PS Hash:', fg='#e8eaed', bg='#111', font=('Arial', 10, 'bold'), anchor='w')
        self.vs_label.grid(row=0, column=0, sticky='nsw', padx=(0, 32))
        self.ps_label.grid(row=1, column=0, sticky='nsw', padx=(0, 32))

        size_values = (16*1024, 256*1024, 1024*1024, 4096*1024)
        size_value_labels = ('16KiB', '256KiB', '1MiB', '4MiB')

        self.ext_filter    = TextFilter(self.header, callback=self.regrid_active_widgets, active=True, values=('', 'dds', 'jpg'), value_labels=('', '.dds', '.jpg'), initial_value_index=1)
        self.width_filter  = ConditionalFilter(self.header, callback=self.regrid_active_widgets, active=False, label_text='W', values=(256, 512, 1024, 2048, 4096), initial_value_index=2)
        self.height_filter = ConditionalFilter(self.header, callback=self.regrid_active_widgets, active=False, label_text='H', values=(256, 512, 1024, 2048, 4096), initial_value_index=2)
        self.size_filter   = ConditionalFilter(self.header, callback=self.regrid_active_widgets, active=False, label_text='S', values=size_values, value_labels=size_value_labels, initial_value_index=2)
        self.pow_2_filter  = FlatImageButton(
            self.header,
            image=tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'pow_2.inverted.44.png')),
            dual_state=True, key='pow_2', value=True,
            bg='#333', active_bg='#E00',
            img_width=100, img_height=44, width=100, height=44,
        )
        self.pow_2_filter.bind('<Button-1>', add='+', func=lambda _: self.regrid_active_widgets())

        self  .size_filter.grid(row=0, rowspan=2, column=1, padx=8, sticky='nse')
        self .width_filter.grid(row=0, rowspan=2, column=2, padx=8, sticky='nse')
        self.height_filter.grid(row=0, rowspan=2, column=3, padx=8, sticky='nse')
        self .pow_2_filter.grid(row=0, rowspan=2, column=4, padx=8, sticky='nse')
        self   .ext_filter.grid(row=0, rowspan=2, column=5, padx=8, sticky='nse')


    def load(self, components: list[Component], component_index: int, first_index: int):
        self.components      = components
        self.component_index = component_index
        self.first_index     = first_index
        self.active_id       = components[component_index].tex_index_id[first_index]

        self.grid_refresh()
        self.vs_label.config(text=f'VS Hash: {self.components[component_index].draw_data[first_index][self.active_id].vs_hash}')
        self.ps_label.config(text=f'PS Hash: {self.components[component_index].draw_data[first_index][self.active_id].ps_hash}')
        
        for i, component in enumerate(components):
            if i not in self.frames: self.frames[i] = {}
            for first_index in component.object_indices:
                frame = ScrollableFrame(self, bg='#111')
                frame.grid(row=1, column=1, sticky='nsew')
                frame.lower()

                initial_id = component.tex_index_id[first_index]
                textures = component.draw_data[first_index][initial_id].textures
                
                self.create_widgets(frame, textures, i, first_index)
                frame.filter_mask = self.get_filter_mask(textures)
                self.grid_widgets(frame)

                self.frames[i][first_index] = {
                    id: None
                    for id in component.draw_data[first_index]
                }
                self.frames[i][first_index][initial_id] = frame
                self.frames[i][first_index]['active_id'] = initial_id

        self.frames[self.component_index][self.first_index][self.active_id].bind("<Configure>", self._on_frame_configure)
        self.frames[self.component_index][self.first_index][self.active_id].tkraise()
        self.refresh_id_picker(self.component_index, self.first_index)

    def regrid_active_widgets(self):
        active_frame = self.frames[self.component_index][self.first_index][self.active_id]
        textures = self.components[self.component_index].draw_data[self.first_index][self.active_id].textures

        filter_mask = self.get_filter_mask(textures)
        for a, b in zip(filter_mask, active_frame.filter_mask):
            if a != b:
                active_frame.filter_mask = filter_mask
                for child in active_frame.interior.winfo_children():
                    child.grid_forget()
                self.grid_widgets(active_frame)
                self.update_idletasks()
                break

    def get_filter_mask(self, textures: list[Texture]):
        filter_mask = []
        for texture in textures:
            texture.async_read_width_height(blocking=True)
            is_visible = (
                True
                and (not self.pow_2_filter.get() or texture.is_power_of_two())
                and self. width_filter.get(texture._width)
                and self.height_filter.get(texture._height)
                and self.  size_filter.get(texture._size)
                and self   .ext_filter.get(texture.extension)
            )
            filter_mask.append(is_visible)

        return filter_mask

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

    def set_active_grid_id(self, component_index: int, first_index: int, id: str, event):
        if self.frames[component_index][first_index][id] is not None:
            self.frames[component_index][first_index]['active_id'] = id
            self.set_active_grid(component_index, first_index)
            return
        
        frame = ScrollableFrame(self, bg='#111')
        frame.grid(row=1, column=1, sticky='nsew')
        frame.lower()
    
        textures = self.components[component_index].draw_data[first_index][id].textures
        self.create_widgets(frame, textures, component_index, first_index)
        frame.filter_mask = self.get_filter_mask(textures)

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

        self.vs_label.config(text=f'VS Hash: {self.components[self.component_index].draw_data[self.first_index][self.active_id].vs_hash}')
        self.ps_label.config(text=f'PS Hash: {self.components[self.component_index].draw_data[self.first_index][self.active_id].ps_hash}')

        self.regrid_active_widgets()
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
        self.components = None

    def create_widgets(self, scrollable_frame, textures, component_index, first_index):
        for texture in textures:
            TextureGridItem(
                scrollable_frame.interior,
                texture, width=272, height=328,
                get_ref=lambda: self.get_ref(component_index, first_index)
            )

    def grid_widgets(self, scrollable_frame: ScrollableFrame):
        grid_i = 0
        for i, item in enumerate(scrollable_frame.interior.winfo_children()):
            if scrollable_frame.filter_mask and not scrollable_frame.filter_mask[i]:
                continue
            self.grid_widget(grid_i, item)
            grid_i += 1

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
            if row == first: pady = 0
            else: pady = self.pady
            item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=pady)

        elif self.padding_style == 'centered':
            # Centered middle items
            # ex: [------X--X--X------]
            padding = (self.empty_space - ((self.column_count - 1) * self.min_padx))//2
            if   column == first: padx = (padding    , self.min_padx//2)
            elif column == last : padx = (self.min_padx//2, padding)
            else: padx = (self.min_padx//2, self.min_padx//2)
            if row == first: pady = 0
            else: pady = self.pady
            item.grid(sticky="nsew", row=row, column=column, padx=padx, pady=pady)

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
