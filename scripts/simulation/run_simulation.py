#!/usr/bin/env python3
"""
================================================================
|         AUTOCHESS HYBRID - 500 Game Reliability Test        |
|  Full performance and reliability simulation with metrics    |
================================================================

REQUIREMENTS:
- Run exactly 500 complete games
- Zero runtime errors
- Structured logging
- Aggregated results
- Performance metrics
- Determinism check
"""

import sys
import os
import json
import csv
import time
import traceback
import random
from collections import defaultdict
from statistics import median

# Add engine_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import game engine
from engine_core import autochess_sim_v06 as sim


def run_determinism_check(seed=42):
    """Run first 10 games twice with same seed to verify determinism."""
    results_1 = []
    results_2 = []
    
    for run_num in range(2):
        random.seed(seed)
        rng = random.Random(seed)
        
        for game_num in range(10):
            shuffled = sim.STRATEGIES[:]
            rng.shuffle(shuffled)
            players = [sim.Player(pid=i, strategy=shuffled[i % len(shuffled)]) for i in range(4)]
            
            game = sim.Game(players, verbose=False, rng=rng)
            winner = game.run()
            
            if run_num == 0:
                results_1.append((winner.strategy, game.turn))
            else:
                results_2.append((winner.strategy, game.turn))
    
    # Compare results
    mismatches = []
    for i, (r1, r2) in enumerate(zip(results_1, results_2)):
        if r1 != r2:
            mismatches.append(f"Game {i+1}: Run1={r1} vs Run2={r2}")
    
    return mismatches


