import tkinter as tk


class FlatButton(tk.Label):
    def __init__(
            self, parent,
            bg=None, fg='#e8eaed',
            hover_bg=None, hover_fg=None, disabled_bg=None, disabled_fg=None,
            on_click:callable=None,
            on_click_kwargs:dict={},
            is_active=True,
            *args, **kwargs,
        ):
        tk.Label.__init__(self, parent)
        self.parent = parent

        bg = bg or self['bg']

        self.config(bg=bg, fg=fg, font=('Arial', 18, 'bold'))
        self.config(*args, **kwargs)

        self.is_active = is_active
        self.on_click = on_click
        self.on_click_kwargs = on_click_kwargs

        self.default_args  = {'cursor': 'hand2', 'bg': bg, 'fg': fg}
        self.hover_args    = {'cursor': 'hand2',}
        self.disabled_args = {'cursor': 'left_ptr',}

        if hover_bg: self.hover_args['bg'] = hover_bg
        if hover_fg: self.hover_args['fg'] = hover_fg

        if disabled_bg: self.disabled_args['bg'] = disabled_bg
        if disabled_fg: self.disabled_args['fg'] = disabled_fg

        if self.is_active:
            self.enable()
        else:
            self.disable()

    def update_args(self, new_bg, new_fg, new_hover_fg, new_hover_bg):
        self.default_args  = {'cursor': 'hand2', 'bg': new_bg, 'fg': new_fg}
        self.hover_args    = {'cursor': 'hand2', 'bg': new_hover_bg, 'fg': new_hover_fg}
        self.config(**self.default_args)


    def disable(self):
        self.unbind('<Enter>')
        self.unbind('<Leave>')

        if self.on_click:
            self.unbind('<Button-1>')

        self.config(**self.disabled_args)
        self.is_active = False

    def enable(self):
        self.bind('<Enter>', lambda e: e.widget.config(**self.hover_args))
        self.bind('<Leave>', lambda e: e.widget.config(**self.default_args))

        if self.on_click:
            self.bind('<Button-1>', lambda e: self.on_click(e, **self.on_click_kwargs))

        self.config(**self.default_args)
        self.is_active = True

    def toggle(self):
        if self.is_active:
            self.disable()
        else:
            self.enable()
