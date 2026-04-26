"""
trainer/experiment_registry.py — Persistent run history & best-run tracker
===========================================================================

All metadata is stored in experiments/registry.json.
The registry is append-only for runs; 'best' is overwritten when improved.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .io_utils import safe_read_json, safe_write_json

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT          = Path(__file__).parent.parent
REGISTRY_PATH  = _ROOT / "experiments" / "registry.json"


# ── Internal helpers ────────────────────────────────────────────────────────

def _load() -> Dict[str, Any]:
    data = safe_read_json(REGISTRY_PATH)
    if data is None or not isinstance(data, dict):
        return {"runs": [], "best": None}
    data.setdefault("runs", [])
    data.setdefault("best", None)
    return data


def _save(data: Dict[str, Any]) -> None:
    safe_write_json(REGISTRY_PATH, data)


# ── Public API ───────────────────────────────────────────────────────────────

def register_run(
    run_id:          str,
    params_snapshot: Dict[str, Any],
    fitness:         float,
    kpi_deltas:      Dict[str, Any],
    run_path:        str,
) -> None:
    """Append a run entry and update best-run metadata if fitness improved.

    Parameters
    ----------
    run_id          Unique identifier string for this run.
    params_snapshot Minimal dict of changed params, e.g. {"tempo.power_center_thresh": 55.0}.
    fitness         Scalar score from fitness.compute_fitness().
    kpi_deltas      Full delta report from compare_runs.compare_runs().
    run_path        Absolute path to the run's artifact directory.
    """
    registry = _load()

    tempo_win = (kpi_deltas
                 .get("strategies", {})
                 .get("tempo", {})
                 .get("new_win_rate_pct"))

    entry: Dict[str, Any] = {
        "run_id":          run_id,
        "timestamp":       datetime.now().isoformat(),
        "params_snapshot": params_snapshot,
        "fitness":         fitness,
        "tempo_win_rate":  tempo_win,
        "run_path":        run_path,
        # Compact KPI snapshot for quick comparison without loading full files
        "kpi_snapshot": {
            "delta_win_rate_pct":      (kpi_deltas
                                        .get("strategies", {})
                                        .get("tempo", {})
                                        .get("delta_win_rate_pct")),
            "delta_max_deviation_pct": (kpi_deltas
                                        .get("balance", {})
                                        .get("delta_max_deviation_pct")),
            "delta_crashes":           (kpi_deltas
                                        .get("crashes", {})
                                        .get("delta_crashes")),
        },
    }

    registry["runs"].append(entry)

    # ── Update best ────────────────────────────────────────────────
    current_best = registry.get("best")
    if current_best is None or fitness > current_best.get("fitness", float("-inf")):
        registry["best"] = entry
        print(f"  [registry] 🏆 New best!  fitness={fitness:.4f}  "
              f"tempo_win={tempo_win}%  run={run_id}")

    _save(registry)


def get_best_run() -> Optional[Dict[str, Any]]:
    """Return metadata of the best run so far, or None."""
    return _load().get("best")


def get_all_runs() -> List[Dict[str, Any]]:
    """Return all run entries (oldest first)."""
    return _load().get("runs", [])


def get_run_count() -> int:
    """Return total number of registered runs."""
    return len(get_all_runs())


def print_registry_summary(tail: int = 12) -> None:
    """Print a formatted table of recent runs and the current best."""
    runs = get_all_runs()
    best = get_best_run()

    print(f"\n  ══ Experiment Registry  ({len(runs)} total runs) ══")

    if best:
        print(f"  Best → {best['run_id']}")
        print(f"         fitness={best['fitness']:.4f}  "
              f"tempo_win={best.get('tempo_win_rate', 'N/A')}%  "
              f"{best['timestamp'][:19]}")

    if not runs:
        print("  (no runs yet)")
        return

    recent = runs[-tail:]
    print(f"\n  {'':2}{'Run ID':<36} {'Fitness':>8} {'Tempo%':>8} {'ΔWin%':>7}")
    print(f"  {'─'*64}")
    for r in recent:
        star   = "⭐" if best and r["run_id"] == best["run_id"] else "  "
        snap   = r.get("kpi_snapshot", {})
        d_win  = snap.get("delta_win_rate_pct")
        d_str  = f"{d_win:+.2f}" if d_win is not None else "  N/A"
        t_win  = r.get("tempo_win_rate")
        t_str  = f"{t_win:.1f}" if t_win is not None else "N/A"
        print(f"  {star}{r['run_id']:<34} "
              f"{r['fitness']:>8.4f} "
              f"{t_str:>8} "
              f"{d_str:>7}")
    print()
