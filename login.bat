@echo off
setlocal EnableExtensions

cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title Gift Sender Login

echo.
echo Gift Sender Login
echo =================
echo.

if not exist "config.py" (
    copy /Y "config.example.py" "config.py" >nul
    echo [SETUP] Created config.py from config.example.py.
    echo Fill in Telegram credentials and ADMIN_IDS, then run login.bat again.
    pause
    exit /b 1
)

set "BOOTSTRAP_PY="
where py >nul 2>&1
if not errorlevel 1 (
    set "BOOTSTRAP_PY=py -3"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PY=python"
)

if not defined BOOTSTRAP_PY (
    echo [ERROR] Python 3 was not found.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating local virtual environment...
    %BOOTSTRAP_PY% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        pause
        exit /b 1
    )
)

set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"

echo [SETUP] Installing dependencies into .venv...
set "NO_PROXY=*"
set "no_proxy=*"
"%PYTHON_CMD%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)
set "NO_PROXY="
set "no_proxy="

"%PYTHON_CMD%" "%~dp0login.py"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%
