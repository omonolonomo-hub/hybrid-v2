"""
engine_core/damage_calculator.py
═══════════════════════════════════════════════════════════════════
Damage and combat resolution — extracted from engine_core/board.py (P1-1 Phase 2).

Single responsibility: resolve single-card combat and calculate damage.
Board class no longer owns combat resolution or damage formula logic.
═══════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from engine_core.card import Card
from engine_core.constants import (
    EARLY_GAME_TURNS, SCALING_END_TURN, EARLY_DAMAGE_PERCENT,
    LATE_DAMAGE_PERCENT, SCALING_PERCENT_STEP, EARLY_CAP_TURNS, EARLY_DAMAGE_CAP,
)
from engine_core.group_registry import GroupRegistry, STAT_TO_GROUP


# ===================================================================
# COMBAT RESULT
# ===================================================================

@dataclass
class CombatResult:
    winner_coord:  Optional[Tuple[int, int]]  # None = draw
    loser_coord:   Optional[Tuple[int, int]]
    card_killed:   bool
    points_a:      int   # points player A earns from this combat
    points_b:      int
    edge_wins_a:   int
    edge_wins_b:   int


# ===================================================================
# COMBAT RESOLVER
# ===================================================================

def resolve_single_combat(card_a: Card, card_b: Card,
                          bonus_a: Dict[int, int] = None,
                          bonus_b: Dict[int, int] = None) -> Tuple[int, int]:
    """
    Compare two cards on one coordinate.
    Returns: (a_wins, b_wins) - edge win counts.
    
    NOTE: Hidden combat bonuses are carried in card meta and distributed evenly
    across all edges.
    """
    if bonus_a is None: bonus_a = {}
    if bonus_b is None: bonus_b = {}
    
    bonus_total_a = card_a.get_combat_bonus_total()
    bonus_total_b = card_b.get_combat_bonus_total()
    
    # Distribute bonuses evenly across edges (integer division)
    bonus_per_edge_a = bonus_total_a // 6 if bonus_total_a > 0 else 0
    bonus_per_edge_b = bonus_total_b // 6 if bonus_total_b > 0 else 0
    
    a_wins = 0
    b_wins = 0
    edges_a = card_a.rotated_edges()   # rotation-aware
    edges_b = card_b.rotated_edges()   # rotation-aware
    for d in range(6):
        va = edges_a[d][1] if d < len(edges_a) else 0
        vb = edges_b[d][1] if d < len(edges_b) else 0
        va += bonus_a.get(d, 0) + bonus_per_edge_a
        vb += bonus_b.get(d, 0) + bonus_per_edge_b

        if va > 0 and vb > 0:
            ga = STAT_TO_GROUP.get(edges_a[d][0]) if d < len(edges_a) else None
            gb = STAT_TO_GROUP.get(edges_b[d][0]) if d < len(edges_b) else None
            if ga and gb:
                if GroupRegistry.beats(ga, gb):
                    va += 1
                elif GroupRegistry.beats(gb, ga):
                    vb += 1

        if va > vb:
            a_wins += 1
        elif vb > va:
            b_wins += 1
    return a_wins, b_wins


# ===================================================================
# DAMAGE FORMULA
# ===================================================================

def calculate_damage(winner_pts: int, loser_pts: int, winner_board, turn: int = 99) -> int:
    """
    DAMAGE = |W_pts - L_pts| + floor(living_cards/2) + rarity term (dampened)
    FIX 8: halved alive_count contribution and rarity to reduce snowball; score gap matters more.
    
    BAL 5 - Early Game Damage Cap & Turn Scaling:
    - Turn 1-5: Damage scaled to 50%
    - Turn 6-15: Damage scales linearly from 50% to 100% (+5% per turn)
    - Turn 16+: Full damage (100%)
    - Turn 1-10: Hard cap at 15 damage maximum (prevents early eliminations)
    
    NOTE: Uses integer-only arithmetic for deterministic cross-platform behavior.
          No float operations to ensure identical results across all CPUs/compilers.
    
    Args:
        winner_pts: Winner's total points
        loser_pts: Loser's total points
        winner_board: Board instance of the winner (for alive_count / rarity_bonus)
        turn: Current game turn number
    
    Returns:
        Final damage value (minimum 1)
    """
    base   = abs(winner_pts - loser_pts)
    alive  = winner_board.alive_count() // 2          # dampened
    rarity = winner_board.rarity_bonus() // 2          # dampened
    raw_damage = max(1, base + alive + rarity)
    
    # BAL 5: Turn-based damage scaling (early game protection)
    # Uses integer percentages (0-100) for deterministic behavior
    if turn <= EARLY_GAME_TURNS:
        # Turns 1-5: 50% damage
        damage_percent = EARLY_DAMAGE_PERCENT
    elif turn <= SCALING_END_TURN:
        # Turns 6-15: Linear scaling from 50% to 100%
        # Formula: 50 + (turn - 5) * 5
        damage_percent = EARLY_DAMAGE_PERCENT + ((turn - EARLY_GAME_TURNS) * SCALING_PERCENT_STEP)
    else:
        # Turn 16+: Full damage
        damage_percent = LATE_DAMAGE_PERCENT
    
    # Apply damage scaling using integer-only arithmetic
    # (raw_damage * percent) // 100 ensures deterministic behavior
    scaled_damage = (raw_damage * damage_percent) // 100
    final_damage = max(1, scaled_damage)  # Minimum 1 damage
    
    # BAL 5: Hard cap for early game
    if turn <= EARLY_CAP_TURNS:
        final_damage = min(final_damage, EARLY_DAMAGE_CAP)
    
    return final_damage