def run_500_games(seed=42):
    """Run exactly 500 games with full metrics collection."""
    
    # Initialize metrics storage
    games_data = []
    strategy_wins = defaultdict(int)
    strategy_games = defaultdict(int)
    all_turns = []
    all_combo = []
    all_synergy = []
    all_damage = []
    gold_stds = []
    
    errors = []
    
    # Set seed for reproducibility
    random.seed(seed)
    rng = random.Random(seed)
    
    start_time = time.time()
    
    # Run 500 games
    for game_num in range(500):
        try:
            # Clear passive log
            sim._passive_trigger_log.clear()
            
            # Create players with shuffled strategies
            shuffled = sim.STRATEGIES[:]
            rng.shuffle(shuffled)
            players = [sim.Player(pid=i, strategy=shuffled[i % len(shuffled)]) for i in range(4)]
            
            # Run game
            game = sim.Game(players, verbose=False, rng=rng)
            winner = game.run()
            
            # Collect per-game metrics
            game_data = {
                'game_num': game_num + 1,
                'winner_strategy': winner.strategy,
                'total_turns': game.turn,
                'winner_hp': winner.hp,
            }
            
            # Player-level metrics
            total_gold = 0
            total_damage = 0
            total_kills = 0
            total_combo = 0
            total_synergy = 0
            rare_cards = 0
            copies_triggered = 0
            gold_values = []
            
            eliminations = []
            
            for p in players:
                strategy_games[p.strategy] += 1
                
                total_gold += p.stats.get('gold_earned', 0)
                total_damage += p.stats.get('damage_dealt', 0)
                total_kills += p.stats.get('kills', 0)
                total_combo += p.stats.get('combo_triggers', 0)
                total_synergy += p.stats.get('synergy_sum', 0)
                copies_triggered += p.stats.get('copies_created', 0)
                
                # Track gold for economy analysis
                gold_values.append(p.stats.get('gold_earned', 0))
                
                # Count rare cards played (rarity 4+)
                for card in p.board.alive_cards():
                    if card.rarity in ('4', '5', 'E'):
                        rare_cards += 1
                
                # Track elimination order
                if not p.alive:
                    eliminations.append(p.strategy)
            
            # Add winner to eliminations (last survivor)
            eliminations.append(winner.strategy)
            
            game_data.update({
                'avg_gold_per_player': total_gold / 4,
                'total_damage': total_damage,
                'total_kills': total_kills,
                'combo_points': total_combo,
                'synergy_points': total_synergy,
                'rare_cards_played': rare_cards,
                'copies_triggered': copies_triggered,
                'eliminations': ','.join(eliminations),
            })
            
            games_data.append(game_data)
            
            # Aggregate metrics
            strategy_wins[winner.strategy] += 1
            all_turns.append(game.turn)
            all_combo.append(total_combo)
            all_synergy.append(total_synergy)
            all_damage.append(total_damage)
            
            # Economy snowball indicator (std dev of gold earned)
            if len(gold_values) > 1:
                mean_gold = sum(gold_values) / len(gold_values)
                variance = sum((x - mean_gold) ** 2 for x in gold_values) / len(gold_values)
                gold_stds.append(variance ** 0.5)
            
        except Exception as e:
            # Capture error details
            error_msg = f"Game {game_num + 1} FAILED: {str(e)}\n{traceback.format_exc()}"
            errors.append(error_msg)
            
            # Write error to log
            with open('output/logs/simulation_errors.log', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(error_msg)
                f.write(f"\n{'='*60}\n")
            
            # Print and exit on error
            print(f"\nERROR in game {game_num + 1}:")
            print(error_msg)
            sys.exit(1)
    
    end_time = time.time()
    runtime = end_time - start_time
    
    # Calculate aggregated metrics
    summary = {
        'games': 500,
        'runtime_seconds': round(runtime, 2),
        'games_per_second': round(500 / runtime, 2),
        'avg_turns': round(sum(all_turns) / len(all_turns), 2),
        'median_turns': median(all_turns),
        'fastest_game': min(all_turns),
        'longest_game': max(all_turns),
        'strategy_win_rates': {
            s: round(strategy_wins[s] / strategy_games[s] * 100, 2)
            for s in sim.STRATEGIES if strategy_games[s] > 0
        },
        'avg_combo': round(sum(all_combo) / len(all_combo), 2),
        'avg_synergy': round(sum(all_synergy) / len(all_synergy), 2),
        'avg_damage': round(sum(all_damage) / len(all_damage), 2),
        'economy_std': round(sum(gold_stds) / len(gold_stds), 2) if gold_stds else 0,
        'errors': len(errors),
    }
    
    return summary, games_data, errors


def write_results(summary, games_data):
    """Write results to files."""
    
    # Write summary JSON
    with open('output/results/simulation_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Write games CSV
    with open('output/results/simulation_games.csv', 'w', newline='', encoding='utf-8') as f:
        if games_data:
            writer = csv.DictWriter(f, fieldnames=games_data[0].keys())
            writer.writeheader()
            writer.writerows(games_data)


def main():
    """Main execution."""
    
    # Clean up old files
    for fname in ['output/results/simulation_summary.json', 'output/results/simulation_games.csv', 
                  'output/logs/simulation_errors.log', 'simulation_log.txt']:
        if os.path.exists(fname):
            os.remove(fname)
    
    # Run determinism check
    print("Running determinism check...")
    mismatches = run_determinism_check(seed=42)
    
    if mismatches:
        print("\nWARNING: Nondeterminism detected!")
        for m in mismatches:
            print(f"  {m}")
        print()
    
    # Run 500 games
    summary, games_data, errors = run_500_games(seed=42)
    
    # Write results
    write_results(summary, games_data)
    
    # Print final output
    print("\nSIMULATION COMPLETE")
    print(f"500 games executed")
    print(f"runtime: {summary['runtime_seconds']} sec")
    print(f"games/sec: {summary['games_per_second']}")
    print(f"summary saved to simulation_summary.json")
    
    if errors:
        print(f"\nERRORS: {len(errors)} errors occurred")
        print("See simulation_errors.log for details")
        sys.exit(1)


if __name__ == '__main__':
    main()
