"""
Combo Passive Handlers

This module contains passive handlers that award bonus combat points based on combo conditions.
These handlers trigger during pre_combat and return variable combat points based on:
- Combo group matching (MIND, CONNECTION)
- Combo count thresholds
- Target category matching
- Board adjacency/positioning

All combo handlers:
- Trigger on "pre_combat"
- Return base 1 point + bonus points based on combo conditions
- Read combo data from ctx dictionary
"""

from typing import TYPE_CHECKING

try:
    from .base import passive
except ImportError:
    from passives.base import passive

try:
    from ..board import _find_coord
except ImportError:
    from board import _find_coord

if TYPE_CHECKING:
    from ..card import Card
    from ..player import Player


# ===================================================================
# COMBO GROUP HANDLERS
# ===================================================================

@passive("Athena")
def _passive_athena(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Athena: Award 1 + combo_count points if combo_group is MIND."""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        combo_group = ctx.get("combo_group", "")
        pts = 1
        if combo_group == "MIND":
            pts += combo_count
        return pts
    return 0


@passive("Ballet")
def _passive_ballet(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Ballet: Award 1 + combo_count points if combo_group is CONNECTION."""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        combo_group = ctx.get("combo_group", "")
        pts = 1
        if combo_group == "CONNECTION":
            pts += combo_count
        return pts
    return 0


@passive("Albert Einstein")
def _passive_albert_einstein(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Albert Einstein: Award 1 + 2 bonus points if combo_group is MIND."""
    if trigger == "pre_combat" and owner is not None:
        combo_group = ctx.get("combo_group", "")
        pts = 1
        if combo_group == "MIND":
            pts += 2
        return pts
    return 0


# ===================================================================
# COMBO COUNT HANDLERS
# ===================================================================

@passive("Impressionism")
def _passive_impressionism(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Impressionism: Award 1 + 1 bonus point if combo_count >= 2."""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        pts = 1
        if combo_count >= 2:
            pts += 1
        return pts
    return 0


# ===================================================================
# COMBO CATEGORY HANDLERS
# ===================================================================

@passive("Nebula")
def _passive_nebula(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Nebula: Award 1 + 2 bonus points if combo_target_category is Cosmos."""
    if trigger == "pre_combat" and owner is not None:
        combo_target_category = ctx.get("combo_target_category", "")
        pts = 1
        if combo_target_category == "Cosmos":
            pts += 2
        return pts
    return 0


# ===================================================================
# POSITIONING COMBO HANDLERS
# ===================================================================

@passive("Golden Ratio")
def _passive_golden_ratio(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Golden Ratio: Award 1 + 3 bonus points if surrounded by 6+ neighbors."""
    if trigger == "pre_combat" and owner is not None:
        pts = 1
        coord = _find_coord(owner.board, card)
        if coord:
            nbs = owner.board.neighbors(coord)
            filled = sum(1 for (nc, _) in nbs if nc in owner.board.grid)
            if filled >= 6:
                pts += 3
        return pts
    return 0
