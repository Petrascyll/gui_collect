import re
import logging
import tkinter as tk

from pathlib import Path

from gui_collect.backend.analysis.targeted_analysis import get_include_path
from gui_collect.frontend.xtk.FlatButton import FlatButton
from gui_collect.frontend.xtk.PathPicker import PathPicker


logger = logging.getLogger(__name__)


def __iterate_ini_dir(root_path: Path):
    for p in root_path.iterdir():
        if p.name.lower().startswith('disabled'): continue

        if p.is_file():
            if p.suffix != '.ini': continue
            if p.name.lower() == 'desktop.ini': continue
            yield p
        else:
            yield from __iterate_ini_dir(p)


def __write_connector_ini(target_path: Path, relative_path: Path):
    target_path.write_text('\n'.join([
        '[IncludeGUICollect]',
        'include = {}'.format(str(relative_path)),
        '',
        '; Required for gui_collect targeted analysis to work',
        '; You must only have one copy of this file in your mods directory',
        '; You can move this file into a different folder as long as it remains within the mods directory.',
        '',
    ]), encoding='utf-8')


def open_install_connector_window(root):
    top_window = __create_top_window(root)
    top_frame = __create_top_frame(top_window)
    text_wdgt = __create_text_widget(top_window, top_frame)
    widgets   = __create_options_frame(top_window, top_frame)
    options_frame, cancel_button, install_button = widgets

    def handle_path_change(mods_path: Path):
        target_path     = (mods_path)/'GUI_Collect_Connector.ini'
        include_path    = get_include_path().absolute()
        relative_path   = include_path.absolute().relative_to(mods_path, walk_up=True)
        include_pattern = re.compile(
            r'^\s*include\s*=\s*{}$'.format(re.escape(str(relative_path))),
            flags=re.MULTILINE
        )

        text_wdgt.insert(tk.END, 'Checking if valid connector is already installed in mods directory...\n', 'GREEN')
        
        for p in __iterate_ini_dir(mods_path):
            text_wdgt.insert(tk.END, '>{}\n'.format(str(p.relative_to(mods_path, walk_up=True))))
            text_wdgt.see(tk.END)
            text_wdgt.update_idletasks()

            try:
                text = p.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                text = p.read_text(encoding='gb2312')

            if include_pattern.search(text):
                text_wdgt.insert(tk.END, '\nValid gui_collect connector .ini already installed '.format(str(p.absolute())), 'WARNING')
                text_wdgt.insert(tk.END, '{}\n'.format(p.absolute()), 'PATH')
                text_wdgt.insert(tk.END, 'No additional actions required.\n\n', 'WARNING')
                text_wdgt.see(tk.END)

                install_button.target_path   = None
                install_button.relative_path = None
                if install_button.is_active:
                    install_button.disable()
                install_button.default_args = {'cursor': 'left_ptr', 'bg': '#333', 'fg': '#666'}
                install_button.config(**install_button.default_args)
                
                break
        else:
        
            if target_path.exists():
                text_wdgt.insert(tk.END, '\nFound invalid GUI_Collect_Connector.ini in mods root folder!\n', 'WARNING')
                text_wdgt.insert(tk.END, 'Installation will OVERWRITE it!\n\n', 'WARNING')
                text_wdgt.see(tk.END)

                install_button.target_path   = target_path
                install_button.relative_path = relative_path

                install_button.default_args = {'cursor': 'hand2', 'bg': '#edae1c', 'fg': '#e8eaed'}
                install_button.hover_args   = {'cursor': 'hand2', 'bg': '#edb83e', 'fg': '#FFF'}
                install_button.config(**install_button.default_args)
                if install_button.is_active:
                    install_button.disable()
                install_button.enable()

            else:
                text_wdgt.insert(tk.END, '\nNo valid gui_collect connector .ini already installed.\n', 'GREEN')
                text_wdgt.insert(tk.END, 'Ready to install! ', 'GREEN')
                text_wdgt.insert(tk.END, '{}\n\n'.format(target_path), 'PATH')
                text_wdgt.see(tk.END)

                install_button.target_path   = target_path
                install_button.relative_path = relative_path

                install_button.default_args = {'cursor': 'hand2', 'bg': '#0A0', 'fg': '#e8eaed'}
                install_button.hover_args   = {'cursor': 'hand2', 'bg': '#6F6', 'fg': '#FFF'}
                install_button.config(**install_button.default_args)
                if install_button.is_active:
                    install_button.disable()
                install_button.enable()

    pp_widget = __create_path_picker_widget(top_window, top_frame, callback=handle_path_change, text_wdgt=text_wdgt)

    top_window.update_idletasks()
    top_window.wait_visibility()

    # 0 Installed
    # 1 Failed
    # 2 Cancelled
    top_window.ret = 1

    pp_widget    .grid(row=0, column=0, sticky='nsew', padx=16, pady=(16, 0))
    text_wdgt    .grid(row=1, column=0, sticky='nsew', padx=16, pady=(8, 0))
    options_frame.grid(row=2, sticky='ns', padx=16, pady=16)

    root.wait_window(top_window)
    return top_window.ret


