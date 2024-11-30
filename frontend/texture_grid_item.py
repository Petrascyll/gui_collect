import tkinter as tk

from functools import partial

from backend.utils.texture_utils.TextureManager import TextureManager
from backend.analysis.structs import Texture

from frontend.state import State

from .xtk.ScrollableFrame import ScrollableFrame
from .xtk.EntryWithPlaceholder import EntryWithPlaceholder

class TextureGridItem(tk.Canvas):
    def __init__(self, parent, texture: Texture, get_ref, *args, **kwargs):
        tk.Canvas.__init__(self, parent)
        self.config(*args, **kwargs)
        self.config(bg='#222', highlightthickness=0)
        self.parent = parent
        self.texture = texture
        self.get_ref = get_ref

        self._texture_picker = State.get_instance().get_texture_picker()

        self.create_canvas_widgets()

    def create_canvas_widgets(self):
        outer_image_bg_tag = self.create_rectangle(0, 0, 272, 272, fill='#333', outline='')
        inner_image_bg_tag = self.create_rectangle(8, 8, 264, 264, fill='#111', outline='')
        self.inner_image_bg_tag = inner_image_bg_tag

        self.invis_event_target = self.create_rectangle(0, 0, 272, 272, fill='', outline='')
        TextureManager.get_instance().get_image(self.texture, 256, callback=self.create_texture_image)
        self.texture.async_read_format(callback=self.create_format_label)

        self.tag_bind(self.invis_event_target, '<Enter>', add='+', func=lambda e: e.widget.itemconfig(outer_image_bg_tag, fill='#A00'))
        self.tag_bind(self.invis_event_target, '<Leave>', add='+', func=lambda e: e.widget.itemconfig(outer_image_bg_tag, fill='#333'))
        self.tag_bind(self.invis_event_target, '<Enter>', add='+', func=lambda e: e.widget.config(cursor='hand2'))
        self.tag_bind(self.invis_event_target, '<Leave>', add='+', func=lambda e: e.widget.config(cursor=''))
        self.tag_bind(self.invis_event_target, '<Button-1>', func=self.show_texture_type_picker)

        if not self.texture.contamination:
            substrs = ('ps-t', str(self.texture.slot), '=', self.texture.hash)
            substrs_color = ('#e8eaed', '#0FF', '#e8eaed', '#0FF')
        else:
            substrs = ('ps-t', str(self.texture.slot), '=', self.texture.contamination, '=', self.texture.hash)
            substrs_color = ('#e8eaed', '#0FF', '#e8eaed', '#FF0', '#e8eaed', '#0FF')

        create_colored_text(self, 272+4, substrs, substrs_color)
        self.create_text(int(self['width'])//2, 272+4+24, anchor='n', font=('Arial', 16, 'bold'), fill='#e8eaed', text=get_size_str(self.texture.get_size()))

    def create_format_label(self):
        def helper_create_format_label():
            format_text_tag    = self.create_text(13,  12, anchor='nw', font=('Arial', 10, 'bold'), fill='#e8eaed', text=self.texture._format)
            format_text_bg_tag = self.create_rectangle(get_padded_bbox(self.bbox(format_text_tag), 4), fill='#222', outline='')
            self.tag_lower(format_text_tag, self.invis_event_target)
            self.tag_lower(format_text_bg_tag, format_text_tag)

        self.update_idletasks()
        self.after_idle(helper_create_format_label)

    def create_texture_image(self, image, width, height):
        def load_image(image, width, height):
            res_text_tag  = self.create_text(13, 36, anchor='nw', font=('Arial', 10, 'bold'), fill='#e8eaed', text=f'{self.texture._width}x{self.texture._height}')
            res_text_bg_tag = self.create_rectangle(get_padded_bbox(self.bbox(res_text_tag), 4), fill='#222', outline='')
            self.tag_lower(res_text_tag, self.invis_event_target)
            self.tag_lower(res_text_bg_tag, res_text_tag)

            self.image_width  = width
            self.image_height = height
            self.img = self.create_image(
                (272 - self.image_width ) // 2,
                (272 - self.image_height) // 2,
                anchor='nw', image=image
            )
            self.tag_lower(self.img, self.inner_image_bg_tag)
            self.tag_raise(self.img, self.inner_image_bg_tag)

        self.update_idletasks()
        self.after_idle(load_image, image, width, height)

    def show_texture_type_picker(self, *args):
        self._texture_picker.unbind_keys()
        self.border_frame = tk.Frame(self, bg='#A00')
        self.border_frame.place(x=0, y=0, width=272, height=272, anchor='nw')

        def handle_leave(e):
            self._texture_picker.bind_keys()
            self.border_frame.destroy()
            
        self.texture_type_frame = TextureTypeFrame(self.border_frame, self.handle_texture_type_click)
        self.texture_type_frame.pack(fill='both', expand=True, padx=8, pady=8)
        self.texture_type_frame.bind('<Leave>', handle_leave)

        self.border_frame.tkraise()

    def handle_texture_type_click(self, texture_type: str, *args):
        self._texture_picker.bind_keys()
        self.get_ref().add_texture(self.texture, texture_type)
        self.border_frame.destroy()


TYPE_STYLE = {
    'bg':'#222', 'fg':'#e8eaed',
    'font':('Arial', 18, 'bold'),
    'justify': 'center',
    'cursor': 'hand2',
}

class TextureTypeFrame(ScrollableFrame):
    def __init__(self, parent, handle_texture_type_click, *args, **kwargs):
        tk.Frame.__init__(self, parent, bg='#111', width=256, height=256)
        self.config(*args, **kwargs)
        self.parent = parent

        self.handle_texture_type_click = handle_texture_type_click
        self.create_widgets()

    def create_widgets(self):
        custom_type = EntryWithPlaceholder(self, placeholder='Custom', **TYPE_STYLE)
        custom_type.pack(side='bottom', fill='x')

        def submit_custom_type(event):
            text = event.widget.get()
            if not text: return
            if not text.replace('_', '').isalnum(): return
            self.handle_texture_type_click(text)

        custom_type.bind('<Enter>', lambda e: e.widget.config(bg='#A00'))
        custom_type.bind('<Leave>', lambda e: e.widget.config(bg='#222'))
        custom_type.bind('<Return>',   submit_custom_type)
        custom_type.bind('<Button-1>', submit_custom_type)
        custom_type.focus()

        tk.Label(
            self, font=('Arial', '10', 'bold'), fg='#444', bg=self['bg'], anchor='center',
            text='Either pick one of the above\noptions or type and hit Enter',
        ).pack(side='bottom', fill='x')

        for texture_type in ['Diffuse', 'NormalMap', 'MaterialMap', 'LightMap', 'StockingMap']:
            texture_type_label = tk.Label(self, text=texture_type, **TYPE_STYLE)
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
