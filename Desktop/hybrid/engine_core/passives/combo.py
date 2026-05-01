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

from engine_core.passives.base import passive
from engine_core.board import _find_coord, _neighbor_cards
from engine_core.effects import Effect, EffectPriority

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


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


@passive("Bioluminescence")
def _passive_bioluminescence(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Bioluminescence: When combo match occurs, +1 Harmony to neighboring ally cards that turn."""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        if combo_count > 0:
            coord = _find_coord(owner.board, card)
            if coord:
                turn = ctx.get("turn", 1)
                for neighbor_card in _neighbor_cards(owner.board, coord):
                    if neighbor_card.has_stat("Harmony"):
                        neighbor_card.add_effect(
                            Effect(
                                source="combo_buff",
                                stat_name="Harmony",
                                delta=1,
                                duration=1,
                                applied_turn=turn,
                                priority=int(EffectPriority.COMBAT_BUFF),
                            )
                        )
        return 1
    return 0