def __create_top_window(root):
    top_window = tk.Toplevel(root, bg='#222')
    top_window.title("Installing Connector .ini")
    
    width  = 800
    height = 400
    # Position the top window in the center of the screen
    x_coordinate = int((root.winfo_screenwidth() / 2) - (width / 2))
    y_coordinate = int((root.winfo_screenheight() / 2) - (height / 2))
    top_window.geometry(f'{width}x{height}+{x_coordinate}+{y_coordinate}')
    
    def handle_window_delete():
        top_window.ret = 1
        top_window.destroy()

    top_window.protocol("WM_DELETE_WINDOW", handle_window_delete)

    top_window.transient(root)
    top_window.grab_set()
    return top_window


def __create_top_frame(top_window):
    top_frame = tk.Frame(top_window, bg='#222')
    top_frame.pack(fill='both', expand=True)
    top_frame.grid_rowconfigure(0, weight=0)
    top_frame.grid_rowconfigure(1, weight=1)
    top_frame.grid_rowconfigure(2, weight=0)
    top_frame.grid_columnconfigure(0, weight=1)
    return top_frame


def __create_options_frame(top_window, top_frame):
    def handle_install(e):
        __write_connector_ini(e.widget.target_path, e.widget.relative_path)
        top_window.ret = 0
        top_window.destroy()
    def handle_cancel(e):
        top_window.ret = 1
        top_window.destroy()

    options_frame = tk.Frame(top_frame, bg=top_frame['bg'])
    cancel_button = FlatButton(
        options_frame,
        text='Cancel', justify='center', anchor='center', font=('Arial', 16, 'bold'),
        bg='#333', hover_bg='#444',
        fg='#CCC', hover_fg='#FFF',
        on_click=handle_cancel,
    )
    install_button = FlatButton(
        options_frame,
        text='Install', justify='center', anchor='center', font=('Arial', 16, 'bold'),
        bg='#333', hover_bg='#444',
        fg='#CCC', hover_fg='#FFF',
        disabled_bg='#333', disabled_fg='#666',
        on_click=handle_install,
        is_active=False,
    )
    cancel_button.pack(side='left', ipadx=16, ipady=8, padx=(0, 8))
    install_button.pack(side='left', ipadx=16, ipady=8)
    return options_frame, cancel_button, install_button


def __create_text_widget(top_window, top_frame):
    text_wdgt = tk.Text(
        top_frame,
        insertbackground='#0FF', takefocus=False, insertofftime=500, insertontime=1000,
        bg='#111', fg='#e8eaed', font=('Lucida Sans Typewriter', 10), wrap='word',
        relief='flat', highlightthickness=0, padx=8, pady=8,
    )
    text_wdgt.tag_config('WARNING', foreground='#FB2', font=('Lucida Sans Typewriter', 10, 'bold'))
    text_wdgt.tag_config('GREEN', foreground='#6F6', font=('Lucida Sans Typewriter', 10, 'bold'))
    text_wdgt.tag_config('PATH', foreground='#4FF')
    return text_wdgt


def __create_path_picker_widget(top_window, top_frame, callback, text_wdgt):
    frame = tk.Frame(top_frame, bg=top_frame['bg'])
    frame.pack(fill='x')
    frame.grid(sticky='nsew', column=0)

    def handle_click(pp: PathPicker, new_path: str):
        path = Path(new_path)
        if (path / 'd3dx.ini').exists() and (path / 'Mods').exists():
            text_wdgt.insert(tk.END, f'Found valid 3dm mods folder path: {str(path)}\n\n', 'GREEN')
            path = path / 'Mods'

            pp.set_path(str(path))
            pp.default_bg = '#0A0'
            pp.refresh_label_bindings()

        elif (path / '..' / 'd3dx.ini').exists() and path.name == 'Mods':
            text_wdgt.insert(tk.END, f'Got valid 3dm mods folder path: {str(path)}\n\n', 'GREEN')
            pp.default_bg = '#0A0'
            pp.refresh_label_bindings()

        else:
            text_wdgt.insert(tk.END, f'Got mods folder path: {str(path)}\n', 'GREEN')
            text_wdgt.insert(
                tk.END,
                'Cannot verify that the selected folder is valid 3dm mods folder path.'
                ' This is expected and normal if you have moved the mods folder to a custom location.\n\n',
                'WARNING',
                )
            pp.default_bg = '#AA0'
            pp.refresh_label_bindings()
        
        callback(path)

    lbl = tk.Label(frame, text='Select 3dmigoto Mods Folder: ', font=('Arial', 16), fg='#CCC', bg='#333', relief='flat')
    pp = PathPicker(
        frame,
        editable=True,
        bg='#A00',
        font=('Arial', 16, 'bold'),
        text_fg='#000',
        hover_text_fg='#000',
        button_bg='',

        override_open=True,
        value='.',
        callback=handle_click,
        pass_self_to_callback=True,
        dialog_title='Select Mods Folder Root',
        dialog_parent=frame,
    )

    frame.grid_columnconfigure(index=0, weight=0)
    frame.grid_columnconfigure(index=1, weight=1)
    lbl.grid(row=0, column=0, sticky='nsew', padx=(0, 0), ipady=8)
    pp.grid(row=0, column=1, sticky='nsew')

    return frame
