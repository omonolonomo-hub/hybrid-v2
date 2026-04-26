"""
Combat Passive Handlers

This module contains passive handlers that trigger during combat phases:
- combat_win: Triggers when the owner wins a combat
- combat_lose: Triggers when the owner loses a combat
- card_killed: Triggers when a card is killed during combat
"""

from typing import TYPE_CHECKING

from engine_core.passives.base import passive

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


def _reduce_stat(card: "Card", stat_name: str, amount: int) -> None:
    if card.has_stat(stat_name):
        current = card.get_base_stat(stat_name, 0)
        card.set_base_stat(stat_name, max(0, current - amount))


@passive("Ragnarok", "Ragnark", "RagnarÃ¶k")
def _passive_ragnarok(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Ragnarok: On combat win, strongest enemy card loses its highest edge."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        max(opponent.board.alive_cards(), key=lambda c: c.total_power()).lose_highest_edge()
    return 0


@passive("World War II")
def _passive_world_war_ii(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """World War II: On combat win, all enemy cards lose their highest edge."""
    if trigger == "combat_win" and opponent:
        for other_card in opponent.board.alive_cards():
            other_card.lose_highest_edge()
    return 0


@passive("Loki")
def _passive_loki(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Loki: On combat win, reduce strongest enemy's Meaning by 1."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        _reduce_stat(target, "Meaning", 1)
    return 0


@passive("Cubism")
def _passive_cubism(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cubism: On combat win, reduce strongest enemy's Size by 1."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        _reduce_stat(target, "Size", 1)
    return 0


@passive("Komodo Dragon")
def _passive_komodo_dragon(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Komodo Dragon: On combat win, reduce strongest enemy's lowest edge by 2."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        if target.edges:
            idx = min(range(len(target.edges)), key=lambda i: target.edges[i][1])
            stat_name, value = target.edges[idx]
            target.set_base_stat(stat_name, max(0, value - 2))
    return 0


@passive("Venus Flytrap")
def _passive_venus_flytrap(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Venus Flytrap: On combat win, reduce strongest enemy's Gravity by 1 (max 2 times)."""
    if trigger == "combat_win":
        count = card.get_meta("_venus_debuffs", 0)
        if count < 2 and opponent and opponent.board.alive_cards():
            target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
            _reduce_stat(target, "Gravity", 1)
            card.inc_meta("_venus_debuffs")
    return 0


@passive("Narwhal")
def _passive_narwhal(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Narwhal: On combat win, gain +1 Power (max 3 times, once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_turn = card.get_meta("_narwhal_last_turn", -1)
        if last_turn != turn:
            buff = card.get_meta("_narwhal_buff", 0)
            if buff < 3 and card.has_stat("Power"):
                card.set_meta("_narwhal_last_turn", turn)
                card.set_meta("_narwhal_buff", buff + 1)
                card.add_base_stat("Power", 1)
    return 0


@passive("Sirius")
def _passive_sirius(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Sirius: On combat win, gain +1 Speed (max 2 times, once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_turn = card.get_meta("_sirius_last_turn", -1)
        if last_turn != turn:
            buff = card.get_meta("_sirius_buff", 0)
            if buff < 2 and card.has_stat("Speed"):
                card.set_meta("_sirius_last_turn", turn)
                card.set_meta("_sirius_buff", buff + 1)
                card.add_base_stat("Speed", 1)
    return 0


@passive("Pulsar")
def _passive_pulsar(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Pulsar: On combat win, award 2 combat points (once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_turn = card.get_meta("_pulsar_last_turn", -1)
        if last_turn != turn:
            card.set_meta("_pulsar_last_turn", turn)
            return 2
    return 0


@passive("Cerberus")
def _passive_cerberus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cerberus: Every 3 combat wins, award 3 combat points."""
    if trigger == "combat_win" and owner is not None:
        count = owner.stats.get("cerberus_win_qty", 0) + 1
        if count >= 3:
            owner.stats["cerberus_win_qty"] = 0
            return 3
        owner.stats["cerberus_win_qty"] = count
    return 0


@passive("Fibonacci Sequence")
def _passive_fibonacci_sequence(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Fibonacci Sequence: bonus combat points based on win streak."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_turn = card.get_meta("_fib_last_turn", -1)
        if last_turn != turn:
            card.set_meta("_fib_last_turn", turn)
            streak = getattr(owner, "win_streak", 0) if owner else 0
            current_streak = streak + 1
            return min(3, max(1, current_streak))
    return 0


@passive("Guernica")
def _passive_guernica(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Guernica: On combat lose, award 1 combat point (max 3 times per turn)."""
    if trigger == "combat_lose":
        turn = ctx.get("turn", 1)
        last_turn = card.get_meta("_guernica_turn", -1)
        if last_turn != turn:
            card.set_meta("_guernica_turn", turn)
            card.set_meta("_guernica_count", 0)
        count = card.get_meta("_guernica_count", 0)
        if count < 3:
            card.set_meta("_guernica_count", count + 1)
            return 1
    return 0


@passive("Minotaur")
def _passive_minotaur(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Minotaur: On combat lose, gain +1 Power (max 2 times per turn, max +4 total per game)."""
    if trigger == "combat_lose" and owner is not None:
        total_buff = card.get_meta("_minotaur_total_buff", 0)
        if total_buff >= 4:
            return 0

        turn = ctx.get("turn", 1)
        last_turn = owner.stats.get("_minotaur_turn", -1)
        if last_turn != turn:
            owner.stats["_minotaur_turn"] = turn
            owner.stats["_minotaur_turn_count"] = 0
        turn_count = owner.stats.get("_minotaur_turn_count", 0)
        if turn_count < 2 and card.has_stat("Power"):
            owner.stats["minotaur_buff"] = owner.stats.get("minotaur_buff", 0) + 1
            owner.stats["_minotaur_turn_count"] = turn_count + 1
            card.add_base_stat("Power", 1)
            card.set_meta("_minotaur_total_buff", total_buff + 1)
    return 0


@passive("Code of Hammurabi")
def _passive_code_of_hammurabi(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Code of Hammurabi: On combat lose, increase first non-zero edge by 2 (max +4 total per game)."""
    if trigger == "combat_lose":
        total_buff = card.get_meta("_hammurabi_total_buff", 0)
        if total_buff >= 4:
            return 0

        for stat_name, value in card.edges:
            if value > 0:
                card.add_base_stat(stat_name, 2)
                card.set_meta("_hammurabi_total_buff", total_buff + 2)
                break
    return 0


@passive("Frida Kahlo")
def _passive_frida_kahlo(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Frida Kahlo: On combat lose, set first zero edge to 1."""
    if trigger == "combat_lose":
        for stat_name, value in card.edges:
            if value == 0:
                card.set_base_stat(stat_name, 1)
                break
    return 0


@passive("Anubis")
def _passive_anubis(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Anubis: When any card is killed, gain +1 Secret (max 2 times)."""
    if trigger == "card_killed":
        buff = card.get_meta("_anubis_buff", 0)
        if buff < 2 and card.has_stat("Secret"):
            card.set_meta("_anubis_buff", buff + 1)
            card.add_base_stat("Secret", 1)
    return 0
