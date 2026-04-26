"""================================================================
|         AUTOCHESS HYBRID - Board Module                      |
|  Board class for hex grid management                         |
================================================================

This module contains the Board class which manages the hex grid.
Combo detection, damage calculation, and combat resolution have
been extracted to dedicated modules (combo_detector.py, damage_calculator.py).
"""

from typing import Dict, List, Optional, Tuple

# Import Card and constants
from engine_core.card import Card
from engine_core.constants import (
    BOARD_RADIUS, HEX_DIRS, RARITY_DMG_BONUS
)

# Backward-compatible re-exports from extracted modules
from engine_core.combo_detector import find_combos  # noqa: F401 — moved to combo_detector.py (P1-1 Phase 1)
from engine_core.damage_calculator import CombatResult, resolve_single_combat, calculate_damage  # noqa: F401 — moved to damage_calculator.py (P1-1 Phase 2)


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
        # Optional callback invoked after board mutations. GameState can hook this
        # to invalidate UI caches even when mutations happen outside GameState APIs.
        self._mutation_callback = None

    def place(self, coord: Tuple[int, int], card: Card):
        # Clean up old card's coord_index entry if replacing
        old = self.grid.get(coord)
        if old is not None:
            self.coord_index.pop(old.uid, None)
        self.grid[coord] = card
        self.coord_index[card.uid] = coord
        if self._mutation_callback is not None:
            self._mutation_callback()

    def remove(self, coord: Tuple[int, int]):
        card = self.grid.pop(coord, None)
        if card is not None:
            self.coord_index.pop(card.uid, None)
            if self._mutation_callback is not None:
                self._mutation_callback()

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


# Note: CombatResult, resolve_single_combat, calculate_damage moved to
#       engine_core/damage_calculator.py (P1-1 Phase 2)


# ===================================================================
# COMBO RESOLVER
# ===================================================================

# ===================================================================
# SYNERGY & CLUSTER CALCULATOR — Delegates to engine_core/synergy.py
# ===================================================================

def calculate_group_synergy_bonus(board: Board) -> int:
    """
    Board objesi üzerinden toplam synergy puanını hesaplar.

    BFS mantığı artık engine_core/synergy.py::compute_board_synergy()
    içinde — tek kaynak (Single Source of Truth).

    Bu fonksiyon combat_engine ve eski çağrı noktaları için
    backward-compatible wrapper olarak kalmıştır.
    """
    from engine_core.synergy import compute_board_synergy
    return compute_board_synergy(board)


# Note: 30% power cap enforced in combat_phase (not here)
# Note: find_combos() moved to engine_core/combo_detector.py (P1-1 Phase 1)
# Note: CombatResult, resolve_single_combat, calculate_damage moved to damage_calculator.py (P1-1 Phase 2)
# Note: combat_phase() moved to engine_core/combat_engine.py (P1-1 Phase 3) — backward-compat re-export below


# Backward-compatible re-export of combat_phase for legacy call-sites.
# The actual implementation lives in engine_core/combat_resolver.py.
# This wrapper delegates to the single-source implementation.

def combat_phase(board_a, board_b,
                 combo_bonus_a, combo_bonus_b,
                 player_a=None, player_b=None, ctx=None):
    """Resolve combat at every overlapping coordinate.

    Backward-compatible wrapper — delegates to combat_resolver.resolve_combat_phase().
    New code should use combat_resolver.resolve_combat_phase() directly.
    """
    from engine_core.combat_resolver import resolve_combat_phase
    from engine_core.passive_trigger import trigger_passive
    return resolve_combat_phase(
        board_a, board_b, combo_bonus_a, combo_bonus_b,
        player_a, player_b, ctx,
        trigger_passive_fn=trigger_passive,
    )
