"""
trainer/builder_tuner.py — Phase 2B Builder Multi-Parameter Grid Sweep
=======================================================================

4D factorial grid sweep for the builder strategy.

Locked params (do NOT touch):
    economist.greed_turn_end = 5.0   (EXP003 winner, fitness 3.3 EXCELLENT)

Sweep space:
    builder.combo_weight       [0.4, 0.6, 0.8, 1.0]
    builder.greed_gold_thresh  [12,  15,  18,  21 ]
    builder.spike_buy_count    [1,   2,   3,   4  ]
    builder.convert_buy_count  [2,   3,   4,   5  ]

Total: 4^4 = 256 runs x 1000 games = 256 000 simulated games

Success condition:
    builder win_rate > 10.5%
    AND builder avg_kill > 7.5
    AND runtime_per_run < 500s

Usage (from project root):
    python -m trainer.builder_tuner
    python -m trainer.builder_tuner --dry-run          # print grid, no sims
    python -m trainer.builder_tuner --resume           # skip already-done runs
    python -m trainer.builder_tuner --top 20           # print top 20 at end
    python -m trainer.builder_tuner --games 100 --cw 0.6 --ggt 15 --sbc 3 --cbc 4
    python -m trainer.builder_tuner --games 100 --cw 0.4 0.8 --ggt 12 18 --sbc 2 3 --cbc 3 4
"""

from __future__ import annotations

import argparse
import csv
import copy
import itertools
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from trainer.io_utils import safe_read_json, safe_write_json, ensure_dirs

# ── Paths ─────────────────────────────────────────────────────────────────────
PARAMS_JSON    = ROOT / "trained_params.json"
SIM_SCRIPT     = ROOT / "sim1000.py"
SIM_OUTPUT     = ROOT / "output" / "results" / "sim1000_summary.json"
PHASE_DIR      = ROOT / "experiments" / "builder_phase2b_testset"
RUNS_DIR       = PHASE_DIR / "runs"
BEST_DIR       = PHASE_DIR / "best"
ARCHIVE_DIR    = PHASE_DIR / "best_archive"
REGISTRY_FILE  = PHASE_DIR / "registry.json"
SESSION_FILE   = PHASE_DIR / "last_session.json"
GRID_JSON      = PHASE_DIR / "test_grid.json"
GRID_CSV       = PHASE_DIR / "test_grid.csv"

# ── Locked constant ───────────────────────────────────────────────────────────
LOCKED_PARAMS = {
    "economist": {"greed_turn_end": 5.0},   # EXP003 winner — DO NOT SWEEP
}

# ── Sweep grid definition ─────────────────────────────────────────────────────
GRID: Dict[str, List[float]] = {
    "builder.combo_weight":    [0.4, 0.6, 0.8, 1.0],
    "builder.greed_turn_end":  [3.0, 5.0, 7.0, 9.0],
    "builder.spike_buy_count":   [1.0, 2.0],
    "builder.convert_buy_count": [2.0, 3.0],
}

# ── Success thresholds ────────────────────────────────────────────────────────
SUCCESS_WIN_RATE  = 10.5    # builder win_rate_pct must exceed this
SUCCESS_AVG_KILL  = 7.5     # builder avg_kills must exceed this
EARLY_STOP_WIN    = 8.5     # (informational — enforced inside sim via --games 300)
DURATION_LIMIT_S  = 500.0   # per-run simulation wall-clock limit

# ── Fitness weights ───────────────────────────────────────────────────────────
W_WIN_RATE   = 0.5
W_AVG_KILL   = 0.3
W_AVG_HP     = 0.2


# ==============================================================================
# Helpers
# ==============================================================================

def _nested_set(d: Dict, dotkey: str, value: Any) -> Dict:
    parts = dotkey.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value
    return d


