"""
engine_core/combo_detector.py
═══════════════════════════════════════════════════════════════════
Combo detection — extracted from engine_core/board.py (P1-1 Phase 1).

Single responsibility: detect combo matches for micro-combat bonuses.
Board class no longer owns combo detection logic.
═══════════════════════════════════════════════════════════════════
"""

from typing import Dict, Tuple

from engine_core.constants import OPP_DIR
from engine_core.group_registry import STAT_TO_GROUP


def find_combos(board) -> Tuple[int, Dict[Tuple[int, int], Dict[int, int]]]:
    """
    Find combo matches for micro-combat bonuses (+1 per edge).
    This logic now aligns with the 'lines' seen in the UI.

    Args:
        board: Board instance with .grid and .neighbors()

    Returns:
        (combo_count, combat_bonus) tuple where:
        - combo_count: total number of combo pairs found
        - combat_bonus: dict mapping coord -> {direction: bonus_count}
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
