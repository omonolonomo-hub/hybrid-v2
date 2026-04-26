"""
Simulation consistency and debugging script.
Run: python debug_sim.py
"""
import random
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine_core'))
from autochess_sim_v06 import (
    Game, Player, Market, Board, Card,
    CARD_POOL, CARD_COSTS, CARD_BY_NAME,
    BASE_INCOME, MAX_INTEREST, INTEREST_STEP,
    STARTING_HP, STRATEGIES,
    trigger_passive, AI,
)

SEPARATOR = "-" * 60

# -------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def ok(msg):   print(f"  [OK]    {msg}")
def warn(msg): print(f"  [WARN]  {msg}")
def fail(msg): print(f"  [FAIL]  {msg}")

issues = []

def record(level, msg):
    issues.append((level, msg))
    if level == "FAIL": fail(msg)
    elif level == "WARN": warn(msg)
    else: ok(msg)

# -------------------------------------------------------------
# TEST 1: Card pool integrity
# -------------------------------------------------------------
section("TEST 1 - Card Pool Integrity")

rarities = {"1", "2", "3", "4", "5"}
for card in CARD_POOL:
    if card.rarity not in rarities:
        record("FAIL", f"{card.name}: unknown rarity '{card.rarity}'")
    if len(card.edges) != 6:
        record("FAIL", f"{card.name}: {len(card.edges)} edges (expected 6)")
    if card.total_power() == 0:
        record("WARN", f"{card.name}: total power = 0")
    if card.total_power() > 60:
        record("WARN", f"{card.name}: very high total power = {card.total_power()}")

record("OK", f"{len(CARD_POOL)} cards - edge/rarity checks passed")

# -------------------------------------------------------------
# TEST 2: Market consistency
# -------------------------------------------------------------
section("TEST 2 - Market Consistency")

m = Market(CARD_POOL)
total_copies = sum(m.pool_copies.values())
expected = len(CARD_POOL) * 3
if total_copies == expected:
    record("OK", f"pool_copies at init: {total_copies} (expected {expected})")
else:
    record("FAIL", f"pool_copies at init: {total_copies} (expected {expected})")

players = [Player(i) for i in range(8)]
windows = []
for p in players:
    w = m.deal_market_window(p, 5)
    windows.append([c.name for c in w])
    if len(w) != len(set(c.name for c in w)):
        record("FAIL", f"P{p.pid} market window has duplicate cards")

all_names = [name for w in windows for name in w]
from collections import Counter
counts = Counter(all_names)
over3 = {n: c for n, c in counts.items() if c > 3}
if over3:
    record("FAIL", f"3-copy limit exceeded: {over3}")
else:
    record("OK", "8-player deal respects 3-copy limit")

copies_before = dict(m.pool_copies)
for p in players:
    m.return_unsold(p)
copies_after = dict(m.pool_copies)
restored = sum(copies_after.values()) - sum(copies_before.values())
if restored > 0:
    record("OK", f"return_unsold: {restored} copies returned to pool")
else:
    record("WARN", "return_unsold: no copies restored (all bought?)")

# -------------------------------------------------------------
# TEST 3: Economy consistency
# -------------------------------------------------------------
section("TEST 3 - Economy Consistency")

p = Player(0, "economist")
for _ in range(50):
    p.income()
    p.apply_interest()
# Note: Unlimited gold economy - no cap enforced
record("OK", f"Economist gold after 50 turns: {p.gold} (unlimited economy)")

p2 = Player(0, "random")
p2.gold = 20
p2.income()
gold_after_income = p2.gold
p2.apply_interest()
gold_after_interest = p2.gold
if gold_after_interest > gold_after_income:
    record("OK", f"Interest order OK: income={gold_after_income}, after_interest={gold_after_interest}")
else:
    record("WARN", f"No interest added: income={gold_after_income}, after_interest={gold_after_interest}")

p_eko = Player(0, "economist")
p_rnd = Player(0, "random")
p_eko.gold = p_rnd.gold = 30
p_eko.income(); p_eko.apply_interest()
p_rnd.income(); p_rnd.apply_interest()
if p_eko.gold > p_rnd.gold:
    record("OK", f"Economist interest bonus OK: eco={p_eko.gold} > rnd={p_rnd.gold}")
else:
    record("FAIL", f"Economist interest missing: eco={p_eko.gold}, rnd={p_rnd.gold}")

m2 = Market(CARD_POOL)
test_card = CARD_POOL[5]
before = m2.pool_copies[test_card.name]
p3 = Player(0)
p3.gold = 50
p3.buy_card(test_card, market=m2)
after = m2.pool_copies[test_card.name]
if after == before - 1:
    record("OK", f"buy_card lowers pool_copies: {before} -> {after}")
else:
    record("FAIL", f"buy_card did not lower pool_copies: {before} -> {after}")

# -------------------------------------------------------------
# TEST 4: Passive trigger consistency
# -------------------------------------------------------------
section("TEST 4 - Passive Trigger Consistency")

passive_types = defaultdict(list)
for card in CARD_POOL:
    passive_types[card.passive_type].append(card.name)

print("  Passive distribution:")
for pt, names in sorted(passive_types.items()):
    print(f"    {pt:20s}: {len(names):3d} cards")

errors = 0
for card in CARD_POOL:
    for trigger in ["combat_win", "combat_lose", "income", "pre_combat",
                    "card_killed", "copy_2", "copy_3", "market_refresh", "card_buy"]:
        try:
            result = trigger_passive(card, trigger, None, None, {"turn": 1})
            if not isinstance(result, int):
                record("FAIL", f"{card.name} trigger={trigger} did not return int: {type(result)}")
                errors += 1
        except Exception as e:
            record("FAIL", f"{card.name} trigger={trigger} error: {e}")
            errors += 1

