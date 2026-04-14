"""
Survival Passive Handlers

This module contains passive handlers that trigger when cards are killed or provide
survival/revival mechanics:
- card_killed: Triggers when a card is killed during combat
- Revival mechanics: Phoenix and Axolotl revive with modified stats
- Death benefits: Valhalla grants gold, Gothic Architecture and Baobab buff neighbors
"""

from typing import TYPE_CHECKING

try:
    from .base import passive
except ImportError:
    from passives.base import passive

try:
    from ..board import _find_coord, _neighbor_cards
except ImportError:
    from board import _find_coord, _neighbor_cards

if TYPE_CHECKING:
    from ..card import Card
    from ..player import Player


# ===================================================================
# DEATH BENEFIT HANDLERS
# ===================================================================

@passive("Valhalla")
def _passive_valhalla(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Valhalla: When killed, grant owner +3 gold (once per game)."""
    if trigger == "card_killed" and owner is not None and not owner.stats.get("valhalla_triggered"):
        owner.stats["valhalla_triggered"] = True
        owner.stats["valhalla_gold_pending"] = owner.stats.get("valhalla_gold_pending", 0) + 3
    return 0


# ===================================================================
# REVIVAL HANDLERS
# ===================================================================

@passive("Phoenix")
def _passive_phoenix(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Phoenix: When killed, revive with all stats set to 1 (once per combat)."""
    if trigger == "card_killed" and not card.stats.get("phoenix_used"):
        card.stats["phoenix_used"] = True
        card.stats["revived_this_combat"] = True
        for s in list(card.stats.keys()):
            if not str(s).startswith("_") and s not in ("phoenix_used", "revived_this_combat"):
                card.stats[s] = 1
        card.edges = [(s, 1) for s, _ in card.edges]
    return 0


@passive("Axolotl")
def _passive_axolotl(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Axolotl: When killed, revive with all stats set to 2 (once per combat)."""
    if trigger == "card_killed" and not card.stats.get("revived_this_combat"):
        card.stats["revived_this_combat"] = True
        card.edges = [(s, 2) for s, _ in card.edges]
        for s, _ in card.edges:
            card.stats[s] = 2
    return 0


# ===================================================================
# NEIGHBOR BUFF ON DEATH HANDLERS
# ===================================================================

@passive("Gothic Architecture")
def _passive_gothic_architecture(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Gothic Architecture: When killed, all neighbors gain +1 Durability."""
    if trigger == "card_killed" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for nc_card in _neighbor_cards(owner.board, coord):
                nc_card.edges = [(s, v+1 if s == "Durability" else v) for s, v in nc_card.edges]
                if "Durability" in nc_card.stats:
                    nc_card.stats["Durability"] += 1
    return 0


@passive("Baobab")
def _passive_baobab(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Baobab: When killed, all neighbors gain +2 Durability."""
    if trigger == "card_killed" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for nc_card in _neighbor_cards(owner.board, coord):
                nc_card.edges = [(s, v+2 if s == "Durability" else v) for s, v in nc_card.edges]
                if "Durability" in nc_card.stats:
                    nc_card.stats["Durability"] += 2
    return 0
