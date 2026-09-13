@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS - Sprache / Language
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" -Mode Language
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [OK] Sprache geaendert. DCS bitte neu starten. / Language changed. Please restart DCS.
) else (
  echo [ERROR] Sprache konnte nicht geaendert werden. / Language could not be changed.
)
pause
exit /b %RC%
