#!/usr/bin/env python3
"""
QA Passive Impact Analyzer - Autochess Hybrid v0.5

Controlled A/B test for every passive card:
  - Baseline: N games, passive enabled
  - Test:     same N seeds, target card's passive silenced

Key improvements over v1:
  - Patch targets module globals directly (bypasses local-binding issue)
  - Target card is placed on board (not just hand) for immediate effect
  - Copy cards get pre-seeded copy_turns to hit thresholds early
  - Survival cards get low-HP + weak-board setup to trigger death
  - Synergy_field cards get same-category board fill for threshold passives
  - Per-type scoring calibrated to realistic delta ranges

Usage:
    python tools/qa_passive_impact.py
    python tools/qa_passive_impact.py --games 200 --seed 99
"""

import sys, os, random, copy as _copy
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine_core'))
import autochess_sim_v06 as sim

# =======================================================
# PATCH INFRASTRUCTURE
# =======================================================

_original_trigger = sim.trigger_passive
_disabled_card: str = ""


def _patched_trigger(card, trigger: str, owner, opponent, ctx: dict, verbose: bool = False) -> int:
    if card.name == _disabled_card:
        return 0
    return _original_trigger(card, trigger, owner, opponent, ctx)


def _enable_patch(card_name: str):
    global _disabled_card
    _disabled_card = card_name
    sim.trigger_passive = _patched_trigger


def _disable_patch():
    global _disabled_card
    _disabled_card = ""
    sim.trigger_passive = _original_trigger


# =======================================================
# BOARD SETUP HELPERS
# =======================================================

def _setup_player_for_card(player: sim.Player, card: sim.Card, rng: random.Random):
    """
    Place target card on player's board and configure state
    to maximise passive trigger probability.
    """
    ptype = card.passive_type

    # Always place target card at center
    cloned = card.clone()
    center = (0, 0)
    player.board.place(center, cloned)
    player.hand = [c for c in player.hand if c.name != card.name]
    player.copies[card.name] = player.copies.get(card.name, 0) + 1

    # Fill board with same-category allies for synergy_field threshold passives
    if ptype in ("synergy_field", "combo"):
        same_cat = [c for c in sim.CARD_POOL
                    if c.category == card.category and c.name != card.name]
        rng.shuffle(same_cat)
        free = player.board.free_coords()
        for ally_proto in same_cat[:min(4, len(free))]:
            if not free:
                break
            coord = free.pop(0)
            player.board.place(coord, ally_proto.clone())

    # Pre-seed copy counters so copy cards hit thresholds by turn 3
    if ptype == "copy":
        player.copies[card.name] = 3
        player.copy_turns[card.name] = sim.COPY_THRESH[1]  # already at 3-copy threshold
        player.copy_applied[card.name] = {"2": False, "3": False}

    # Survival: low HP so the player takes damage and cards die in combat.
    # The target card itself needs to die - so we give it very low stats
    # by weakening its edges, making it likely to lose duels.
    if ptype == "survival":
        player.hp = rng.randint(15, 50)
        # Weaken the cloned card so it loses combat and triggers card_killed
        for i in range(len(cloned.edges)):
            s, v = cloned.edges[i]
            cloned.edges[i] = (s, max(1, v - 4))
            cloned.stats[s] = max(1, v - 4)


# =======================================================
# SINGLE GAME RUNNER
# =======================================================

def _run_game(seed: int, n_players: int, target_card: sim.Card,
              disabled: bool) -> Dict:
    """
    Run one game. Player 0 always carries the target card on board.
    disabled=True -> target card's passive is silenced via module patch.
    """
    if disabled:
        _enable_patch(target_card.name)
    else:
        _disable_patch()

    rng = random.Random(seed)
    random.seed(seed)

    strategies = sim.STRATEGIES[:]
    rng.shuffle(strategies)

    players = []
    for i in range(n_players):
        strat = strategies[i % len(strategies)]
        p = sim.Player(pid=i, strategy=strat)
        players.append(p)

    # Setup player 0 with target card
    _setup_player_for_card(players[0], target_card, rng)

    random.seed(seed)
    game = sim.Game(players, verbose=False)
    try:
        winner = game.run()
    except Exception:
        winner = players[0]

    _disable_patch()

    p0 = players[0]
    return {
        "won":    p0.pid == winner.pid,
        "damage": p0.stats.get("damage_dealt", 0),
        "hp":     p0.hp,
        "gold":   p0.stats.get("gold_earned", 0),
        "turns":  game.turn,
        "kills":  p0.stats.get("kills", 0),
    }


