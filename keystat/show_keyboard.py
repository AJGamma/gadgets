#!/usr/bin/env python3
"""
Keyboard layout visualizer that reads keyboardlayout.json and keymapc files.
Supports displaying pressed keys in gray.
"""
import json
import os
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.font_manager import FontProperties

# Use Maple Mono NF CN for text, DejaVu Sans for symbols (has arrows and more)
font_text = FontProperties(fname='/usr/share/fonts/MapleMono/MapleMono-NF-CN-Regular.ttf', size=8)
font_symbols = FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size=10)
font_title = FontProperties(fname='/usr/share/fonts/MapleMono/MapleMono-NF-CN-Regular.ttf', size=20)

# White background theme
BG_COLOR = '#ffffff'
EMPTY_COLOR = '#f0f0f0'
EDGE_COLOR = '#333333'
TEXT_COLOR = '#000000'

# Gray color for pressed keys
PRESSED_COLOR = '#808080'

QMK_TO_EVDEV = {
    # Letters
    'KC_A': 'KEY_A', 'KC_B': 'KEY_B', 'KC_C': 'KEY_C', 'KC_D': 'KEY_D',
    'KC_E': 'KEY_E', 'KC_F': 'KEY_F', 'KC_G': 'KEY_G', 'KC_H': 'KEY_H',
    'KC_I': 'KEY_I', 'KC_J': 'KEY_J', 'KC_K': 'KEY_K', 'KC_L': 'KEY_L',
    'KC_M': 'KEY_M', 'KC_N': 'KEY_N', 'KC_O': 'KEY_O', 'KC_P': 'KEY_P',
    'KC_Q': 'KEY_Q', 'KC_R': 'KEY_R', 'KC_S': 'KEY_S', 'KC_T': 'KEY_T',
    'KC_U': 'KEY_U', 'KC_V': 'KEY_V', 'KC_W': 'KEY_W', 'KC_X': 'KEY_X',
    'KC_Y': 'KEY_Y', 'KC_Z': 'KEY_Z',

    # Numbers
    'KC_0': 'KEY_0', 'KC_1': 'KEY_1', 'KC_2': 'KEY_2', 'KC_3': 'KEY_3',
    'KC_4': 'KEY_4', 'KC_5': 'KEY_5', 'KC_6': 'KEY_6', 'KC_7': 'KEY_7',
    'KC_8': 'KEY_8', 'KC_9': 'KEY_9',

    # Special keys
    'KC_MINS': 'KEY_MINUS',
    'KC_EQL': 'KEY_EQUAL',
    'KC_BSPC': 'KEY_BACKSPACE',
    'KC_DEL': 'KEY_DELETE',
    'KC_LBRC': 'KEY_LEFTBRACE',
    'KC_RBRC': 'KEY_RIGHTBRACE',
    'KC_SCLN': 'KEY_SEMICOLON',
    'KC_QUOT': 'KEY_APOSTROPHE',
    'KC_BSLS': 'KEY_BACKSLASH',
    'KC_COMM': 'KEY_COMMA',
    'KC_DOT': 'KEY_DOT',
    'KC_SLSH': 'KEY_SLASH',
    'KC_GRAVE': 'KEY_GRAVE',
    'KC_TAB': 'KEY_TAB',
    'KC_SPC': 'KEY_SPACE',
    'KC_ENTER': 'KEY_ENTER',
    'KC_ESC': 'KEY_ESC',
    'KC_CAPS': 'KEY_CAPSLOCK',
    'KC_HOME': 'KEY_HOME',
    'KC_END': 'KEY_END',

    'KC_LEFT': 'KEY_LEFT',
    'KC_RIGHT': 'KEY_RIGHT',
    'KC_UP': 'KEY_UP',
    'KC_DOWN': 'KEY_DOWN',

    # Media keys
    'KC_MPRV': 'KEY_MPRV',
    'KC_MNXT': 'KEY_MNXT',
    'KC_MPLY': 'KEY_MPLY',
    'KC_MSTP': 'KEY_MSTP',
    'KC_PAUS': 'KEY_PAUSE',
    'KC_VOLD': 'KEY_VOLD',
    'KC_VOLU': 'KEY_VOLU',
    'KC_MUTE': 'KEY_MUTE',
    'KC_MRWD': 'KEY_REWIND',
    'KC_MFFD': 'KEY_FASTFORWARD',
    'KC_PWR': 'KEY_POWER',
    'KC_BRID': 'KEY_BRID',
    'KC_BRIU': 'KEY_BRIU',

    # Modifiers
    'KC_LSFT': 'KEY_LEFTSHIFT',
    'KC_RSFT': 'KEY_RIGHTSHIFT',
    'KC_LCTL': 'KEY_LEFTCTRL',
    'KC_RCTL': 'KEY_RIGHTCTRL',
    'KC_LGUI': 'KEY_LEFTMETA',
    'KC_RGUI': 'KEY_RIGHTMETA',
    'KC_LALT': 'KEY_LEFTALT',
    'KC_RALT': 'KEY_RIGHTALT',
    'KC_TRNS': ' ',
    '_______': ' ',
    'PRESSED': ' ',
    'MO(_DOUBLE)': 'layer(2)',
    'LT(_MOUSE, KC_V)': 'LT(_MOUSE, KC_V)',
    'LT(_NUM, KC_SPC)': 'LT(_NUM, KC_SPC)',
    'LT(_NAV, KC_ESC)': 'LT(_NAV, KC_ESC)',
    'LT(_SYM, KC_BSPC)': 'LT(_SYM, KC_BSPC)',
    'LMTL': 'KEY_LMTL',
    'LMTR': 'KEY_LMTR',
    'RMTD': 'KEY_RMTD',
    'RMTU': 'KEY_RMTU',
}

