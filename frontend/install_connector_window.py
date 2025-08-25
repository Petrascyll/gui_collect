import re
import tkinter as tk

from pathlib import Path

from backend.analysis.targeted_analysis import get_include_path
from frontend.xtk.FlatButton import FlatButton


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


def open_install_connector_window(root, mods_path: Path):
    target_path     = (mods_path)/'GUI_Collect_Connector.ini'
    include_path    = get_include_path().absolute()
    relative_path   = include_path.absolute().relative_to(mods_path, walk_up=True)
    include_pattern = re.compile(
        r'^\s*include\s*=\s*{}$'.format(re.escape(str(relative_path))),
        flags=re.MULTILINE
    )

    top_window = __create_top_window(root)
    top_frame = __create_top_frame(top_window)
    text_wdgt = __create_text_widget(top_window, top_frame)
    widgets   = __create_options_frame(top_window, top_frame, target_path, relative_path)
    options_frame, cancel_button, install_button = widgets

    # 0 Installed
    # 1 Failed
    # 2 Cancelled
    top_window.ret = 1

    text_wdgt    .grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
    options_frame.grid(row=1, sticky='ns', padx=8, pady=(0, 8))

    top_window.update_idletasks()
    top_window.wait_visibility()

    
    for p in __iterate_ini_dir(mods_path):
        if p.name.lower().startswith('disabled'): continue
        if p.name.lower() == 'desktop.ini': continue

        text_wdgt.insert(tk.END, '>{}\n'.format(str(p.relative_to(mods_path, walk_up=True))))
        text_wdgt.see(tk.END)
        text_wdgt.update_idletasks()

        try:
            text = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = p.read_text(encoding='gb2312')

        if include_pattern.search(text):
            text_wdgt.insert(tk.END, 'Valid gui_collect connector .ini already installed '.format(str(p.absolute())), 'WARNING')
            text_wdgt.insert(tk.END, '{}\n'.format(p.absolute()), 'PATH')
            text_wdgt.insert(tk.END, 'No additional actions required.', 'WARNING')
            text_wdgt.see(tk.END)
            cancel_button.update_args(
                new_bg='#0A0', new_hover_bg='#6F6',
                new_fg='#e8eaed', new_hover_fg='#FFF'
            )
            break
    else:
    
        if target_path.exists():
            text_wdgt.insert(tk.END, 'Found invalid GUI_Collect_Connector.ini in mods root folder!\n', 'WARNING')
            text_wdgt.insert(tk.END, 'Installation will OVERWRITE it!', 'WARNING')
            text_wdgt.see(tk.END)

            install_button.toggle()
            install_button.update_args(
                new_bg='#edae1c', new_hover_bg='#edb83e',
                new_fg='#e8eaed', new_hover_fg='#FFF'
            )
        else:
            text_wdgt.insert(tk.END, 'No valid gui_collect connector .ini already installed.\n', 'GREEN')
            text_wdgt.insert(tk.END, 'Ready to install! ', 'GREEN')
            text_wdgt.insert(tk.END, '{}'.format(target_path), 'PATH')
            text_wdgt.see(tk.END)

            install_button.toggle()
            install_button.update_args(
                new_bg='#0A0', new_hover_bg='#6F6',
                new_fg='#e8eaed', new_hover_fg='#FFF'
            )

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
    top_frame.grid_rowconfigure(0, weight=1)
    top_frame.grid_rowconfigure(1, weight=0)
    top_frame.grid_columnconfigure(0, weight=1)
    return top_frame


def __create_options_frame(top_window, top_frame, target_path, relative_path):
    def handle_install(e):
        __write_connector_ini(target_path, relative_path)
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

