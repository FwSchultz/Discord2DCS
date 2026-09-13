@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS Update
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" -Mode Update
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [ERROR] Update failed / Update fehlgeschlagen. Code %RC%
    pause
)
exit /b %RC%
