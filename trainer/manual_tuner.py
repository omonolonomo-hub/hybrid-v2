"""
trainer/manual_tuner.py — Phase 2A Experiment Orchestrator
===========================================================

Runs a controlled parameter-sweep loop for one AI parameter at a time.

Usage (run from the project root)
----------------------------------
    python -m trainer.manual_tuner
    python -m trainer.manual_tuner --param tempo.power_center_thresh --values 50,55,60,65,70
    python -m trainer.manual_tuner --step 5 --count 6
    python -m trainer.manual_tuner --force-baseline

Contract
--------
* NEVER modifies engine_core/ai.py
* NEVER modifies gameplay logic
* Only writes to: trained_params.json, experiments/

Flow per experiment
-------------------
1. Deep-copy baseline params
2. Mutate one parameter (dot-notation key)
3. Write mutated dict → trained_params.json   (ParameterizedAI reads this)
4. Run sim1000.py via subprocess
5. Load output/results/sim1000_summary.json
6. compare_runs() → KPI deltas
7. compute_fitness() → scalar score
8. Save artifacts to experiments/runs/<run_id>/
9. Register in experiment_registry
10. (after all runs) Restore trained_params.json to baseline
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── Path bootstrap (allow `python trainer/manual_tuner.py` as well) ────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from trainer.io_utils            import (safe_read_json, safe_write_json,
                                         ensure_dirs, copy_json)
from trainer.compare_runs        import compare_runs, format_delta_report
from trainer.fitness             import compute_fitness, score_label, PRIMARY_STRATEGY
from trainer.experiment_registry import (register_run, print_registry_summary,
                                         get_best_run)

# ── Key paths ────────────────────────────────────────────────────────────────
EXPERIMENTS  = ROOT / "experiments"
BASELINE_DIR = EXPERIMENTS / "baseline"
RUNS_DIR     = EXPERIMENTS / "runs"
BEST_DIR     = EXPERIMENTS / "best"
PARAMS_JSON  = ROOT / "trained_params.json"
SIM_SCRIPT   = ROOT / "sim1000.py"
SIM_OUTPUT   = ROOT / "output" / "results" / "sim1000_summary.json"

# ── Baseline parameter snapshot ──────────────────────────────────────────────
# Mirrors TRAINED_PARAMS hardcoded in engine_core/ai.py.
# DO NOT touch engine_core/ai.py — this dict is the single source of truth
# for the tuner's baseline.  Kept in sync manually.
BASELINE_PARAMS: Dict[str, Any] = {
    "economist": {
        "thresh_high":          27.012525825899594,
        "thresh_mid":            5.887870123764179,
        "thresh_low":           11.572130722067811,
        "buy_2_thresh":         15.0,
        "greed_turn_end":        5.0,                # TRAINED CONSTANT — EXP003 winner, fitness=3.3 EXCELLENT
        "spike_turn_end":       14.773731014667712,
        "greed_gold_thresh":    15.0,
        "spike_r4_thresh":      42.07452062733782,
        "convert_r5_thresh":    80.0,
        "spike_buy_count":       3.1891953600814538,
        "convert_buy_count":     3.6086842743641023,
    },
    "warrior":     {"power_weight": 1.0, "rarity_weight": 0.0},
    "builder":     {"group_weight": 1.0, "power_weight": 0.0},
    "evolver":     {
        "evo_near_bonus":     1000.0,
        "evo_one_bonus":       500.0,
        "rarity_weight_mult":   10.0,
        "power_weight":          1.0,
    },
    "balancer":    {"group_bonus": 5.0, "group_thresh": 3.0, "power_weight": 1.0},
    "rare_hunter": {"fallback_rarity": 3.0},
    "tempo":       {"power_center_thresh": 45.0, "combo_center_weight": 1.5},
    "random":      {},
}


# ── Persistent best-params loader ───────────────────────────────────────────

def load_best_so_far() -> Dict[str, Any]:
    """Load trained_params.json as the live starting baseline.

    This makes every tuner run a continuation of the previous one:
    the file accumulates knowledge instead of being reset each session.

    Falls back to the hardcoded BASELINE_PARAMS dict if the file is absent
    or unreadable (first-ever run).
    """
    data = safe_read_json(PARAMS_JSON)
    if data:
        print(f"  [tuner] 📂 Loaded previous best from trained_params.json "
              f"— continuing where we left off")
        return data
    print(f"  [tuner] ℹ️  trained_params.json not found "
          f"— starting from hardcoded baseline")
    import copy as _copy
    return _copy.deepcopy(BASELINE_PARAMS)


# ── Dot-notation helpers ─────────────────────────────────────────────────────

def _nested_set(d: Dict, dotkey: str, value: Any) -> Dict:
    """Set d[a][b][c] = value given dotkey='a.b.c'. Mutates and returns d."""
    parts = dotkey.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value
    return d


def _nested_get(d: Dict, dotkey: str, default: Any = None) -> Any:
    """Get d[a][b][c] given dotkey='a.b.c'. Returns default if missing."""
    cur = d
    for p in dotkey.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


# ── Simulation runner ─────────────────────────────────────────────────────────

def _run_sim(timeout: int = 900) -> bool:
    """Launch sim1000.py in a subprocess. Returns True on clean exit."""
    print(f"  [tuner] 🚀 Launching {SIM_SCRIPT.name} ...")
    t0 = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(SIM_SCRIPT)],
            cwd=str(ROOT),
            timeout=timeout,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"  [tuner] ❌ sim1000.py returned exit code {result.returncode}")
            return False
        print(f"  [tuner] ✅ Done in {elapsed:.1f}s")
        return True
    except subprocess.TimeoutExpired:
        print(f"  [tuner] ❌ Timed out after {timeout}s")
        return False
    except Exception as exc:
        print(f"  [tuner] ❌ Subprocess error: {exc}")
        return False


# ── Artifact persistence ──────────────────────────────────────────────────────

def _save_run_artifacts(run_id: str, params: Dict, kpi_deltas: Dict,
                        fitness: float, sim_summary: Dict) -> Path:
    """Persist all artifacts for one experiment run. Returns the run directory."""
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    safe_write_json(run_dir / "params.json",      params)
    safe_write_json(run_dir / "kpi_deltas.json",  kpi_deltas)
    safe_write_json(run_dir / "sim_summary.json", sim_summary)
    safe_write_json(run_dir / "score.json", {
        "run_id":    run_id,
        "fitness":   fitness,
        "label":     score_label(fitness),
        "timestamp": datetime.now().isoformat(),
        "tempo_win_rate": (kpi_deltas
                           .get("strategies", {})
                           .get(PRIMARY_STRATEGY, {})
                           .get("new_win_rate_pct")),
    })
    return run_dir


def _maybe_promote_to_best(run_dir: Path,
                           fitness: float,
                           mutated_params: Dict[str, Any],
                           param_key: str = "",
                           candidate_value: float = 0.0) -> bool:
    """Promote this run if it beats the current best.

    Three things happen when a new best is found:
    1. experiments/best/ is replaced with this run's artifacts.
    2. A timestamped snapshot is archived under experiments/best/archive/
       so no history is ever lost.
    3. trained_params.json is immediately updated with the winning params,
       making the improvement durable across sessions.
    """
    score_file = BEST_DIR / "score.json"
    current_best_fitness = float("-inf")

    if score_file.exists():
        stored = safe_read_json(score_file)
        if stored:
            current_best_fitness = stored.get("fitness", float("-inf"))

    if fitness <= current_best_fitness:
        return False

    # ── 1. Overwrite experiments/best/ ────────────────────────────
    if BEST_DIR.exists():
        shutil.rmtree(BEST_DIR)
    shutil.copytree(run_dir, BEST_DIR)
    print(f"  [tuner] 🏆 New best promoted → experiments/best/")

    # ── 2. Timestamped archive snapshot ───────────────────────────
    archive_dir = BEST_DIR.parent / "best_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug     = param_key.replace(".", "_")
    val_slug = f"{candidate_value:.2f}".replace(".", "p")
    fit_slug = f"{fitness:.3f}".replace(".", "p")
    snap_name = f"{ts}_{slug}_{val_slug}_fit{fit_slug}"
    snap_dir  = archive_dir / snap_name
    shutil.copytree(run_dir, snap_dir)
    print(f"  [tuner] 📸 Snapshot archived → experiments/best_archive/{snap_name}")

    # ── 3. Persist winning params to trained_params.json immediately ─
    if safe_write_json(PARAMS_JSON, mutated_params):
        print(f"  [tuner] 💾 trained_params.json updated with new best params")
    else:
        print(f"  [tuner] ⚠️  Could not update trained_params.json")

    return True


# ── Single experiment ─────────────────────────────────────────────────────────

def run_experiment(
    param_key:        str,
    candidate_value:  float,
    baseline_params:  Dict,
    baseline_summary: Dict,
    run_index:        int,
) -> Dict[str, Any]:
    """Execute one full experiment cycle.

    Returns a result dict with keys:
        run_id, param_key, candidate_value, fitness,
        tempo_win_rate, delta_win_rate, run_dir, error (optional)
    """
    # ── Build run ID ───────────────────────────────────────────────
    param_slug = param_key.replace(".", "_")
    val_slug   = f"{candidate_value:.2f}".replace(".", "p")
    ts_slug    = datetime.now().strftime("%H%M%S")
    run_id     = f"run_{run_index:03d}_{param_slug}_{val_slug}_{ts_slug}"

    print(f"\n  {'═' * 62}")
    print(f"  EXP {run_index:03d}  {param_key} = {candidate_value}")
    print(f"  ID : {run_id}")
    print(f"  {'─' * 62}")

    # ── 1. Mutate params ───────────────────────────────────────────
    mutated = copy.deepcopy(baseline_params)
    _nested_set(mutated, param_key, candidate_value)

    # ── 2. Write trained_params.json ──────────────────────────────
    if not safe_write_json(PARAMS_JSON, mutated):
        print(f"  [tuner] ❌ Could not write {PARAMS_JSON} — skipping")
        return {"run_id": run_id, "fitness": -99.0, "error": "write_failed"}
    print(f"  [tuner] ✍  trained_params.json  ← {param_key} = {candidate_value}")

    # ── 3. Run simulation ─────────────────────────────────────────
    if not _run_sim():
        return {"run_id": run_id, "fitness": -99.0, "error": "sim_failed"}

    # ── 4. Load sim output ────────────────────────────────────────
    sim_summary = safe_read_json(SIM_OUTPUT)
    if sim_summary is None:
        print(f"  [tuner] ❌ Output not found: {SIM_OUTPUT}")
        return {"run_id": run_id, "fitness": -99.0, "error": "no_output"}

    # ── 5. Compare vs baseline ────────────────────────────────────
    kpi_deltas = compare_runs(baseline_summary, sim_summary)

    # ── 6. Compute fitness ────────────────────────────────────────
    fitness = compute_fitness(kpi_deltas, PRIMARY_STRATEGY)

    # ── 7. Print delta report ─────────────────────────────────────
    print(format_delta_report(kpi_deltas, PRIMARY_STRATEGY))
    print(f"\n  [result] fitness = {fitness:.4f}  {score_label(fitness)}")

    # ── 8. Save artifacts ─────────────────────────────────────────
    run_dir  = _save_run_artifacts(run_id, mutated, kpi_deltas, fitness, sim_summary)
    copy_json(SIM_OUTPUT, run_dir / "sim1000_summary.json")
    promoted = _maybe_promote_to_best(
        run_dir, fitness, mutated,
        param_key=param_key, candidate_value=candidate_value,
    )

    # ── 9. Register ───────────────────────────────────────────────
    register_run(
        run_id=run_id,
        params_snapshot={param_key: candidate_value},
        fitness=fitness,
        kpi_deltas=kpi_deltas,
        run_path=str(run_dir),
    )

    tempo_delta = kpi_deltas.get("strategies", {}).get(PRIMARY_STRATEGY, {})
    return {
        "run_id":          run_id,
        "param_key":       param_key,
        "candidate_value": candidate_value,
        "fitness":         fitness,
        "tempo_win_rate":  tempo_delta.get("new_win_rate_pct"),
        "delta_win_rate":  tempo_delta.get("delta_win_rate_pct"),
        "run_dir":         str(run_dir),
        "promoted":        promoted,          # True → this run became new best
        "mutated_params":  mutated,           # full param dict for this run
    }


# ── Baseline setup ────────────────────────────────────────────────────────────

def setup_baseline(force: bool = False,
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ensure a valid baseline summary exists.

    * If experiments/baseline/sim_summary.json is present and force=False,
      loads and returns it (fast path — no re-simulation needed).
    * Otherwise writes `params` (or BASELINE_PARAMS as fallback) →
      trained_params.json, runs sim1000.py, and caches the output.

    The `params` argument should be the output of load_best_so_far() so
    that the baseline always reflects the most recent known-good state.

    Returns the baseline sim summary dict.
    Raises RuntimeError if the simulation fails.
    """
    baseline_summary_path = BASELINE_DIR / "sim_summary.json"
    baseline_params_path  = BASELINE_DIR / "params.json"
    effective_params      = params if params is not None else BASELINE_PARAMS

    if not force and baseline_summary_path.exists():
        cached = safe_read_json(baseline_summary_path)
        if cached is not None:
            tempo_win = (cached.get("strategies", {})
                               .get("tempo", {})
                               .get("win_rate_pct", "?"))
            print(f"  [tuner] ✅ Baseline loaded from cache "
                  f"(tempo win_rate = {tempo_win}%)")
            return cached
        print(f"  [tuner] ⚠️  Cached baseline file is corrupt — re-running")

    print(f"\n  {'═' * 62}")
    print(f"  BASELINE RUN")
    print(f"  {'─' * 62}")

    ensure_dirs(BASELINE_DIR, RUNS_DIR, BEST_DIR)

    safe_write_json(PARAMS_JSON,          effective_params)
    safe_write_json(baseline_params_path, effective_params)
    pct_thresh = (effective_params.get("tempo", {})
                                  .get("power_center_thresh", "?"))
    print(f"  [tuner] ✍  Baseline params written "
          f"(tempo.power_center_thresh = {pct_thresh})")

    if not _run_sim():
        raise RuntimeError("Baseline simulation failed — cannot proceed with tuning")

    sim_summary = safe_read_json(SIM_OUTPUT)
    if sim_summary is None:
        raise RuntimeError(f"Baseline output missing: {SIM_OUTPUT}")

    copy_json(SIM_OUTPUT, baseline_summary_path)

    tempo_win = (sim_summary.get("strategies", {})
                             .get("tempo", {})
                             .get("win_rate_pct", "?"))
    print(f"  [tuner] 📊 Baseline tempo win_rate = {tempo_win}%")
    print(f"  [tuner] 💾 Saved → experiments/baseline/")

    return sim_summary


