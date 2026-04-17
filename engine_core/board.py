"""
================================================================
|         AUTOCHESS HYBRID - Board Module                      |
|  Board class and combat/combo resolution functions           |
================================================================

This module contains the Board class which manages the hex grid,
along with combat resolution, combo detection, and damage calculation.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Import Card, constants and passive trigger
try:
    from .card import Card
    from .constants import (
        BOARD_RADIUS, HEX_DIRS, OPP_DIR, RARITY_DMG_BONUS,
        STAT_TO_GROUP, GROUP_BEATS, KILL_PTS
    )
except ImportError:
    from card import Card
    from constants import (
        BOARD_RADIUS, HEX_DIRS, OPP_DIR, RARITY_DMG_BONUS,
        STAT_TO_GROUP, GROUP_BEATS, KILL_PTS
    )


# ===================================================================
# HEX GRID UTILITIES
# ===================================================================

def hex_coords(radius: int) -> List[Tuple[int, int]]:
    """Return all hex coordinates within the given radius.
    
    Uses axial coordinate system (q, r) with center at (0, 0).
    
    Formula: |q| + |r| + |q+r| <= 2*radius
    Simplified: abs(q+r) <= radius for range(-radius, radius+1)
    
    Examples:
      radius=2 -> 19 hexes (small board)
      radius=3 -> 37 hexes (standard board)
      radius=4 -> 61 hexes (large board)
    """
    return [(q, r) for q in range(-radius, radius+1)
                   for r in range(-radius, radius+1)
                   if abs(q+r) <= radius]


# Initialize board coordinates
BOARD_COORDS = hex_coords(BOARD_RADIUS)  # 37 hex (was 19)


# ===================================================================
# BOARD CLASS
# ===================================================================

class Board:
    def __init__(self):
        self.grid: Dict[Tuple[int, int], Card] = {}   # coord -> Card
        self.coord_index: Dict[int, Tuple[int, int]] = {}  # card.uid -> coord (O(1) lookup)
        self.square_card: Optional[Card] = None      # Catalyst or Eclipse
        self.has_catalyst = False
        self.has_eclipse   = False

    def place(self, coord: Tuple[int, int], card: Card):
        # Clean up old card's coord_index entry if replacing
        old = self.grid.get(coord)
        if old is not None:
            self.coord_index.pop(old.uid, None)
        self.grid[coord] = card
        self.coord_index[card.uid] = coord

    def remove(self, coord: Tuple[int, int]):
        card = self.grid.pop(coord, None)
        if card is not None:
            self.coord_index.pop(card.uid, None)

    def free_coords(self) -> List[Tuple[int, int]]:
        return [c for c in BOARD_COORDS if c not in self.grid]

    def neighbors(self, coord: Tuple[int, int]) -> List[Tuple[Tuple[int, int], int]]:
        """Return list of (neighbor_coord, direction_index)."""
        result = []
        q, r = coord
        for d, (dq, dr) in enumerate(HEX_DIRS):
            nc = (q+dq, r+dr)
            if nc in self.grid:
                result.append((nc, d))
        return result

    def alive_cards(self) -> List[Card]:
        return list(self.grid.values())

    def alive_count(self) -> int:
        return len(self.grid)

    def rarity_bonus(self) -> int:
        """Living rarity-4 x2 + rarity-5 x3 (damage formula; empty if RARITY_DMG_BONUS cleared)."""
        bonus = 0
        for card in self.grid.values():
            bonus += RARITY_DMG_BONUS.get(card.rarity, 0)
        return bonus


# ===================================================================
# BOARD HELPER FUNCTIONS
# ===================================================================

def _find_coord(board: Board, c: Card) -> Optional[Tuple[int, int]]:
    """Find board coordinate of card instance c. O(1) lookup via coord_index."""
    return board.coord_index.get(c.uid)


def _neighbor_cards(board: Board, coord: Tuple[int, int]) -> List[Card]:
    """Neighbor cards on board at coord."""
    return [board.grid[nc] for (nc, _) in board.neighbors(coord) if nc in board.grid]


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
    
    NOTE: Includes _ prefix bonuses (e.g., _yggdrasil_bonus, _pulsar_buff) in combat.
    These bonuses are distributed evenly across all edges.
    """
    if bonus_a is None: bonus_a = {}
    if bonus_b is None: bonus_b = {}
    
    # Calculate total _ prefix bonuses for each card
    bonus_total_a = sum(v for k, v in card_a.stats.items() if str(k).startswith("_") and isinstance(v, int))
    bonus_total_b = sum(v for k, v in card_b.stats.items() if str(k).startswith("_") and isinstance(v, int))
    
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
                if GROUP_BEATS.get(ga) == gb:
                    va += 1
                elif GROUP_BEATS.get(gb) == ga:
                    vb += 1

        if va > vb:
            a_wins += 1
        elif vb > va:
            b_wins += 1
    return a_wins, b_wins


