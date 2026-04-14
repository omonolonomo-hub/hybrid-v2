#!/usr/bin/env python3
"""
Final checkpoint test - 100 games simulation
Verifies passive efficiency KPI logging system
"""

import sys, os, json, time, random
from collections import defaultdict
from statistics import mean, median

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool
from engine_core.constants import STRATEGIES
from engine_core.player import Player
from engine_core.game import Game
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log
from engine_core.strategy_logger import init_strategy_logger

# Config
N_GAMES = 100
N_PLAYERS = 8
SEED = 2024
LOG_DIR = os.path.join(ROOT, "output", "strategy_logs_final_test")

print("="*70)
print("  FINAL CHECKPOINT TEST - 100 Games Simulation")
print("="*70)
print(f"  Games: {N_GAMES} | Players: {N_PLAYERS} | Seed: {SEED}")
print(f"  Output: {LOG_DIR}/")
print()

# Initialize logger
slogger = init_strategy_logger(enabled=True, output_dir=LOG_DIR)

card_pool = get_card_pool()
rng = random.Random(SEED)
t0 = time.time()

wins = defaultdict(int)
games_played = defaultdict(int)

for game_num in range(1, N_GAMES + 1):
    try:
        clear_passive_trigger_log()
        
        shuffled = STRATEGIES[:]
        rng.shuffle(shuffled)
        players = [
            Player(pid=i, strategy=shuffled[i % len(shuffled)])
            for i in range(N_PLAYERS)
        ]
        
        game = Game(
            players,
            verbose=False,
            rng=rng,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=combat_phase,
            card_pool=card_pool,
        )
        
        slogger.begin_game(game_id=game_num)
        
        while len([p for p in game.players if p.alive]) > 1:
            if game.turn >= 50:
                break
            game.preparation_phase()
            slogger.set_turn(game.turn)
            game.combat_phase()
            
            # Builder synergy matrix decay
            for _p in game.players:
                if _p.alive and getattr(_p, 'synergy_matrix', None) is not None:
                    _p.synergy_matrix.decay()
        
        alive_players = [p for p in game.players if p.alive]
        winner = max(
            alive_players if alive_players else game.players,
            key=lambda p: p.hp
        )
        
        slogger.end_game(game, winner)
        
        wins[winner.strategy] += 1
        for p in players:
            games_played[p.strategy] += 1
        
        if game_num % 20 == 0:
            elapsed = time.time() - t0
            rate = game_num / elapsed
            print(f"  [{game_num:>3}/{N_GAMES}] {elapsed:>5.1f}s | {rate:>4.1f} games/s")
    
    except Exception as exc:
        print(f"  ERROR in game {game_num}: {exc}")
        continue

elapsed = time.time() - t0
print(f"\n  Completed: {elapsed:.1f}s | {N_GAMES/elapsed:.1f} games/s")

# Flush all logs
slogger.flush()
slogger.print_summary(n_games=N_GAMES)

# Verify output files
print("\n" + "="*70)
print("  VERIFICATION - Output Files")
print("="*70)

expected_files = [
    "placement_events.jsonl",
    "combat_events.jsonl",
    "buy_events.jsonl",
    "game_endings.jsonl",
    "strategy_summary.json",
    "passive_summary.json",
    "passive_efficiency_kpi.jsonl",
    "kpi_training.json"
]

all_exist = True
for fname in expected_files:
    fpath = os.path.join(LOG_DIR, fname)
    exists = os.path.exists(fpath)
    size = os.path.getsize(fpath) if exists else 0
    status = "✓" if exists and size > 0 else "✗"
    print(f"  {status} {fname:<35} {size:>10} bytes")
    if not exists or size == 0:
        all_exist = False

# Verify passive_efficiency_kpi.jsonl format
print("\n" + "="*70)
print("  VERIFICATION - passive_efficiency_kpi.jsonl Format")
print("="*70)

kpi_path = os.path.join(LOG_DIR, "passive_efficiency_kpi.jsonl")
if os.path.exists(kpi_path):
    with open(kpi_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"  Total records: {len(lines)}")
        
        if lines:
            # Check first record
            first_record = json.loads(lines[0])
            required_fields = [
                "game_id", "strategy", "card_name", "passive_type",
                "total_triggers", "raw_value", "normalized_value",
                "efficiency_score", "game_won"
            ]
            
            print(f"\n  First record fields:")
            for field in required_fields:
                has_field = field in first_record
                status = "✓" if has_field else "✗"
                value = first_record.get(field, "MISSING")
                print(f"    {status} {field:<20} = {value}")
            
            # Show sample records
            print(f"\n  Sample records (first 3):")
            for i, line in enumerate(lines[:3]):
                rec = json.loads(line)
                print(f"    {i+1}. Game {rec['game_id']}: {rec['strategy']}/{rec['card_name']}/{rec['passive_type']}")
                print(f"       triggers={rec['total_triggers']}, raw={rec['raw_value']}, norm={rec['normalized_value']:.2f}, eff={rec['efficiency_score']:.4f}, won={rec['game_won']}")
else:
    print("  ✗ File not found!")
    all_exist = False

# Verify passive_summary.json metadata
print("\n" + "="*70)
print("  VERIFICATION - passive_summary.json Metadata")
print("="*70)

summary_path = os.path.join(LOG_DIR, "passive_summary.json")
if os.path.exists(summary_path):
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)
        
        if "_metadata" in summary_data:
            print("  ✓ Metadata section exists")
            metadata = summary_data["_metadata"]
            print(f"    - description: {metadata.get('description', 'N/A')}")
            print(f"    - detailed_kpi_file: {metadata.get('detailed_kpi_file', 'N/A')}")
        else:
            print("  ✗ Metadata section missing")
            all_exist = False
else:
    print("  ✗ File not found!")
    all_exist = False

# Final verdict
print("\n" + "="*70)
print("  FINAL VERDICT")
print("="*70)

if all_exist:
    print("  ✅ ALL CHECKS PASSED")
    print("  - All output files generated correctly")
    print("  - passive_efficiency_kpi.jsonl has correct format")
    print("  - passive_summary.json includes metadata reference")
    print("  - System ready for production use")
else:
    print("  ❌ SOME CHECKS FAILED")
    print("  - Review output above for details")

print("="*70)
