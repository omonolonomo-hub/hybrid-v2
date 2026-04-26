"""
Synergy Field Passive Handlers

These handlers trigger on pre_combat. Permanent growth uses base stats plus meta,
while short-lived combat debuffs use the effect layer.
"""

from typing import TYPE_CHECKING

from engine_core.board import _find_coord, _neighbor_cards
from engine_core.effects import Effect, EffectPriority
from engine_core.passives.base import passive

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


def _mark_pre_combat(card: "Card") -> None:
    card.inc_meta("_sf_pc")


def _current_stacks(card: "Card") -> int:
    return card.get_meta("_sf_stacks", 0)


def _add_temp_effect(card: "Card", stat_name: str, delta: int, turn: int) -> None:
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


@passive("Odin")
def _passive_odin(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Odin: Buff neighboring Mythology & Gods cards' Meaning by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.category == "Mythology & Gods" and neighbor_card.has_stat("Meaning"):
                    neighbor_card.add_base_stat("Meaning", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Olympus")
def _passive_olympus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Olympus: If 2+ neighboring Mythology & Gods cards, buff all their Prestige by +1."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        mito_neighbors = []
        if coord:
            mito_neighbors = [
                neighbor_card
                for neighbor_card in _neighbor_cards(owner.board, coord)
                if neighbor_card.category == "Mythology & Gods"
            ]
        if len(mito_neighbors) >= 2:
            for neighbor_card in mito_neighbors:
                if neighbor_card.has_stat("Prestige"):
                    neighbor_card.add_base_stat("Prestige", 1)
        return 1
    return 0


@passive("Medusa")
def _passive_medusa(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Medusa: Reduce all enemy cards' Speed by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            turn = ctx.get("turn", 1)
            for other_card in opponent.board.alive_cards():
                _add_temp_effect(other_card, "Speed", -1, turn)
        return 1
    return 0


@passive("Black Hole")
def _passive_black_hole(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Hole: Reduce enemy center card's Gravity by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            center = opponent.board.grid.get((0, 0))
            if center:
                _add_temp_effect(center, "Gravity", -1, ctx.get("turn", 1))
        return 1
    return 0


@passive("Entropy")
def _passive_entropy(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Entropy: Every 3rd turn, all neighbors lose their highest edge."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        turn = ctx.get("turn", 1)
        if turn % 3 == 0:
            coord = _find_coord(owner.board, card)
            if coord:
                for neighbor_card in _neighbor_cards(owner.board, coord):
                    neighbor_card.lose_highest_edge()
        return 1
    return 0


@passive("Gravity")
def _passive_gravity(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Gravity: Reduce all neighbors' Speed by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord:
            turn = ctx.get("turn", 1)
            for neighbor_card in _neighbor_cards(owner.board, coord):
                _add_temp_effect(neighbor_card, "Speed", -1, turn)
        return 1
    return 0


@passive("Isaac Newton")
def _passive_isaac_newton(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Isaac Newton: If 3+ Science cards on board, buff all their Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        science_cards = [board_card for board_card in owner.board.alive_cards() if board_card.category == "Science"]
        if len(science_cards) >= 3:
            for science_card in science_cards:
                if science_card.has_stat("Intelligence"):
                    science_card.add_base_stat("Intelligence", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Nikola Tesla")
def _passive_nikola_tesla(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Nikola Tesla: Buff neighboring Science cards' Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.category == "Science" and neighbor_card.has_stat("Intelligence"):
                    neighbor_card.add_base_stat("Intelligence", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Black Death")
def _passive_black_death(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Death: Reduce all enemy cards' Spread by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            turn = ctx.get("turn", 1)
            for other_card in opponent.board.alive_cards():
                _add_temp_effect(other_card, "Spread", -1, turn)
        return 1
    return 0


@passive("French Revolution")
def _passive_french_revolution(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """French Revolution: If 3+ History & Civilizations cards, reduce enemy's highest stat by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        hist_count = sum(
            1
            for board_card in owner.board.alive_cards()
            if board_card.category == "History & Civilizations"
        )
        if hist_count >= 3 and opponent:
            best_opponent = None
            best_stat = None
            best_value = -1
            for opponent_card in opponent.board.alive_cards():
                for stat_name, value in opponent_card.stats.items():
                    if value > best_value:
                        best_value = value
                        best_opponent = opponent_card
                        best_stat = stat_name
            if best_opponent is not None and best_stat is not None:
                _add_temp_effect(best_opponent, best_stat, -1, ctx.get("turn", 1))
        return 1
    return 0