# ===================================================================
# COMBO RESOLVER
# ===================================================================

# ===================================================================
# SYNERGY & CLUSTER CALCULATOR
# ===================================================================

def calculate_group_synergy_bonus(board: Board) -> int:
    """
    v0.8 CONNECTED CLUSTER SYNERGY:
    Rewrites the synergy system to be purely based on physical connections (lines).
    
    1. For each group (MIND, CONNECTION, EXISTENCE):
       - Find all connected clusters of cards via edge matches of that group.
       - Each cluster of size N gives a tiered bonus.
       - Each internal match (line) gives a linear bonus.
    2. A card can parttake in multiple clusters of DIFFERENT groups.
    
    Scoring Tiers (N = Cards in Cluster):
      - N=2: 3 Puan
      - N=3: 9 Puan
      - N=4-5: 16 Puan
      - N=6+: 25 Puan (+ 3 per additional card)
    
    Connection Bonus (L = Active Lines):
      - +2 Puan per matching edge pair.
    """
    total_bonus = 0
    groups = ["MIND", "CONNECTION", "EXISTENCE"]
    grid   = board.grid
    
    # Track which cards are already in a cluster for EACH group independently
    # group -> set of coords
    global_visited = {g: set() for g in groups}
    
    for g in groups:
        for coord in grid:
            if coord in global_visited[g]:
                continue
            
            # Start BFS to find cluster of group 'g'
            cluster_coords, edge_matches = _find_cluster_for_group(board, coord, g)
            
            # Must have at least a connection to count as a cluster (N >= 2)
            n = len(cluster_coords)
            if n >= 2:
                # 1. Tiered Card Bonus
                if n == 2:   tier_pts = 3
                elif n == 3: tier_pts = 9
                elif n <= 5: tier_pts = 16
                else:        tier_pts = 25 + (n - 6) * 3
                
                # 2. Linear Connection Bonus (each line = 2 pts)
                # find_cluster returns total edge matches (L), each pair counted once
                conn_pts = edge_matches * 2
                
                total_bonus += (tier_pts + conn_pts)
                global_visited[g].update(cluster_coords)
                
    return total_bonus


def _find_cluster_for_group(board: Board, start_coord: Tuple[int, int], group_name: str) -> Tuple[set, int]:
    """
    Finds a group-specific cluster starting from start_coord using BFS.
    Returns: (set of coords in cluster, total internal edge matches)
    """
    cluster = {start_coord}
    queue   = [start_coord]
    visited = {start_coord}
    internal_matches = 0
    match_pairs = set() # To avoid double counting (A,B) vs (B,A)
    
    grid = board.grid
    
    # Get initial card info
    card_start = grid[start_coord]
    
    while queue:
        curr_coord = queue.pop(0)
        curr_card  = grid[curr_coord]
        curr_edges = curr_card.rotated_edges()
        
        for neighbor_coord, direction in board.neighbors(curr_coord):
            neighbor_card = grid[neighbor_coord]
            nb_edges      = neighbor_card.rotated_edges()
            
            # Check edge match of group_name
            # dir_idx for current card matches opp_dir for neighbor
            opp_dir = OPP_DIR[direction]
            
            stat_a, _ = curr_edges[direction]
            stat_b, _ = nb_edges[opp_dir]
            
            group_a = STAT_TO_GROUP.get(stat_a)
            group_b = STAT_TO_GROUP.get(stat_b)
            
            if group_a == group_name and group_b == group_name:
                # It's a group match!
                pair = tuple(sorted((curr_coord, neighbor_coord)))
                if pair not in match_pairs:
                    internal_matches += 1
                    match_pairs.add(pair)
                
                if neighbor_coord not in visited:
                    visited.add(neighbor_coord)
                    cluster.add(neighbor_coord)
                    queue.append(neighbor_coord)
                    
    return cluster, internal_matches


# ===================================================================
# COMBO RESOLVER (Legacy compatibility & micro-bonuses)
# ===================================================================

def find_combos(board: Board) -> Tuple[int, Dict[Tuple[int, int], Dict[int, int]]]:
    """
    Find combo matches for micro-combat bonuses (+1 per edge).
    This logic now aligns with the 'lines' seen in the UI.
    """
    combo_count = 0
    combat_bonus: Dict[Tuple[int, int], Dict[int, int]] = {}
    counted: set = set()

    grid = board.grid
    for coord, card in grid.items():
        edges = card.rotated_edges()
        for neighbor_coord, direction in board.neighbors(coord):
            pair = tuple(sorted((coord, neighbor_coord)))
            if pair in counted:
                continue
            
            neighbor_card = grid[neighbor_coord]
            nb_edges      = neighbor_card.rotated_edges()
            opp_dir       = OPP_DIR[direction]
            
            stat_a, _ = edges[direction]
            stat_b, _ = nb_edges[opp_dir]
            
            if STAT_TO_GROUP.get(stat_a) == STAT_TO_GROUP.get(stat_b):
                combo_count += 1
                if coord not in combat_bonus: combat_bonus[coord] = {}
                if neighbor_coord not in combat_bonus: combat_bonus[neighbor_coord] = {}
                combat_bonus[coord][direction] = combat_bonus[coord].get(direction, 0) + 1
                combat_bonus[neighbor_coord][opp_dir] = combat_bonus[neighbor_coord].get(opp_dir, 0) + 1
            counted.add(pair)

    return combo_count, combat_bonus

    
    # Note: 30% power cap enforced in combat_phase (not here)
    # This allows flexibility while preventing synergy from dominating
    
    return total_bonus


