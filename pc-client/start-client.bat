@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS PC Client

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] PC client is not set up yet / PC-Client noch nicht eingerichtet. Starting setup ...
    call "%~dp0setup-client.bat" --silent
    if errorlevel 1 (
        echo [ERROR] Automatic setup failed / Automatische Einrichtung fehlgeschlagen.
        pause
        exit /b 1
    )
)

if not exist "config.json" (
    echo [ERROR] config.json missing / fehlt. Please run / Bitte INSTALL.bat ausfuehren.
    pause
    exit /b 1
)

echo ==========================================
echo Discord2DCS PC Client
echo ==========================================
echo.
".venv\Scripts\python.exe" client.py

echo.
echo Discord2DCS stopped / wurde beendet.
pause
