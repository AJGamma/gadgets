#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.colors import Normalize
from matplotlib.transforms import Affine2D

THEMES = {
    'plasma': {
        'cmap': 'plasma',
        'bg': '#1a1a2e',
        'empty': '#16162a',
        'edge': '#4a4a6a',
        'text_threshold': 0.7,
        'cmap_start': 0.15,
    },
    'inferno': {
        'cmap': 'inferno',
        'bg': '#0d0d0d',
        'empty': '#1a1a1a',
        'edge': '#3d3d3d',
        'text_threshold': 0.6,
        'cmap_start': 0.1,
    },
    'viridis': {
        'cmap': 'viridis',
        'bg': '#1a1a2e',
        'empty': '#1e1e3a',
        'edge': '#4a4a6a',
        'text_threshold': 0.7,
        'cmap_start': 0.1,
    },
    'hot': {
        'cmap': 'hot',
        'bg': '#0a0a0a',
        'empty': '#1a1a1a',
        'edge': '#3a3a3a',
        'text_threshold': 0.5,
        'cmap_start': 0.1,
    },
    'cool': {
        'cmap': 'cool',
        'bg': '#1a1a2e',
        'empty': '#202040',
        'edge': '#4a4a7a',
        'text_threshold': 0.6,
        'cmap_start': 0.0,
    },
    'magma': {
        'cmap': 'magma',
        'bg': '#0d0d1a',
        'empty': '#15152a',
        'edge': '#3a3a5a',
        'text_threshold': 0.65,
        'cmap_start': 0.15,
    },
    'turbo': {
        'cmap': 'turbo',
        'bg': '#0a0a15',
        'empty': '#151525',
        'edge': '#3a3a5a',
        'text_threshold': 0.5,
        'cmap_start': 0.1,
    },
    'cividis': {
        'cmap': 'cividis',
        'bg': '#1a1a1a',
        'empty': '#252525',
        'edge': '#4a4a4a',
        'text_threshold': 0.7,
        'cmap_start': 0.1,
    },
}


def select_theme_with_fzf():
    """Use fzf to interactively select a theme."""
    theme_names = list(THEMES.keys())
    try:
        result = subprocess.run(
            ['fzf', '--prompt=Select theme: ', '--height=40%', '--reverse'],
            input='\n'.join(theme_names),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print("No theme selected, using default 'plasma'")
            return 'plasma'
    except FileNotFoundError:
        print("fzf not found, using default 'plasma'")
        return 'plasma'

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
    
    # Modifiers
    'KC_LSFT': 'KEY_LEFTSHIFT',
    'KC_RSFT': 'KEY_RIGHTSHIFT',
    'KC_LCTL': 'KEY_LEFTCTRL',
    'KC_RCTL': 'KEY_RIGHTCTRL',
    'KC_LGUI': 'KEY_LEFTMETA',
    'KC_RGUI': 'KEY_RIGHTMETA',
    'KC_LALT': 'KEY_LEFTALT',
    'KC_RALT': 'KEY_RIGHTALT',
}

DISPLAY_NAMES = {
    'KEY_BACKSPACE': 'Bksp',
    'KEY_DELETE': 'Del',
    'KEY_LEFTSHIFT': 'LShift',
    'KEY_RIGHTSHIFT': 'RShift',
    'KEY_LEFTCTRL': 'LCtrl',
    'KEY_RIGHTCTRL': 'RCtrl',
    'KEY_LEFTMETA': 'Super',
    'KEY_RIGHTMETA': 'Super',
    'KEY_LEFTALT': 'Alt',
    'KEY_RIGHTALT': 'Alt',
    'KEY_RIGHT': '→',
    'KEY_LEFT': '←',
    'KEY_UP': '↑',
    'KEY_DOWN': '↓',
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
    'KEY_SLASH': '/',
    'KEY_GRAVE': '`',
}


def qmk_to_evdev(qmk_name):
    """Convert QMK key name to evdev key name."""
    if qmk_name in QMK_TO_EVDEV:
        return QMK_TO_EVDEV[qmk_name]
    if qmk_name.startswith('KC_'):
        return 'KEY_' + qmk_name[3:]
    return None


