import tkinter as tk

from frontend.style import brighter


class ConditionalFilter(tk.Frame):
    def __init__(
            self, parent, *args,
            callback: callable, active:bool, label_text:str,
            values:tuple[str], value_labels:tuple[str]=None, initial_value_index:int,
            **kwargs
        ):
        tk.Frame.__init__(self, parent, bg='#111')
        self.config(*args, **kwargs)

        self.callback = callback
        self.active = active
        self.active_fg = '#E00'
        self.inactive_fg = '#333'

        self.create_lhs(values, value_labels, initial_value_index)
        self.create_operator()
        self.create_rhs(label_text)

        self.lhs.pack(side='left')
        self.operator.pack(side='left', pady=(0,2))
        self.label.pack(side='left')

    def get(self, rhs_value: int):
        if not self.active: return True
        if self.operator.value_index == 0:
            return self.lhs.value <= rhs_value
        else:
            return self.lhs.value > rhs_value

    def create_rhs(self, text):
        self.label = tk.Label(
            self, bg=self['bg'], cursor='hand2',
            text=text, font=('Arial', 16, 'bold'),
        )

        def refresh():
            if self.active:
                self.label.config(fg=self.active_fg)
            else:
                self.label.config(fg=self.inactive_fg)

        def handle_click(event):
            self.active = not self.active
            self.lhs.refresh()
            self.label.refresh()
            self.operator.refresh()
            self.callback()

        def handle_enter(event):
            event.widget.config(fg=brighter(event.widget['fg']))
        def handle_leave(event):
            event.widget.config(fg=self.active_fg if self.active else self.inactive_fg)

        self.label.bind('<Button-1>', handle_click)
        self.label.bind('<Enter>', handle_enter)
        self.label.bind('<Leave>', handle_leave)
        self.label.refresh = refresh
        self.label.refresh()

    def create_operator(self):
        values = ('≤','>')
        self.operator = tk.Label(
            self, bg=self['bg'],
            font=('Consolas', 22, 'bold'),
        )
        self.operator.value_index = 0
        self.operator.config(text=values[self.operator.value_index])

        def refresh():
            if self.active:
                self.operator.config(cursor='hand2', fg=self.active_fg)
            else:
                self.operator.config(cursor='left_ptr', fg=self.inactive_fg)

        def handle_click(event):
            if not self.active: return
            operator = event.widget
            operator.value_index = (operator.value_index + 1) % len(values)
            operator.config(text=values[operator.value_index])
            self.callback()

        def handle_enter(event):
            if not self.active: return
            operator = event.widget
            operator.config(fg=brighter(operator['fg']))

        def handle_leave(event):
            if not self.active: return
            operator = event.widget
            operator.config(fg=self.active_fg if self.active else self.inactive_fg)

        self.operator.bind('<Button-1>', handle_click)
        self.operator.bind('<Enter>', handle_enter)
        self.operator.bind('<Leave>', handle_leave)
        self.operator.refresh = refresh
        self.operator.refresh()

    def create_lhs(self, values: tuple[int], value_labels: tuple[str]=None, initial_value_index: int=0):
        if value_labels is None:
            value_labels = values

        self.lhs = tk.Label(
            self, bg=self['bg'],
            font=('Arial', 16, 'bold'), cursor='hand2',
            width=max([len(f'{v}') for v in value_labels]), anchor='e'
        )
        self.lhs.value_index = initial_value_index
        self.lhs.value = values[self.lhs.value_index]
        self.lhs.config(text=value_labels[self.lhs.value_index])

        def refresh():
            if self.active:
                self.lhs.config(cursor='hand2', fg=self.active_fg)
            else:
                self.lhs.config(cursor='left_ptr', fg=self.inactive_fg)

        def handle_click(event):
            if not self.active: return
            lhs = event.widget
            lhs.value_index = (lhs.value_index + 1) % len(values)
            lhs.value = values[lhs.value_index]
            lhs.config(text=value_labels[lhs.value_index])
            self.callback()

        def handle_enter(event):
            if not self.active: return
            lhs = event.widget
            lhs.config(fg=brighter(lhs['fg']))

        def handle_leave(event):
            if not self.active: return
            lhs = event.widget
            lhs.config(fg=self.active_fg if self.active else self.inactive_fg)

        self.lhs.bind('<Button-1>', handle_click)
        self.lhs.bind('<Enter>', handle_enter)
        self.lhs.bind('<Leave>', handle_leave)
        self.lhs.refresh = refresh
        self.lhs.refresh()
