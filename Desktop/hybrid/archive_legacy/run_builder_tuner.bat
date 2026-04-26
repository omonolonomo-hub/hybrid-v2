@echo off
:: ================================================================
::  BUILDER TEST SET - 64-Run Combo+Survival Sweep Launcher
::
::  LOCKED:
::    economist.greed_turn_end = 5.0
::
::  DEFAULT SWEEP:
::    builder.combo_weight       [0.5, 0.6, 0.7, 0.8]
::    builder.greed_gold_thresh  [8, 10, 12, 14]
::    builder.spike_buy_count    [1, 2]
::    builder.convert_buy_count  [2, 3]
::
::  FITNESS:
::    win_rate * 0.5 + avg_kill * 0.3 + avg_hp * 0.2
::
::  OUTPUT:
::    experiments/builder_phase2b_testset/runs/<run_id>/
::    experiments/builder_phase2b_testset/best/
::    experiments/builder_phase2b_testset/registry.json
::    experiments/builder_phase2b_testset/last_session.json
::    experiments/builder_phase2b_testset/test_grid.json
::    experiments/builder_phase2b_testset/test_grid.csv
:: ================================================================

cd /d "%~dp0"
echo.
echo  ================================================================
echo  BUILDER TEST SET -- 64-Run Combo+Survival Sweep
echo  economist.greed_turn_end = 5.0  [LOCKED]
echo  Fitness = win_rate*0.5 + avg_kill*0.3 + avg_hp*0.2
echo  ================================================================
echo.

set PYTHON=.venv\Scripts\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo  [launcher] Python : %PYTHON%
echo  [launcher] Root   : %CD%
echo  [launcher] Args   : %*
echo.

%PYTHON% -m trainer.builder_tuner %*

echo.
echo  ================================================================
echo  Builder test set complete.
echo  Best params  -> trained_params.json
echo  Full results -> experiments/builder_phase2b_testset/last_session.json
echo  ================================================================
pause