def get_display_name(evdev_name):
    """Get a short display name for a key."""
    if evdev_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[evdev_name]
    if evdev_name.startswith('KEY_'):
        name = evdev_name[4:]
        if len(name) == 1:
            return name
        return name.capitalize()
    return evdev_name


def load_layout(layout_dir):
    """Load keyboard layout from layout directory."""
    json_path = os.path.join(layout_dir, 'keyboard.json')
    keymap_path = os.path.join(layout_dir, 'keymapc')
    
    with open(json_path, 'r') as f:
        keyboard_data = json.load(f)
    
    layout = keyboard_data['layouts']['LAYOUT_split_70']['layout']
    
    with open(keymap_path, 'r') as f:
        keymap_lines = [line.strip().rstrip(',') for line in f.readlines()]
    
    keys = []
    for i, (pos, qmk_name) in enumerate(zip(layout, keymap_lines)):
        if qmk_name == 'IGNORE':
            continue
        
        evdev_name = qmk_to_evdev(qmk_name)
        if evdev_name is None:
            print(f"Warning: Unknown key mapping for {qmk_name}")
            continue
        
        keys.append({
            'x': pos['x'],
            'y': pos['y'],
            'r': pos.get('r', 0),
            'qmk': qmk_name,
            'evdev': evdev_name,
            'display': get_display_name(evdev_name),
        })
    
    return keys


def load_stats():
    """Load key statistics from stats file."""
    stats_file = os.path.expanduser('~/.local/share/keystat/stats.json')
    if not os.path.exists(stats_file):
        print(f"Stats file not found: {stats_file}")
        print("Please run keystatd first to collect keyboard statistics.")
        return {}
    
    with open(stats_file, 'r') as f:
        data = json.load(f)
    return data.get('keys', {})


