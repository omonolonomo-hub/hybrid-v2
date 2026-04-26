"""
Survival Passive Handlers

This module contains passive handlers that trigger when cards are killed or provide
survival or revival mechanics.
"""

from typing import TYPE_CHECKING

from engine_core.board import _find_coord, _neighbor_cards
from engine_core.passives.base import passive

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


@passive("Valhalla")
def _passive_valhalla(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Valhalla: When killed, grant owner +3 gold (once per game)."""
    if trigger == "card_killed" and owner is not None and not owner.stats.get("valhalla_triggered"):
        owner.stats["valhalla_triggered"] = True
        owner.stats["valhalla_gold_pending"] = owner.stats.get("valhalla_gold_pending", 0) + 3
    return 0


@passive("Phoenix")
def _passive_phoenix(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Phoenix: When killed, revive with all stats set to 1 (once per combat)."""
    if trigger == "card_killed" and not card.get_meta("phoenix_used"):
        card.set_meta("phoenix_used", True)
        card.set_meta("revived_this_combat", True)
        for stat_name in list(card.get_base_stats().keys()):
            card.set_base_stat(stat_name, 1)
    return 0


@passive("Axolotl")
def _passive_axolotl(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Axolotl: When killed, revive with all stats set to 2 (once per combat)."""
    if trigger == "card_killed" and not card.get_meta("revived_this_combat"):
        card.set_meta("revived_this_combat", True)
        for stat_name in list(card.get_base_stats().keys()):
            card.set_base_stat(stat_name, 2)
    return 0


@passive("Gothic Architecture")
def _passive_gothic_architecture(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Gothic Architecture: When killed, all neighbors gain +1 Durability."""
    if trigger == "card_killed" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.has_stat("Durability"):
                    neighbor_card.add_base_stat("Durability", 1)
    return 0


@passive("Baobab")
def _passive_baobab(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Baobab: When killed, all neighbors gain +2 Durability."""
    if trigger == "card_killed" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.has_stat("Durability"):
                    neighbor_card.add_base_stat("Durability", 2)
    return 0