def _combo_slug(combo: Dict[str, float]) -> str:
    """Compact string key for a parameter combo, used as run-id suffix."""
    parts = []
    for k, v in sorted(combo.items()):
        short_k = k.split(".")[-1][:6]
        val_s   = f"{v:.2f}".replace(".", "p")
        parts.append(f"{short_k}{val_s}")
    return "_".join(parts)


def _run_id(combo: Dict[str, float], idx: int) -> str:
    """Stable builder test-set run id."""
    cw  = int(round(combo["builder.combo_weight"] * 100))
    gte = int(round(combo["builder.greed_turn_end"]))
    sbc = int(round(combo["builder.spike_buy_count"]))
    cbc = int(round(combo["builder.convert_buy_count"]))
    return (
        f"b2b_test_combo{cw:02d}_gte{gte:02d}_"
        f"spike{sbc}_copy{cbc}_{idx:03d}"
    )


def _write_grid_manifest(combos: List[Dict[str, float]]) -> None:
    """Persist the planned test grid as JSON and CSV for inspection."""
    rows = []
    for idx, combo in enumerate(combos, 1):
        rows.append({
            "index": idx,
            "cw":  combo["builder.combo_weight"],
            "gte": combo["builder.greed_turn_end"],
            "sbc": combo["builder.spike_buy_count"],
            "cbc": combo["builder.convert_buy_count"],
            "run_id": _run_id(combo, idx),
        })

    safe_write_json(GRID_JSON, {
        "notes": {
            "goal": "aggressive combo + survivability + passive efficiency",
            "fitness": "win_rate*0.5 + avg_kill*0.3 + avg_hp*0.2",
            "passive_priority": {
                "early": ["Isaac Newton", "Frida Kahlo"],
                "mid": ["Space-Time", "Event Horizon"],
                "late": ["Narwhal", "Anubis"],
            },
        },
        "runs": rows,
    })

    GRID_CSV.parent.mkdir(parents=True, exist_ok=True)
    with GRID_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["index", "cw", "gte", "sbc", "cbc", "run_id"])
        writer.writeheader()
        writer.writerows(rows)


def _build_mutated_params(base: Dict, combo: Dict[str, float]) -> Dict:
    """Deep-copy base params, apply locked constants, then overlay sweep combo."""
    mutated = copy.deepcopy(base)
    mutated.setdefault("builder", {}).pop("high_rarity_bonus", None)
    mutated.setdefault("builder", {}).pop("group_weight", None)
    mutated.setdefault("builder", {}).pop("gold_spend_threshold", None)
    for strat, overrides in LOCKED_PARAMS.items():
        for k, v in overrides.items():
            mutated.setdefault(strat, {})[k] = v
    for dotkey, value in combo.items():
        _nested_set(mutated, dotkey, value)
    return mutated


def _extract_builder_kpis(summary: Dict) -> Dict[str, float]:
    """Pull builder KPIs from sim1000_summary.json."""
    b = summary.get("strategies", {}).get("builder", {})
    return {
        "win_rate":        b.get("win_rate_pct",  0.0),
        "avg_kill":        b.get("avg_kills",     0.0),
        "avg_hp":          b.get("avg_final_hp",  0.0),
        "avg_damage":      b.get("avg_damage",    0.0),
        "gold_efficiency": b.get("avg_eco_eff",   0.0),
        "avg_synergy":     b.get("avg_synergy",   0.0),
    }


def _compute_fitness(summary: Dict, elapsed: float) -> Tuple[float, Dict]:
    """Compute the lightweight builder test-set fitness."""
    kpis = _extract_builder_kpis(summary)

    win_term = kpis["win_rate"] * W_WIN_RATE
    kill_term = kpis["avg_kill"] * W_AVG_KILL
    hp_term = kpis["avg_hp"] * W_AVG_HP
    fitness = win_term + kill_term + hp_term

    detail = {
        "win_rate":        kpis["win_rate"],
        "avg_kill":        kpis["avg_kill"],
        "avg_hp":          kpis["avg_hp"],
        "win_term":        round(win_term,  4),
        "kill_term":       round(kill_term, 4),
        "hp_term":         round(hp_term,   4),
        "elapsed_s":       round(elapsed,   2),
    }
    return round(fitness, 4), detail


