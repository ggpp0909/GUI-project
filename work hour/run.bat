@echo off

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo Failed to install pip. Please check your Python installation.
        pause
        exit /b 1
    )
)

REM Check and install PyQt5 package
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt5 is not installed. Installing PyQt5...
    pip install PyQt5
    if %errorlevel% neq 0 (
        echo Failed to install PyQt5. Please check your internet connection and Python setup.
        pause
        exit /b 1
    )
)

REM Run the main.py script using py command
py main.py
if %errorlevel% neq 0 (
    echo Failed to execute main.py. Please check the script for errors.
    pause
    exit /b 1
)

REM Close the command prompt window
exit