def _aggregate(runs: List[Dict]) -> Dict:
    n = len(runs) or 1
    return {
        "win_rate":   sum(r["won"]    for r in runs) / n,
        "avg_damage": sum(r["damage"] for r in runs) / n,
        "avg_hp":     sum(r["hp"]     for r in runs) / n,
        "avg_gold":   sum(r["gold"]   for r in runs) / n,
        "avg_turns":  sum(r["turns"]  for r in runs) / n,
        "avg_kills":  sum(r["kills"]  for r in runs) / n,
    }


# =======================================================
# IMPACT SCORING
# =======================================================

# Per-type calibration caps - based on realistic delta ranges
# with improved board setup (higher deltas expected vs v1)
_CAPS = {
    "economy":       {"wr": 0.12, "dmg": 20.0, "hp": 10.0, "gold": 10.0},
    "combat":        {"wr": 0.15, "dmg": 40.0, "hp": 15.0, "gold":  5.0},
    "synergy_field": {"wr": 0.12, "dmg": 35.0, "hp": 12.0, "gold":  5.0},
    # survival: revive passives keep cards alive -> more damage dealt, more wins
    # HP delta is near-zero because revived cards are weak; use WR + DMG
    "survival": {"wr": 0.08, "dmg": 15.0, "hp":  8.0, "gold":  3.0},
    "copy":         {"wr": 0.12, "dmg": 30.0, "hp": 12.0, "gold":  8.0},
    "combo":         {"wr": 0.12, "dmg": 30.0, "hp": 12.0, "gold":  5.0},
}

# Per-type metric weights (must sum to 100)
_WEIGHTS = {
    "economy":       {"wr": 30, "dmg": 20, "hp": 15, "gold": 35},
    "combat":        {"wr": 40, "dmg": 40, "hp": 20, "gold":  0},
    "synergy_field": {"wr": 35, "dmg": 40, "hp": 25, "gold":  0},
    # survival: revive = more combat rounds = more damage; WR is primary signal
    "survival": {"wr": 50, "dmg": 35, "hp": 15, "gold":  0},
    "copy":         {"wr": 35, "dmg": 35, "hp": 20, "gold": 10},
    "combo":         {"wr": 40, "dmg": 40, "hp": 20, "gold":  0},
}

_DEFAULT_CAPS    = {"wr": 0.12, "dmg": 30.0, "hp": 12.0, "gold": 5.0}
_DEFAULT_WEIGHTS = {"wr": 40, "dmg": 30, "hp": 30, "gold": 0}


def _impact_score(en: Dict, di: Dict, passive_type: str) -> float:
    caps    = _CAPS.get(passive_type, _DEFAULT_CAPS)
    weights = _WEIGHTS.get(passive_type, _DEFAULT_WEIGHTS)

    wr   = min(1.0, abs(en["win_rate"]   - di["win_rate"])   / caps["wr"])
    dmg  = min(1.0, abs(en["avg_damage"] - di["avg_damage"]) / caps["dmg"])
    hp   = min(1.0, abs(en["avg_hp"]     - di["avg_hp"])     / caps["hp"])
    gold = min(1.0, abs(en["avg_gold"]   - di["avg_gold"])   / caps["gold"])

    score = (weights["wr"]   * wr
           + weights["dmg"]  * dmg
           + weights["hp"]   * hp
           + weights["gold"] * gold)

    return round(score, 1)   # 0-100


def _classify(score: float) -> str:
    if score >= 55:  return "STRONG"
    if score >= 30:  return "MODERATE"
    if score >= 12:  return "WEAK"
    return "INERT"


