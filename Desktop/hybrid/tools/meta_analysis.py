"""
META ANALYSIS - OP / weak cards & strategy signals
Run: python meta_analysis.py
"""
import random
import sys
import os
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine_core'))
from autochess_sim_v06 import (
    Game, Player, Market, Board, Card,
    CARD_POOL, CARD_COSTS, CARD_BY_NAME,
    STRATEGIES, trigger_passive, AI,
    combat_phase, find_combos, calculate_group_synergy_bonus,
)

# -------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------

def section(title):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print('='*62)

def subsection(title):
    print(f"\n  -- {title} --")

RARITY_ORDER = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}

# -------------------------------------------------------------
# SECTION 1: STATIC CARD ANALYSIS
# -------------------------------------------------------------
section("SECTION 1 - Static card value (total_power / cost)")

# total_power / cost per card
card_value = []
for card in CARD_POOL:
    cost = CARD_COSTS[card.rarity]
    power = card.total_power()
    ratio = power / cost
    passive_bonus = 0 if card.passive_type == "none" else 1
    card_value.append({
        "name": card.name,
        "category": card.category,
        "rarity": card.rarity,
        "rarity_n": RARITY_ORDER[card.rarity],
        "cost": cost,
        "power": power,
        "ratio": ratio,
        "passive": card.passive_type,
    })

card_value.sort(key=lambda x: x["ratio"], reverse=True)

subsection("Highest power/cost ratio (TOP 15 - potential OP)")
print(f"  {'Card':<30} {'Rarity':>7} {'Pow':>5} {'Cost':>8} {'Ratio':>7}  Passive")
print(f"  {'-'*70}")
for cv in card_value[:15]:
    print(f"  {cv['name']:<30} {cv['rarity']:>7} {cv['power']:>5} {cv['cost']:>8} {cv['ratio']:>7.1f}  {cv['passive']}")

subsection("Lowest power/cost ratio (BOTTOM 10 - potential weak)")
print(f"  {'Card':<30} {'Rarity':>7} {'Pow':>5} {'Cost':>8} {'Ratio':>7}  Passive")
print(f"  {'-'*70}")
for cv in card_value[-10:]:
    print(f"  {cv['name']:<30} {cv['rarity']:>7} {cv['power']:>5} {cv['cost']:>8} {cv['ratio']:>7.1f}  {cv['passive']}")

# Mean power by rarity
subsection("Mean power by rarity")
rarity_powers = defaultdict(list)
for cv in card_value:
    rarity_powers[cv["rarity"]].append(cv["power"])
for r in ["1", "2", "3", "4", "5"]:
    powers = rarity_powers[r]
    avg = sum(powers) / len(powers)
    mn, mx = min(powers), max(powers)
    print(f"  {r:>7}: avg={avg:.1f}  min={mn}  max={mx}  ({len(powers)} cards)")

# -------------------------------------------------------------
# SECTION 2: CATEGORY SYNERGY
# -------------------------------------------------------------
section("SECTION 2 - Category synergy snapshot")

# Per category: mean power, synergy_field count, combo count, etc.
cats = defaultdict(lambda: {"cards": [], "synergy_field": 0, "combo": 0, "copy": 0, "economy": 0})
for card in CARD_POOL:
    c = cats[card.category]
    c["cards"].append(card)
    if card.passive_type == "synergy_field":
        c["synergy_field"] += 1
    elif card.passive_type == "combo":
        c["combo"] += 1
    elif card.passive_type == "copy":
        c["copy"] += 1
    elif card.passive_type == "economy":
        c["economy"] += 1

print(f"\n  {'Category':<28} {'#':>5} {'AvgPow':>7} {'SynFld':>9} {'Combo':>6} {'Copy':>6} {'Eco':>5}")
print(f"  {'-'*68}")
cat_scores = []
for cat, data in sorted(cats.items()):
    cards = data["cards"]
    avg_power = sum(c.total_power() for c in cards) / len(cards)
    cat_synergy = data["synergy_field"] * 2 + data["combo"] * 1.5 + data["copy"] * 1
    cat_scores.append((cat, avg_power, cat_synergy, data))
    print(f"  {cat:<28} {len(cards):>5} {avg_power:>7.1f} {data['synergy_field']:>9} {data['combo']:>6} {data['copy']:>6} {data['economy']:>5}")

