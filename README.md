# URL Clip Changer

A utility that automatically modifies clipboard URLs based on configurable rules.

## Features

- Automatically processes URLs copied to the clipboard
- Applies custom rules to transform URLs based on domains
- Available in both GUI and background service modes
- Import and export rule sets

## Usage

### Background Service

Run `URLClipChanger.exe` to start the application in background mode. It will monitor your clipboard and automatically apply rules to URLs that you copy.

### GUI Application

Run `URLClipChangerGUI.exe` to open the graphical interface where you can:

- View all configured rules
- Add new rules
- Remove existing rules
- Import rules from a JSON file
- Export your rules to a JSON file

The clipboard monitoring continues to run while the GUI is open.

## Rule Configuration

Each rule consists of:

- **Domains**: A list of domain patterns to match
- **Suffix**: The modification to apply to matching URLs

### Rule Types

The application supports different types of URL modifications:

- Query parameters: Starting with `?` (e.g., `?ref=123`)
- Path extensions: Starting with `/` (e.g., `/refer/456`)
- Complete URL replacement: Starting with `http://` or `https://`
- Simple suffix: Any other format will be appended to the URL

## Building from Source

### Prerequisites
- Python 3.8+
- Required packages: `pywin32`, `pyperclip`, `pyinstaller`

### Build Commands

```
# Build both GUI and background service
python build.py both

# Build only the GUI
python build.py gui

# Build only the background service
python build.py cli
```