# =======================================================
# MAIN ANALYSIS
# =======================================================

def run_impact_analysis(n_games: int = 150, seed_base: int = 42,
                        n_players: int = 4) -> List[Dict]:
    passive_cards = [c for c in sim.CARD_POOL if c.passive_type != "none"]
    seeds = list(range(seed_base, seed_base + n_games))
    total = len(passive_cards)
    results = []

    for idx, card in enumerate(passive_cards):
        name  = card.name
        ptype = card.passive_type
        print(f"  [{idx+1:>2}/{total}] {name:<30} ({ptype})", end="", flush=True)

        en_runs = [_run_game(s, n_players, card, disabled=False) for s in seeds]
        di_runs = [_run_game(s, n_players, card, disabled=True)  for s in seeds]

        en = _aggregate(en_runs)
        di = _aggregate(di_runs)

        score = _impact_score(en, di, ptype)
        cls   = _classify(score)

        results.append({
            "name":         name,
            "passive_type": ptype,
            "rarity":       card.rarity,
            "category":     card.category,
            "score":        score,
            "class":        cls,
            "enabled":      en,
            "disabled":     di,
            "wr_delta":     round(en["win_rate"]   - di["win_rate"],   4),
            "dmg_delta":    round(en["avg_damage"] - di["avg_damage"], 2),
            "hp_delta":     round(en["avg_hp"]     - di["avg_hp"],     2),
            "gold_delta":   round(en["avg_gold"]   - di["avg_gold"],   2),
        })
        print(f"  score={score:>5.1f}  [{cls}]"
              f"  WR d={en['win_rate']-di['win_rate']:>+.3f}"
              f"  DMG d={en['avg_damage']-di['avg_damage']:>+.1f}")

    results.sort(key=lambda x: -x["score"])
    return results


# =======================================================
# REPORT
# =======================================================

_ICON = {"STRONG": "[STRONG]", "MODERATE": "[MOD]", "WEAK": "[WEAK]", "INERT": "[INERT]"}

