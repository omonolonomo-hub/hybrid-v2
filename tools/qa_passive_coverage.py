#!/usr/bin/env python3
"""
QA Passive Coverage Analyzer - Autochess Hybrid (instrumented trigger_passive).

Runs many simulated games with a wrapped trigger_passive(), then prints coverage.
"""

import sys, os, json, random, copy
from collections import defaultdict
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine_core'))
import autochess_sim_v06 as sim

# =======================================================
# INSTRUMENTATION
# =======================================================

# Global log: card_name -> {total_triggers, events: {event: count}, effective_count}
passive_trigger_log: Dict[str, Dict] = defaultdict(lambda: {
    "total_triggers": 0,
    "events": defaultdict(int),
    "effective_count": 0,
    "ineffective_count": 0,
})

_original_trigger_passive = sim.trigger_passive

def _instrumented_trigger_passive(card, trigger: str, owner, opponent, ctx: dict, verbose: bool = False) -> int:
    """Wraps trigger_passive to log every activation and measure effect."""
    name = card.name

    # Capture pre-state
    pre_gold = owner.gold if owner and hasattr(owner, "gold") else None
    pre_stats = dict(card.stats) if isinstance(card.stats, dict) else dict(getattr(card.stats, "values", {}))
    pre_board_count = len(owner.board.grid) if owner and hasattr(owner, "board") else None

    result = _original_trigger_passive(card, trigger, owner, opponent, ctx)

    # Capture post-state
    post_gold = owner.gold if owner and hasattr(owner, "gold") else None
    post_stats = dict(card.stats) if isinstance(card.stats, dict) else dict(getattr(card.stats, "values", {}))
    post_board_count = len(owner.board.grid) if owner and hasattr(owner, "board") else None

    # Measure effect
    gold_delta = (post_gold - pre_gold) if (pre_gold is not None and post_gold is not None) else 0
    stat_delta = sum(abs(post_stats.get(k, 0) - pre_stats.get(k, 0)) for k in set(list(pre_stats) + list(post_stats)))
    board_delta = abs((post_board_count or 0) - (pre_board_count or 0))
    effective = (result != 0) or (gold_delta != 0) or (stat_delta != 0) or (board_delta != 0)

    log = passive_trigger_log[name]
    log["total_triggers"] += 1
    log["events"][trigger] += 1
    if effective:
        log["effective_count"] += 1
    else:
        log["ineffective_count"] += 1

    return result

# Monkey-patch
sim.trigger_passive = _instrumented_trigger_passive

# =======================================================
# CARD METADATA
# =======================================================

ALL_CARDS = sim.CARD_POOL
CARD_BY_NAME = sim.CARD_BY_NAME

# Cards with non-none passives
PASSIVE_CARDS = [c for c in ALL_CARDS if c.passive_type != "none"]
NONE_CARDS    = [c for c in ALL_CARDS if c.passive_type == "none"]

# Expected trigger events per passive_type (English identifiers, post-normalization)
EXPECTED_EVENTS = {
    "combat":          ["combat_win", "combat_lose", "card_killed"],
    "economy":         ["income", "market_refresh", "card_buy"],
    "copy":            ["copy_2", "copy_3", "pre_combat"],
    "survival":        ["card_killed", "combat_lose"],
    "synergy_field":   ["pre_combat"],
    "combo":           ["pre_combat"],
}

# =======================================================
# DISPATCH TABLE AUDIT (optional - v0.6 monolithic trigger_passive may omit these)
# =======================================================

_DISPATCH_ATTRS = [
    "COMBAT_WIN_PASSIVES",
    "COMBAT_LOSE_PASSIVES",
    "COMBAT_CARD_KILLED_PASSIVES",
    "ECONOMY_INCOME_PASSIVES",
    "ECONOMY_MARKET_REFRESH_PASSIVES",
    "ECONOMY_CARD_BUY_PASSIVES",
    "COPY_COPY_PASSIVES",
    "COPY_PRECOMBAT_PASSIVES",
    "SURVIVAL_CARD_KILLED_PASSIVES",
    "SURVIVAL_COMBAT_LOSE_PASSIVES",
    "SYNERGY_PRECOMBAT_PASSIVES",
    "COMBO_PRECOMBAT_PASSIVES",
]
DISPATCH_TABLES: Dict[str, Any] = {}
for _attr in _DISPATCH_ATTRS:
    _tbl = getattr(sim, _attr, None)
    if isinstance(_tbl, dict):
        DISPATCH_TABLES[_attr] = _tbl

