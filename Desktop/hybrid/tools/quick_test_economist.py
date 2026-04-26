#!/usr/bin/env python3
"""
Quick test for Economist Phase Logic (50 games).
Tests Step 1 & 2 implementation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("tools", ""))

from engine_core.game import Game
from engine_core.player import Player
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log

print("=" * 80)
print("Testing Economist Phase Logic (50 games)...")
print("=" * 80 + "\n")

stats = {
    "gold_spent": [],
    "gold_earned": [],
    "win_rate": 0,
    "hp_end": [],
    "crash": 0,
    "turns_played": [],
}

strategies = ["economist", "warrior", "tempo", "builder", "balancer", "evolver", "rare_hunter", "random"]

for i in range(50):
    try:
        clear_passive_trigger_log()
        players = [Player(j, strategies[j % 8]) for j in range(8)]
        game = Game(
            players,
            verbose=False,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=combat_phase
        )
        winner = game.run()

        # Collect economist stats
        for p in game.players:
            if p.strategy == "economist":
                spent = p.stats.get("gold_spent", 0)
                earned = p.stats.get("gold_earned", 0)

                stats["gold_spent"].append(spent)
                stats["gold_earned"].append(earned)
                stats["hp_end"].append(p.hp)
                stats["turns_played"].append(p.turns_played)

                if p.pid == winner.pid:
                    stats["win_rate"] += 1

        if (i + 1) % 10 == 0:
            print(f"  ✓ Game {i+1:2d}/50 complete")

    except Exception as e:
        stats["crash"] += 1
        print(f"  ⚠️  Game {i+1}: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("RESULTS (50 games)")
print("=" * 80)

avg_spent = sum(stats["gold_spent"]) / len(stats["gold_spent"]) if stats["gold_spent"] else 0
avg_earned = sum(stats["gold_earned"]) / len(stats["gold_earned"]) if stats["gold_earned"] else 0
avg_hp = sum(stats["hp_end"]) / len(stats["hp_end"]) if stats["hp_end"] else 0
avg_turns = sum(stats["turns_played"]) / len(stats["turns_played"]) if stats["turns_played"] else 0
win_rate_pct = (stats["win_rate"] / 50 * 100) if stats["gold_spent"] else 0

print(f"\n  Gold spent avg:        {avg_spent:6.1f}  (target ≥120, old was 104.9)")
print(f"  Gold earned avg:       {avg_earned:6.1f}  (baseline ~290)")
print(f"  Efficiency (spent/earned): {avg_spent/avg_earned:.3f}  (target ≥0.55, old was 0.358)")
print(f"  HP end avg:            {avg_hp:6.1f}  (survival indicator)")
print(f"  Avg turns played:      {avg_turns:6.1f}  (max ~50)")
print(f"  Win rate:              {win_rate_pct:6.1f}%  (target ≥13%, old was 11.5%)")
print(f"  Crashes:               {stats['crash']:3d}  (target = 0)")

print("\n" + "=" * 80)

# Validation
if stats["crash"] > 0:
    print("  ❌ CRASH DETECTED! Check code for errors")
elif avg_spent < 110:
    print("  ⚠️  Gold spent still too low (expect ≥120). Phase logic may not trigger.")
elif win_rate_pct < 12:
    print("  ⚠️  Win rate not improving. May need Step 3 (GA training).")
elif avg_spent >= 120:
    print("  ✅ PHASE LOGIC WORKING! Gold spent increased.")
    print("  ✅ Ready for Step 3 (PARAM_SPACE + GA training).")
else:
    print("  ✓ Test complete. Check metrics above.")

print("=" * 80 + "\n")

