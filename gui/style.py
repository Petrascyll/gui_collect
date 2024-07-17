from colorsys import rgb_to_hls, hls_to_rgb

COLOR = {
    'Black.1': '#111111',
    'Black.2': '#222222',
    'Black.3': '#333333',
    'Alabaster':   '#ECEBE4',
    'Night Black': '#080F0F',
    'Crayola Red': '#EE4266',
    'Aquamarine':  '#16F4D0',
    'Aquamarine.Hover':  '#82f4e2',
    'ZZZ Orange': '#e2751e'
}

def clamp(n, min_n, max_n):
    return max(min(max_n, n), min_n)

def adjust_luminance(hex_code:str, amount:float):
    hls_code = rgb_to_hls(*hex_to_rgb(hex_code))
    hls_code = (
        hls_code[0],
        clamp(hls_code[1] + amount, 0, 1),
        hls_code[2]
    )
    hex_code = rgb_to_hex(hls_to_rgb(*hls_code))
    return hex_code

def brighter(hex_code:str):
    return adjust_luminance(hex_code, +0.1)

def darker(hex_code:str):
    return adjust_luminance(hex_code, -0.1)


def hex_to_rgb(hex_code: str):
    '''
    RGB output is a triplet of floats in the range [0.0...1.0]
    '''
    hex_code = hex_code.lstrip('#')
    if len(hex_code) == 3: hex_code += hex_code
    return tuple(int(hex_code[i:i+2], 16)/256 for i in (0, 2, 4))


def rgb_to_hex(rgb_code: tuple[str]):
    '''
    RGB input is a triplet of floats in the range [0.0...1.0]
    '''
    # hex_code = '#'
    # for c in rgb_code:
    #     h = hex(int(c*255))
    #     h = h.removeprefix('0x')
    #     hex_code += h.zfill(2)
    # return hex_code
    return '#' + ''.join([hex(int(c*255)).removeprefix('0x').zfill(2) for c in rgb_code])


APP_STYLE = {
    'app_background': COLOR['Black.1'],
    'sidebar_background': COLOR['ZZZ Orange'],
    'text_light': COLOR['Alabaster'],
    'text_dark': COLOR['Black.1'],
    'button': {
        'default': {
            'foreground': COLOR['Alabaster'],
            'background': COLOR['Black.2'],
        },
        'active': {
            'foreground': COLOR['Black.1'],
            'background': COLOR['Aquamarine']
        },
    },
    'image': {
        'default': {
            'border': COLOR['Black.2']
        },
        'active': {
            'border': COLOR['Aquamarine']
        }
    }
}

DEFAULT_BUTTON_STYLE = {
    'relief': 'flat',
    'borderwidth': 0,
    'padx': 0,
    'pady': 0,
    # All tk Cursors: https://www.tcl.tk/man/tcl8.4/TkCmd/cursors.htm
    'cursor': 'hand2'
}

BUTTON_STYLE = {
    **DEFAULT_BUTTON_STYLE,
    'bg': APP_STYLE['button']['default']['background'],
    'fg': APP_STYLE['button']['default']['foreground'],
    'activebackground': APP_STYLE['button']['active']['background'],
}

ACTIVE_BUTTON_STYLE = {
    **BUTTON_STYLE,
    'bg': APP_STYLE['button']['active']['background'],
    'fg': APP_STYLE['button']['active']['foreground'],
}

DEFAULT_CANVAS_STYLE = {
    'highlightthickness': 0,
    'relief': 'flat'
}

# [
#     'Arial',
#     'Arial Baltic',
#     'Arial Black',
#     'Arial CE',
#     'Arial CYR',
#     'Arial Greek',
#     'Arial Narrow',
#     'Arial Rounded MT Bold',
#     'Arial TUR'
#     'Bahnschrift',
#     'Bahnschrift Condensed',
#     'Bahnschrift Light',
#     'Bahnschrift Light Condensed',
#     'Bahnschrift Light SemiCondensed',
#     'Bahnschrift SemiBold',
#     'Bahnschrift SemiBold Condensed',
#     'Bahnschrift SemiBold SemiConden',
#     'Bahnschrift SemiCondensed',
#     'Bahnschrift SemiLight',
#     'Bahnschrift SemiLight Condensed',
#     'Bahnschrift SemiLight SemiConde'
# ]