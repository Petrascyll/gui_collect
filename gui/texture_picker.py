import tkinter as tk
from functools import partial
from pathlib import Path

from config.config import Config
from frame_analysis.structs import Component

from .texture_grid import TextureGrid
from .xtk.ScrollableFrame import ScrollableFrame
from .xtk.FlatImageButton import FlatImageButton
from .xtk.FlatButton import FlatButton

from texture_utilities.Texture import Texture
from texture_utilities.TextureManager import TextureManager


class TexturePicker(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs, bg='#111')
        self.parent = parent

        self.temp_dir = Config.get_instance().temp_data['temp_dir']

        self.configure_grid()
        self.create_widgets()

    def create_widgets(self):
        self.texture_bar = TextureBar(self)
        self.texture_bar.grid(row=0, column=0, sticky='nsew')

        self.middle_bar = tk.Frame(self, width=74, bg='#333')
        self.middle_bar.grid(row=0, column=1, padx=(1,0), sticky='nsew')
        
        # There's no built in anti aliasing AHHHHHHHHHHHHHHHHHH
        # TODO replace with images from photoshop later
        prev_canvas = tk.Canvas(self.middle_bar, bg=self.middle_bar['bg'], width=64, height=64, cursor='hand2', relief='flat', highlightthickness=0)
        self.prev_canvas = prev_canvas
        item_id = prev_canvas.create_polygon([8,56, 32,8, 56,56], fill='#444')
        prev_canvas.bind('<Button-1>', self.texture_bar.go_to_prev)
        prev_canvas.bind('<Enter>', lambda _: prev_canvas.itemconfigure(item_id, fill='#e8eaed'))
        prev_canvas.bind('<Leave>', lambda _: prev_canvas.itemconfigure(item_id, fill='#444'))
        prev_canvas.bind('<Enter>', lambda _: prev_canvas.config(bg='#A00'), add='+')
        prev_canvas.bind('<Leave>', lambda _: prev_canvas.config(bg='#333'), add='+')
        prev_canvas.pack()

        next_canvas = tk.Canvas(self.middle_bar, bg=self.middle_bar['bg'], width=64, height=64, cursor='hand2', relief='flat', highlightthickness=0)
        self.next_canvas = next_canvas
        item_id = next_canvas.create_polygon([8,8, 56,8, 32,56], fill='#444')
        next_canvas.bind('<Button-1>', self.texture_bar.go_to_next)
        next_canvas.bind('<Enter>', lambda _: next_canvas.itemconfigure(item_id, fill='#e8eaed'))
        next_canvas.bind('<Leave>', lambda _: next_canvas.itemconfigure(item_id, fill='#444'))
        next_canvas.bind('<Enter>', lambda _: next_canvas.config(bg='#A00'), add='+')
        next_canvas.bind('<Leave>', lambda _: next_canvas.config(bg='#333'), add='+')
        next_canvas.pack()


        self.texture_grid = TextureGrid(self, get_ref=self.texture_bar.get_component_part_frame)
        self.texture_grid.grid(row=0, column=2, sticky='nsew')

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

    def load(self, export_name, components: list[Component], callback):
        print('Texture picker loaded')

        self.export_name = export_name
        self.components  = components
        self.callback    = callback

        self.update_idletasks()
        self.texture_grid.load(component_index=0, first_index=0, components=self.components)
        self.texture_bar .load(component_index=0, first_index=0, components=self.components)

        self.bind_all('<s>', lambda _: self.do_fake_click(self.next_canvas))
        self.bind_all('<w>', lambda _: self.do_fake_click(self.prev_canvas))
    
    # TODO improve later
    def do_fake_click(self, widget, *args):
        widget.event_generate('<Button-1>')
        widget.event_generate('<Enter>')
        widget.after(100, lambda: widget.event_generate('<Leave>'))

    def set_active_texture_grid(self, component_index, first_index):
        self.texture_grid.set_active_grid(component_index, first_index)

    def done(self, collected_textures):
        self.callback(self.export_name, self.components, collected_textures)
        self.unload()

    def unload(self):
        self.lower()

        self.export_name = None
        self.components  = None
        self.callback    = None

        self.texture_grid.unload()
        self.texture_bar .unload()

        self.unbind_all('<s>')
        self.unbind_all('<w>')

