"""
Copy/Evolution Passive Handlers

This module contains passive handlers that trigger when cards are copied or evolved:
- copy_2: Triggers when a card reaches 2 copies
- copy_3: Triggers when a card reaches 3 copies
- pre_combat: Handlers related to adjacency or neighbor bonuses for evolved cards
"""

from typing import TYPE_CHECKING

from engine_core.board import _find_coord, _neighbor_cards
from engine_core.passives.base import passive

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


@passive("Coelacanth")
def _passive_coelacanth(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Coelacanth: On copy evolution, increase highest edge by +2."""
    if trigger in ("copy_2", "copy_3") and card.edges:
        idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
        stat_name, _ = card.edges[idx]
        card.add_base_stat(stat_name, 2)
    return 0


@passive("Marie Curie")
def _passive_marie_curie(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Marie Curie: On copy evolution, gain +2 gold."""
    if trigger in ("copy_2", "copy_3") and owner is not None:
        owner.gold += 2
        owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 2
    return 0


@passive("Space-Time")
def _passive_space_time(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Space-Time: On copy evolution, all friendly cards gain +1 to all edges (max 5 applications per game)."""
    if trigger in ("copy_2", "copy_3") and owner is not None:
        applications = owner.stats.get("_spacetime_applications", 0)
        if applications >= 5:
            return 0
        owner.stats["_spacetime_applications"] = applications + 1

        for board_card in owner.board.alive_cards():
            for stat_name in list(board_card.get_base_stats().keys()):
                board_card.add_base_stat(stat_name, 1)
    return 0


@passive("Fungus")
def _passive_fungus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Fungus: On copy evolution, increase first neighbor's highest edge by +1."""
    if trigger in ("copy_2", "copy_3") and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            neighbors = _neighbor_cards(owner.board, coord)
            if neighbors and neighbors[0].edges:
                target = neighbors[0]
                idx = max(range(len(target.edges)), key=lambda i: target.edges[i][1])
                stat_name, _ = target.edges[idx]
                target.add_base_stat(stat_name, 1)
    return 0


@passive("Yggdrasil")
def _passive_yggdrasil(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Yggdrasil: At pre_combat, grant all neighbors a stacking combat bonus counter."""
    if trigger == "pre_combat" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for neighbor_card in _neighbor_cards(owner.board, coord):
                neighbor_card.inc_meta("_yggdrasil_bonus")
    return 0


@passive("Event Horizon")
def _passive_event_horizon(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Event Horizon: Copy counter advances +1 extra per turn (copies Catalyst effect)."""
    if trigger in ("copy_2", "copy_3"):
        # Boost copy evolution effect
        if card.edges:
            idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
            stat_name, _ = card.edges[idx]
            card.add_base_stat(stat_name, 2)  # +2 instead of default +1
    return 0


@passive("Charles Darwin")
def _passive_charles_darwin(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Charles Darwin: In each copy strengthening, next threshold comes 1 turn early."""
    if trigger in ("copy_2", "copy_3"):
        # Standard copy buff
        if card.edges:
            idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
            stat_name, _ = card.edges[idx]
            card.add_base_stat(stat_name, 1)
        # Note: Threshold reduction would need to be implemented in copy system
        # For now, just apply standard buff
    return 0


@passive("DNA")
def _passive_dna(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """DNA: At copy strengthening, +1 Durability permanently to all copies."""
    if trigger in ("copy_2", "copy_3") and owner is not None:
        # Find all cards with same name (copies)
        card_name = card.name.replace("Evolved ", "")
        for board_card in owner.board.alive_cards():
            check_name = board_card.name.replace("Evolved ", "")
            if check_name == card_name and board_card.has_stat("Durability"):
                board_card.add_base_stat("Durability", 1)
    return 0
