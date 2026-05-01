@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] .venv Python was not found.
    echo Expected: "%PYTHON_EXE%"
    echo.
    echo Create the project virtual environment with:
    echo   py -3.13 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] This project venv must use Python 3.13.
    "%PYTHON_EXE%" --version
    echo.
    echo Recreate it with:
    echo   rmdir /s /q .venv
    echo   py -3.13 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" v2\main.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Game exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
