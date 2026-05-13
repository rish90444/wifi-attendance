@echo off
:: WiFi Attendance System — Windows Task Scheduler Setup
:: Run this file as Administrator (one time only).

echo ============================================
echo  WiFi Attendance System — Task Scheduler
echo ============================================
echo.

:: Detect Python path automatically
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i

if "%PYTHON_PATH%"=="" (
    echo ERROR: Python not found in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Get the directory of this batch file (= project root)
set PROJECT_DIR=%~dp0
set MAIN_PY=%PROJECT_DIR%main.py

echo Python  : %PYTHON_PATH%
echo Project : %PROJECT_DIR%
echo Script  : %MAIN_PY%
echo.

:: Delete existing task if it exists (ignore error)
schtasks /delete /tn "WiFiAttendance" /f >nul 2>&1

:: Create the scheduled task
schtasks /create ^
  /tn "WiFiAttendance" ^
  /tr "\"%PYTHON_PATH%\" \"%MAIN_PY%\"" ^
  /sc ONSTART ^
  /ru SYSTEM ^
  /rl HIGHEST ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task created successfully!
    echo The system will start automatically on every Windows startup.
    echo.
    echo To start it now without rebooting, run:
    echo   schtasks /run /tn "WiFiAttendance"
    echo.
    echo To check status:
    echo   schtasks /query /tn "WiFiAttendance"
) else (
    echo.
    echo ERROR: Could not create task. Make sure you are running as Administrator.
)

pause
