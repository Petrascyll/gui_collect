import re
import time
import tkinter as tk
from pathlib import Path

from .state import State
from .xtk.FlatImageButton import FlatImageButton

# Doesn't support nested tags
tag_pattern = re.compile(r'<(.*?)>([\s\S]*?)<\/\1>')


class Terminal(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(*args, **kwargs)
        self.config(background='#080808')

        self.chevron_down_img = tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'chevron.down.16.png'))
        self.chevron_up_img   = tk.PhotoImage(file=Path('resources', 'images', 'buttons', 'chevron.up.16.png'))

        self._state = State.get_instance()
        self._state.register_terminal(self)

        self.terminal_visible = True
        self.create_widgets()

    def create_widgets(self):
        self   .grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.text_wdgt = tk.Text(
            self,
            wrap='word', height=12,
            insertbackground='#0FF', takefocus=False,
            insertofftime=500, insertontime=1000,
            # bg=self['bg'],
            bg='#080808',
            fg='#e8eaed',
            font=('Lucida Sans Typewriter', 10),
            relief='flat', highlightthickness=0
        )
        self.text_wdgt.grid(row=0, column=0, sticky='nsew', padx=16)

        # TODO: Makes "read only" but breaks copy/paste
        # self.text_wdgt.bind("<Key>", lambda e: "break")

        self.text_wdgt.tag_config('TIMESTAMP', foreground='#999')
        self.text_wdgt.tag_config('PATH', foreground='#4FF')
        self.text_wdgt.tag_config('GAME', foreground='#4F4')
        self.text_wdgt.tag_config('LINK', foreground='#08F', font=('Lucida Sans Typewriter', 10, 'underline'))
        self.text_wdgt.tag_config('ERROR', foreground='#F44', font=('Lucida Sans Typewriter', 10, 'bold'))
        self.text_wdgt.tag_config('WARNING', foreground='#FB2', font=('Lucida Sans Typewriter', 10, 'bold'))

        self.btn = FlatImageButton(self, image=self.chevron_down_img, bg=self['bg'], img_width=16, img_height=16, width=34, height=34)
        self.btn.place(relx=1.0, x=0, y=0, anchor='ne')
        self.btn.bind('<Button-1>', self.toggle_terminal_visible)


    def toggle_terminal_visible(self, event):
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self.btn.set_image(self.chevron_down_img, img_width=16, img_height=16, width=32, height=32)
            self.text_wdgt.config(height=12)
        else:
            self.btn.set_image(self.chevron_up_img, img_width=16, img_height=16, width=32, height=32)
            self.text_wdgt.config(height=2)
        self.update_idletasks()
        self.text_wdgt.see(tk.END)


    def print(self, text='', timestamp=True):
        self.text_wdgt.insert(tk.END, '\n')

        if timestamp and text != '':
            struct_time = time.localtime(time.time())
            time_str = f'[{struct_time.tm_hour:02}:{struct_time.tm_min:02}:{struct_time.tm_sec:02}] '
            self.text_wdgt.insert(tk.END, time_str, 'TIMESTAMP')
        
        if not timestamp:
            self.text_wdgt.insert(tk.END, ' ' * 11)

        insert_start = 0
        for tag_match in tag_pattern.finditer(text):
            match_start, match_end = tag_match.span()
            if insert_start != match_start:
                self.text_wdgt.insert(tk.END, text[insert_start:match_start])

            tag     = tag_match.group(1)
            content = tag_match.group(2)
            self.text_wdgt.insert(tk.END, content, tag)

            insert_start = match_end

        if insert_start != len(text):
            self.text_wdgt.insert(tk.END, text[insert_start:])

        self.text_wdgt.see(tk.END)