# Strongest category synergy score
cat_scores.sort(key=lambda x: x[1] + x[2], reverse=True)
print(f"\n  Combined score (avg power + synergy bonus):")
for cat, avg_p, syn, _ in cat_scores:
    bar = "#" * int((avg_p + syn) / 5)
    print(f"  {cat:<28} {avg_p + syn:>6.1f}  {bar}")

# -------------------------------------------------------------
# SECTION 3: PASSIVE-TYPE EFFECT PROXY
# -------------------------------------------------------------
section("SECTION 3 - Passive-type combat/income trigger means")

# Many trigger_passive samples per card
N_COMBAT = 200
passive_combat_pts = defaultdict(list)
passive_income_pts = defaultdict(list)

for _ in range(N_COMBAT):
    for card in CARD_POOL:
        # Combat win points
        ctx = {"turn": random.randint(1, 20)}
        try:
            pts = trigger_passive(card, "combat_win", None, None, ctx)
            passive_combat_pts[card.passive_type].append(pts)
        except:
            passive_combat_pts[card.passive_type].append(0)

        # Income points (gold proxy)
        try:
            pts2 = trigger_passive(card, "income", None, None, ctx)
            passive_income_pts[card.passive_type].append(pts2)
        except:
            passive_income_pts[card.passive_type].append(0)

subsection("Mean combat / income points by passive_type")
print(f"  {'Passive type':<20} {'Avg combat':>15} {'Avg income':>15}")
print(f"  {'-'*52}")
for pt in sorted(passive_combat_pts.keys()):
    cp = passive_combat_pts[pt]
    ip = passive_income_pts[pt]
    avg_c = sum(cp) / len(cp) if cp else 0
    avg_i = sum(ip) / len(ip) if ip else 0
    print(f"  {pt:<20} {avg_c:>15.3f} {avg_i:>15.3f}")

# -------------------------------------------------------------
# SECTION 4: CARD WIN RATE (400 GAMES)
# -------------------------------------------------------------
section("SECTION 4 - Card owner win rate (400 games)")

N_GAMES = 400

# card_owner_wins[name]  = wins when any owner held this card
# card_owner_games[name] = games where at least one player owned this card
# contribution = win_rate / (1/8)

card_owner_wins  = defaultdict(int)
card_owner_games = defaultdict(int)

strategy_wins  = defaultdict(int)
strategy_games = defaultdict(int)
strategy_hp_end      = defaultdict(list)
strategy_damage      = defaultdict(list)
strategy_gold_spent  = defaultdict(list)
strategy_cards_bought = defaultdict(list)

def all_cards_of(player: "Player"):
    """All card names on board + hand."""
    names = set()
    for card in player.board.grid.values():
        names.add(card.name)
    for card in player.hand:
        names.add(card.name)
    return names

print(f"  Simulating {N_GAMES} games...")

for game_i in range(N_GAMES):
    random.seed(game_i + 42)
    strats = STRATEGIES[:8]
    players = [Player(i, strats[i % len(strats)]) for i in range(8)]
    game = Game(players, verbose=False)
    try:
        winner = game.run()
        strategy_wins[winner.strategy] += 1

        winner_cards = all_cards_of(winner)

        for p in game.players:
            strategy_games[p.strategy] += 1
            strategy_hp_end[p.strategy].append(p.hp)
            strategy_damage[p.strategy].append(p.stats.get("damage_dealt", 0))
            strategy_gold_spent[p.strategy].append(p.stats.get("gold_spent", 0))
            strategy_cards_bought[p.strategy].append(p.stats.get("cards_bought", 0))

            p_cards = all_cards_of(p)
            is_winner = (p.pid == winner.pid)
            for name in p_cards:
                card_owner_games[name] += 1
                if is_winner:
                    card_owner_wins[name] += 1

    except Exception as e:
        pass

# -------------------------------------------------------------
# SECTION 5: STRATEGY META
# -------------------------------------------------------------
section("SECTION 5 - Strategy meta (same N_GAMES run)")

print(f"\n  {'Strategy':<15} {'Win%':>9} {'AvgHP':>8} {'AvgDmg':>10} {'AvgSpend':>12} {'AvgBuy':>9}")
print(f"  {'-'*68}")

