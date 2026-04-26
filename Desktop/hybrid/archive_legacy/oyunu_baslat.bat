@echo off
del "%~dp0_tmp_origin.py" 2>nul
del "%~dp0_cleanup.bat" 2>nul
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -c "import pygame" >nul 2>&1 || pip install pygame
python main.py
if errorlevel 1 ( echo. & echo [HATA] Yukaridaki mesaji kontrol edin. & pause )
