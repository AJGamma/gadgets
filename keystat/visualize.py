#!/usr/bin/env python3
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize

KEYBOARD_LAYOUT = [
    ['ESC', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'],
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'BACKSPACE'],
    ['TAB', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
    ['CAPS', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'ENTER'],
    ['LFSH', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'RFSH'],
    ['LCTL', 'LWIN', 'LALT', 'SPACE', 'RALT', 'RWIN', 'MENU', 'RCTL'],
]

MODIFIER_KEYS = {
    'LFSH': 'KEY_LEFTSHIFT', 'RFSH': 'KEY_RIGHTSHIFT',
    'LCTL': 'KEY_LEFTCTRL', 'RCTL': 'KEY_RIGHTCTRL',
    'LWIN': 'KEY_LEFTMETA', 'RWIN': 'KEY_RIGHTMETA',
    'LALT': 'KEY_LEFTALT', 'RALT': 'KEY_RIGHTALT',
    'MENU': 'KEY_COMPOSE',
    'CAPS': 'KEY_CAPSLOCK',
    'TAB': 'KEY_TAB',
    'BACKSPACE': 'KEY_BACKSPACE',
    'ENTER': 'KEY_ENTER',
    'SPACE': 'KEY_SPACE',
    'ESC': 'KEY_ESC',
}

KEY_WIDTHS = {
    'BACKSPACE': 2, 'TAB': 1.5, '\\': 1.5, 'CAPS': 1.5, 'ENTER': 2.25,
    'LFSH': 2.25, 'RFSH': 2.75, 'LCTL': 1.25, 'LWIN': 1.25, 'LALT': 1.25,
    'SPACE': 6.25, 'RALT': 1.25, 'RWIN': 1.25, 'MENU': 1.25, 'RCTL': 1.25,
    'F1': 1, 'F2': 1, 'F3': 1, 'F4': 1, 'F5': 1, 'F6': 1, 'F7': 1, 'F8': 1,
    'F9': 1, 'F10': 1, 'F11': 1, 'F12': 1,
}

KEY_CODE_MAP = {
    '`': 'KEY_GRAVE', '1': 'KEY_1', '2': 'KEY_2', '3': 'KEY_3', '4': 'KEY_4',
    '5': 'KEY_5', '6': 'KEY_6', '7': 'KEY_7', '8': 'KEY_8', '9': 'KEY_9',
    '0': 'KEY_0', '-': 'KEY_MINUS', '=': 'KEY_EQUAL',
    'Q': 'KEY_Q', 'W': 'KEY_W', 'E': 'KEY_E', 'R': 'KEY_R', 'T': 'KEY_T',
    'Y': 'KEY_Y', 'U': 'KEY_U', 'I': 'KEY_I', 'O': 'KEY_O', 'P': 'KEY_P',
    '[': 'KEY_LEFTBRACE', ']': 'KEY_RIGHTBRACE',
    'A': 'KEY_A', 'S': 'KEY_S', 'D': 'KEY_D', 'F': 'KEY_F', 'G': 'KEY_G',
    'H': 'KEY_H', 'J': 'KEY_J', 'K': 'KEY_K', 'L': 'KEY_L',
    ';': 'KEY_SEMICOLON', "'": 'KEY_APOSTROPHE',
    'Z': 'KEY_Z', 'X': 'KEY_X', 'C': 'KEY_C', 'V': 'KEY_V', 'B': 'KEY_B',
    'N': 'KEY_N', 'M': 'KEY_M', ',': 'KEY_COMMA', '.': 'KEY_DOT', '/': 'KEY_SLASH',
    'F1': 'KEY_F1', 'F2': 'KEY_F2', 'F3': 'KEY_F3', 'F4': 'KEY_F4',
    'F5': 'KEY_F5', 'F6': 'KEY_F6', 'F7': 'KEY_F7', 'F8': 'KEY_F8',
    'F9': 'KEY_F9', 'F10': 'KEY_F10', 'F11': 'KEY_F11', 'F12': 'KEY_F12',
    'ESC': 'KEY_ESC',
    'BACKSPACE': 'KEY_BACKSPACE', 'TAB': 'KEY_TAB', 'ENTER': 'KEY_ENTER',
    'CAPS': 'KEY_CAPSLOCK', 'SPACE': 'KEY_SPACE',
    'LFSH': 'KEY_LEFTSHIFT', 'RFSH': 'KEY_RIGHTSHIFT',
    'LCTL': 'KEY_LEFTCTRL', 'RCTL': 'KEY_RIGHTCTRL',
    'LWIN': 'KEY_LEFTMETA', 'RWIN': 'KEY_RIGHTMETA',
    'LALT': 'KEY_LEFTALT', 'RALT': 'KEY_RIGHTALT',
    'MENU': 'KEY_COMPOSE',
}

def get_key_code(display_name):
    if display_name in MODIFIER_KEYS:
        return MODIFIER_KEYS[display_name]
    if display_name in KEY_CODE_MAP:
        return KEY_CODE_MAP[display_name]
    return f'KEY_{display_name.upper()}'

def load_stats():
    stats_file = os.path.expanduser('~/.local/share/keystat/stats.json')
    if not os.path.exists(stats_file):
        print(f"Stats file not found: {stats_file}")
        print("Please run keystatd first to collect keyboard statistics.")
        return {}
    
    with open(stats_file, 'r') as f:
        data = json.load(f)
    return data.get('keys', {})

def create_keyboard_grid():
    rows = len(KEYBOARD_LAYOUT)
    cols = 15
    
    key_map = []
    
    for row_idx, row in enumerate(KEYBOARD_LAYOUT):
        row_keys = []
        col_idx = 0
        
        for key in row:
            width = KEY_WIDTHS.get(key, 1)
            key_code = get_key_code(key)
            row_keys.append({
                'display': key,
                'code': key_code,
                'row': row_idx,
                'col': col_idx,
                'width': width
            })
            col_idx += int(width * 2)
        
        key_map.append(row_keys)
    
    return key_map

def generate_heatmap(output_file='heatmap.png'):
    key_stats = load_stats()
    
    if not key_stats:
        return
    
    key_map = create_keyboard_grid()
    
    rows = len(KEYBOARD_LAYOUT)
    cols = 15
    
    heatmap = np.zeros((rows, cols))
    max_count = 0
    
    for row in key_map:
        for key_info in row:
            key_code = key_info['code']
            if key_code in key_stats:
                count = key_stats[key_code]
                heatmap[key_info['row'], key_info['col']] = count
                max_count = max(max_count, count)
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    if max_count > 0:
        heatmap_normalized = np.log1p(heatmap) / np.log1p(max_count)
    else:
        heatmap_normalized = heatmap
    
    cmap = plt.cm.YlOrRd
    
    for row_idx, row in enumerate(KEYBOARD_LAYOUT):
        col_idx = 0
        for key in row:
            width = KEY_WIDTHS.get(key, 1)
            count = int(heatmap[row_idx, col_idx])
            
            if count > 0:
                color = cmap(heatmap_normalized[row_idx, col_idx])
            else:
                color = (0.9, 0.9, 0.9, 1.0)
            
            rect = Rectangle(
                (col_idx, rows - 1 - row_idx),
                width - 0.1,
                0.9,
                linewidth=0.5,
                edgecolor='gray',
                facecolor=color
            )
            ax.add_patch(rect)
            
            display_text = key
            if count > 0:
                if count >= 1000000:
                    text = f'{display_text}\n{count/1000000:.1f}M'
                elif count >= 1000:
                    text = f'{display_text}\n{count/1000:.1f}K'
                else:
                    text = f'{display_text}\n{count}'
            else:
                text = display_text
            
            font_size = 7 if len(key) > 1 else 9
            ax.text(
                col_idx + width/2 - 0.05,
                rows - 1 - row_idx + 0.45,
                text,
                ha='center',
                va='center',
                fontsize=font_size,
                fontweight='bold' if count > 0 else 'normal'
            )
            
            col_idx += width
    
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis('off')
    ax.set_title('Keyboard Usage Heatmap', fontsize=14, fontweight='bold', pad=10)
    
    total_presses = sum(key_stats.values())
    ax.text(cols - 0.5, -0.3, f'Total key presses: {total_presses:,}', 
            ha='right', fontsize=10, transform=ax.transData)
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(0, 1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=20)
    cbar.set_label('Usage (log scale)', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Heatmap saved to: {output_file}")
    
    print("\nTop 20 most used keys:")
    sorted_keys = sorted(key_stats.items(), key=lambda x: x[1], reverse=True)[:20]
    for key, count in sorted_keys:
        print(f"  {key}: {count:,}")

if __name__ == '__main__':
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else 'heatmap.png'
    generate_heatmap(output)