def _success(kpis: Dict) -> bool:
    return (kpis["win_rate"] > SUCCESS_WIN_RATE
            and kpis["avg_kill"] > SUCCESS_AVG_KILL)


# ==============================================================================
# Simulation runner
# ==============================================================================

def _run_sim(n_games: int = 1000, seed: int = 2024,
             timeout: int = 620) -> Tuple[bool, float]:
    """Launch sim1000.py.  Returns (success, elapsed_seconds)."""
    t0  = time.time()
    cmd = [sys.executable, str(SIM_SCRIPT),
           "--games", str(n_games),
           "--seed",  str(seed)]
    try:
        result = subprocess.run(cmd, cwd=str(ROOT), timeout=timeout)
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"    ❌ sim exited {result.returncode}")
            return False, elapsed
        return True, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"    ❌ sim timed out after {timeout}s")
        return False, elapsed
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"    ❌ sim error: {exc}")
        return False, elapsed


# ==============================================================================
# Artifact persistence
# ==============================================================================

def _load_registry() -> List[Dict]:
    data = safe_read_json(REGISTRY_FILE)
    return data if isinstance(data, list) else []


def _save_registry(reg: List[Dict]) -> None:
    safe_write_json(REGISTRY_FILE, reg)


def _save_run(run_id: str, combo: Dict, mutated: Dict,
              fitness: float, detail: Dict, summary: Dict) -> Path:
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    safe_write_json(run_dir / "params.json",     mutated)
    safe_write_json(run_dir / "combo.json",       combo)
    safe_write_json(run_dir / "sim_summary.json", summary)
    safe_write_json(run_dir / "score.json", {
        "run_id":    run_id,
        "fitness":   fitness,
        "detail":    detail,
        "timestamp": datetime.now().isoformat(),
    })
    if SIM_OUTPUT.exists():
        shutil.copy2(SIM_OUTPUT, run_dir / "sim1000_summary.json")
    return run_dir


def _maybe_promote_best(run_dir: Path, run_id: str,
                        fitness: float, mutated: Dict,
                        combo: Dict, detail: Dict) -> bool:
    score_file   = BEST_DIR / "score.json"
    current_best = float("-inf")
    if score_file.exists():
        stored = safe_read_json(score_file)
        if stored:
            current_best = stored.get("fitness", float("-inf"))

    if fitness <= current_best:
        return False

    if BEST_DIR.exists():
        shutil.rmtree(BEST_DIR)
    shutil.copytree(run_dir, BEST_DIR)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _combo_slug(combo)
    fit_s = f"{fitness:.3f}".replace(".", "p")
    snap  = ARCHIVE_DIR / f"{ts}_{slug}_fit{fit_s}"
    shutil.copytree(run_dir, snap)

    if safe_write_json(PARAMS_JSON, mutated):
        print(f"    💾 trained_params.json <- new best written")
    print(f"    🏆 New best -> {BEST_DIR}/  "
          f"(fitness {fitness:.4f})")
    return True


# ==============================================================================
# Grid generation
# ==============================================================================

def _normalize_cli_values(values: Optional[List[float]],
                          fallback: List[float]) -> List[float]:
    """Return CLI-provided values or the default sweep list."""
    if not values:
        return list(fallback)
    return [float(v) for v in values]


def build_grid(custom_grid: Optional[Dict[str, List[float]]] = None) -> List[Dict[str, float]]:
    """Generate parameter combinations in reproducible order."""
    source = custom_grid or GRID
    keys   = list(source.keys())
    values = [source[k] for k in keys]
    combos = []
    for vals in itertools.product(*values):
        combos.append(dict(zip(keys, vals)))
    return combos


