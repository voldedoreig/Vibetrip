@echo off
title VibeTrip - Nepal Travel Consultation Engine
cd /d "%~dp0"

echo ======================================================================
echo    * * *   VIBETRIP: NEPAL TRAVEL ITINERARY ENGINE   * * *
echo    Kathmandu Valley and Nepal Cultural Personalization Platform
echo ======================================================================
echo.

:: Automatically launch default browser to the web app in 3 seconds
start "" cmd /c "ping 127.0.0.1 -n 4 >nul & start http://127.0.0.1:5000"

echo  * Web Server URL:    http://127.0.0.1:5000
echo.
echo  * Pre-configured Test Accounts:
echo    - Creator Account:  bishesh       / password123
echo    - Demo Traveler:    demo_user_123 / password123
echo.
echo  * Note: Keep this black terminal window OPEN while using the website.
echo  * Press CTRL + C in this window when you want to stop the server.
echo ======================================================================
echo.

:: 1. Check for uv package manager first
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Launching with uv runtime...
    echo.
    uv run python app.py
    goto after_run
)

:: 2. Check for project virtual environment (.venv)
if exist ".venv\Scripts\python.exe" (
    echo [OK] Launching with project virtual environment...
    echo.
    ".venv\Scripts\python.exe" app.py
    goto after_run
)

:: 3. Fallback to system Python
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Launching with system Python...
    echo.
    python app.py
    goto after_run
)

echo.
echo [ERROR] Neither uv nor Python was found on your system!
echo Please ensure Python 3.10+ is installed and added to PATH.
echo.

:after_run
echo.
echo Server has stopped.
pause
