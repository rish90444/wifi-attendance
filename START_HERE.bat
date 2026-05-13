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

:: ── Step 2: Move to script directory 