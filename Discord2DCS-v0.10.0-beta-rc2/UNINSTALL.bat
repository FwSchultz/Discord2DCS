@echo off
setlocal
cd /d "%~dp0"
title Discord2DCS Uninstall / Deinstallation
echo Discord2DCS uninstall / deinstallieren?
echo DCS hook, client, autostart and shortcuts will be removed.
echo DCS-Hook, Client, Autostart und Verknuepfungen werden entfernt.
choice /C YN /N /M "Continue / Fortfahren? [Y/N]: "
if errorlevel 2 exit /b 0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" -Mode Uninstall
exit /b %ERRORLEVEL%