strat_meta = []
for s in STRATEGIES:
    wins = strategy_wins.get(s, 0)
    games = strategy_games.get(s, 1)
    win_pct = wins / N_GAMES * 100
    hp = sum(strategy_hp_end[s]) / len(strategy_hp_end[s]) if strategy_hp_end[s] else 0
    dmg = sum(strategy_damage[s]) / len(strategy_damage[s]) if strategy_damage[s] else 0
    gold = sum(strategy_gold_spent[s]) / len(strategy_gold_spent[s]) if strategy_gold_spent[s] else 0
    cards = sum(strategy_cards_bought[s]) / len(strategy_cards_bought[s]) if strategy_cards_bought[s] else 0
    strat_meta.append((s, win_pct, hp, dmg, gold, cards))
    bar = "#" * int(win_pct / 2)
    print(f"  {s:<15} {win_pct:>8.1f}%  {hp:>7.1f}  {dmg:>9.1f}  {gold:>11.1f}  {cards:>8.1f}  {bar}")

EXPECTED_WIN = 100 / len(STRATEGIES)
print(f"\n  Expected win rate (uniform): {EXPECTED_WIN:.1f}%")

subsection("Strategy assessment")
for s, win_pct, hp, dmg, gold, cards in sorted(strat_meta, key=lambda x: -x[1]):
    ratio = win_pct / EXPECTED_WIN
    if ratio >= 1.8:
        tag = "[OP]"
    elif ratio >= 1.3:
        tag = "[STRONG]"
    elif ratio >= 0.7:
        tag = "[BALANCED]"
    elif ratio >= 0.4:
        tag = "[WEAK]"
    else:
        tag = "[VERY WEAK]"
    print(f"  {tag}  {s:<15} {win_pct:.1f}% (expected {EXPECTED_WIN:.1f}%, ratio={ratio:.2f}x)")

# -------------------------------------------------------------
# SECTION 6: CARD META
# -------------------------------------------------------------
section("SECTION 6 - Card meta (owner win rate)")

BASELINE = 1.0 / len(STRATEGIES)

card_meta = []
for card in CARD_POOL:
    n_games = card_owner_games.get(card.name, 0)
    n_wins  = card_owner_wins.get(card.name, 0)
    if n_games < 10:
        win_rate    = 0.0
        contribution = 0.0
    else:
        win_rate    = n_wins / n_games
        contribution = win_rate / BASELINE

    card_meta.append({
        "name":         card.name,
        "category":     card.category,
        "rarity":       card.rarity,
        "cost":         CARD_COSTS[card.rarity],
        "power":        card.total_power(),
        "passive":      card.passive_type,
        "n_games":      n_games,
        "n_wins":       n_wins,
        "win_rate":     win_rate,
        "contribution": contribution,
    })

card_meta.sort(key=lambda x: x["contribution"], reverse=True)

subsection("Highest owner win rate (TOP 20 - OP candidates)")
print(f"  {'Card':<30} {'Rarity':>7} {'Pow':>5} {'WinRate':>8} {'N':>5} {'Contrib':>8}  Passive")
print(f"  {'-'*78}")
for cm in card_meta[:20]:
    flag = " [OP]" if cm["contribution"] > 1.5 else (" [STRONG]" if cm["contribution"] > 1.2 else "")
    print(f"  {cm['name']:<30} {cm['rarity']:>7} {cm['power']:>5} {cm['win_rate']:>8.3f} {cm['n_games']:>5} {cm['contribution']:>8.2f}  {cm['passive']}{flag}")

subsection("Lowest owner win rate (BOTTOM 15 - weak candidates)")
print(f"  {'Card':<30} {'Rarity':>7} {'Pow':>5} {'WinRate':>8} {'N':>5} {'Contrib':>8}  Passive")
print(f"  {'-'*78}")
for cm in [x for x in card_meta if x["n_games"] >= 10][-15:]:
    flag = " [VERY WEAK]" if cm["contribution"] < 0.5 else (" [WEAK]" if cm["contribution"] < 0.8 else "")
    print(f"  {cm['name']:<30} {cm['rarity']:>7} {cm['power']:>5} {cm['win_rate']:>8.3f} {cm['n_games']:>5} {cm['contribution']:>8.2f}  {cm['passive']}{flag}")

