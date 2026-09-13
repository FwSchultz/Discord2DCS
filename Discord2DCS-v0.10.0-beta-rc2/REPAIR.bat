@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS Repair / Reparatur
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" -Mode Repair
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo [OK] Repair completed / Reparatur abgeschlossen.) else (echo [ERROR] Repair failed / Reparatur fehlgeschlagen. Code %RC%)
pause
exit /b %RC%
