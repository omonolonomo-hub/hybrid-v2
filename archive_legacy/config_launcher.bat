@echo off
setlocal enabledelayedexpansion
title Autochess Hybrid - Builder Config Launcher

cd /d "%~dp0"

:START_MENU
cls
echo ================================================================
echo   BUILDER STRATEGY - PRESET ^& CONFIG MENU (100 GAMES)
echo ================================================================
echo  [1] Aggressive Combo-Econ  [cw:0.8, ggt:12, sbc:4, cbc:5]
echo  [2] Stable Builder-Econ    [cw:0.6, ggt:15, sbc:3, cbc:4]
echo  [3] Conservative Economy   [cw:0.4, ggt:18, sbc:2, cbc:3]
echo  [4] MANUAL ENTRY (Kendi degerlerini gir)
echo ================================================================
echo.

set /p CHOICE="Seciminizi yapin [1-4]: "

if "%CHOICE%"=="1" (
    set CW=0.8
    set GGT=12
    set SBC=4
    set CBC=5
    goto RUN
)
if "%CHOICE%"=="2" (
    set CW=0.6
    set GGT=15
    set SBC=3
    set CBC=4
    goto RUN
)
if "%CHOICE%"=="3" (
    set CW=0.4
    set GGT=18
    set SBC=2
    set CBC=3
    goto RUN
)
if "%CHOICE%"=="4" goto MANUAL

goto START_MENU

:MANUAL
echo.
echo Lutfen test etmek istediginiz parametre araliklarini girin.
echo (Ornek: Birden fazla deger icin araya bosluk birakin: 0.4 0.6)
echo.

set /p CW="1. Combo Weight (cw) girin [Varsayilan: 0.6]: "
if "!CW!"=="" set CW=0.6

set /p GGT="2. Greed Gold Threshold (ggt) girin [Varsayilan: 15]: "
if "!GGT!"=="" set GGT=15

set /p SBC="3. Spike Buy Count (sbc) girin [Varsayilan: 3]: "
if "!SBC!"=="" set SBC=3

set /p CBC="4. Convert Buy Count (cbc) girin [Varsayilan: 4]: "
if "!CBC!"=="" set CBC=4

:RUN
echo.
echo ----------------------------------------------------------------
echo CALISTIRILIYOR: CW:!CW!  GGT:!GGT!  SBC:!SBC!  CBC:!CBC!
echo Mod: 100 Oyun / Run (Hizli Test)
echo ----------------------------------------------------------------
echo.

set PYTHON=.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

%PYTHON% -m trainer.builder_tuner --games 100 --cw !CW! --ggt !GGT! --sbc !SBC! --cbc !CBC!

echo.
echo Test tamamlandi. Menuye donmek icin bir tusa basin.
pause
goto START_MENU
