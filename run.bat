@echo off
echo ================================
echo Street Signal - Quick Start
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check if USER_AGENT is configured
findstr /C:"contact@example.com" config.py >nul
if %errorlevel%==0 (
    echo.
    echo ================================
    echo WARNING: Please update USER_AGENT in config.py
    echo ================================
    echo.
)

REM Run the application
echo.
echo Starting Street Signal...
echo Open your browser to: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python app.py
