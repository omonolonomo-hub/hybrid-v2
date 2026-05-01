"""
Generated SYNERGY_FIELD Passive Handlers
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

def _mark_pre_combat(card: 'Card') -> None:
    card.inc_meta("_sf_pc")

def _current_stacks(card: 'Card') -> int:
    return card.get_meta("_sf_stacks", 0)

def _add_temp_effect(card: 'Card', stat_name: str, delta: int, turn: int) -> None:
    if card.has_stat(stat_name):
        card.add_effect(
            Effect(
                source="synergy_field",
                stat_name=stat_name,
                delta=delta,
                duration=1,
                applied_turn=turn,
                priority=int(EffectPriority.COMBAT_DEBUFF),
            )
        )

# SYNERGY_FIELD HANDLERS - Missing implementations
# ======================================================================

@passive("Kraken")
def _passive_kraken(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Kraken: While on board, neighboring enemy cards' Connection edges take -1 field effect."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord and opponent:
            turn = ctx.get("turn", 1)
            # Find enemy cards adjacent to this position
            for neighbor_card in opponent.board.alive_cards():
                enemy_coord = _find_coord(opponent.board, neighbor_card)
                if enemy_coord and _is_adjacent(coord, enemy_coord):
                    _add_temp_effect(neighbor_card, "Connection", -1, turn)
        return 1
    return 0

def _is_adjacent(coord1, coord2):
    """Check if two hex coordinates are adjacent"""
    dx = abs(coord1[0] - coord2[0])
    dy = abs(coord1[1] - coord2[1])
    return (dx <= 1 and dy <= 1 and dx + dy <= 2)

@passive("Opera")
def _passive_opera(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Opera: When 2+ Art cards on board, +1 Prestige to all Art cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "Art & Culture" in c.category]
        if len(category_cards) >= 2:
            for target_card in category_cards:
                if target_card.has_stat("Prestige"):
                    target_card.add_base_stat("Prestige", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Baroque")
def _passive_baroque(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Baroque: When 2+ Art cards on board, +1 to Prestige edges."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "Art & Culture" in c.category]
        if len(category_cards) >= 2:
            for target_card in category_cards:
                if target_card.has_stat("Prestige"):
                    target_card.add_base_stat("Prestige", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Blue Whale")
def _passive_blue_whale(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Blue Whale: When 3+ Nature cards on board, +1 Harmony to all ally cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        category_cards = [c for c in owner.board.alive_cards() if "Nature" in c.category]
        if len(category_cards) >= 3:
            for target_card in owner.board.alive_cards():
                if target_card.has_stat("Harmony"):
                    target_card.add_base_stat("Harmony", 1)
        return 1
    return 0

@passive("Coral Reef")
def _passive_coral_reef(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Coral Reef: Spreads +1 Harmony to neighboring ally Nature cards per turn."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if "Nature" in neighbor_card.category and neighbor_card.has_stat("Harmony"):
                    neighbor_card.add_base_stat("Harmony", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Rainforest")
def _passive_rainforest(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Rainforest: When 4+ Nature cards on board, +1 Spread to all Nature cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "Nature" in c.category]
        if len(category_cards) >= 4:
            for target_card in category_cards:
                if target_card.has_stat("Spread"):
                    target_card.add_base_stat("Spread", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Cordyceps")
def _passive_cordyceps(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cordyceps: While on board, opponent's neighboring cards take -1 Trace per turn."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord and opponent:
            turn = ctx.get("turn", 1)
            # Find enemy cards adjacent to this position
            for neighbor_card in opponent.board.alive_cards():
                enemy_coord = _find_coord(opponent.board, neighbor_card)
                if enemy_coord and _is_adjacent(coord, enemy_coord):
                    _add_temp_effect(neighbor_card, "Trace", -1, turn)
        return 1
    return 0

def _is_adjacent(coord1, coord2):
    """Check if two hex coordinates are adjacent"""
    dx = abs(coord1[0] - coord2[0])
    dy = abs(coord1[1] - coord2[1])
    return (dx <= 1 and dy <= 1 and dx + dy <= 2)

@passive("Milky Way")
def _passive_milky_way(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Milky Way: When 3+ Cosmos cards on board, +1 Gravity to all Cosmos cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(category_cards) >= 3:
            for target_card in category_cards:
                if target_card.has_stat("Gravity"):
                    target_card.add_base_stat("Gravity", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Andromeda Galaxy")
def _passive_andromeda_galaxy(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Andromeda Galaxy: When 4+ Cosmos cards on board, Gravity edges +2."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(category_cards) >= 4:
            for target_card in category_cards:
                if target_card.has_stat("Gravity"):
                    target_card.add_base_stat("Gravity", 2)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Europa")
def _passive_europa(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Europa: Spreads +1 Harmony to neighboring ally Cosmos cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if "Cosmos" in neighbor_card.category and neighbor_card.has_stat("Harmony"):
                    neighbor_card.add_base_stat("Harmony", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0

@passive("Quasar")
def _passive_quasar(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Quasar: When 3+ Cosmos cards on board, +1 Spread to all cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        category_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(category_cards) >= 3:
            for target_card in owner.board.alive_cards():
                if target_card.has_stat("Spread"):
                    target_card.add_base_stat("Spread", 1)
        return 1
    return 0

# TODO: Template 'category_count_multi_buff' not implemented for Periodic Table

# TODO: Template 'global_buff' not implemented for Higgs Boson

# TODO: Template 'diversity_buff' not implemented for Renaissance

@passive("Roman Empire")
def _passive_roman_empire(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Roman Empire: When 4+ History cards on board, +1 Durability to all ally cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        category_cards = [c for c in owner.board.alive_cards() if "History" in c.category]
        if len(category_cards) >= 4:
            for target_card in owner.board.alive_cards():
                if target_card.has_stat("Durability"):
                    target_card.add_base_stat("Durability", 1)
        return 1
    return 0

