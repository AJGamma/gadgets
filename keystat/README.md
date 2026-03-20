# Keystat - Linux Keyboard Statistics Monitor

A transparent keyboard monitoring daemon that tracks all key presses and visualizes them as a heatmap.

## Features

- **Transparent Monitoring**: Uses Linux evdev interface, captures input without interfering with any applications (including input methods)
- **Complete Coverage**: Tracks all keys including modifiers (Ctrl, Shift, Alt, Super, etc.)
- **Persistent Storage**: 重启后从 `~/.local/share/keystat/stats.json` 恢复计数并继续累加
- **Heatmap Visualization**: Generate visual heatmaps of key usage

## Requirements

- Linux with evdev support
- libevdev
- Python 3 with matplotlib and numpy (for visualization)

启动时会读取已有的 `stats.json`（若存在），在原有按键计数上继续累加；请用同一用户身份运行守护进程与可视化（依赖 `$HOME` 下的数据路径）。

## Building

```bash
mkdir build && cd build
cmake ..
make
```

## Usage

### Starting the daemon

```bash
./keystatd
```

The daemon will:
- Run in background
- Monitor all keyboard devices
- Save statistics to `~/.local/share/keystat/stats.json` every 30 seconds

### Stopping the daemon

```bash
pkill keystatd
```

### Generating heatmap visualization

```bash
python3 visualize.py
```

This will read the statistics file and generate a heatmap image.

## Data Format

Statistics are stored in JSON format:

```json
{
    "keys": {
        "KEY_A": 1234,
        "KEY_B": 567,
        ...
    },
    "last_updated": 1234567890
}
```

## How it works

The daemon uses libevdev to:
1. Open all `/dev/input/event*` devices
2. Filter for EV_KEY events (key presses)
3. Track press counts (not key repeats, only actual presses)
4. Periodically flush statistics to disk

The program is completely transparent - it opens devices in `O_RDONLY | O_NONBLOCK` mode, which only monitors events without consuming them.