def get_all_dispatched_names() -> set:
    names = set()
    for table in DISPATCH_TABLES.values():
        names.update(table.keys())
    return names

# =======================================================
# SIMULATION WITH HIGH DIVERSITY
# =======================================================

def _force_diverse_hand(player: sim.Player, market: sim.Market):
    """Force at least 1 high-rarity passive card into starting hand."""
    rare_passives = [c for c in PASSIVE_CARDS if c.rarity in ("4", "5")]
    mid_passives  = [c for c in PASSIVE_CARDS if c.rarity == "3"]
    eco_passives  = [c for c in PASSIVE_CARDS if c.passive_type == "economy"]
    surv_passives = [c for c in PASSIVE_CARDS if c.passive_type == "survival"]
    combo_passives= [c for c in PASSIVE_CARDS if c.passive_type == "combo"]

    picks = []
    if rare_passives:
        picks.append(random.choice(rare_passives).clone())
    if mid_passives:
        picks.append(random.choice(mid_passives).clone())
    if eco_passives:
        picks.append(random.choice(eco_passives).clone())
    if surv_passives:
        picks.append(random.choice(surv_passives).clone())
    if combo_passives:
        picks.append(random.choice(combo_passives).clone())

    # Fill rest randomly from all passive cards
    remaining = [c for c in PASSIVE_CARDS if c.name not in {p.name for p in picks}]
    random.shuffle(remaining)
    picks += [c.clone() for c in remaining[:max(0, 3 - len(picks))]]

    for card in picks[:5]:
        player.hand.append(card)
        player.copies[card.name] = player.copies.get(card.name, 0) + 1


def run_diverse_simulation(n_games: int = 500) -> None:
    """Run n_games with forced diversity to maximize passive coverage."""
    strategies = sim.STRATEGIES
    print(f"Running {n_games} games with passive instrumentation...")

    for game_num in range(n_games):
        random.shuffle(strategies)
        n_players = random.choice([4, 6, 8])
        players = []
        for i in range(n_players):
            strat = strategies[i % len(strategies)]
            p = sim.Player(pid=i, strategy=strat)
            players.append(p)

        # Force diverse starting hands for first 2 players
        market = sim.Market(sim.CARD_POOL)
        for p in players[:2]:
            _force_diverse_hand(p, market)

        # Occasionally force low-HP scenario
        if game_num % 10 == 0:
            for p in players:
                p.hp = random.randint(10, 45)  # trigger HP bonus passives

        game = sim.Game(players, verbose=False)
        # Override market with our pre-seeded one
        game.market = market

        try:
            game.run()
        except Exception:
            pass  # Don't let crashes stop coverage collection

        if (game_num + 1) % 100 == 0:
            print(f"  {game_num + 1}/{n_games} games done...")

    print("Simulation complete.\n")

# =======================================================
# COVERAGE ANALYSIS
# =======================================================

def analyze_coverage():
    dispatched_names = get_all_dispatched_names()

    # Build per-card report
    report = {}
    for card in ALL_CARDS:
        name = card.name
        ptype = card.passive_type
        log = passive_trigger_log.get(name, {})
        total = log.get("total_triggers", 0)
        events = dict(log.get("events", {}))
        eff = log.get("effective_count", 0)
        ineff = log.get("ineffective_count", 0)
        eff_ratio = round(eff / total, 3) if total > 0 else 0.0

        # Expected events for this passive type
        expected = EXPECTED_EVENTS.get(ptype, [])
        covered_events = [e for e in expected if events.get(e, 0) > 0]
        missing_events = [e for e in expected if events.get(e, 0) == 0]

        # Dispatch table presence
        in_dispatch = name in dispatched_names

        report[name] = {
            "passive_type": ptype,
            "rarity": card.rarity,
            "category": card.category,
            "total_triggers": total,
            "events": events,
            "effective_count": eff,
            "ineffective_count": ineff,
            "effectiveness_ratio": eff_ratio,
            "expected_events": expected,
            "covered_events": covered_events,
            "missing_events": missing_events,
            "in_dispatch_table": in_dispatch,
        }

    return report

