#!/usr/bin/env python3
"""
Direct test: Economist Phase Logic
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("tools", ""))

from engine_core.game import Game
from engine_core.player import Player
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log

print("=" * 80)
print("Testing Economist Phase Logic (20 games, no crash test)")
print("=" * 80 + "\n")

crash_count = 0

for i in range(20):
    try:
        clear_passive_trigger_log()
        # 8 players: economist (pid 0) + 7 others
        players = [
            Player(0, "economist"),
            Player(1, "warrior"),
            Player(2, "tempo"),
            Player(3, "builder"),
            Player(4, "balancer"),
            Player(5, "evolver"),
            Player(6, "rare_hunter"),
            Player(7, "random"),
        ]

        game = Game(
            players,
            verbose=False,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=combat_phase
        )
        winner = game.run()

        # Economist is always pid 0
        econ = players[0]

        print(f"Game {i+1:2d}/20: Economist HP={econ.hp:2d}, "
              f"Gold={econ.gold:3d}, Turns={econ.turns_played:2d}, "
              f"Final={econ.hp}, Win={econ.pid == winner.pid}")

    except Exception as e:
        crash_count += 1
        print(f"  ⚠️  Game {i+1} CRASH: {type(e).__name__}: {str(e)[:60]}")

print("\n" + "=" * 80)
print(f"RESULTS: {20 - crash_count}/20 games completed, {crash_count} crashes")
if crash_count == 0:
    print("✅ No crashes! Phase logic working.")
else:
    print("❌ Crashes detected!")
print("=" * 80 + "\n")

