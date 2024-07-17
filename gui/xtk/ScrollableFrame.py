import tkinter as tk
import tkinter.ttk as ttk

# TODO: whole class is scuff
platform = 'Windows'

# Tkinter has no elegant way to implement scrollable frames and it obviously isn't built in
# Adapted from https://stackoverflow.com/a/76513452
class ScrollableFrame(tk.Frame):
    """
    A scrollable frame with a scroll bar to the right, which can be moved using the mouse wheel.

    Add content to the scrollable area by making self.interior the root object.
    """
    def __init__(self, parent, scrollable_parent=None, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.config(*args, **kwargs)
        self.parent = parent
        self.scrollable_parent = scrollable_parent

        self   .grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # The Scrollbar, layout to the right
        # https://tkdocs.com/shipman/scrollbar.html
        # https://www.tcl.tk/man/tcl/TkCmd/scrollbar.htm


        self._scrollbar = ttk.Scrollbar(self, orient="vertical", style='no_arrows.Vertical.TScrollbar')
        # print(self._scrollbar.configure(elementborderwidth=0, highlightcolor='#f00', bg='#0f0', activebackground='#00f', relief='flat', troughcolor='#f00'))
        # exit()
        # self._scrollbar = tk.Scrollbar(self, orient='vertical')
        self._scrollbar.grid(row=0, column=1, sticky="nes")

        # The Canvas which supports the Scrollbar Interface, layout to the left
        self._canvas = tk.Canvas(self, bd=0, highlightthickness=0, width=self['width'], height=self['height'])
        self._canvas.grid(row=0, column=0, sticky="nesw")
        self._canvas.config(bg=self['bg'])

        # Bind the Scrollbar to the canvas Scrollbar Interface
        self   ._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.configure(command=self.yview_wrapper)

        # Reset the view
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

        # The scrollable area, placed into the canvas
        # All widgets to be scrolled have to use this Frame as parent
        self.interior = tk.Frame(self._canvas, bg=self['bg'], width=20, height=20)
        self.interior.parent = self
        
        self._canvas_frame = self._canvas.create_window(
            0, 0,
            window=self.interior,
            anchor='nw'
        )

        self.interior.bind("<Configure>", self._on_interior_configure)
        self._canvas .bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel when the mouse is hovering the canvas
        self._canvas.bind('<Enter>', self._bind_to_mousewheel)
        self._canvas.bind('<Leave>', self._unbind_from_mousewheel)

    def yview_wrapper(self, *args):
        # logging.getLogger().debug(f"yview_wrapper({args})")
        moveto_val = float(args[1])
        new_moveto_val = str(moveto_val) if moveto_val > 0 else "0.0"
        return self._canvas.yview('moveto', new_moveto_val)

    def _on_interior_configure(self, event):
        """
        Configure canvas size and scroll region according to the interior frame's size
        """
        reqwidth, reqheight = self.interior.winfo_reqwidth(), self.interior.winfo_reqheight()
        self._canvas.config(scrollregion=f"0 0 {reqwidth} {reqheight}")
        if self.interior.winfo_reqwidth() != self._canvas.winfo_width():
            # print(f'Interior Configure: Interior Width {self.interior.winfo_reqwidth()} != Canvas Width {self._canvas.winfo_width()}')
            # Update the canvas's width to fit the inner frame.
            self._canvas.config(width=self.interior.winfo_reqwidth())

    def _on_canvas_configure(self, event):
        # logging.getLogger().debug(f"_configure_canvas")
        # if self.interior.winfo_reqwidth() != self._canvas.winfo_width():
        if self.interior.winfo_reqwidth() != self._canvas.winfo_width():
            # print(f'Canvas Configure: Interior Width {self.interior.winfo_reqwidth()} != Canvas Width {self._canvas.winfo_width()}')
            # Update the inner frame's width to fill the canvas.
            self._canvas.itemconfigure(self._canvas_frame, width=self._canvas.winfo_width())

    def _on_mousewheel(self, event, scroll=None):
        """
        Can handle windows or linux
        """
        speed = 1 / 6
        if platform == "linux" or platform == "linux2":
            fraction = self._scrollbar.get()[0] + scroll * speed
        else:
            units = event.delta / 120
            fraction = self._scrollbar.get()[0] - units * speed

        fraction = max(0, fraction)
        self._canvas.yview_moveto(fraction)

    def _bind_to_mousewheel(self, event):
        # print('Bind_all', self.winfo_name())

        if self.scrollable_parent:
            return
            # self.scrollable_parent._unbind_from_mousewheel(None)

        if platform == "linux" or platform == "linux2":
            self._canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, scroll=-1))
            self._canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel(e, scroll=1))
        else:
            self.bind_all("<MouseWheel>", self._on_mousewheel)
            # self.bind_class

    def _unbind_from_mousewheel(self, event):
        # print('Unbind_all', self.winfo_name())

        if self.scrollable_parent:
            return
            # self.scrollable_parent._bind_to_mousewheel(None)

        if platform == "linux" or platform == "linux2":
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
        else:
            self.unbind_all("<MouseWheel>")
