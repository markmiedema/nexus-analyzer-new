@echo off
REM Backend setup script for Windows

echo Setting up Nexus Analyzer Backend...

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Prompt for dev dependencies
set /p INSTALL_DEV="Install development dependencies? (y/n): "
if /i "%INSTALL_DEV%"=="y" (
    pip install -r requirements-dev.txt
)

echo.
echo ✅ Backend setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo To deactivate, run:
echo   deactivate
