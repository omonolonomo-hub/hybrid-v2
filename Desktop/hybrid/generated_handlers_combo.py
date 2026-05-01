"""
Generated COMBO Passive Handlers
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

# COMBO HANDLERS - Missing implementations
# ======================================================================

@passive("Jazz")
def _passive_jazz(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Jazz: When combo match occurs, gain +1 gold (max 2/turn)."""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        if combo_count > 0:
            turn = ctx.get("turn", 1)
            last_turn = card.get_meta("_jazz_turn", -1)
            if last_turn != turn:
                card.set_meta("_jazz_turn", turn)
                card.set_meta("_jazz_count", 0)
            
            count = card.get_meta("_jazz_count", 0)
            if count < 2:
                owner.gold += 1
                owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
                card.set_meta("_jazz_count", count + 1)
        return 1
    return 0

# TODO: Template 'combo_neighbor_temp_buff' not implemented for Bioluminescence