# -------------------------------------------------------------
# SECTION 7: CATEGORY META
# -------------------------------------------------------------
section("SECTION 7 - Category meta")

cat_contribution = defaultdict(list)
for cm in card_meta:
    if cm["n_games"] >= 10:
        cat_contribution[cm["category"]].append(cm["contribution"])

print(f"\n  {'Category':<28} {'AvgContrib':>12} {'Min':>6} {'Max':>6}  Rating")
print(f"  {'-'*65}")
cat_results = []
for cat, contribs in sorted(cat_contribution.items()):
    avg = sum(contribs) / len(contribs)
    mn, mx = min(contribs), max(contribs)
    cat_results.append((cat, avg, mn, mx))

for cat, avg, mn, mx in sorted(cat_results, key=lambda x: -x[1]):
    if avg > 1.2:
        tag = "[OP]"
    elif avg > 1.05:
        tag = "[STRONG]"
    elif avg > 0.85:
        tag = "[BALANCED]"
    elif avg > 0.6:
        tag = "[WEAK]"
    else:
        tag = "[VERY WEAK]"
    print(f"  {cat:<28} {avg:>12.3f} {mn:>6.2f} {mx:>6.2f}  {tag}")

# -------------------------------------------------------------
# SECTION 8: RARITY META
# -------------------------------------------------------------
section("SECTION 8 - Rarity meta")

rarity_contribution = defaultdict(list)
for cm in card_meta:
    if cm["n_games"] >= 10:
        rarity_contribution[cm["rarity"]].append(cm["contribution"])

print(f"\n  {'Rarity':>7} {'AvgContrib':>12} {'Cost':>8}  Rating")
print(f"  {'-'*45}")
for r in ["1", "2", "3", "4", "5"]:
    contribs = rarity_contribution[r]
    avg = sum(contribs) / len(contribs) if contribs else 0
    cost = CARD_COSTS[r]
    if avg > 1.2:
        tag = "[OP]"
    elif avg > 1.05:
        tag = "[STRONG]"
    elif avg > 0.85:
        tag = "[BALANCED]"
    else:
        tag = "[WEAK]"
    print(f"  {r:>7} {avg:>12.3f} {cost:>8}  {tag}")

# -------------------------------------------------------------
# SECTION 9: BALANCE HINTS
# -------------------------------------------------------------
section("SECTION 9 - Balance hints")

print("\n  STRATEGY BALANCE:")
for s, win_pct, hp, dmg, gold, cards in sorted(strat_meta, key=lambda x: -x[1]):
    ratio = win_pct / EXPECTED_WIN
    if ratio >= 1.5:
        print(f"  [NERF] Consider nerf: {s} ({win_pct:.1f}%) - reduce combo/placement edge")
    elif ratio <= 0.5:
        print(f"  [BUFF] Consider buff: {s} ({win_pct:.1f}%) - strategy underperforming")

print("\n  CARD BALANCE (contribution > 1.5 or < 0.7, min 10 games):")
op_cards   = [cm for cm in card_meta if cm["contribution"] > 1.5  and cm["n_games"] >= 10]
weak_cards = [cm for cm in card_meta if cm["contribution"] < 0.7  and cm["n_games"] >= 10]

if op_cards:
    print("  High contribution (nerf candidates):")
    for cm in op_cards:
        print(f"    [HIGH] {cm['name']} ({cm['rarity']}, contrib={cm['contribution']:.2f})")
else:
    print("  No extreme OP by contribution > 1.8")

if weak_cards:
    print("  Low contribution (buff candidates):")
    for cm in weak_cards:
        print(f"    [LOW] {cm['name']} ({cm['rarity']}, contrib={cm['contribution']:.2f})")
else:
    print("  No extreme weak by contribution < 0.4")

print("\n  CATEGORY BALANCE:")
for cat, avg, mn, mx in sorted(cat_results, key=lambda x: -x[1]):
    if avg > 1.3:
        print(f"  [HIGH] {cat}: avg contrib={avg:.2f} - category synergy may be high")
    elif avg < 0.7:
        print(f"  [LOW] {cat}: avg contrib={avg:.2f} - category synergy may be low")

print()
