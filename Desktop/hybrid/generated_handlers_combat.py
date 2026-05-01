"""
Generated COMBAT Passive Handlers
======================================================================
Auto-generated handler implementations for missing passives.
"""

from typing import TYPE_CHECKING
from engine_core.passives.base import passive
from engine_core.board import _find_coord, _neighbor_cards
from engine_core.effects import Effect, EffectPriority

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player

def _add_temp_effect(card: 'Card', stat_name: str, delta: int, turn: int) -> None:
    if card.has_stat(stat_name):
        card.add_effect(
            Effect(
                source="combat",
                stat_name=stat_name,
                delta=delta,
                duration=1,
                applied_turn=turn,
                priority=int(EffectPriority.COMBAT_BUFF),
            )
        )

# COMBAT HANDLERS - Missing implementations
# ======================================================================

@passive("Quetzalcoatl")
def _passive_quetzalcoatl(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Quetzalcoatl: If combat is won, grants +1 Speed to 1 neighboring ally card for that turn."""
    if trigger == "combat_win" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            neighbors = _neighbor_cards(owner.board, coord)
            if neighbors:
                turn = ctx.get("turn", 1)
                target = neighbors[0]  # First neighbor
                _add_temp_effect(target, "Speed", 1, turn)
    return 0

@passive("Flamenco")
def _passive_flamenco(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Flamenco: If combat is won, +1 Speed to all ally cards that turn."""
    if trigger == "combat_win" and owner is not None:
        turn = ctx.get("turn", 1)
        for ally_card in owner.board.alive_cards():
            _add_temp_effect(ally_card, "Speed", 1, turn)
    return 0

# TODO: Template 'combat_win_enemy_debuff' not implemented for Asteroid Belt

# TODO: Template 'combat_win_swap_edges' not implemented for Quantum Mechanics

# TODO: Template 'combat_win_enemy_neighbor_debuff' not implemented for Mongol Empire

@passive("Sparta")
def _passive_sparta(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Sparta: If combat is won, accumulates +2 Power permanently (max +4 throughout game)."""
    if trigger == "combat_win":
        total_buff = card.get_meta("_sparta_total", 0)
        if total_buff >= 4:
            return 0
        
        if card.has_stat("Power"):
            card.add_base_stat("Power", 2)
            card.set_meta("_sparta_total", total_buff + 2)
    return 0

