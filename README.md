# AutoRaku

AutoRaku automates the **RakuRaku** gamemode in **Forza Horizon 6** by watching the screen and sending key presses when it detects the expected game state.

## What it does

- Scans the game with OCR and image processing.
- Presses configured keys for menu navigation and auto-drive actions.
- Lets you start and stop automation from a GUI.
- Saves your key bindings and theme preference in `autoraku_settings.json`.

## Important

- Start the activity in-game first.
- Keep AutoRaku in the open while it runs.
- Install Tesseract OCR at `C:\Program Files\Tesseract-OCR\tesseract.exe` if possible.
- **To make the program read info more easily, go into `Settings/Visual Accessibility` and change Increased Text Size to 125% and Interface Visuals to High Contrast**

## Requirements

- Windows or Linux
- Python 3.13 or newer
- Tesseract OCR

## Install

### Windows

1. Open a terminal in this folder.
2. Or double-click `AutoRaku.bat` to install the dependencies and launch the app.
3. You can also double-click `install_requirements.bat` if you only want to install the dependencies.
4. If you prefer the terminal, install Python dependencies:

```bash
pip install -r requirements.txt
```

5. If needed, install Tesseract OCR.

Quick launch options on Windows:

- Double-click `AutoRaku.pyw` for a no-console launch.
- Double-click `AutoRaku.bat` to install and then launch the app.

### Linux

1. Open a terminal in this folder.
2. Install system packages:

```bash
sudo apt update
sudo apt install python3 python3-pip tesseract-ocr
```

3. Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

If your distro uses a virtual environment, activate it first and run the same `pip` command inside it.

## Start

Run the app with one of these:

```bash
python AutoRaku.py
```

If `python` is not available on your system, try:

```bash
py AutoRaku.py
```

For a no-console launch on Windows, double-click `AutoRaku.pyw`.

For an install-and-launch flow on Windows, double-click `AutoRaku.bat`.

On Linux, use:

```bash
python3 AutoRaku.py
```

## Usage

1. Launch the game.
2. Start the RakuRaku activity.
3. Bring AutoRaku to the foreground.
4. Press **Start** in the app.
5. Use the configured stop hotkey to stop automation.

## Disclaimer

Use this tool at your own risk. I am not responsible for any warnings, suspensions, bans, account loss, or other consequences that may happen if you use automation or botting tools in a game or online service.

This README is not legal advice. Make sure you understand and follow the game rules, platform terms of service, and any applicable laws before using AutoRaku.

## Settings

Use the Settings tab to change keys such as map, confirm, movement, and auto-drive controls. Click a field, then press the key you want to record.

## Notes

- The default layout used is qwerty
- If OCR behaves poorly, make sure the game is visible and not minimized.