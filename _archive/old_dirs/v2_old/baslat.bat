@echo off
cd /d "%~dp0"
echo [Hybrid v2] Baslatiliyor...
echo.

:: pygame_gui yuklu mu kontrol et
python -c "import pygame_gui" 2>nul
if errorlevel 1 (
    echo pygame_gui bulunamadi, yukleniyor...
    pip install pygame_gui
)

python main.py
pause