class TextureBar(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent

        self.config(bg='#222')
        self.components: list[Component] = []
        self.component_textures: list[dict[int, ComponentPartFrame]] = []
        self.component_sequence = []
        # self.component_textures = [
        #     {
        #         first_index: ComponentPartFrame,
        #         first_index: ComponentPartFrame,
        #         ...
        #     },
        #     ...
        # ]

        self.component_index: int = 0
        self.first_index    : int = 0

        self.configure_grid()
        self.create_widgets()

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        self.component_summary = ScrollableFrame(self, bg='#222')
        self.component_summary.grid(sticky="nsew", row=0, column=0, columnspan=2)

        self.cancel = FlatButton(self, text='Cancel', bg='#444', hover_bg='#A00')
        self.cancel.bind('<Button-1>', lambda _: self.cancel_texture_collection())
        self.cancel.grid(sticky='nsew', row=1, column=0, padx=(0, 2), ipadx=56, ipady=16)

        # self.go_back = tk.Label(self, text='Back')
        # self.go_back.bind('<Button-1>', lambda _: self.go_to_prev())

        # self.go_next = tk.Label(self, text='Next')
        # self.go_next.bind('<Button-1>', lambda _: self.go_to_next())

        self.done = FlatButton(self, text='Done', bg='#444', hover_bg='#A00')
        self.done.bind('<Button-1>', lambda _: self.done_texture_collection())
        self.done.grid(sticky='nsew', row=1, column=1, padx=(0, 0), ipadx=56, ipady=16)

        # for i, w in enumerate((self.cancel, self.done)):
        #     w.config(fg='#e8eaed', bg='#444', font=('Arial', 16, 'bold'), cursor='hand2')
        #     w.bind('<Enter>', func=lambda e: e.widget.config(bg='#A00'))
        #     w.bind('<Leave>', func=lambda e: e.widget.config(bg='#444'))

        #     padx = (0, 2) if i != 3 else None
        #     w.grid(sticky='nsew', row=1, column=i, padx=padx, ipadx=32, ipady=16)



    def populate_widgets(self):
        for child in self.component_summary.interior.winfo_children():
            child.destroy()

        for i, component in enumerate(self.components):
            for j, first_index in enumerate(sorted(component.object_indices)):

                pady = (4, 4) if j == 0 else (0, 4)
                is_active = i == self.component_index and j == self.first_index

                # component_part_name = '{} - {}{}'.format(first_index, component.name, component.object_classification[j])
                component_part_name = '{}{}'.format(component.name, component.object_classification[j])
                component_part = ComponentPartFrame(self.component_summary.interior, active=is_active, header_text=component_part_name)
                component_part.header.bind('<Button-1>', partial(self.handle_jump, i, first_index))
                # component_part.header.bind('<Button-1>', lambda _: print('hi'))

                component_part.pack(side='top', pady=pady, fill='x', expand=True)

                self.component_textures[i][first_index] = component_part

    def load(self, component_index, first_index, components: list[Component]):
        self.components      = components
        self.component_index = component_index
        self.first_index     = first_index
        self.component_sequence = [
            component.object_indices
            for component in self.components
        ]
        
        self.component_textures = [{} for _ in range(len(self.components))]
        self.populate_widgets()

    def unload(self):
        for child in self.component_summary.interior.winfo_children():
            child.destroy()

        self.components      = None
        self.component_index = -1
        self.first_index     = -1
        self.component_sequence = None
        self.component_textures = None

        self.component_summary.destroy()
        self.component_summary = ScrollableFrame(self, bg='#222')
        self.component_summary.grid(sticky="nsew", row=0, column=0, columnspan=3)



    def get_component_part_frame(self, component_index: int, object_index: int):
        return self.component_textures[component_index][object_index]

    def handle_jump(self, component_index: int, first_index: int, *args):
        self.component_textures[self.component_index][self.first_index].set_inactive()
        
        self.component_index = component_index
        self.first_index     = first_index
        
        self.component_textures[self.component_index][self.first_index].set_active()
        self.parent.set_active_texture_grid(self.component_index, self.first_index)

    def go_to_next(self, *args):
        
        first_index     = self.first_index 
        component_index = self.component_index

        # Last Index of Component
        if first_index == self.component_sequence[component_index][-1]:

            # Last component => Loop back to the beginning
            if component_index == len(self.component_sequence) - 1:
                first_index     = 0
                component_index = 0
            
            # Not last component => go to first index of next component
            else:
                first_index = 0
                component_index += 1
        else:
            first_index_i = self.component_sequence[component_index].index(first_index)
            first_index   = self.component_sequence[component_index][first_index_i + 1]

        self.handle_jump(component_index, first_index)
    
    def go_to_prev(self, *args):
                
        first_index     = self.first_index 
        component_index = self.component_index

        # First Index of Component
        if first_index == 0:

            # First component => Loop back to the end
            if component_index == 0:
                first_index     = self.component_sequence[-1][-1]
                component_index = len(self.component_sequence) - 1
            
            # Not first component => go to last index of prev component
            else:
                component_index -= 1
                first_index = self.component_sequence[component_index][-1]
        else:
            first_index_i = self.component_sequence[component_index].index(first_index)
            first_index   = self.component_sequence[component_index][first_index_i - 1]

        self.handle_jump(component_index, first_index)

    def done_texture_collection(self):
        textures: list[dict[int, (Texture, str)]] = [
            {
                first_index: single_component_textures[first_index].get_textures()
                for first_index in single_component_textures
            } 
            for single_component_textures in self.component_textures
        ]

        self.parent.done(textures)

                # for slot in t.textures:
                # t.textures
            #     for a in self.component_textures[i][component_index].

    def cancel_texture_collection(self):
        self.parent.unload()
        self.parent.parent.extract_form.cancel_extraction()

class ComponentPartFrame(tk.Frame):
    def __init__(self, parent, header_text, active=False, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#222')
        self.parent = parent

        self.header_text = header_text
        self.active = active
        self.texture_frames: dict[int, ComponentPartTextureFrame] = {
            # slot: {
            #    file_path: texture.file_path
            #    add_to_json: False
            # }
        }
        self.create_widgets()
    
    def set_active(self):
        self.active = True
        self.conditional_config(self.header)
    
    def set_inactive(self):
        self.active = False
        self.conditional_config(self.header)

    def conditional_config(self, widget):
        fg       = '#e8eaed'
        bg       = '#444' if not self.active else '#A00'
        bg_hover = '#A00'

        widget.config(fg=fg, bg=bg)
        widget.bind('<Enter>', func=lambda e: e.widget.config(bg=bg_hover))
        widget.bind('<Leave>', func=lambda e: e.widget.config(bg=bg))


    def create_widgets(self):
        self.header = tk.Label(self, text=self.header_text, anchor='center', font=('Arial', 20, 'bold'), cursor='hand2')
        self.conditional_config(self.header)

        self.header.pack(fill='both', expand=True)

    def clear_list_widgets(self):
        for c in self.texture_frames.values():
            c.pack_forget()

    def pack_list_widgets(self):
        for _, c in sorted(self.texture_frames.items(), key=lambda item: item[0]):
            c.pack(fill='both', expand=True, pady=(2, 0))

    def add_texture(self, texture: Texture, texture_type: str):
        c = ComponentPartTextureFrame(self, texture, texture_type, handle_remove=self.handle_remove)
        
        self.clear_list_widgets()
        self.texture_frames[texture.slot] = c
        self.pack_list_widgets()

    def get_textures(self):
        sorted_textures = sorted(self.texture_frames.items(), key=lambda item: item[0])
        return [
            item[1].get_texture()
            for item in sorted_textures
        ]
    
    def handle_remove(self, slot, *args):
        self.texture_frames[slot].pack_forget()
        del self.texture_frames[slot]


class ComponentPartTextureFrame(tk.Frame):
    def __init__(self, parent, texture: Texture, texture_type: str, handle_remove, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#222')
        self.parent = parent

        self.handle_remove = handle_remove

        self.texture      = texture
        self.texture_type = texture_type
        self.sub_level    = 4 # TODO: future config option

        self.configure_grid()
        self.create_widgets()
        TextureManager.get_instance().get_image(self.texture, max_width=256, callback=self.set_thumbnail_image)

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self   .grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=0)

    def set_thumbnail_image(self, thumbnail_image: tk.PhotoImage, width, height):
        self.thumbnail_image = thumbnail_image.subsample(self.sub_level)
        self.thumbnail_canvas.delete('all')
        self.thumbnail_canvas.create_image(
            int(self.thumbnail_canvas['width'])  // 2 - width  // self.sub_level // 2,
            int(self.thumbnail_canvas['height']) // 2 - height // self.sub_level // 2,
            anchor='nw',
            image=self.thumbnail_image
        )

    def create_widgets(self):
        slot_label = tk.Label(self, text=self.texture.slot, font=('Arial', 16, 'bold'), bg='#333',  fg='#e8eaed')
        slot_label.grid(row=0, column=0, ipadx=4, padx=(0, 2), rowspan=2, sticky='nsew')

        self.thumbnail_canvas = tk.Canvas(self, width=256//self.sub_level, height=256//self.sub_level, bg='#111', highlightthickness=0)
        self.thumbnail_canvas.grid(row=0, column=1, padx=(0, 2), rowspan=2, sticky='nsew')

        texture_type_label = tk.Label(self, text=self.texture_type, font=('Arial', 20, 'bold'), bg='#333', fg='#e8eaed')
        texture_type_label.grid(row=0, column=2, sticky='nsew')
        
        hash_label = tk.Label(self, text=self.texture.hash, font=('Arial', 12, 'bold'), bg='#333', fg='#e8eaed')
        hash_label.grid(row=1, column=2, sticky='nsew')

        button_frame = tk.Frame(self, bg='#333')
        button_frame.grid(row=0, rowspan=2, column=3, padx=(2,0), sticky='nsew')

        img = tk.PhotoImage(file=Path('./resources/images/buttons/close.256.png').absolute()).subsample(8)
        remove_btn = FlatImageButton(button_frame, width=32, height=32, img_width=32, img_height=32, bg='#b92424', image=img)
        remove_btn.bind('<Button-1>', lambda _: self.handle_remove(self.texture.slot))
        remove_btn.pack(fill='both')

    def get_texture(self):
        return (self.texture, self.texture_type)
