@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Discord2DCS PC Client - Setup

set "SILENT=0"
if /I "%~1"=="--silent" set "SILENT=1"
set "LANG=%D2DCS_LANG%"
if /I not "%LANG%"=="en" set "LANG=de"

set "PYTHON_VERSION=3.12.10"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\Discord2DCS-python-3.12.10-amd64.exe"
set "PYTHON_EXE="

if "%SILENT%"=="0" (
    echo ==========================================
    echo Discord2DCS PC Client - Setup
    echo ==========================================
    echo.
    echo Python 3.12 ^(64-Bit^) required / benoetigt
    echo.
)

call :find_python312

if not defined PYTHON_EXE (
    echo [INFO] Python 3.12 not found / wurde nicht gefunden.
    echo [INFO] Installing Python %PYTHON_VERSION% automatically from python.org / automatische Installation.
    call :install_python312
    if errorlevel 1 goto :setup_failed
    call :find_python312
    if not defined PYTHON_EXE (
        echo [ERROR] Python 3.12 installed but not found afterwards / installiert, danach nicht gefunden.
        goto :setup_failed
    )
)

echo [OK] Python 3.12 found / gefunden: !PYTHON_EXE!
"!PYTHON_EXE!" --version
if errorlevel 1 goto :setup_failed

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
    if errorlevel 1 (
        echo [INFO] Existing .venv is not Python 3.12; rebuilding / wird neu erstellt.
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating Python environment / Erstelle Python-Umgebung ...
    "!PYTHON_EXE!" -m venv ".venv"
    if errorlevel 1 goto :setup_failed
)

echo [INFO] Updating pip / Aktualisiere pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
if errorlevel 1 goto :setup_failed

echo [INFO] Installing Discord2DCS dependencies / Abhaengigkeiten ...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto :setup_failed

echo [OK] PC client ready / PC-Client eingerichtet.
if "%SILENT%"=="0" pause
exit /b 0

:find_python312
set "PYTHON_EXE="
set "CANDIDATE="

for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do (
    set "CANDIDATE=%%P"
    if exist "!CANDIDATE!" (
        "!CANDIDATE!" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_EXE=!CANDIDATE!"
            exit /b 0
        )
    )
)

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%ProgramFiles%\Python312\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_EXE=%%~P"
            exit /b 0
        )
    )
)

for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do (
    set "CANDIDATE=%%Bpython.exe"
    if exist "!CANDIDATE!" (
        set "PYTHON_EXE=!CANDIDATE!"
        exit /b 0
    )
)
for /f "tokens=2,*" %%A in ('reg query "HKLM\Software\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do (
    set "CANDIDATE=%%Bpython.exe"
    if exist "!CANDIDATE!" (
        set "PYTHON_EXE=!CANDIDATE!"
        exit /b 0
    )
)

for /f "delims=" %%P in ('where python 2^>nul') do (
    echo %%~P | findstr /I /C:"WindowsApps" >nul
    if errorlevel 1 (
        if exist "%%~P" (
            "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
            if not errorlevel 1 (
                set "PYTHON_EXE=%%~P"
                exit /b 0
            )
        )
    )
)
exit /b 0

:install_python312
if exist "%PYTHON_INSTALLER%" del /q "%PYTHON_INSTALLER%" >nul 2>nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'; $sig=Get-AuthenticodeSignature '%PYTHON_INSTALLER%'; if($sig.Status -ne 'Valid'){ throw 'Python-Installer hat keine gueltige digitale Signatur: ' + $sig.Status }"
if errorlevel 1 (
    echo [ERROR] Python download/signature verification failed / Download oder Signaturpruefung fehlgeschlagen.
    exit /b 1
)

start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1 Include_test=0 SimpleInstall=1
set "INSTALL_RC=!errorlevel!"
del /q "%PYTHON_INSTALLER%" >nul 2>nul
if not "!INSTALL_RC!"=="0" (
    echo [ERROR] Python installer failed / Python-Installer fehlgeschlagen. Code !INSTALL_RC!.
    exit /b 1
)
exit /b 0

:setup_failed
echo.
echo [ERROR] PC client setup aborted / Einrichtung abgebrochen.
if "%SILENT%"=="0" pause
exit /b 1
