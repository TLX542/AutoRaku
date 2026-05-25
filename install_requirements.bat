@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
	where python >nul 2>nul
	if %errorlevel%==0 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
	echo Python was not found on this system.
	echo Install Python 3.13 or newer, then run this file again.
	pause
	exit /b 1
)

echo Using %PYTHON_CMD% to install requirements...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Requirements installed.
pause