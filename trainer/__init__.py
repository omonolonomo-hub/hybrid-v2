"""
trainer — Phase 2A Manual Tuning Infrastructure
================================================
Experiment-driven parameter tuning pipeline for Autochess Hybrid.

Modules:
    manual_tuner        Orchestrates the full experiment loop
    compare_runs        Compares current run vs baseline; calculates KPI deltas
    fitness             Computes scalar score from KPI deltas
    io_utils            Safe JSON I/O, folder creation, timestamped paths
    experiment_registry Stores run history; tracks best run metadata
"""