DISPLAY_NAMES = {
    'KEY_BACKSPACE': '\u232b',
    'KEY_DELETE': 'Del',
    'KEY_LEFTSHIFT': 'Shift',
    'KEY_RIGHTSHIFT': 'Shift',
    'KEY_LEFTCTRL': 'Ctrl',
    'KEY_RIGHTCTRL': 'Ctrl',
    'KEY_LEFTMETA': 'Super',
    'KEY_RIGHTMETA': 'Super',
    'KEY_LEFTALT': 'Alt',
    'KEY_RIGHTALT': 'Alt',
    'KEY_LMTL': '←\nCtrl',
    'KEY_LMTR': '→\nShift',
    'KEY_RMTD': '↑\nAlt',
    'KEY_RMTU': '↓\nSuper',
    'KEY_RIGHT': '\u2192',
    'KEY_RGHT': '→',
    'KEY_LEFT': '\u2190',
    'KEY_UP': '\u2191',
    'KEY_DOWN': '\u2193',
    'KEY_SPACE': 'Space',
    'KEY_ENTER': 'Enter',
    'KEY_CAPSLOCK': 'Caps',
    'KEY_TAB': 'Tab',
    'KEY_ESC': 'Esc',
    'KEY_HOME': 'Home',
    'KEY_END': 'End',
    'KEY_MINUS': '-',
    'KEY_EQUAL': '=',
    'KEY_LEFTBRACE': '[',
    'KEY_RIGHTBRACE': ']',
    'KEY_SEMICOLON': ';',
    'KEY_APOSTROPHE': "'",
    'KEY_BACKSLASH': '\\',
    'KEY_COMMA': ',',
    'KEY_DOT': '.',
    'KEY_ASTR': '*',
    'KEY_SLASH': '/',
    'KEY_GRAVE': '`',
    'KEY_AMPR': '&',
    'KEY_HASH': '#',
    'KEY_UNDS': '_',
    'KEY_PLUS': '+',
    'KEY_LPRN': '(',
    'KEY_DQT': '"',
    'KEY_CIRC': '^',
    'KEY_RPRN': ')',
    'KEY_LCBR': '{',
    'KEY_RCBR': '}',
    'KEY_DOLLAR': '$',
    'KEY_PERC': '%',
    'KEY_AT': '@',
    'KEY_TILD': '~',
    'KEY_GRV': '`',
    'KEY_EXLM': '!',
    'KEY_VOLD': 'Vol-',
    'KEY_VOLU': 'Vol+',
    'KEY_MUTE': 'Mute',

    'LT(_MOUSE, KC_V)': 'V\nLayer(4)',
    'LT(_NUM, KC_SPC)': 'Space\nLayer(3)',
    'LT(_NAV, KC_ESC)': 'Esc\nLayer(2)',
    'LT(_SYM, KC_BSPC)': '\u232b\nLayer(1)',
    'KEY_MUTE': 'Mute',
    'QK_USER_0': '8\nRep 8',

    # 'LMTL': '\uf060\nCtrl',
    # 'LMTR': '\uf061\nShift',
    # 'RMTD': '\uf063\nAlt',
    # 'RMTU': '\uf062\nSuper',
    # 'KEY_LMTL': '\uf060\nCtrl',
    # 'KEY_LMTR': '\uf061\nShift',
    # 'KEY_RMTD': '\uf063\nAlt',
    # 'KEY_RMTU': '\uf062\nSuper',

    'LMTL': '←\nCtrl',
    'LMTR': '→\nShift',
    'RMTD': '↑\nAlt',
    'RMTU': '↓\nSuper',
    'IREP8': 'I\nRep 8',

    'KEY_MPLY': '\u25b6',           # ▶ Play
    'KEY_MPRV': '\u23ee',           # ⏮ Previous
    'KEY_MNXT': '\u23ed',           # ⏭ Next
    'KEY_MSTP': '\u23f9',           # ⏹ Stop
    'KEY_PAUSE': '\u23f8',          # ⏸ Pause
    'KEY_PLAYPAUSE': '\u23ef',      # ⏯ Play/Pause
    'KEY_RECORD': '\u23fa',         # ⏺ Record
    'KEY_FASTFORWARD': '\u23e9',    # ⏩ Fast Forward
    'KEY_REWIND': '\u23ea',         # ⏪ Rewind
    'KEY_POWER': 'Power',
    'KEY_MS_WH_UP': '\u2191',
    'KEY_MS_WH_DOWN': '\u2193',
    'KEY_BRID': '\u2600\u2193',     # Sun + down arrow
    'KEY_BRIU': '\u2600\u2191',     # Sun + up arrow
}


