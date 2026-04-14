#!/usr/bin/env python3
"""
Analyze rarity cost efficiency and compute power_per_gold ratios.
"""

import sys
sys.path.insert(0, 'engine_core')

from autochess_sim_v06 import CARD_POOL, CARD_COSTS
from collections import defaultdict

def analyze_rarity_balance():
    """Compute average power per rarity and power_per_gold efficiency."""
    
    # Group cards by rarity
    by_rarity = defaultdict(list)
    for card in CARD_POOL:
        if card.rarity != "E":  # Exclude evolved cards
            by_rarity[card.rarity].append(card)
    
    print("="*70)
    print("CURRENT RARITY BALANCE ANALYSIS")
    print("="*70)
    print()
    
    # Current costs
    print("Current Costs:")
    for rarity in ["1", "2", "3", "4", "5"]:
        cost = CARD_COSTS[rarity]
        print(f"  r{rarity}: {cost} gold")
    print()
    
    # Calculate stats per rarity
    print("="*70)
    print(f"{'Rarity':<10} {'Count':<8} {'Avg Power':<12} {'Cost':<8} {'Power/Gold':<12}")
    print("="*70)
    
    stats = {}
    for rarity in ["1", "2", "3", "4", "5"]:
        cards = by_rarity[rarity]
        if not cards:
            continue
        
        avg_power = sum(c.total_power() for c in cards) / len(cards)
        cost = CARD_COSTS[rarity]
        power_per_gold = avg_power / cost if cost > 0 else 0
        
        stats[rarity] = {
            'count': len(cards),
            'avg_power': avg_power,
            'cost': cost,
            'power_per_gold': power_per_gold
        }
        
        print(f"r{rarity:<9} {len(cards):<8} {avg_power:<12.2f} {cost:<8} {power_per_gold:<12.2f}")
    
    print("="*70)
    print()
    
    # Efficiency comparison
    print("EFFICIENCY ANALYSIS:")
    print("-" * 70)
    baseline = stats["1"]["power_per_gold"]
    for rarity in ["1", "2", "3", "4", "5"]:
        if rarity in stats:
            ppg = stats[rarity]["power_per_gold"]
            ratio = ppg / baseline if baseline > 0 else 0
            print(f"  r{rarity}: {ppg:.2f} power/gold ({ratio:.2f}x vs r1)")
    print()
    
    return stats

def propose_new_costs():
    """Propose new cost structure and show comparison."""
    
    # New proposed costs
    NEW_COSTS = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0}
    
    # Group cards by rarity
    by_rarity = defaultdict(list)
    for card in CARD_POOL:
        if card.rarity != "E":
            by_rarity[card.rarity].append(card)
    
    print("="*70)
    print("PROPOSED NEW COSTS")
    print("="*70)
    print()
    
    print("New Costs:")
    for rarity in ["1", "2", "3", "4", "5"]:
        old_cost = CARD_COSTS[rarity]
        new_cost = NEW_COSTS[rarity]
        change = "unchanged" if old_cost == new_cost else f"{old_cost} → {new_cost}"
        print(f"  r{rarity}: {new_cost} gold ({change})")
    print()
    
    # Calculate new stats
    print("="*70)
    print(f"{'Rarity':<10} {'Avg Power':<12} {'Old Cost':<10} {'New Cost':<10} {'Old PPG':<12} {'New PPG':<12}")
    print("="*70)
    
    new_stats = {}
    for rarity in ["1", "2", "3", "4", "5"]:
        cards = by_rarity[rarity]
        if not cards:
            continue
        
        avg_power = sum(c.total_power() for c in cards) / len(cards)
        old_cost = CARD_COSTS[rarity]
        new_cost = NEW_COSTS[rarity]
        old_ppg = avg_power / old_cost if old_cost > 0 else 0
        new_ppg = avg_power / new_cost if new_cost > 0 else 0
        
        new_stats[rarity] = {
            'avg_power': avg_power,
            'old_cost': old_cost,
            'new_cost': new_cost,
            'old_ppg': old_ppg,
            'new_ppg': new_ppg
        }
        
        print(f"r{rarity:<9} {avg_power:<12.2f} {old_cost:<10} {new_cost:<10} {old_ppg:<12.2f} {new_ppg:<12.2f}")
    
    print("="*70)
    print()
    
    # Efficiency comparison
    print("NEW EFFICIENCY ANALYSIS:")
    print("-" * 70)
    baseline = new_stats["1"]["new_ppg"]
    for rarity in ["1", "2", "3", "4", "5"]:
        if rarity in new_stats:
            old_ppg = new_stats[rarity]["old_ppg"]
            new_ppg = new_stats[rarity]["new_ppg"]
            ratio = new_ppg / baseline if baseline > 0 else 0
            improvement = ((new_ppg - old_ppg) / old_ppg * 100) if old_ppg > 0 else 0
            print(f"  r{rarity}: {new_ppg:.2f} power/gold ({ratio:.2f}x vs r1) | {improvement:+.1f}% change")
    print()
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Key Changes:")
    print("  • r4: 8 → 5 gold (37.5% cost reduction)")
    print("  • r5: 10 → 7 gold (30% cost reduction)")
    print("  • r1-r3: unchanged")
    print()
    print("Impact:")
    print("  • Rare cards become more accessible early-mid game")
    print("  • rare_hunter strategy no longer stalls early game")
    print("  • Power/gold efficiency more balanced across rarities")
    print("  • Shop roll odds unchanged (only costs adjusted)")
    print()
    
    return NEW_COSTS

if __name__ == "__main__":
    # Analyze current balance
    current_stats = analyze_rarity_balance()
    
    # Propose new costs
    new_costs = propose_new_costs()
    
    print("="*70)
    print("IMPLEMENTATION")
    print("="*70)
    print()
    print("Update engine_core/autochess_sim_v06.py:")
    print()
    print("OLD:")
    print('  CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 8, "5": 10, "E": 0}')
    print()
    print("NEW:")
    print('  CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0}')
    print()
    print("="*70)
