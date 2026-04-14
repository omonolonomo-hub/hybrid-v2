"""
Copy/Evolution Passive Handlers

This module contains passive handlers that trigger when cards are copied or evolved:
- copy_2: Triggers when a card reaches 2 copies (evolution to 2-star)
- copy_3: Triggers when a card reaches 3 copies (evolution to 3-star)
- pre_combat: Handlers related to adjacency/neighbor bonuses for evolved cards

These handlers typically provide bonuses when cards are strengthened through the copy system.
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
# COPY HANDLERS (copy_2, copy_3)
# ===================================================================

@passive("Coelacanth")
def _passive_coelacanth(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Coelacanth: On copy evolution, increase highest edge by +2."""
    if trigger in ("copy_2", "copy_3") and card.edges:
        idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
        s, v = card.edges[idx]
        card.edges[idx] = (s, v + 2)
        card.stats[s] = v + 2
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
        # Cap total applications at 5 per game
        applications = owner.stats.get("_spacetime_applications", 0)
        if applications >= 5:
            return 0
        owner.stats["_spacetime_applications"] = applications + 1
        
        for c in owner.board.alive_cards():
            c.edges = [(s, v + 1) for s, v in c.edges]
            for s, v in c.edges:
                c.stats[s] = v
    return 0


@passive("Fungus")
def _passive_fungus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Fungus: On copy evolution, increase first neighbor's highest edge by +1."""
    if trigger in ("copy_2", "copy_3") and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            nbs = _neighbor_cards(owner.board, coord)
            if nbs:
                nc_card = nbs[0]
                if nc_card.edges:
                    idx = max(range(len(nc_card.edges)), key=lambda i: nc_card.edges[i][1])
                    s, v = nc_card.edges[idx]
                    nc_card.edges[idx] = (s, v + 1)
                    nc_card.stats[s] = v + 1
    return 0


# ===================================================================
# ADJACENCY/NEIGHBOR HANDLERS (pre_combat)
# ===================================================================

@passive("Yggdrasil")
def _passive_yggdrasil(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Yggdrasil: At pre_combat, grant all neighbors a stacking bonus counter."""
    if trigger == "pre_combat" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            for nc_card in _neighbor_cards(owner.board, coord):
                nc_card.stats["_yggdrasil_bonus"] = nc_card.stats.get("_yggdrasil_bonus", 0) + 1
    return 0