def qmk_to_evdev(qmk_name):
    """Convert QMK key name to evdev key name."""
    if qmk_name in QMK_TO_EVDEV:
        return QMK_TO_EVDEV[qmk_name]
    if qmk_name.startswith('KC_'):
        return 'KEY_' + qmk_name[3:]
    print("warining: no match found")
    return qmk_name


# Media keys that use symbols from Noto Sans Symbols2 font
MEDIA_SYMBOL_KEYS = {'KEY_MPLY', 'KEY_MPRV', 'KEY_MNXT', 'KEY_MSTP', 'KEY_PAUSE',
                     'KEY_PLAYPAUSE', 'KEY_RECORD', 'KEY_FASTFORWARD', 'KEY_REWIND',
                     'KEY_BACKSPACE', 'KEY_MS_WH_UP', 'KEY_MS_WH_DOWN',
                     'KEY_BRID', 'KEY_BRIU',
                     'KEY_LMTL', 'KEY_LMTR', 'KEY_RMTD', 'KEY_RMTU'}

def get_display_name(evdev_name):
    """Get a short display name for a key.

    Returns tuple: (display_text, font_type)
    font_type: 'text' for Maple Mono, 'symbols' for Noto Sans Symbols2
    """
    if evdev_name in DISPLAY_NAMES:
        display = DISPLAY_NAMES[evdev_name]
        # Check if display contains symbol characters (non-ASCII)
        has_symbol = any(ord(c) > 127 for c in display)
        if has_symbol:
            return (display, 'symbols')
        else:
            return (display, 'text')
    if evdev_name.startswith('KEY_'):
        name = evdev_name[4:]
        if len(name) == 1:
            return (name, 'text')
        return (name.capitalize(), 'text')
    return (evdev_name, 'text')


def load_layout(layout_dir, keymap_file='keymapc'):
    """Load keyboard layout from keyboardlayout.json and keymapc files.

    keymapc 文件中每行可以是一个键名（如 KC_A）或 PRESSED。
    如果是 PRESSED，则该键显示为灰色且无文字。
    """
    layout_path = os.path.join(layout_dir, 'keyboardlayout.json')
    keymap_path = os.path.join(layout_dir, keymap_file)

    with open(layout_path, 'r') as f:
        layout_data = json.load(f)

    with open(keymap_path, 'r') as f:
        keymap_lines = [line.strip().rstrip(',') for line in f.readlines() if line.strip()]

    keys = []
    for i, pos in enumerate(layout_data):
        if i >= len(keymap_lines):
            break

        qmk_name = keymap_lines[i]

        # 如果值是 PRESSED，标记为按下状态
        is_pressed = (qmk_name == 'PRESSED')

        if is_pressed:
            # 按下的键，使用索引作为唯一标识
            evdev_name = f'__PRESSED_{i}__'
            display_name = ''
            font_type = 'text'
        else:
            if qmk_name == 'IGNORE':
                continue

            evdev_name = qmk_to_evdev(qmk_name)
            if evdev_name is None:
                print(f"Warning: Unknown key mapping for {qmk_name}")
                continue
            display_name, font_type = get_display_name(evdev_name)

        keys.append({
            'x': pos['x'],
            'y': pos['y'],
            'r': pos.get('r', 0),
            'w': pos.get('w', 1),
            'h': pos.get('h', 1),
            'color': pos.get('color', None),
            'qmk': qmk_name,
            'evdev': evdev_name,
            'display': display_name,
            'is_pressed': is_pressed,
            'font_type': font_type,
        })

    return keys