def print_impact_report(results: List[Dict]):
    W = 120

    def sep(c="="): print(c * W)
    def hdr(t):     sep(); print(f"  {t}"); sep("-")

    sep()
    print("  AUTOCHESS HYBRID - Passive Impact Analysis  (v2 - improved board setup)")
    print(f"  {len(results)} passive cards  |  A/B controlled simulation  |  score 0-100")
    sep()

    # 1. FULL TABLE
    hdr("1. FULL IMPACT TABLE  (sorted by impact score)")
    print(f"  {'CARD':<30} {'TYPE':<18} {'RR':<8} {'SCORE':>6}  {'CLASS':<10}"
          f"  {'WR d':>7}  {'DMG d':>7}  {'HP d':>7}  {'GOLD d':>7}")
    print("  " + "-" * (W - 2))
    for r in results:
        icon = _ICON[r["class"]]
        print(f"  {r['name']:<30} {r['passive_type']:<18} {r['rarity']:<8}"
              f" {r['score']:>6.1f}  {icon} {r['class']:<8}"
              f"  {r['wr_delta']:>+7.3f}  {r['dmg_delta']:>+7.2f}"
              f"  {r['hp_delta']:>+7.2f}  {r['gold_delta']:>+7.2f}")

    # 2. CLASSIFICATION SUMMARY
    hdr("2. CLASSIFICATION SUMMARY")
    cc = defaultdict(int)
    for r in results: cc[r["class"]] += 1
    for cls in ["STRONG", "MODERATE", "WEAK", "INERT"]:
        icon = _ICON[cls]
        n    = cc[cls]
        bar  = "#" * n
        pct  = n / len(results) * 100
        print(f"  {icon:<10}  {n:>3} cards  ({pct:4.1f}%)  {bar}")

    # 3. TOP 10
    hdr("3. TOP 10 STRONGEST PASSIVES")
    for i, r in enumerate(results[:10], 1):
        icon = _ICON[r["class"]]
        print(f"  {i:>2}. {icon} {r['name']:<30} {r['passive_type']:<18}"
              f"  score={r['score']:>5.1f}  WR d={r['wr_delta']:>+.3f}"
              f"  DMG d={r['dmg_delta']:>+.2f}  HP d={r['hp_delta']:>+.2f}"
              f"  GOLD d={r['gold_delta']:>+.2f}")

    # 4. BOTTOM 10
    hdr("4. BOTTOM 10 WEAKEST / INERT PASSIVES")
    for i, r in enumerate(results[-10:][::-1], 1):
        icon = _ICON[r["class"]]
        print(f"  {i:>2}. {icon} {r['name']:<30} {r['passive_type']:<18}"
              f"  score={r['score']:>5.1f}  WR d={r['wr_delta']:>+.3f}"
              f"  DMG d={r['dmg_delta']:>+.2f}  HP d={r['hp_delta']:>+.2f}"
              f"  GOLD d={r['gold_delta']:>+.2f}")

    # 5. PER TYPE
    hdr("5. IMPACT BY PASSIVE TYPE")
    tg = defaultdict(list)
    for r in results: tg[r["passive_type"]].append(r["score"])
    print(f"  {'TYPE':<20} {'N':>4} {'AVG':>7} {'MAX':>7} {'MIN':>7}  DISTRIBUTION")
    print("  " + "-" * 70)
    for pt, scores in sorted(tg.items()):
        avg = sum(scores) / len(scores)
        dist = (f"STRONG x{sum(1 for s in scores if s>=55)} "
                f"MOD x{sum(1 for s in scores if 30<=s<55)} "
                f"WEAK x{sum(1 for s in scores if 12<=s<30)} "
                f"INERT x{sum(1 for s in scores if s<12)}")
        print(f"  {pt:<20} {len(scores):>4} {avg:>7.1f} {max(scores):>7.1f}"
              f" {min(scores):>7.1f}  {dist}")

    # 6. INERT DETAIL
    inert = [r for r in results if r["class"] == "INERT"]
    if inert:
        hdr(f"6. INERT PASSIVES ({len(inert)}) -- no measurable gameplay impact")
        for r in inert:
            print(f"  [INERT] {r['name']:<30} {r['passive_type']:<18}"
                  f"  score={r['score']:.1f}"
                  f"  WR d={r['wr_delta']:>+.4f}"
                  f"  DMG d={r['dmg_delta']:>+.2f}"
                  f"  HP d={r['hp_delta']:>+.2f}"
                  f"  GOLD d={r['gold_delta']:>+.2f}")

    # 7. DESIGN NOTES
    hdr("7. DESIGN NOTES -- cards that may need attention")
    print("  Cards scoring INERT despite non-trivial passive descriptions:")
    for r in results:
        if r["class"] == "INERT" and r["rarity"] in ("3", "4", "5"):
            print(f"  [!] {r['name']:<30} rarity={r['rarity']}  type={r['passive_type']}"
                  f"  score={r['score']:.1f}")

    sep()
    print("  IMPACT ANALYSIS COMPLETE")
    sep()


# =======================================================
# ENTRY POINT
# =======================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Passive Impact Analyzer v2")
    parser.add_argument("--games",   type=int, default=150)
    parser.add_argument("--seed",    type=int, default=42)
    parser.add_argument("--players", type=int, default=4)
    args = parser.parse_args()

    passive_count = len([c for c in sim.CARD_POOL if c.passive_type != "none"])

    print(f"\n{'='*60}")
    print("  Passive Impact Analyzer v2 -- Autochess Hybrid v0.5")
    print(f"  {args.games} games/card x 2 conditions x {passive_count} cards")
    print(f"  Total game runs: {args.games * 2 * passive_count:,}")
    print(f"  Improvements: board pre-placement, copy pre-seeding,")
    print(f"                survival low-HP setup, synergy_field fill")
    print(f"{'='*60}\n")

    results = run_impact_analysis(
        n_games=args.games,
        seed_base=args.seed,
        n_players=args.players,
    )
    print()
    print_impact_report(results)