# =======================================================
# REPORT GENERATION
# =======================================================

def print_report(report: dict):
    passive_cards_report = {k: v for k, v in report.items() if v["passive_type"] != "none"}
    none_cards_report    = {k: v for k, v in report.items() if v["passive_type"] == "none"}

    # -- 1. PASSIVE COVERAGE TABLE --
    print("=" * 100)
    print("1. PASSIVE COVERAGE TABLE")
    print("=" * 100)
    header = f"{'CARD':<30} {'TYPE':<18} {'RARITY':<8} {'TRIGGERS':>8} {'EFF':>6} {'INEFF':>6} {'EFF%':>6}  EVENTS"
    print(header)
    print("-" * 100)

    for name, d in sorted(passive_cards_report.items(), key=lambda x: -x[1]["total_triggers"]):
        events_str = ", ".join(f"{e}:{c}" for e, c in sorted(d["events"].items()))
        print(f"{name:<30} {d['passive_type']:<18} {d['rarity']:<8} "
              f"{d['total_triggers']:>8} {d['effective_count']:>6} {d['ineffective_count']:>6} "
              f"{d['effectiveness_ratio']:>6.1%}  {events_str}")

    # -- 2. MISSING PASSIVES (trigger_count == 0) --
    print("\n" + "=" * 100)
    print("2. MISSING PASSIVES (trigger_count == 0)")
    print("=" * 100)
    missing = [(k, v) for k, v in passive_cards_report.items() if v["total_triggers"] == 0]
    if missing:
        for name, d in sorted(missing, key=lambda x: x[1]["passive_type"]):
            dispatch_note = "NOT IN DISPATCH TABLE" if not d["in_dispatch_table"] else "in dispatch"
            print(f"  {name:<30} type={d['passive_type']:<18} rarity={d['rarity']}  [{dispatch_note}]")
    else:
        print("  (none)")

    # -- 3. PARTIAL PASSIVES (incomplete event coverage) --
    print("\n" + "=" * 100)
    print("3. PARTIAL PASSIVES (triggered but missing expected events)")
    print("=" * 100)
    partial = [(k, v) for k, v in passive_cards_report.items()
               if v["total_triggers"] > 0 and v["missing_events"]]
    if partial:
        for name, d in sorted(partial, key=lambda x: x[1]["passive_type"]):
            print(f"  {name:<30} type={d['passive_type']:<18}  "
                  f"covered={d['covered_events']}  MISSING={d['missing_events']}")
    else:
        print("  (none)")

    # -- 4. INEFFECTIVE PASSIVES (triggered but 0% effective) --
    print("\n" + "=" * 100)
    print("4. INEFFECTIVE PASSIVES (triggered but no measurable effect)")
    print("=" * 100)
    ineffective = [(k, v) for k, v in passive_cards_report.items()
                   if v["total_triggers"] > 0 and v["effectiveness_ratio"] == 0.0]
    if ineffective:
        for name, d in sorted(ineffective, key=lambda x: -x[1]["total_triggers"]):
            print(f"  {name:<30} type={d['passive_type']:<18} triggers={d['total_triggers']:>6}  eff=0%")
    else:
        print("  (none)")

    # -- 5. PASSIVE HEATMAP SUMMARY --
    print("\n" + "=" * 100)
    print("5. PASSIVE HEATMAP SUMMARY")
    print("=" * 100)

    sorted_by_triggers = sorted(passive_cards_report.items(), key=lambda x: -x[1]["total_triggers"])
    total_all = sum(v["total_triggers"] for v in passive_cards_report.values())
    n = len(sorted_by_triggers)
    top10_cutoff = max(1, n // 10)
    bot10_cutoff = max(1, n // 10)

    print(f"\n  Total passive triggers across all games: {total_all}")
    print(f"  Cards with active passives: {len(passive_cards_report)}")
    print(f"  Cards with passive_type=none: {len(none_cards_report)}")
    triggered_count = sum(1 for v in passive_cards_report.values() if v["total_triggers"] > 0)
    print(f"  Cards triggered at least once: {triggered_count}/{len(passive_cards_report)}")
    coverage_pct = triggered_count / len(passive_cards_report) * 100 if passive_cards_report else 0
    print(f"  Coverage: {coverage_pct:.1f}%")

    print(f"\n  TOP 10% MOST TRIGGERED (overactive):")
    for name, d in sorted_by_triggers[:top10_cutoff]:
        bar = "#" * min(40, d["total_triggers"] // max(1, total_all // 400))
        print(f"    {name:<30} {d['total_triggers']:>6}  {bar}")

    print(f"\n  BOTTOM 10% LEAST TRIGGERED (rare):")
    for name, d in sorted_by_triggers[-bot10_cutoff:]:
        print(f"    {name:<30} {d['total_triggers']:>6}  eff={d['effectiveness_ratio']:.0%}")

    # -- 6. DISPATCH TABLE AUDIT --
    print("\n" + "=" * 100)
    print("6. DISPATCH TABLE AUDIT (static wiring check)")
    print("=" * 100)

    dispatched = get_all_dispatched_names()
    passive_names = {c.name for c in PASSIVE_CARDS}

    # Cards with passive but NOT in any dispatch table
    not_dispatched = passive_names - dispatched
    if not_dispatched:
        print(f"\n  PASSIVE CARDS NOT IN ANY DISPATCH TABLE ({len(not_dispatched)}):")
        for name in sorted(not_dispatched):
            card = CARD_BY_NAME[name]
            print(f"    {name:<30} type={card.passive_type}")
    else:
        print("  All passive cards are in at least one dispatch table.")

    # Dispatch entries for cards that are passive_type=none (wrong wiring)
    wrong_wired = dispatched - passive_names
    if wrong_wired:
        print(f"\n  DISPATCH ENTRIES FOR none-TYPE CARDS (wrong wiring):")
        for name in sorted(wrong_wired):
            print(f"    {name}")
    else:
        print("  No wrong-wired dispatch entries.")

    # -- 7. PER-TYPE SUMMARY --
    print("\n" + "=" * 100)
    print("7. PER PASSIVE TYPE SUMMARY")
    print("=" * 100)
    type_stats = defaultdict(lambda: {"cards": 0, "triggered": 0, "total_triggers": 0, "effective": 0})
    for name, d in passive_cards_report.items():
        pt = d["passive_type"]
        type_stats[pt]["cards"] += 1
        if d["total_triggers"] > 0:
            type_stats[pt]["triggered"] += 1
        type_stats[pt]["total_triggers"] += d["total_triggers"]
        type_stats[pt]["effective"] += d["effective_count"]

    print(f"  {'TYPE':<20} {'CARDS':>6} {'TRIGGERED':>10} {'TOTAL_TRIG':>12} {'EFFECTIVE':>10}")
    print("  " + "-" * 62)
    for pt, s in sorted(type_stats.items()):
        print(f"  {pt:<20} {s['cards']:>6} {s['triggered']:>10} {s['total_triggers']:>12} {s['effective']:>10}")

    # -- 8. NONE-TYPE CARDS (no passive, for completeness) --
    print("\n" + "=" * 100)
    print("8. NONE-TYPE CARDS (passive_type=none, no trigger expected)")
    print("=" * 100)
    for name, d in sorted(none_cards_report.items(), key=lambda x: x[1]["rarity"]):
        print(f"  {name:<30} rarity={d['rarity']}  category={d['category']}")

    print("\n" + "=" * 100)
    print("REPORT COMPLETE")
    print("=" * 100)


# =======================================================
# ENTRY POINT
# =======================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=500)
    parser.add_argument("--seed",  type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    run_diverse_simulation(n_games=args.games)
    report = analyze_coverage()
    print_report(report)