# ==============================================================================
# Main sweep loop
# ==============================================================================

def run_sweep(dry_run: bool = False,
              resume:  bool = False,
              top_n:   int  = 10,
              n_games: int  = 1000,
              seed:    int  = 2024,
              custom_grid: Optional[Dict[str, List[float]]] = None) -> None:

    ensure_dirs(RUNS_DIR, BEST_DIR, ARCHIVE_DIR)

    active_grid = custom_grid or GRID
    combos   = build_grid(active_grid)
    _write_grid_manifest(combos)
    registry = _load_registry()
    base     = safe_read_json(PARAMS_JSON) or {}

    total        = len(combos)
    skipped      = 0
    done         = 0
    success_runs: List[Dict] = []
    t_sweep      = time.time()

    print("=" * 68)
    print("  BUILDER TEST SET -- Combo + Survival Sweep")
    print("=" * 68)
    dims = " x ".join(str(len(v)) for v in active_grid.values())
    print(f"  Grid size   : {total} combinations  ({dims})")
    print(f"  Games/run   : {n_games} | seed={seed}")
    print(f"  Output      : {PHASE_DIR}")
    print(f"  Locked      : economist.greed_turn_end = 5.0")
    print(f"  Resume      : {resume}")
    print(f"  Dry run     : {dry_run}")
    print(f"  Grid files  : {GRID_JSON.name}, {GRID_CSV.name}")
    print()

    if dry_run:
        print("  DRY RUN -- printing grid only, no simulations")
        print()
        print(f"  {'#':<5} {'cw':>5} {'ggt':>5} {'sbc':>5} {'cbc':>5}  {'run_id'}")
        print(f"  {'-' * 68}")
        for i, c in enumerate(combos, 1):
            print(f"  {i:<5} "
                  f"{c['builder.combo_weight']:>5.2f} "
                  f"{c['builder.greed_gold_thresh']:>5.0f} "
                  f"{c['builder.spike_buy_count']:>5.0f} "
                  f"{c['builder.convert_buy_count']:>5.0f}  "
                  f"{_run_id(c, i)}")
        print(f"\n  Total: {total} runs")
        return

    # ── Already-done run IDs (for resume) ────────────────────────────────────
    done_slugs = set()
    if resume:
        for r in registry:
            combo_done = r.get("combo")
            if isinstance(combo_done, dict):
                done_slugs.add(_combo_slug(combo_done))

    for idx, combo in enumerate(combos, 1):
        slug   = _combo_slug(combo)
        run_id = _run_id(combo, idx)

        # ── Resume check ──────────────────────────────────────────────────────
        if resume and slug in done_slugs:
            skipped += 1
            print(f"  SKIP {idx:>3}/{total}  {slug}  (already done)")
            continue

        cw  = combo["builder.combo_weight"]
        gte = combo["builder.greed_turn_end"]
        sbc = combo["builder.spike_buy_count"]
        cbc = combo["builder.convert_buy_count"]

        print(f"\n  {'=' * 65}")
        print(f"  RUN {idx:>3}/{total}  |  "
              f"cw={cw:.2f}  gte={gte:.0f}  sbc={sbc:.0f}  cbc={cbc:.0f}")
        print(f"  ID : {run_id}")
        if done > 0:
            avg_t = (time.time() - t_sweep) / done
            eta_m = (total - idx) * avg_t / 60
            print(f"  ETA: ~{eta_m:.0f} min  ({total - idx} runs left)")
        print(f"  {'-' * 65}")

        # ── Build & write params ──────────────────────────────────────────────
        mutated = _build_mutated_params(base, combo)
        if not safe_write_json(PARAMS_JSON, mutated):
            print(f"    ❌ Could not write trained_params.json -- skipping")
            continue
        print(f"    ✍  trained_params.json updated")

        # ── Run simulation ────────────────────────────────────────────────────
        ok, elapsed = _run_sim(n_games=n_games, seed=seed,
                                timeout=int(DURATION_LIMIT_S + 120))
        if not ok:
            print(f"    ❌ Sim failed -- skipping")
            continue

        # ── Load & evaluate ───────────────────────────────────────────────────
        summary = safe_read_json(SIM_OUTPUT)
        if summary is None:
            print(f"    ❌ Output missing: {SIM_OUTPUT}")
            continue

        fitness, detail = _compute_fitness(summary, elapsed)
        kpis            = _extract_builder_kpis(summary)

        # ── Mini-report ───────────────────────────────────────────────────────
        dom     = summary.get("balance", {}).get("dominant_strategy", "?")
        max_dev = summary.get("balance", {}).get("max_deviation_pct", 0.0)
        print(f"    builder  win={kpis['win_rate']:.1f}%  "
              f"kill={kpis['avg_kill']:.2f}  hp={kpis['avg_hp']:.2f}  "
              f"eco={kpis['gold_efficiency']:.3f}")
        print(f"    global   dom={dom}  maxDev={max_dev:.2f}%  "
              f"elapsed={elapsed:.1f}s")
        print(f"    fitness  {fitness:+.4f}")

        if _success(kpis):
            print(f"    ✅ SUCCESS CONDITION MET!")
            success_runs.append({"run_id": run_id, "fitness": fitness,
                                  "combo": combo, "kpis": kpis})

        # ── Persist ───────────────────────────────────────────────────────────
        run_dir  = _save_run(run_id, combo, mutated, fitness, detail, summary)
        promoted = _maybe_promote_best(run_dir, run_id, fitness,
                                       mutated, combo, detail)

        # ── Register ──────────────────────────────────────────────────────────
        registry.append({
            "run_id":    run_id,
            "idx":       idx,
            "combo":     combo,
            "fitness":   fitness,
            "win_rate":  kpis["win_rate"],
            "avg_kill":  kpis["avg_kill"],
            "avg_hp":    kpis["avg_hp"],
            "elapsed":   round(elapsed, 1),
            "promoted":  promoted,
            "timestamp": datetime.now().isoformat(),
        })
        _save_registry(registry)
        done += 1

    # ==========================================================================
    # Session complete
    # ==========================================================================
    total_elapsed = time.time() - t_sweep

    # Restore best-ever params
    best_params_file = BEST_DIR / "params.json"
    if best_params_file.exists():
        best_p = safe_read_json(best_params_file)
        if best_p:
            best_p.setdefault("builder", {}).pop("high_rarity_bonus", None)
            safe_write_json(PARAMS_JSON, best_p)
            print(f"\n  ↩  trained_params.json <- best run params restored")

    valid = [r for r in registry if r.get("fitness") is not None]
    top   = sorted(valid, key=lambda r: r["fitness"], reverse=True)[:top_n]

    safe_write_json(SESSION_FILE, {
        "phase":           "builder_testset",
        "total_runs":      done,
        "skipped":         skipped,
        "total_elapsed_s": round(total_elapsed, 1),
        "success_runs":    success_runs,
        "top_results":     top,
        "timestamp":       datetime.now().isoformat(),
    })

    # ── Final leaderboard ─────────────────────────────────────────────────────
    print(f"\n  {'=' * 68}")
    print(f"  BUILDER TEST SET COMPLETE -- {done} runs  ({total_elapsed / 60:.1f} min total)")
    print(f"  {'─' * 68}")

    if top:
        n_show = min(top_n, len(top))
        print(f"\n  TOP {n_show} PARAMETER COMBINATIONS (ranked by fitness)\n")
        hdr = (f"  {'Rk':<4} {'cw':>5} {'gte':>5} {'sbc':>5} {'cbc':>5}"
               f"  {'Win%':>6} {'Kill':>6} {'HP':>6} {'Fitness':>9}  OK?")
        print(hdr)
        print(f"  {'-' * 68}")
        for rank, r in enumerate(top, 1):
            c    = r["combo"]
            win  = r.get("win_rate", 0)
            kl   = r.get("avg_kill", 0)
            hp   = r.get("avg_hp",   0)
            fit  = r["fitness"]
            star = "⭐" if rank == 1 else "  "
            ok   = "✅" if win > SUCCESS_WIN_RATE and kl > SUCCESS_AVG_KILL else "  "
            print(f"  {star}{rank:<3} "
                  f"{c['builder.combo_weight']:>5.2f} "
                  f"{c['builder.greed_turn_end']:>5.0f} "
                  f"{c['builder.spike_buy_count']:>5.0f} "
                  f"{c['builder.convert_buy_count']:>5.0f} "
                  f"  {win:>6.2f} {kl:>6.2f} {hp:>6.2f} {fit:>9.4f}  {ok}")

        best = top[0]
        bc   = best["combo"]
        print(f"\n  Recommended builder params (greedily best fitness):")
        print(f"    combo_weight       = {bc['builder.combo_weight']}")
        print(f"    greed_turn_end     = {bc['builder.greed_turn_end']}")
        print(f"    spike_buy_count    = {bc['builder.spike_buy_count']}")
        print(f"    convert_buy_count  = {bc['builder.convert_buy_count']}")
        print(f"    fitness              = {best['fitness']:.4f}")
        print(f"    builder win_rate     = {best.get('win_rate', 0):.2f}%")
        print(f"    builder avg_kill     = {best.get('avg_kill', 0):.2f}")
    else:
        print("  No valid results -- check simulation errors above.")

    if success_runs:
        print(f"\n  ✅ SUCCESS condition met in {len(success_runs)} run(s)!")
    else:
        print(f"\n  (No run met win>{SUCCESS_WIN_RATE}% AND kill>{SUCCESS_AVG_KILL})")
        print(f"  Use top results above as next trained_params baseline.")

    print(f"\n  All artifacts  -> {PHASE_DIR}")
    print(f"  Session file   -> {SESSION_FILE}")
    print(f"  Best params    -> trained_params.json")
    print()