# ── Candidate list builders ───────────────────────────────────────────────────

def build_candidates_grid(base_val: float, step: float, count: int) -> List[float]:
    """Return a sorted list of candidate values around base_val.

    Generates `count` steps in each direction (up + down), deduplicates,
    removes non-positive values, and returns sorted unique candidates.
    """
    candidates: List[float] = []
    for i in range(1, count + 1):
        candidates.append(round(base_val + step * i, 4))
        candidates.append(round(base_val - step * i, 4))
    # Remove non-positive and deduplicate
    return sorted({c for c in candidates if c > 0})


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 2A — Manual Tuning Orchestrator",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--param", default="tempo.power_center_thresh",
        help="Dot-notation parameter key  (default: tempo.power_center_thresh)",
    )
    parser.add_argument(
        "--values", default=None,
        help="Comma-separated explicit candidate values,\n"
             "e.g. '50,55,60,65,70'  (overrides --step / --count)",
    )
    parser.add_argument(
        "--step", type=float, default=5.0,
        help="Grid-search step size  (default: 5.0)",
    )
    parser.add_argument(
        "--count", type=int, default=6,
        help="Number of steps in each direction  (default: 6)",
    )
    parser.add_argument(
        "--force-baseline", action="store_true",
        help="Re-run baseline simulation even if a cached result exists",
    )
    args = parser.parse_args()

    # ── Header ────────────────────────────────────────────────────
    print("=" * 65)
    print("  PHASE 2A — Manual Tuning Infrastructure")
    print("=" * 65)
    print(f"  Param  : {args.param}")
    print(f"  Root   : {ROOT}")
    print(f"  Output : {EXPERIMENTS}")
    print()

    ensure_dirs(BASELINE_DIR, RUNS_DIR, BEST_DIR)

    # ── Step 0: Load accumulated knowledge ───────────────────────
    # This is the key change: instead of always starting from the
    # hardcoded BASELINE_PARAMS, we load whatever the best
    # trained_params.json currently says.  Every session is a
    # continuation — no hard-earned gains are thrown away.
    current_params: Dict[str, Any] = load_best_so_far()
    session_best_params: Optional[Dict[str, Any]] = None   # tracks in-session improvements

    # ── Step 1: Baseline ──────────────────────────────────────────
    baseline_summary = setup_baseline(force=args.force_baseline,
                                      params=current_params)

    # ── Step 2: Candidate values ──────────────────────────────────
    base_val = _nested_get(current_params, args.param)
    if base_val is None:
        print(f"  [tuner] ❌ Unknown param key: {args.param}")
        sys.exit(1)

    if args.values:
        candidates = [float(v.strip()) for v in args.values.split(",")]
    else:
        candidates = build_candidates_grid(base_val, args.step, args.count)

    print(f"\n  Baseline value : {base_val}")
    print(f"  Candidates     : {candidates}")
    print(f"  Total runs     : {len(candidates)}")
    t_total = time.time()

    # ── Step 3: Experiment loop ───────────────────────────────────
    results: List[Dict[str, Any]] = []

    for idx, val in enumerate(candidates, start=1):
        result = run_experiment(
            param_key        = args.param,
            candidate_value  = val,
            baseline_params  = current_params,   # ← live params, not hardcoded
            baseline_summary = baseline_summary,
            run_index        = idx,
        )
        results.append(result)

        # Track the best params found so far this session
        if result.get("promoted") and result.get("mutated_params"):
            session_best_params = result["mutated_params"]

    # ── Step 4: Persist best-known params ───────────────────────
    # If we found a new best this session, trained_params.json was
    # already written by _maybe_promote_to_best().  If not, we write
    # back the params we started with (no regression).
    if session_best_params is not None:
        print(f"\n  [tuner] ✅ Session improved — "
              f"trained_params.json already holds new best params")
    else:
        safe_write_json(PARAMS_JSON, current_params)
        print(f"\n  [tuner] ↩️  No improvement this session — "
              f"trained_params.json restored to session-start values")

    # ── Step 5: Session summary ───────────────────────────────────
    elapsed_total = time.time() - t_total
    valid = [r for r in results if r.get("fitness", -99) > -90]

    print(f"\n  {'═' * 65}")
    print(f"  TUNING COMPLETE — {len(results)} experiments  "
          f"({elapsed_total / 60:.1f} min total)")
    print(f"  {'─' * 65}")

    if valid:
        sorted_valid = sorted(valid, key=lambda r: r["fitness"], reverse=True)
        best         = sorted_valid[0]

        header = (f"  {'#':<4} {'Value':>8}  {'Tempo Win%':>11}  "
                  f"{'ΔWin%':>7}  {'Fitness':>9}  Label")
        print(header)
        print(f"  {'─' * 65}")
        for rank, r in enumerate(sorted_valid, 1):
            star  = "⭐" if r["run_id"] == best["run_id"] else "  "
            d_win = r.get("delta_win_rate")
            d_str = f"{d_win:+.2f}" if d_win is not None else "  N/A"
            t_win = r.get("tempo_win_rate")
            t_str = f"{t_win:.1f}" if t_win is not None else " N/A"
            print(f"  {star}{rank:<3} {r['candidate_value']:>8.2f}  "
                  f"{t_str:>11}  {d_str:>7}  "
                  f"{r['fitness']:>9.4f}  {score_label(r['fitness'])}")

        print(f"\n  Recommended value : {args.param} = {best['candidate_value']}")
        print(f"  Best fitness      : {best['fitness']:.4f}  "
              f"{score_label(best['fitness'])}")
        print(f"  Best tempo win%   : {best.get('tempo_win_rate', 'N/A')}")

        # Persist session summary
        session = {
            "param_key":            args.param,
            "base_value":           base_val,
            "best_value":           best["candidate_value"],
            "best_fitness":         best["fitness"],
            "best_tempo_win_rate":  best.get("tempo_win_rate"),
            "candidates_tested":    candidates,
            "all_results":          results,
            "timestamp":            datetime.now().isoformat(),
            "total_elapsed_secs":   round(elapsed_total, 1),
        }
        safe_write_json(EXPERIMENTS / "last_session.json", session)
        print(f"\n  Session saved → experiments/last_session.json")
    else:
        print("  ⚠️  No valid results — check sim errors above")

    print_registry_summary()
    print()


if __name__ == "__main__":
    main()
