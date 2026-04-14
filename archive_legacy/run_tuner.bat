@echo off
:: ============================================================
::  PHASE 2A — Manual Tuner Launcher
::
::  Aktif hedefler (sırayla çalıştırılır):
::
::  [1] economist.greed_turn_end
::      Hedef: Economist çok erken hoarding yapıyor (GoldEff=0.33)
::      Düşürürsek daha erken harcamaya başlar
::
::  [2] builder.power_weight
::      Hedef: Builder șu an 0.0 — sadece grup uyumuna bakıyor,
::      kart gücünü hiç gözetmiyor (WinRate=%9.1, AvgHP=4.6)
::
::  Sonuçlar:
::    experiments/runs/<run_id>/
::    experiments/best/
::    experiments/last_session.json
::    experiments/registry.json
:: ============================================================

cd /d "%~dp0"
echo.
echo  [launcher] Working dir: %CD%
echo.

set PYTHON=.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo  [launcher] Using: %PYTHON%
echo.

:: ── Hedef 1: Economist greed_turn_end ─────────────────────────────
echo  [launcher] Target 1/2: economist.greed_turn_end
%PYTHON% -m trainer.manual_tuner ^
    --param economist.greed_turn_end ^
    --values 3.0,4.0,5.0,6.0,7.0,8.0

echo.
echo  ── Target 1 complete. Starting Target 2... ────────────────────
echo.

:: ── Hedef 2: Builder power_weight ────────────────────────────────
echo  [launcher] Target 2/2: builder.power_weight
%PYTHON% -m trainer.manual_tuner ^
    --param builder.power_weight ^
    --values 0.2,0.4,0.6,0.8,1.0,1.5

echo.
echo  ============================================================
echo  Sweep complete.  See experiments/last_session.json for results.
echo  ============================================================
pause
