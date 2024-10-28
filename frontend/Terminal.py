import re
import time
import tkinter as tk

from .state import State


# Doesn't support nested tags
tag_pattern = re.compile(r'<(.*?)>([\s\S]*?)<\/\1>')


class Terminal(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(*args, **kwargs)
        self.config(background='#080808')

        self._state = State.get_instance()
        self._state.register_terminal(self)

        self.create_widgets()

    def create_widgets(self):

        self.text_wdgt = tk.Text(
            self,
            wrap='word', height=12,
            insertbackground='#0FF', takefocus=False,
            insertofftime=500, insertontime=1000,
            bg=self['bg'], fg='#e8eaed',
            font=('Lucida Sans Typewriter', 10),
            relief='flat', highlightthickness=0
        )
        self.text_wdgt.pack(fill='both', expand=True, padx=16, pady=16)

        # TODO: Makes "read only" but breaks copy/paste
        # self.text_wdgt.bind("<Key>", lambda e: "break")

        self.text_wdgt.tag_config('TIMESTAMP', foreground='#999')
        self.text_wdgt.tag_config('PATH', foreground='#4FF')
        self.text_wdgt.tag_config('GAME', foreground='#4F4')
        self.text_wdgt.tag_config('LINK', foreground='#08F', font=('Lucida Sans Typewriter', 10, 'underline'))
        self.text_wdgt.tag_config('ERROR', foreground='#F44', font=('Lucida Sans Typewriter', 10, 'bold'))
        self.text_wdgt.tag_config('WARNING', foreground='#FB2', font=('Lucida Sans Typewriter', 10, 'bold'))

        # self.text_wdgt.tag_bind('PATH', '<Enter>', lambda e: e.widget.config(cursor='hand2'))
        # self.text_wdgt.tag_bind('PATH', '<Leave>', lambda e: e.widget.config(cursor='left_ptr'))

    def print(self, text='', end='\n', timestamp=True):

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

        self.text_wdgt.insert(tk.END, end)
        self.text_wdgt.see(tk.END)



