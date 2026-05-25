@echo off
echo ====== AutoRaku Installer ======
echo.

cd /d "%~dp0"

echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% neq 0 (
	echo Python is not installed or not in PATH.
	echo Opening Microsoft Store to install Python...
	start ms-windows-store://pdp/?ProductId=9NRWMJP3717K
	echo.
	echo Please install Python from the Microsoft Store, then run this installer again.
	pause
	exit /b 1
)

echo Python is installed!
python --version
echo.

echo Installing required packages...
echo.

echo [1/5] Installing pynput...
python -m pip install pynput
if %errorlevel% neq 0 (
	echo Failed to install pynput
	pause
	exit /b 1
)
echo pynput installed successfully!
echo.

echo [2/5] Installing pyautogui...
python -m pip install pyautogui
if %errorlevel% neq 0 (
	echo Failed to install pyautogui
	pause
	exit /b 1
)
echo pyautogui installed successfully!
echo.

echo [3/5] Installing pytesseract...
python -m pip install pytesseract
if %errorlevel% neq 0 (
	echo Failed to install pytesseract
	pause
	exit /b 1
)
echo pytesseract installed successfully!
echo.

echo [4/5] Installing opencv-python...
python -m pip install opencv-python
if %errorlevel% neq 0 (
	echo Failed to install opencv-python
	pause
	exit /b 1
)
echo opencv-python installed successfully!
echo.

echo [5/5] Installing numpy...
python -m pip install numpy
if %errorlevel% neq 0 (
	echo Failed to install numpy
	pause
	exit /b 1
)
echo numpy installed successfully!
echo.

echo.
echo ====== Installation Complete! ======
echo.
echo You can now double-click AutoRaku.pyw to start the GUI app.
echo.
echo Quick Start:
echo 1. Double-click AutoRaku.pyw to open the GUI
echo 2. Configure your settings in the Settings tab
echo 3. Start the game and the activity
echo 4. Click Start in the Control tab
echo.
echo IMPORTANT: If the program fails to start with a tkinter error:
echo - You need to reinstall Python from the Microsoft Store
echo - Link: ms-windows-store://pdp/?ProductId=9NRWMJP3717K
echo - OR download from python.org and check "Install tkinter"
echo.
pause
