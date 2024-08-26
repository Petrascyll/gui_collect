import tkinter as tk

from functools import partial

from texture_utilities.TextureManager import TextureManager
from texture_utilities.Texture import Texture

from .xtk.ScrollableFrame import ScrollableFrame


class LightTextureGridItem(tk.Canvas):
    def __init__(self, parent, texture: Texture, get_ref, *args, **kwargs):
        tk.Canvas.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#222', highlightthickness=0)
        self.parent = parent
        self.texture = texture
        self.get_ref = get_ref

        self.create_canvas_widgets()

    def create_canvas_widgets(self):
        outer_image_bg_tag = self.create_rectangle(0, 0, 272, 272, fill='#333', outline='')
        inner_image_bg_tag = self.create_rectangle(8, 8, 264, 264, fill='#111', outline='')
        self.inner_image_bg_tag = inner_image_bg_tag
        TextureManager.get_instance().get_image(self.texture, 256, self.callback)

        # I'm 1px off horizontally for some reason, so using x=13 instead of x=12
        text_color = '#e8eaed'
        font = ('Arial', 10, 'bold')
        format_text_tag    = self.create_text(13,  12, anchor='nw', font=font, fill=text_color, text=f'{self.texture.format}')
        format_text_bg_tag = self.create_rectangle(get_padded_bbox(self.bbox(format_text_tag), 4), fill='#222', outline='')
        self.tag_lower(format_text_bg_tag, format_text_tag)

        res_text_tag       = self.create_text(13, 36, anchor='nw', font=font, fill=text_color, text=f'{self.texture.width}x{self.texture.height}')
        res_text_bg_tag    = self.create_rectangle(get_padded_bbox(self.bbox(res_text_tag), 4), fill='#222', outline='')
        self.tag_lower(res_text_bg_tag, res_text_tag)

        invis_event_target = self.create_rectangle(0, 0, 272, 272, fill='', outline='')
        self.tag_bind(invis_event_target, '<Enter>', add='+', func=lambda e: e.widget.itemconfig(outer_image_bg_tag, fill='#A00'))
        self.tag_bind(invis_event_target, '<Leave>', add='+', func=lambda e: e.widget.itemconfig(outer_image_bg_tag, fill='#333'))
        self.tag_bind(invis_event_target, '<Enter>', add='+', func=lambda e: e.widget.config(cursor='hand2'))
        self.tag_bind(invis_event_target, '<Leave>', add='+', func=lambda e: e.widget.config(cursor=''))
        self.tag_bind(invis_event_target, '<Button-1>', func=self.show_texture_type_picker)

        if not self.texture.contamination:
            substrs = ('ps-t', str(self.texture.slot), '=', self.texture.hash)
            substrs_color = ('#e8eaed', '#0FF', '#e8eaed', '#0FF')
        else:
            substrs = ('ps-t', str(self.texture.slot), '=', self.texture.contamination, '=', self.texture.hash)
            substrs_color = ('#e8eaed', '#0FF', '#e8eaed', '#FF0', '#e8eaed', '#0FF')

        create_colored_text(self, 272+4, substrs, substrs_color)
        self.create_text(int(self['width'])//2, 272+4+24, anchor='n', font=('Arial', 16, 'bold'), fill=text_color, text=get_size_str(self.texture.get_size()))

    def callback(self, image, width, height):
        self.update_idletasks()
        self.after_idle(self.load_image, image, width, height)

    def load_image(self, image, width, height):
        self.image_width  = width
        self.image_height = height
        img = self.create_image(
            (272 - self.image_width ) // 2,
            (272 - self.image_height) // 2,
            anchor='nw', image=image
        )
        self.tag_lower(img, self.inner_image_bg_tag)
        self.tag_raise(img, self.inner_image_bg_tag)

    def show_texture_type_picker(self, *args):
        self.border_frame = tk.Frame(self, bg='#A00')
        self.border_frame.place(x=0, y=0, width=272, height=272, anchor='nw')

        self.texture_type_frame = TextureTypeFrame(self.border_frame, self.handle_texture_type_click)
        self.texture_type_frame.pack(fill='both', expand=True, padx=8, pady=8)
        self.texture_type_frame.bind('<Leave>', lambda _: self.border_frame.destroy())

        self.border_frame.tkraise()

    def handle_texture_type_click(self, texture_type: str, *args):
        self.get_ref().add_texture(self.texture, texture_type)
        self.border_frame.destroy()


class TextureTypeFrame(ScrollableFrame):
    def __init__(self, parent, handle_texture_type_click, *args, **kwargs):
        ScrollableFrame.__init__(self, parent, scrollable_parent=parent.master.parent.parent, bg='#111', width=256-16, height=256-16)
        self.config(*args, **kwargs)
        self.parent = parent

        self.handle_texture_type_click = handle_texture_type_click
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


def get_size_str(size: int):
    if size < 1_000:
        size_unit = 'B'
    elif size < 1_000_000:
        size = size / 1024
        size_unit = 'KiB'
    else:
        size = size / (1024*1024)
        size_unit = 'MiB'
    return '{:.3f} {}'.format(size, size_unit)


def get_padded_bbox(bbox: list[int], padding: int):
    return [bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding]


# TODO: move to some other file
from .state import State
from tkinter import font as tkfont

def create_colored_text(canvas: tk.Canvas, y: int, substrs: tuple[str], substrs_color: tuple[str]):
    state = State.get_instance()
    if not state.has_var(State.K.F_ARIAL16):
        F_Arial16 = tkfont.Font(family='Arial', size=16, weight='bold')
        state.set_var(State.K.F_ARIAL16, F_Arial16)
    else:
        F_Arial16 = state.get_var(State.K.F_ARIAL16)

    total_width   = 0
    substrs_width = []
    for substr in substrs:
        width = F_Arial16.measure(substr)        
        total_width += width
        substrs_width.append(width)

    offset = 0
    start  = ( int(canvas['width']) - total_width ) // 2
    for substr, color, width in zip(substrs, substrs_color, substrs_width):
        x = start + offset
        canvas.create_text(x, y, anchor='nw', text=substr, font=F_Arial16, fill=color)
        offset += width
