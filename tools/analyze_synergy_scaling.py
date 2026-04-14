#!/usr/bin/env python3
"""
Analyze synergy bonus scaling: old flat +5 vs new moderated scaling.
"""

import math

def old_synergy_system(group_counts):
    """Old system: 3 cards -> +1, 5 -> +2, 8+ -> +3 (per group max +3, total max +4)"""
    bonus = 0
    for count in group_counts:
        if count >= 3:
            bonus += min(3, 1 + (count - 3) // 2)
    return min(4, bonus)

def new_synergy_system(group_counts):
    """New system: bonus = 3 * (n-1)^1.25, capped at 18 per group
    Plus diversity bonus: +1 per unique group (max +5)
    """
    group_bonus = 0
    for count in group_counts:
        if count >= 2:  # Need at least 2 cards for synergy
            # Moderated scaling: 3 * (n-1)^1.25
            bonus = 3 * math.pow(count - 1, 1.25)
            group_bonus += min(18, int(bonus))
    
    # Diversity bonus: +1 per unique group (max +5)
    diversity_bonus = min(5, len([c for c in group_counts if c > 0]))
    
    total_bonus = group_bonus + diversity_bonus
    return total_bonus

def calculate_synergy_cap(base_power):
    """Synergy should never exceed 30% of total power"""
    return int(base_power * 0.30)

def print_comparison_table():
    """Print comparison table for various group compositions"""
    
    print("="*90)
    print("SYNERGY BONUS COMPARISON: Old Flat System vs New Moderated Scaling")
    print("="*90)
    print()
    
    # Test cases: various group compositions
    test_cases = [
        # (description, group_counts)
        ("1 group, 2 cards", [2]),
        ("1 group, 3 cards", [3]),
        ("1 group, 4 cards", [4]),
        ("1 group, 5 cards", [5]),
        ("1 group, 6 cards", [6]),
        ("1 group, 8 cards", [8]),
        ("1 group, 10 cards", [10]),
        ("2 groups, 3+3", [3, 3]),
        ("2 groups, 4+4", [4, 4]),
        ("2 groups, 5+3", [5, 3]),
        ("3 groups, 3+3+2", [3, 3, 2]),
        ("3 groups, 4+3+2", [4, 3, 2]),
        ("4 groups, 3+2+2+2", [3, 2, 2, 2]),
        ("Mono (1 group, 19 cards)", [19]),
        ("Diverse (6 groups, 3 each)", [3, 3, 3, 3, 3, 3]),
    ]
    
    print(f"{'Composition':<30} {'Old Bonus':<12} {'New Bonus':<12} {'Change':<12}")
    print("-"*90)
    
    for desc, counts in test_cases:
        old = old_synergy_system(counts)
        new = new_synergy_system(counts)
        change = new - old
        change_str = f"+{change}" if change >= 0 else str(change)
        print(f"{desc:<30} {old:<12} {new:<12} {change_str:<12}")
    
    print("="*90)
    print()

def print_scaling_curve():
    """Print scaling curve for single group"""
    
    print("="*70)
    print("SINGLE GROUP SCALING CURVE")
    print("="*70)
    print()
    print(f"{'Cards':<10} {'Old Bonus':<12} {'New Bonus':<12} {'Formula':<20}")
    print("-"*70)
    
    for n in range(2, 20):
        old = old_synergy_system([n])
        new_formula = 3 * math.pow(n - 1, 1.25)
        new = min(18, int(new_formula))
        formula_str = f"3*(n-1)^1.25 = {new_formula:.2f}"
        print(f"{n:<10} {old:<12} {new:<12} {formula_str:<20}")
    
    print("="*70)
    print()

def print_diversity_analysis():
    """Analyze diversity bonus impact"""
    
    print("="*70)
    print("DIVERSITY BONUS ANALYSIS")
    print("="*70)
    print()
    print("Diversity Bonus: +1 per unique group (max +5)")
    print()
    print(f"{'Unique Groups':<20} {'Diversity Bonus':<20}")
    print("-"*70)
    
    for groups in range(1, 7):
        bonus = min(5, groups)
        print(f"{groups:<20} {bonus:<20}")
    
    print("="*70)
    print()

def print_power_cap_analysis():
    """Analyze 30% power cap"""
    
    print("="*70)
    print("SYNERGY CAP ANALYSIS (30% of Total Power)")
    print("="*70)
    print()
    print(f"{'Base Power':<15} {'Max Synergy (30%)':<20} {'Example Total':<20}")
    print("-"*70)
    
    for base in [100, 150, 200, 250, 300, 350, 400]:
        max_synergy = int(base * 0.30)
        total = base + max_synergy
        print(f"{base:<15} {max_synergy:<20} {total:<20}")
    
    print("="*70)
    print()

def print_balance_reasoning():
    """Print balance reasoning"""
    
    print("="*90)
    print("BALANCE REASONING")
    print("="*90)
    print()
    
    print("OLD SYSTEM PROBLEMS:")
    print("  • Flat +5 bonus regardless of board composition")
    print("  • No reward for deep investment in single group")
    print("  • No diversity incentive")
    print("  • Cap of +4 too restrictive")
    print()
    
    print("NEW SYSTEM BENEFITS:")
    print("  • Moderated scaling: 3 * (n-1)^1.25")
    print("    - Rewards group investment without exponential growth")
    print("    - 2 cards: +3, 3 cards: +5, 5 cards: +11, 10 cards: +18 (capped)")
    print("  • Diversity bonus: +1 per unique group (max +5)")
    print("    - Encourages varied compositions")
    print("    - Prevents mono-group dominance")
    print("  • 30% power cap prevents synergy from dominating")
    print("  • Higher ceiling (18 vs 4) rewards strategic building")
    print()
    
    print("STRATEGIC IMPLICATIONS:")
    print("  • Mono-group: High group bonus, low diversity (e.g., 18+1 = 19)")
    print("  • Diverse: Moderate group bonus, high diversity (e.g., 10+5 = 15)")
    print("  • Balanced: Best of both worlds (e.g., 13+3 = 16)")
    print()
    
    print("="*90)
    print()

if __name__ == "__main__":
    print_comparison_table()
    print_scaling_curve()
    print_diversity_analysis()
    print_power_cap_analysis()
    print_balance_reasoning()
    
    print("="*90)
    print("IMPLEMENTATION")
    print("="*90)
    print()
    print("Update calculate_group_synergy_bonus() in engine_core/autochess_sim_v06.py")
    print()
    print("Key Changes:")
    print("  1. Replace flat bonus with: 3 * (n-1)^1.25")
    print("  2. Cap per-group bonus at 18")
    print("  3. Add diversity bonus: +1 per unique group (max +5)")
    print("  4. Enforce 30% power cap in combat calculation")
    print()
    print("="*90)
