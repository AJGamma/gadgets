# Keystat - Linux Keyboard Statistics Monitor

A transparent keyboard monitoring daemon that tracks all key presses and visualizes them as a heatmap.

## Features

- **Transparent Monitoring**: Uses Linux evdev interface, captures input without interfering with any applications (including input methods)
- **Complete Coverage**: Tracks all keys including modifiers (Ctrl, Shift, Alt, Super, etc.)
- **Persistent Storage**: Statistics survive reboots
- **Heatmap Visualization**: Generate visual heatmaps of key usage

## Requirements

- Linux with evdev support
- libevdev
- libjson-c
- Python 3 with matplotlib and numpy (for visualization)

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