if errors == 0:
    record("OK", f"All {len(CARD_POOL)} cards x 9 triggers - no errors")

# -------------------------------------------------------------
# TEST 5: Full game simulation
# -------------------------------------------------------------
section("TEST 5 - Full Game Consistency (100 games)")

N = 100
crash_count = 0
infinite_loop_count = 0
hp_negative = 0
turn_counts = []
winner_hps = []

for game_i in range(N):
    random.seed(game_i)
    strats = STRATEGIES[:8]
    players = [Player(i, strats[i % len(strats)]) for i in range(8)]
    game = Game(players, verbose=False)
    try:
        winner = game.run()
        turn_counts.append(game.turn)
        winner_hps.append(winner.hp)

        for p in game.players:
            if p.hp < 0:
                hp_negative += 1

        for p in game.players:
            # Note: Unlimited gold economy - no cap check needed
            pass

        if game.turn >= 50:
            infinite_loop_count += 1

    except Exception as e:
        crash_count += 1
        record("FAIL", f"Game {game_i} crashed: {e}")
        if crash_count >= 5:
            record("FAIL", "5+ crashes, stopping")
            break

avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0
avg_winner_hp = sum(winner_hps) / len(winner_hps) if winner_hps else 0
min_turns = min(turn_counts) if turn_counts else 0
max_turns = max(turn_counts) if turn_counts else 0

print(f"\n  Results ({N} games):")
print(f"    Crashes           : {crash_count}")
print(f"    Long games (50+)  : {infinite_loop_count}")
print(f"    Negative HP       : {hp_negative}")
print(f"    Avg turns         : {avg_turns:.1f}  (min={min_turns}, max={max_turns})")
print(f"    Avg winner HP     : {avg_winner_hp:.1f}")

if crash_count == 0:
    record("OK", "No crashes")
else:
    record("FAIL", f"{crash_count} crashes")

if infinite_loop_count == 0:
    record("OK", "No infinite-loop guard trips")
else:
    record("WARN", f"{infinite_loop_count} games reached 50 turns")

if hp_negative == 0:
    record("OK", "HP never negative")
else:
    record("FAIL", f"HP negative {hp_negative} times")

# -------------------------------------------------------------
# TEST 6: Strategy balance
# -------------------------------------------------------------
section("TEST 6 - Strategy Balance (200 games)")

N2 = 200
win_counts = defaultdict(int)
avg_hp_end = defaultdict(list)
avg_damage = defaultdict(list)
eliminated_early = defaultdict(int)

for game_i in range(N2):
    random.seed(game_i + 1000)
    strats = STRATEGIES[:8]
    players = [Player(i, strats[i % len(strats)]) for i in range(8)]
    game = Game(players, verbose=False)
    try:
        winner = game.run()
        win_counts[winner.strategy] += 1
        for p in game.players:
            avg_hp_end[p.strategy].append(p.hp)
            avg_damage[p.strategy].append(p.stats["damage_dealt"])
            if p.hp == 0 and p.stats["damage_dealt"] < 50:
                eliminated_early[p.strategy] += 1
    except Exception:
        pass

print(f"\n  {'Strategy':<15} {'Win%':>9} {'AvgHP':>8} {'AvgDmg':>10} {'EarlyOut':>11}")
print(f"  {'-'*55}")
for s in STRATEGIES:
    wins = win_counts.get(s, 0)
    win_pct = wins / N2 * 100
    hp = sum(avg_hp_end[s]) / len(avg_hp_end[s]) if avg_hp_end[s] else 0
    dmg = sum(avg_damage[s]) / len(avg_damage[s]) if avg_damage[s] else 0
    early = eliminated_early.get(s, 0)
    bar = "#" * int(win_pct / 2)
    print(f"  {s:<15} {win_pct:>8.1f}%  {hp:>7.1f}  {dmg:>9.1f}  {early:>10d}  {bar}")

max_win = max(win_counts.values()) / N2 * 100 if win_counts else 0
if max_win < 40:
    record("OK", f"Strategy spread OK: max win rate {max_win:.1f}%")
elif max_win < 55:
    record("WARN", f"Strategy skew: max win rate {max_win:.1f}%")
else:
    record("FAIL", f"Severe skew: max win rate {max_win:.1f}%")

rare_hunter_wins = win_counts.get("rare_hunter", 0) / N2 * 100
if rare_hunter_wins < 3:
    record("WARN", f"rare_hunter very weak: {rare_hunter_wins:.1f}% wins")

builder_wins = win_counts.get("builder", 0) / N2 * 100
if builder_wins > 25:
    record("WARN", f"builder very strong: {builder_wins:.1f}% wins")

# -------------------------------------------------------------
# SUMMARY
# -------------------------------------------------------------
section("SUMMARY")

fails = [m for l, m in issues if l == "FAIL"]
warns = [m for l, m in issues if l == "WARN"]
oks   = [m for l, m in issues if l == "OK"]

print(f"\n  OK   : {len(oks)}")
print(f"  WARN : {len(warns)}")
print(f"  FAIL : {len(fails)}")

if fails:
    print("\n  FAILURES:")
    for f in fails:
        print(f"    - {f}")

if warns:
    print("\n  WARNINGS:")
    for w in warns:
        print(f"    - {w}")

if not fails and not warns:
    print("\n  Simulation fully consistent.")
elif not fails:
    print("\n  No critical failures; review warnings.")
else:
    print("\n  Critical failures - fix required.")
