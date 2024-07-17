import tkinter as tk

from .xtk.ScrollableFrame import ScrollableFrame
from .texture_grid_item import TextureGridItem

import time
    

# class TextureGrid(ScrollableFrame):
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

    def load(self, component_index, first_index, temp_texture_file_paths, skipped_texture_file_paths, map_texture_file_paths):
        self.first_index     = first_index
        self.component_index = component_index

        self.temp_texture_file_paths    = temp_texture_file_paths
        self.skipped_texture_file_paths = skipped_texture_file_paths
        self.map_texture_file_paths     = map_texture_file_paths

        temp_frame = ScrollableFrame(self, bg='#111')
        temp_frame.lower()
        temp_frame.grid(row=0, column=0, sticky='nsew')

        self.create_widgets(temp_frame)
        self  .grid_widgets()

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

        self.temp_texture_file_paths = None
        self.skipped_texture_file_paths = None
        self.map_texture_file_paths = None


    def create_widgets(self, scrollable_frame):
        self.grid_items = []
        component = self.parent.components[self.component_index]
        for texture_filepath in component.texture_data[self.first_index]:

            if texture_filepath.name in self.skipped_texture_file_paths:
                continue
            if texture_filepath.name in self.map_texture_file_paths:
                original_texture_name = self.map_texture_file_paths[texture_filepath.name]
                saved_texture = self.temp_texture_file_paths[original_texture_name]
            elif texture_filepath.name in self.temp_texture_file_paths:
                saved_texture = self.temp_texture_file_paths[texture_filepath.name]
            else:
                raise Exception('Failed to find converted ' + texture_filepath.name)

            texture_grid_item = TextureGridItem(
                scrollable_frame.interior,
                saved_texture,
                width=256, height=256,
                get_ref=lambda: self.get_ref(self.component_index, self.first_index)
            )
            self.grid_items.append(texture_grid_item)

    def grid_widgets(self):
        for i, item in enumerate(self.grid_items):
            item.grid(sticky="nsew", row=i//3, column=i%3, padx=4, pady=(4, 0))
