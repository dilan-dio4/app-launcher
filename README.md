# macOS Keyboard Launcher

> Lightning-fast macOS app and URL launcher with global hotkey access

[![macOS](https://img.shields.io/badge/macOS-12.0+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, native macOS application launcher that gives you instant access to your favorite apps and websites through a global hotkey. Built with Python and AppleScript for optimal performance and seamless macOS integration.

## Quick Start

**Requirements:** macOS 12+, Python 3.12+

```bash
# 1. Install dependencies
uv sync

# 2. Compile AppleScript components
./scripts/compile.sh

# 3. Launch the app launcher
uv run main.py
```

Press `Ctrl+/` anywhere to open your launcher menu!

## Features

- **Global Hotkey** - Access from anywhere with `Ctrl+/`
- **Keyboard Focus** - Use the keyboard to select and launch items
- **Lightning Fast** - Sub-100ms response time
- **Native macOS** - Status bar integration with SF Symbols
- **Mixed Content** - Launch both applications and websites
- **Lightweight** - Minimal memory footprint
- **Customizable** - Easy configuration through Python code

## Installation

### Prerequisites

- **macOS 12.0+** (Monterey or later)
- **Python 3.12+**
- **uv package manager** ([install here](https://docs.astral.sh/uv/getting-started/installation/))

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dilan-dio4/app-launcher.git
   cd app-launcher
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Compile AppleScript components**
   ```bash
   chmod +x scripts/compile.sh
   ./scripts/compile.sh
   ```

4. **Grant accessibility permissions**
   - Open **System Preferences** - **Security & Privacy** - **Privacy**
   - Select **Accessibility** from the left sidebar
   - Click the lock to make changes
   - Add your **Terminal** app (or wherever you're running the script)

5. **Launch the application**
   ```bash
   uv run main.py
   ```

6. **Verify installation**
   - Look for the app badge icon in your menu bar
   - Press `Ctrl+/` to test the global hotkey
   - You should see a dropdown menu with launcher items

## Usage

### Basic Operation

1. **Trigger**: Press `Ctrl+/` from anywhere in macOS
2. **Select**: Either click any item from the dropdown menu or use the keyboard to focus an item. Use 'enter' to launch the selected item.
3. **Launch**: Applications open instantly, URLs open in your default browser

### Default Launcher Items

The launcher comes pre-configured with these items:

**Applications:**
- Visual Studio Code
- Xcode
- Microsoft Edge
- Messages
- Warp Terminal
- Spotify
- Claude
- OrbStack
- Todoist
- YouTube

**Websites:**
- Gmail
- X (Twitter)
- GitHub

### Global Hotkey

The default hotkey is `Ctrl+/`, chosen for:
- **Ergonomic** - Easy single-hand access
- **Universal** - Works in all applications
- **Memorable** - "/" suggests "search" or "quick access"

## Configuration

### Adding New Launcher Items

Edit the `LAUNCHER_ITEMS` dictionary in `main.py`:

```python
LAUNCHER_ITEMS: dict[str, LauncherItem] = {
    # Add an application
    "notion": LauncherItem(
        action_type=ActionType.APP,
        target="Notion",  # Exact app name as it appears in Applications
    ),

    # Add a website
    "docs": LauncherItem(
        action_type=ActionType.URL,
        target="https://docs.company.com",
    ),
}
```

### Action Types

- **`ActionType.APP`** - Launches macOS applications
  - `target`: Exact application name (case-sensitive)
  - Example: `"Visual Studio Code"`, `"Spotify"`, `"System Preferences"`

- **`ActionType.URL`** - Opens websites in default browser
  - `target`: Full URL including protocol
  - Example: `"https://github.com"`, `"https://mail.google.com"`

### Customizing the Hotkey

Change the `HOTKEY` constant in `main.py`:

```python
HOTKEY = "<ctrl>+space"  # Ctrl+Space
HOTKEY = "<cmd>+/"       # Cmd+/
HOTKEY = "<ctrl>+<alt>+l" # Ctrl+Alt+L
```

### Building from Source

1. **Clone and setup**
   ```bash
   git clone https://github.com/dilan-dio4/app-launcher.git
   cd app-launcher
   uv sync
   ```

2. **Compile AppleScript components**
   ```bash
   ./scripts/compile.sh
   ```

3. **Run in development mode**
   ```bash
   uv run main.py
   ```

### Development Workflow

1. **Make changes** to Python code in `main.py`
2. **Modify AppleScript** files in `scripts/applescript/`
3. **Recompile** with `./scripts/compile.sh` if AppleScript changed
4. **Restart** the application to test changes

### Testing Changes

- **Python changes**: Restart `main.py`
- **AppleScript changes**: Run `./scripts/compile.sh` then restart
- **Configuration changes**: Restart to reload launcher items

## Acknowledgments

- **pynput** - Cross-platform keyboard input library
- **macOS AppleScript** - Native automation framework
- **uv** - Fast Python package manager
- **SF Symbols** - Apple's icon system
