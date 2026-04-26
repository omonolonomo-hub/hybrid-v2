"""
trainer/compare_runs.py — KPI delta calculator
===============================================

Compares a current sim1000 summary against a baseline summary
and returns a structured delta report used by fitness.py.

Phase 2A+: Also loads kpi_training.json as the "oracle" so that
callers can reference true per-strategy baseline KPIs (g3_gold_efficiency,
g5_win_rate, g6_r4r5_ratio, etc.) alongside the sim-summary deltas.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# ── KPI Oracle loader (mirrors fitness.py — shared source of truth) ─────────
_KPI_ORACLE_PATH = Path(__file__).parent.parent / "output" / "strategy_logs" / "kpi_training.json"


def load_kpi_baseline(path: Path = _KPI_ORACLE_PATH) -> Dict[str, Any]:
    """Load kpi_training.json. Returns {} on missing/corrupt file."""
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _strat_kpis(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the per-strategy KPI block from a sim1000 summary."""
    return summary.get("strategies", {})


def compare_runs(baseline_summary: Dict[str, Any],
                 current_summary:  Dict[str, Any],
                 kpi_baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compare current run vs baseline.  Returns a KPI delta report.

    Now also enriches each strategy block with kpi_training.json oracle values
    so that fitness.py and manual_tuner.py can reference true baseline KPIs
    (e.g. g3_gold_efficiency, g5_avg_final_hp) without re-reading the file.

    Shape of the returned dict
    --------------------------
    {
        "strategies": {
            "<strategy>": {
                # ── sim-summary deltas (as before) ──────────────────────
                "baseline_win_rate_pct": float,
                "new_win_rate_pct":      float,
                "delta_win_rate_pct":    float,   # current − baseline
                "baseline_avg_damage":   float,
                "new_avg_damage":        float,
                "delta_avg_damage":      float,
                "baseline_avg_kills":    float,
                "new_avg_kills":         float,
                "delta_avg_kills":       float,
                "baseline_avg_final_hp": float,
                "new_avg_final_hp":      float,
                "delta_avg_final_hp":    float,
                "baseline_avg_synergy":  float,
                "new_avg_synergy":       float,
                "delta_avg_synergy":     float,
                # ── kpi_training.json oracle values (new) ────────────────
                "oracle_win_rate":        float | None,   # g5_win_rate
                "oracle_gold_efficiency": float | None,   # g3_gold_efficiency
                "oracle_r4r5_ratio":      float | None,   # g6_r4r5_ratio
                "oracle_combat_wr":       float | None,   # g2_combat_win_rate
                "oracle_avg_final_hp":    float | None,   # g5_avg_final_hp
                # ── derived gold_efficiency from sim-summary (new) ──────
                "new_gold_efficiency":    float | None,
                "delta_gold_efficiency":  float | None,
            },
            ...
        },
        "balance": {
            "baseline_max_deviation_pct": float,
            "new_max_deviation_pct":      float,
            "delta_max_deviation_pct":    float,
            "baseline_dominant":          str,
            "new_dominant":               str,
        },
        "game_length": {
            "baseline_avg_turns": float,
            "new_avg_turns":      float,
            "delta_avg_turns":    float,
        },
        "crashes": {
            "baseline_crashes": int,
            "new_crashes":      int,
            "delta_crashes":    int,
        },
        "kpi_oracle_loaded": bool,   # True if kpi_training.json was found
    }
    """
    # Load KPI oracle (lazy — only once per call)
    if kpi_baseline is None:
        kpi_baseline = load_kpi_baseline()
    oracle_loaded = bool(kpi_baseline)

    b_strats = _strat_kpis(baseline_summary)
    c_strats = _strat_kpis(current_summary)

    all_strategies = sorted(set(list(b_strats) + list(c_strats)))

    strategy_deltas: Dict[str, Any] = {}
    for strat in all_strategies:
        b = b_strats.get(strat, {})
        c = c_strats.get(strat, {})
        oracle = kpi_baseline.get(strat, {})

        def _d(key: str) -> float:
            """Round difference: current − baseline."""
            return round(c.get(key, 0.0) - b.get(key, 0.0), 4)

        # ── gold_efficiency: kpi_training.json ile aynı formula ───────────────
        # kpi_training.json: g3_gold_efficiency = gold_spent / gold_earned  (düşük = israf)
        # sim1000_summary:   avg_eco_eff        = gold_earned / gold_spent  (yüksek = israf)
        # Oracle ile karşılaştırabilmek için avg_eco_eff'in tersini alıyoruz.
        raw_eco  = c.get("avg_eco_eff",  None)   # earned/spent ≈ 3.07
        new_eco  = (round(1.0 / raw_eco, 4) if (raw_eco is not None and raw_eco > 0)
                    else None)                    # spent/earned ≈ 0.33  (oracle scale)
        raw_eco_b = b.get("avg_eco_eff", None)
        base_eco  = (round(1.0 / raw_eco_b, 4) if (raw_eco_b is not None and raw_eco_b > 0)
                     else None)
        delta_eco = (round(new_eco - base_eco, 4)
                     if new_eco is not None and base_eco is not None
                     else None)

        strategy_deltas[strat] = {
            # ── sim-summary deltas ───────────────────────────────────────
            "baseline_win_rate_pct":  b.get("win_rate_pct",  0.0),
            "new_win_rate_pct":       c.get("win_rate_pct",  0.0),
            "delta_win_rate_pct":     _d("win_rate_pct"),
            "baseline_avg_damage":    b.get("avg_damage",    0.0),
            "new_avg_damage":         c.get("avg_damage",    0.0),
            "delta_avg_damage":       _d("avg_damage"),
            "baseline_avg_kills":     b.get("avg_kills",     0.0),
            "new_avg_kills":          c.get("avg_kills",     0.0),
            "delta_avg_kills":        _d("avg_kills"),
            "baseline_avg_final_hp":  b.get("avg_final_hp",  0.0),
            "new_avg_final_hp":       c.get("avg_final_hp",  0.0),
            "delta_avg_final_hp":     _d("avg_final_hp"),
            "baseline_avg_synergy":   b.get("avg_synergy",   0.0),
            "new_avg_synergy":        c.get("avg_synergy",   0.0),
            "delta_avg_synergy":      _d("avg_synergy"),
            # ── kpi_training.json oracle values ─────────────────────────
            "oracle_win_rate":         oracle.get("g5_win_rate"),
            "oracle_gold_efficiency":  oracle.get("g3_gold_efficiency"),
            "oracle_r4r5_ratio":       oracle.get("g6_r4r5_ratio"),
            "oracle_combat_wr":        oracle.get("g2_combat_win_rate"),
            "oracle_avg_final_hp":     oracle.get("g5_avg_final_hp"),
            # ── derived gold_efficiency delta ────────────────────────────
            "new_gold_efficiency":     new_eco,
            "delta_gold_efficiency":   delta_eco,
        }

    # ── Balance block ──────────────────────────────────────────────────────
    b_bal = baseline_summary.get("balance", {})
    c_bal = current_summary.get("balance",  {})
    b_dev = b_bal.get("max_deviation_pct", 0.0)
    c_dev = c_bal.get("max_deviation_pct", 0.0)

    balance_delta = {
        "baseline_max_deviation_pct": b_dev,
        "new_max_deviation_pct":      c_dev,
        "delta_max_deviation_pct":    round(c_dev - b_dev, 4),
        "baseline_dominant":          b_bal.get("dominant_strategy", ""),
        "new_dominant":               c_bal.get("dominant_strategy", ""),
    }

    # ── Game-length block ──────────────────────────────────────────────────
    b_gl = baseline_summary.get("game_length", {})
    c_gl = current_summary.get("game_length",  {})

    game_length_delta = {
        "baseline_avg_turns": b_gl.get("avg", 0.0),
        "new_avg_turns":      c_gl.get("avg", 0.0),
        "delta_avg_turns":    round(c_gl.get("avg", 0.0) - b_gl.get("avg", 0.0), 4),
    }

    # ── Crash block ────────────────────────────────────────────────────────
    b_crashes = baseline_summary.get("crashes", 0)
    c_crashes = current_summary.get("crashes",  0)

    crash_delta = {
        "baseline_crashes": b_crashes,
        "new_crashes":      c_crashes,
        "delta_crashes":    c_crashes - b_crashes,
    }

    return {
        "strategies":       strategy_deltas,
        "balance":          balance_delta,
        "game_length":      game_length_delta,
        "crashes":          crash_delta,
        "kpi_oracle_loaded": oracle_loaded,
    }


def format_delta_report(kpi_deltas: Dict[str, Any],
                        primary_strategy: str = "tempo") -> str:
    """Return a human-readable summary of the delta report."""
    lines = []
    strats = kpi_deltas.get("strategies", {})
    oracle_loaded = kpi_deltas.get("kpi_oracle_loaded", False)

    lines.append("  ┌─ Strategy KPI Deltas " + "─" * 40)
    for s, d in sorted(strats.items()):
        flag = " ◄" if s == primary_strategy else ""
        b    = d.get("baseline_win_rate_pct", 0)
        n    = d.get("new_win_rate_pct",      0)
        delta = d.get("delta_win_rate_pct",   0)
        sign  = "+" if delta >= 0 else ""
        lines.append(
            f"  │  {s:<14}  win%: {b:>5.1f} → {n:>5.1f}  "
            f"({sign}{delta:.2f}%){flag}"
        )

    # ── Oracle weak-spot monitor ───────────────────────────────────────────────
    if oracle_loaded:
        lines.append("  ├─ Oracle Weak-Spot Monitor (vs kpi_training.json)")
        eco = strats.get("economist", {})
        eco_oracle = eco.get("oracle_gold_efficiency")
        eco_new    = eco.get("new_gold_efficiency")
        if eco_oracle is not None and eco_new is not None:
            eco_delta = eco_new - eco_oracle
            flag = " ✓" if eco_delta > 0.01 else (" ↓" if eco_delta < -0.01 else " =")
            lines.append(
                f"  │  economist gold_eff:   oracle={eco_oracle:.4f}  "
                f"new={eco_new:.4f}  ({eco_delta:+.4f}){flag}"
            )
        bld = strats.get("builder", {})
        bld_oracle = bld.get("oracle_avg_final_hp")
        bld_new    = bld.get("new_avg_final_hp")
        if bld_oracle is not None and bld_new is not None:
            bld_delta = bld_new - bld_oracle
            flag = " ✓" if bld_delta > 0.2 else (" ↓" if bld_delta < -0.2 else " =")
            lines.append(
                f"  │  builder avg_final_hp: oracle={bld_oracle:.3f}  "
                f"new={bld_new:.3f}  ({bld_delta:+.3f}){flag}"
            )

    bal = kpi_deltas.get("balance", {})
    lines.append("  ├─ Balance")
    lines.append(
        f"  │  max_deviation: "
        f"{bal.get('baseline_max_deviation_pct', 0):.2f}% → "
        f"{bal.get('new_max_deviation_pct', 0):.2f}%  "
        f"(Δ {bal.get('delta_max_deviation_pct', 0):+.2f}%)"
    )
    lines.append(
        f"  │  dominant: {bal.get('baseline_dominant','')} → "
        f"{bal.get('new_dominant','')}"
    )

    gl = kpi_deltas.get("game_length", {})
    lines.append("  ├─ Game Length")
    lines.append(
        f"  │  avg turns: "
        f"{gl.get('baseline_avg_turns', 0):.1f} → "
        f"{gl.get('new_avg_turns', 0):.1f}  "
        f"(Δ {gl.get('delta_avg_turns', 0):+.1f})"
    )

    cr = kpi_deltas.get("crashes", {})
    lines.append(
        f"  └─ Crashes: {cr.get('baseline_crashes', 0)} → "
        f"{cr.get('new_crashes', 0)}  "
        f"(Δ {cr.get('delta_crashes', 0):+d})"
    )
    return "\n".join(lines)
