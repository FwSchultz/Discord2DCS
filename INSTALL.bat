@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS Community Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" -Mode Install
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [ERROR] Installation failed / Installation fehlgeschlagen. Code %RC%
    pause
)
exit /b %RC%