def generate_heatmap(output_file='heatmap.png', theme_name='plasma'):
    """Generate keyboard heatmap visualization."""
    theme = THEMES.get(theme_name, THEMES['plasma'])
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    layout_dir = os.path.join(script_dir, 'layout')
    
    keys = load_layout(layout_dir)
    key_stats = load_stats()
    
    if not key_stats:
        return
    
    counts = []
    for key in keys:
        count = key_stats.get(key['evdev'], 0)
        key['count'] = count
        if count > 0:
            counts.append(count)
    
    if not counts:
        print("No key press data found")
        return
    
    max_count = max(counts)
    
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor(theme['bg'])
    ax.set_facecolor(theme['bg'])
    
    cmap = plt.colormaps[theme['cmap']]
    
    key_size = 0.9
    
    for key in keys:
        x, y = key['x'], key['y']
        rotation = key['r']
        count = key['count']
        
        if count > 0:
            normalized = np.log1p(count) / np.log1p(max_count)
            color = cmap(theme['cmap_start'] + normalized * (1 - theme['cmap_start']))
        else:
            color = theme['empty']
        
        rect = FancyBboxPatch(
            (-key_size/2, -key_size/2),
            key_size, key_size,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1,
            edgecolor=theme['edge'],
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
        
        text_color = 'black' if count > 0 and normalized > theme['text_threshold'] else 'white'
        
        display_text = key['display']
        if count > 0:
            if count >= 1000000:
                count_text = f'{count/1000000:.1f}M'
            elif count >= 1000:
                count_text = f'{count/1000:.1f}K'
            else:
                count_text = str(count)
            display_text = f"{key['display']}\n{count_text}"
        
        font_size = 7 if len(key['display']) > 2 else 8
        
        ax.text(
            x, -y,
            display_text,
            ha='center', va='center',
            fontsize=font_size,
            fontweight='bold' if count > 0 else 'normal',
            color=text_color,
            rotation=rotation,
            transform=ax.transData,
        )
    
    xs = [k['x'] for k in keys]
    ys = [-k['y'] for k in keys]
    margin = 1.5
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.set_title('Sheriff Keyboard Usage Heatmap', 
                 fontsize=16, fontweight='bold', color='white', pad=20)
    
    total_presses = sum(key_stats.values())
    ax.text(0.5, -0.05, f'Total key presses: {total_presses:,}',
            ha='center', fontsize=11, color='white',
            transform=ax.transAxes)
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(0, 1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=25, pad=0.02)
    cbar.set_label('Usage (log scale)', fontsize=10, color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight', 
                facecolor=fig.get_facecolor())
    print(f"Heatmap saved to: {output_file}")
    
    print("\nTop 20 most used keys:")
    sorted_keys = sorted(key_stats.items(), key=lambda x: x[1], reverse=True)[:20]
    for key, count in sorted_keys:
        print(f"  {key}: {count:,}")


def generate_bar_chart(output_file='top_keys.png', theme_name='plasma', top_n=20):
    """Generate horizontal bar chart for top N keys."""
    theme = THEMES.get(theme_name, THEMES['plasma'])
    key_stats = load_stats()
    
    if not key_stats:
        return
    
    sorted_keys = sorted(key_stats.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    if not sorted_keys:
        print("No key press data found")
        return
    
    keys = [get_display_name(k) for k, _ in sorted_keys]
    counts = [c for _, c in sorted_keys]
    max_count = max(counts)
    
    keys = keys[::-1]
    counts = counts[::-1]
    
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor(theme['bg'])
    ax.set_facecolor(theme['bg'])
    
    cmap = plt.colormaps[theme['cmap']]
    normalized = [np.log1p(c) / np.log1p(max_count) for c in counts]
    colors = [cmap(theme['cmap_start'] + n * (1 - theme['cmap_start'])) for n in normalized]
    
    y_pos = np.arange(len(keys))
    bars = ax.barh(y_pos, counts, color=colors, edgecolor=theme['edge'], linewidth=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(keys, fontsize=11, color='white')
    ax.set_xlabel('Press Count', fontsize=12, color='white')
    ax.set_title(f'Top {top_n} Most Used Keys', fontsize=16, fontweight='bold', color='white', pad=15)
    
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    for spine in ax.spines.values():
        spine.set_color(theme['edge'])
    
    for bar, count, norm in zip(bars, counts, normalized):
        width = bar.get_width()
        text_color = 'black' if norm > theme['text_threshold'] else 'white'
        if count >= 1000000:
            label = f'{count/1000000:.1f}M'
        elif count >= 1000:
            label = f'{count/1000:.1f}K'
        else:
            label = str(count)
        ax.text(width - max_count * 0.02, bar.get_y() + bar.get_height()/2,
                label, ha='right', va='center', fontsize=9, 
                fontweight='bold', color=text_color)
    
    total_presses = sum(key_stats.values())
    ax.text(0.98, 0.02, f'Total: {total_presses:,}',
            ha='right', va='bottom', fontsize=10, color='white',
            transform=ax.transAxes)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"Bar chart saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate keyboard usage visualization')
    parser.add_argument('-o', '--output', default=None,
                        help='Output file path')
    parser.add_argument('-t', '--theme', choices=list(THEMES.keys()),
                        help='Color theme')
    parser.add_argument('-l', '--list-themes', action='store_true',
                        help='List available themes and exit')
    parser.add_argument('-m', '--mode', choices=['heatmap', 'bar', 'both'],
                        default='heatmap',
                        help='Visualization mode (default: heatmap)')
    parser.add_argument('-n', '--top-n', type=int, default=40,
                        help='Number of top keys for bar chart (default: 40)')
    
    args = parser.parse_args()
    
    if args.list_themes:
        print("Available themes:")
        for name in THEMES.keys():
            print(f"  {name}")
        exit(0)
    
    theme = args.theme if args.theme else select_theme_with_fzf()
    
    if args.mode == 'heatmap':
        output = args.output if args.output else 'heatmap.png'
        generate_heatmap(output, theme)
    elif args.mode == 'bar':
        output = args.output if args.output else 'top_keys.png'
        generate_bar_chart(output, theme, args.top_n)
    elif args.mode == 'both':
        generate_heatmap(args.output if args.output else 'heatmap.png', theme)
        generate_bar_chart('top_keys.png', theme, args.top_n)
