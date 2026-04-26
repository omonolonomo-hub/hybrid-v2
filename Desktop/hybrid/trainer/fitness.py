"""
trainer/fitness.py — Scalar fitness scorer for KPI deltas
==========================================================

Phase 2A+: Dynamic baseline from kpi_training.json
---------------------------------------------------
Instead of hardcoded win-rate targets, fitness is now computed relative to
each strategy's actual baseline KPIs stored in kpi_training.json.

Multi-metric scoring considers:
  • Primary strategy win-rate direction and target range
  • Secondary strategy health (economist gold_efficiency, builder survival)
  • Global balance (max deviation across all strategies)
  • Crash safety guard

Fitness range (approximate): −15 … +6
    Higher is better.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# ── Config ─────────────────────────────────────────────────────────────────
TARGET_WIN_RATE_PCT: float = 100.0 / 8   # fair-game expected = 12.5 %
PRIMARY_STRATEGY:    str   = "tempo"
TUNING_TARGET_LO:   float = 17.0         # lower bound of desired tempo win-rate
TUNING_TARGET_HI:   float = 18.0         # upper bound of desired tempo win-rate

# Path to the KPI oracle — relative to this file's project root
_KPI_ORACLE_PATH = Path(__file__).parent.parent / "output" / "strategy_logs" / "kpi_training.json"


def load_kpi_baseline(path: Path = _KPI_ORACLE_PATH) -> Dict[str, Any]:
    """Load kpi_training.json as the dynamic baseline oracle.

    Returns an empty dict (safe fallback) if file is missing or corrupt.
    Per-strategy keys match kpi_training.json top-level keys:
        g5_win_rate, g3_gold_efficiency, g6_r4r5_ratio, g2_combat_win_rate …
    """
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def compute_fitness(kpi_deltas: Dict[str, Any],
                    primary_strategy: str = PRIMARY_STRATEGY,
                    kpi_baseline: Optional[Dict[str, Any]] = None) -> float:
    """Compute a scalar fitness score from the KPI delta report.

    Now uses kpi_training.json as the dynamic reference point instead of
    hardcoded constants — so fitness is always relative to the true baseline.

    Scoring breakdown
    -----------------
    PRIMARY STRATEGY (tempo default)
    +0.5  per 1 % reduction in win-rate vs baseline        (direction reward)
    +2.0  bull's-eye bonus if win-rate inside target range
    −0.5  per 1 % below target low                         (over-nerf penalty)

    ECONOMIST HEALTH  (gold_efficiency is its Achilles heel)
    +1.0  if economist gold_efficiency improved vs kpi_baseline
    −1.0  if economist gold_efficiency regressed vs kpi_baseline

    BUILDER SURVIVAL  (high combo but low win-rate — survival is the problem)
    +0.5  if builder avg_final_hp improved vs kpi_baseline
    −0.5  if builder avg_final_hp regressed vs kpi_baseline

    GLOBAL BALANCE
    +0.2  per 1 % reduction in max-deviation across all strategies

    CRASH GUARD
    −1.0  per extra crash vs baseline

    Returns
    -------
    float — scalar fitness score, rounded to 4 dp.
            Returns −99.0 when the run could not be evaluated.
    """
    # Load oracle if not provided (lazy load for convenience)
    if kpi_baseline is None:
        kpi_baseline = load_kpi_baseline()

    strat_delta = (kpi_deltas
                   .get("strategies", {})
                   .get(primary_strategy, {}))

    new_win_rate = strat_delta.get("new_win_rate_pct")
    delta_win    = strat_delta.get("delta_win_rate_pct", 0.0)

    if new_win_rate is None:
        return -99.0          # evaluation not possible

    score = 0.0

    # ── 1. Primary strategy direction reward ───────────────────────
    if delta_win < 0:
        score += abs(delta_win) * 0.5   # +0.5 per 1 % reduced

    # ── 2. Target-range bull's-eye ─────────────────────────────────
    if TUNING_TARGET_LO <= new_win_rate <= TUNING_TARGET_HI:
        score += 2.0
    elif new_win_rate < TUNING_TARGET_LO:
        score -= (TUNING_TARGET_LO - new_win_rate) * 0.5

    # ── 3. Economist gold_efficiency health ────────────────────────
    #   Baseline: 0.3257 (very low — hoarding gold without spending)
    #   Any tuning that accidentally improves or degrades this is penalised/rewarded.
    eco_delta = kpi_deltas.get("strategies", {}).get("economist", {})
    eco_baseline_eff = kpi_baseline.get("economist", {}).get("g3_gold_efficiency", None)
    if eco_baseline_eff is not None:
        new_eco_eff = eco_delta.get("new_gold_efficiency")
        if new_eco_eff is not None:
            eco_improvement = new_eco_eff - eco_baseline_eff
            if eco_improvement > 0.01:
                score += 1.0    # Economist became more efficient — bonus
            elif eco_improvement < -0.01:
                score -= 1.0    # Regressed — penalty

    # ── 4. Builder survival health ─────────────────────────────────
    #   Baseline: avg_final_hp = 4.639 (lowest among non-random strategies)
    #   High combo (2.304) but dying too early — survival is the weak link.
    builder_delta = kpi_deltas.get("strategies", {}).get("builder", {})
    builder_baseline_hp = kpi_baseline.get("builder", {}).get("g5_avg_final_hp", None)
    if builder_baseline_hp is not None:
        new_builder_hp = builder_delta.get("new_avg_final_hp")
        if new_builder_hp is not None:
            hp_improvement = new_builder_hp - builder_baseline_hp
            if hp_improvement > 0.2:
                score += 0.5
            elif hp_improvement < -0.2:
                score -= 0.5

    # ── 5. Global balance reward ───────────────────────────────────
    balance_delta = (kpi_deltas
                     .get("balance", {})
                     .get("delta_max_deviation_pct", 0.0))
    if balance_delta < 0:
        score += abs(balance_delta) * 0.2

    # ── 6. Crash-safety guard ──────────────────────────────────────
    crash_delta = kpi_deltas.get("crashes", {}).get("delta_crashes", 0)
    if crash_delta > 0:
        score -= 1.0

    return round(score, 4)


def score_label(fitness: float) -> str:
    """Human-readable label for a fitness score."""
    if fitness >= 3.0:   return "🏆 EXCELLENT"
    if fitness >= 2.0:   return "✅ GOOD"
    if fitness >= 1.0:   return "📈 IMPROVING"
    if fitness >= 0.0:   return "➡️  NEUTRAL"
    if fitness > -90.0:  return "⚠️  WORSE"
    return                      "❌ FAILED"


def get_strategy_target(strategy: str,
                        metric: str = "g5_win_rate",
                        kpi_baseline: Optional[Dict[str, Any]] = None) -> Optional[float]:
    """Convenience: look up a specific strategy's baseline KPI value.

    Example usage in compare_runs.py or manual_tuner.py:
        target_win = get_strategy_target("tempo", "g5_win_rate")
        target_eco = get_strategy_target("economist", "g3_gold_efficiency")

    Returns None if kpi_training.json is missing or the key doesn't exist.
    """
    if kpi_baseline is None:
        kpi_baseline = load_kpi_baseline()
    return kpi_baseline.get(strategy, {}).get(metric)