# ===================================================================
# DAMAGE FORMULA
# ===================================================================

def calculate_damage(winner_pts: int, loser_pts: int, winner_board: Board, turn: int = 99) -> int:
    """
    DAMAGE = |W_pts - L_pts| + floor(living_cards/2) + rarity term (dampened)
    FIX 8: halved alive_count contribution and rarity to reduce snowball; score gap matters more.
    
    BAL 5 - Early Game Damage Cap & Turn Multiplier:
    - Turn 1-5: Damage multiplier starts at 0.5x
    - Turn 6-15: Multiplier scales linearly from 0.5x to 1.0x
    - Turn 16+: Full damage (1.0x multiplier)
    - Turn 1-10: Hard cap at 15 damage maximum (prevents early eliminations)
    """
    base   = abs(winner_pts - loser_pts)
    alive  = winner_board.alive_count() // 2          # dampened
    rarity = winner_board.rarity_bonus() // 2          # dampened
    raw_damage = max(1, base + alive + rarity)
    
    # BAL 5: Turn-based damage multiplier (early game protection)
    if turn <= 5:
        # Turns 1-5: 50% damage
        turn_multiplier = 0.5
    elif turn <= 15:
        # Turns 6-15: Linear scaling from 0.5x to 1.0x
        # Formula: 0.5 + (turn - 5) * 0.05
        turn_multiplier = 0.5 + ((turn - 5) * 0.05)
    else:
        # Turn 16+: Full damage
        turn_multiplier = 1.0
    
    # Apply turn multiplier
    scaled_damage = int(raw_damage * turn_multiplier)
    final_damage = max(1, scaled_damage)  # Minimum 1 damage
    
    # BAL 5: Hard cap for early game (turns 1-10)
    if turn <= 10:
        final_damage = min(final_damage, 15)
    
    return final_damage


# ===================================================================
# COMBAT PHASE
# ===================================================================

def combat_phase(board_a: Board, board_b: Board,
                 combo_bonus_a: Dict[Tuple[int, int], Dict[int, int]],
                 combo_bonus_b: Dict[Tuple[int, int], Dict[int, int]],
                 player_a=None, player_b=None, ctx=None) -> Tuple[int, int, int]:
    """
    Resolve combat at every overlapping coordinate.
    Returns: (kill_pts_a, kill_pts_b, draw_count)
    """
    # Lazy import avoids circular dependency:
    # board <- passive_trigger <- passives.registry <- copy_handlers <- board
    try:
        from .passive_trigger import trigger_passive
    except ImportError:
        from passive_trigger import trigger_passive

    if ctx is None: ctx = {}
    kill_a = 0
    kill_b = 0
    draws  = 0

    grid_a = board_a.grid
    grid_b = board_b.grid
    shared_coords = set(grid_a.keys()) & set(grid_b.keys())

    for coord in shared_coords:
        if coord not in grid_a or coord not in grid_b:
            continue
        card_a = grid_a[coord]
        card_b = grid_b[coord]

        ba = combo_bonus_a.get(coord, {})
        bb = combo_bonus_b.get(coord, {})

        a_wins, b_wins = resolve_single_combat(card_a, card_b, ba, bb)

        if a_wins > b_wins:
            kill_a += trigger_passive(card_a, "combat_win", player_a, player_b, ctx, verbose=False)
            kill_b += trigger_passive(card_b, "combat_lose", player_b, player_a, ctx, verbose=False)

            card_b.lose_highest_edge()
            if card_b.is_eliminated():
                trigger_passive(card_b, "card_killed", player_b, player_a, ctx, verbose=False)
                board_b.remove(coord)
                kill_a += KILL_PTS
        elif b_wins > a_wins:
            kill_b += trigger_passive(card_b, "combat_win", player_b, player_a, ctx, verbose=False)
            kill_a += trigger_passive(card_a, "combat_lose", player_a, player_b, ctx, verbose=False)

            card_a.lose_highest_edge()
            if card_a.is_eliminated():
                trigger_passive(card_a, "card_killed", player_a, player_b, ctx, verbose=False)
                board_a.remove(coord)
                kill_b += KILL_PTS
        else:
            draws += 1

    return kill_a, kill_b, draws
