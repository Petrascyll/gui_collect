import tkinter as tk

from functools import partial

from frame_analysis.texture_utilities import SavedTexture
from .xtk.ScrollableFrame import ScrollableFrame

class TextureGridItem(tk.Frame):
    def __init__(self, parent, saved_texture: SavedTexture, get_ref, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs, bg='#222')
        self.parent = parent

        self.saved_texture = saved_texture
        self.get_ref = get_ref
        self.configure_grid()
        self.create_widgets()

    def configure_grid(self):
        self   .grid_rowconfigure(0, weight=1)
        self   .grid_rowconfigure(1, weight=0)
        self   .grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        texture_image_frame = TextureImageFrame(self, saved_texture=self.saved_texture, width=256, height=256)
        texture_image_frame.image_canvas.bind('<Button-1>', self.show_texture_type_picker)
        # texture_image_frame.image_canvas.bind('<Button-1>', lambda _: self.get_ref().add_texture(self.saved_texture, 'MaterialMap'))
        texture_image_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', ipadx=8, ipady=8)

        shared = {
            'font': ('Arial', 16, 'bold'),
            'bg': '#222', 'fg': '#e8eaed',
            'anchor': 'center',
        }
        texture_hash = tk.Label(self, text=self.saved_texture.hash, **shared)
        texture_hash.grid(row=1, column=1, stick='nsew')
        
        texture_slot = tk.Label(self, text=self.saved_texture.slot, **shared)
        texture_slot.grid(row=1, column=0)

        texture_size = tk.Label(self, text=self.saved_texture.size, **shared)
        texture_size.grid(row=2, column=1)

    def show_texture_type_picker(self, *args):
        self.border_frame = tk.Frame(self, bg='#A00')
        self.border_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', ipadx=8, ipady=8)

        self.texture_type_frame = TextureTypeFrame(self.border_frame, self.handle_texture_type_click)
        self.texture_type_frame.pack(fill='both', expand=True, padx=8, pady=8)
        self.texture_type_frame.bind('<Leave>', lambda _: self.border_frame.destroy())
        
        self.border_frame.tkraise()
        self.texture_type_frame.tkraise()

    def handle_texture_type_click(self, texture_type: str, *args):
        self.get_ref().add_texture(self.saved_texture, texture_type)
        # self.texture_type_frame.lower()
        # self.border_frame.lower()
        self.border_frame.destroy()

class TextureImageFrame(tk.Frame):
    def __init__(self, parent, saved_texture: SavedTexture, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent

        self.config(cursor='hand2', bg='#333')

        self.image        = tk.PhotoImage(file=str(saved_texture.path))
        self.image_width  = saved_texture._width
        self.image_height = saved_texture._height
        self.max_side     = 256

        self.texture_width  = saved_texture.width
        self.texture_height = saved_texture.height
        self.texture_format = saved_texture.type

        self.create_widgets()
        self.bind('<Enter>', lambda e: e.widget.config(bg='#A00'))
        self.bind('<Leave>', lambda e: e.widget.config(bg='#333'))

    def create_widgets(self):
        self.image_canvas = tk.Canvas(self, width=self.max_side, height=self.max_side, bg='#111', highlightthickness=0)
        self.image_canvas.create_image(
            int(self['width'])  // 2 - self.image_width  // 2,
            int(self['height']) // 2 - self.image_height // 2,
            anchor='nw',
            image=self.image
        )
        self.image_canvas.place(x=8, y=8)

        font = ('Arial', 10, 'bold')
        text = f'{self.texture_format}'
        texture_format_label = tk.Label(self, text=text, font=font, padx=4, pady=4, bg='#222', fg='#e8eaed')
        texture_format_label.place(x=8, y=8)

        text = f'{self.texture_width}x{self.texture_height}'
        texture_resolution_label = tk.Label(self, text=text, font=font, padx=4, pady=4, bg='#222', fg='#e8eaed')
        texture_resolution_label.place(x=8, y=35)


class TextureTypeFrame(ScrollableFrame):
    def __init__(self, parent, handle_texture_type_click, *args, **kwargs):
        ScrollableFrame.__init__(self, parent, scrollable_parent=parent.master.parent.parent, bg='#111', width=256-16, height=256-16)
        self.config(*args, **kwargs)
        self.parent = parent

        self.handle_texture_type_click = handle_texture_type_click
        # self.config()

        self.create_widgets()

    def create_widgets(self):

        for texture_type in ['Diffuse', 'NormalMap', 'MaterialMap', 'LightMap', 'StockingMap', 'ShadowRamp', 'Shadow', 'ExpressionMap']:
            texture_type_label = tk.Label(self.interior, text=texture_type, bg='#222', fg='#e8eaed', font=('Arial', 18, 'bold'), cursor='hand2')
            texture_type_label.pack(side='top', fill='x', pady=(0, 1))
            
            texture_type_label.bind('<Enter>', lambda e: e.widget.config(bg='#A00'))
            texture_type_label.bind('<Leave>', lambda e: e.widget.config(bg='#222'))
            texture_type_label.bind(
                '<Button-1>',
                partial(self.handle_texture_type_click, texture_type)
            )

    def add_texture(self):
        self.parent.parent