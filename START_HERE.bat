@echo off
title WiFi Attendance System — Setup & Start
color 0A

echo.
echo  =====================================================
echo   WiFi Attendance System — S.P. Timber Industries
echo   One-click Setup ^& Start
echo  =====================================================
echo.

:: ── Step 0: Check for Administrator privileges ────────────────────────────
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo  [ERROR] This script must be run as Administrator.
    echo.
    echo  Right-click START_HERE.bat and choose "Run as administrator"
    echo.
    pause
    exit /b 1
)
echo  [OK] Running as Administrator

:: ── Step 1: Check Python ──────────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.10 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During install, tick "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] %PYVER% found

:: ── Step 2: Move to script directory ─────────────────────────────────────
cd /d "%~dp0"
echo  [OK] Working directory: %~dp0

:: ── Step 3: Copy config if not already done ───────────────────────────────
if not exist "config.py" (
    if exist "config.example.py" (
        copy "config.example.py" "config.py" >nul
        echo.
        echo  [ACTION REQUIRED] config.py has been created from the template.
        echo  Please fill in your details now:
        echo    - TELEGRAM_BOT_TOKEN
        echo    - TELEGRAM_CHAT_ID
        echo    - NETWORK_RANGE  (your office WiFi subnet, e.g. 192.168.1.0/24)
        echo    - DASHBOARD_PASSWORD
        echo.
        echo  Opening config.py in Notepad...
        notepad config.py
        echo.
        echo  Press any key once you have saved config.py to continue setup.
        pause >nul
    ) else (
        echo  [WARNING] config.py not found and no config.example.py to copy from.
        echo  Please create config.py manually before running.
        pause
        exit /b 1
    )
) else (
    echo  [OK] config.py already exists
)

:: ── Step 4: Install Python dependencies ──────────────────────────────────
echo.
echo  [STEP] Installing Python dependencies...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo  [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed

:: ── Step 5: Create data and logs directories ──────────────────────────────
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo  [OK] data\ and logs\ directories ready

:: ── Step 6: Register Windows Task Scheduler (auto-start on boot) ─────────
echo.
echo  [STEP] Registering Windows startup task...

for /f "delims=" %%i in ('where python') do set PYTHON_EXE=%%i
set MAIN_PY=%~dp0main.py

:: Remove old task silently
schtasks /delete /tn "WiFiAttendance" /f >nul 2>&1

schtasks /create ^
  /tn "WiFiAttendance" ^
  /tr "\"%PYTHON_EXE%\" \"%MAIN_PY%\"" ^
  /sc ONSTART ^
  /ru SYSTEM ^
  /rl HIGHEST ^
  /f >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo  [OK] Startup task registered — system will auto-start on every reboot
) else (
    echo  [WARNING] Could not register startup task ^(non-fatal^)
    echo            You can start the system manually with: python main.py
)

:: ── Step 7: Start the app now ────────────────────────────────────────────
echo.
echo  =====================================================
echo   Setup complete! Starting WiFi Attendance System...
echo  =====================================================
echo.
echo  Dashboard will be available at:
echo    http://localhost:47832
echo.
echo  Default password: as set in config.py
echo.
echo  To stop the system, close this window.
echo.

:: Run the app (in foreground so the window stays open and shows logs)
python main.py

pause