# ==============================================================================
# Entry point
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Builder test set -- 64-run combo/survival sweep",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print all planned combos without running simulations",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip combos already found in registry.json",
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Number of top results to display (default: 10)",
    )
    parser.add_argument(
        "--games", type=int, default=1000,
        help="Games per simulation run (default: 1000)",
    )
    parser.add_argument(
        "--seed", type=int, default=2024,
        help="RNG seed (default: 2024)",
    )
    parser.add_argument(
        "--cw", type=float, nargs="+",
        help="Builder combo_weight values (space-separated)",
    )
    parser.add_argument(
        "--gte", type=float, nargs="+",
        help="Builder greed_turn_end values (space-separated)",
    )
    parser.add_argument(
        "--sbc", type=float, nargs="+",
        help="Builder spike_buy_count values (space-separated)",
    )
    parser.add_argument(
        "--cbc", type=float, nargs="+",
        help="Builder convert_buy_count values (space-separated)",
    )
    args = parser.parse_args()

    custom_grid = {
        "builder.combo_weight": _normalize_cli_values(
            args.cw, GRID["builder.combo_weight"]
        ),
        "builder.greed_turn_end": _normalize_cli_values(
            args.gte, GRID["builder.greed_turn_end"]
        ),
        "builder.spike_buy_count": _normalize_cli_values(
            args.sbc, GRID["builder.spike_buy_count"]
        ),
        "builder.convert_buy_count": _normalize_cli_values(
            args.cbc, GRID["builder.convert_buy_count"]
        ),
    }

    run_sweep(
        dry_run = args.dry_run,
        resume  = args.resume,
        top_n   = args.top,
        n_games = args.games,
        seed    = args.seed,
        custom_grid = custom_grid,
    )


if __name__ == "__main__":
    main()