def generate_keyboard_layout(output_file='keyboard.png', keymap_file='keymapc', title='Keyboard Layout'):
    """Generate keyboard layout visualization with pressed keys shown in gray."""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    layout_dir = os.path.join(script_dir, 'layout')

    keys = load_layout(layout_dir, keymap_file)

    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    key_size = 0.9

    for key in keys:
        x, y = key['x'], key['y']
        rotation = key['r']
        w = key['w']
        h = key['h']
        custom_color = key['color']
        is_pressed = key['is_pressed']
        display = key['display']

        if is_pressed:
            color = PRESSED_COLOR
        elif custom_color:
            color = custom_color
        else:
            color = EMPTY_COLOR

        rect = FancyBboxPatch(
            (-key_size * w / 2, -key_size * h / 2),
            key_size * w, key_size * h,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1,
            edgecolor=EDGE_COLOR,
            facecolor=color,
        )

        transform = (
            Affine2D()
            .rotate_deg(rotation)
            .translate(x, -y)
            + ax.transData
        )
        rect.set_transform(transform)
        ax.add_patch(rect)

        # 只有未按下的键才显示文字
        if not is_pressed and display:
            # 如果包含换行符，分别渲染每一行
            if '\n' in display:
                lines = display.split('\n')
                # 第一行在上，第二行在下
                for i, line in enumerate(lines):
                    # 判断该行包含什么类型的字符
                    # Unicode arrows: U+2190-U+2193 (←↑→↓)
                    # Noto Sans Symbols2: U+23xx (⌫⏭ etc)
                    has_symbol = any(ord(c) > 127 for c in line)

                    if has_symbol:
                        line_font = font_symbols
                        line_size = 10
                    else:
                        line_font = font_text
                        line_size = 7

                    # 计算每行的垂直偏移（第一行在上，第二行在下）
                    line_offset = ((len(lines) - 1) / 2 - i) * 0.15

                    ax.text(
                        x, -y + line_offset,
                        line,
                        ha='center', va='center',
                        fontsize=line_size,
                        fontweight='bold',
                        color=TEXT_COLOR,
                        rotation=rotation,
                        transform=ax.transData,
                        fontproperties=line_font,
                    )
            else:
                font_size = 8 if len(display) > 2 else 11
                # Check if display contains symbol characters
                has_symbol = any(ord(c) > 127 for c in display)
                if has_symbol:
                    font_props = font_symbols
                else:
                    font_props = font_text

                ax.text(
                    x, -y,
                    display,
                    ha='center', va='center',
                    fontsize=font_size,
                    fontweight='bold',
                    color=TEXT_COLOR,
                    rotation=rotation,
                    transform=ax.transData,
                    fontproperties=font_props,
                )

    xs = [k['x'] for k in keys]
    ys = [-k['y'] for k in keys]
    margin = 1.5
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)

    ax.set_aspect('equal')
    ax.axis('off')

    ax.set_title(title, fontweight='bold', color=TEXT_COLOR, pad=20, fontproperties=font_title)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"Keyboard layout saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate keyboard layout visualization')
    parser.add_argument('-o', '--output', default='keyboard.png',
                        help='Output file path (default: keyboard.png)')
    parser.add_argument('-k', '--keymap', default='keymapc2',
                        help='Keymap file to use (default: keymapc2)')

    parser.add_argument('-t', '--title', default='Keyboard Layout',
                        help='Title')
    args = parser.parse_args()

    generate_keyboard_layout(args.output, args.keymap, args.title)
