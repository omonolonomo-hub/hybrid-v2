"""
Combat Passive Handlers

This module contains passive handlers that trigger during combat phases:
- combat_win: Triggers when the owner wins a combat
- combat_lose: Triggers when the owner loses a combat
- card_killed: Triggers when a card is killed during combat
"""

from typing import TYPE_CHECKING

try:
    from .base import passive
except ImportError:
    from passives.base import passive

if TYPE_CHECKING:
    from ..card import Card
    from ..player import Player


# ===================================================================
# COMBAT WIN HANDLERS
# ===================================================================

@passive("Ragnarök", "Ragnark")
def _passive_ragnarok(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Ragnarök: On combat win, strongest enemy card loses its highest edge."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        max(opponent.board.alive_cards(), key=lambda c: c.total_power()).lose_highest_edge()
    return 0


@passive("World War II")
def _passive_world_war_ii(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """World War II: On combat win, all enemy cards lose their highest edge."""
    if trigger == "combat_win" and opponent:
        for c in opponent.board.alive_cards():
            c.lose_highest_edge()
    return 0


@passive("Loki")
def _passive_loki(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Loki: On combat win, reduce strongest enemy's Meaning by 1."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        if "Meaning" in target.stats:
            target.stats["Meaning"] = max(0, target.stats["Meaning"] - 1)
            target.edges = [(s, max(0, v-1) if s == "Meaning" else v) for s, v in target.edges]
    return 0


@passive("Cubism")
def _passive_cubism(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cubism: On combat win, reduce strongest enemy's Size by 1."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        if "Size" in target.stats:
            target.stats["Size"] = max(0, target.stats["Size"] - 1)
            target.edges = [(s, max(0, v-1) if s == "Size" else v) for s, v in target.edges]
    return 0


@passive("Komodo Dragon")
def _passive_komodo_dragon(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Komodo Dragon: On combat win, reduce strongest enemy's lowest edge by 2."""
    if trigger == "combat_win" and opponent and opponent.board.alive_cards():
        target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
        if target.edges:
            idx = min(range(len(target.edges)), key=lambda i: target.edges[i][1])
            s, v = target.edges[idx]
            new_v = max(0, v - 2)
            target.edges[idx] = (s, new_v)
            target.stats[s] = new_v
    return 0


@passive("Venus Flytrap")
def _passive_venus_flytrap(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Venus Flytrap: On combat win, reduce strongest enemy's Gravity by 1 (max 2 times)."""
    if trigger == "combat_win":
        count = card.stats.get("_venus_debuffs", 0)
        if count < 2 and opponent and opponent.board.alive_cards():
            target = max(opponent.board.alive_cards(), key=lambda c: c.total_power())
            if "Gravity" in target.stats:
                target.stats["Gravity"] = max(0, target.stats["Gravity"] - 1)
                target.edges = [(s, max(0, v-1) if s == "Gravity" else v) for s, v in target.edges]
            card.stats["_venus_debuffs"] = count + 1
    return 0


@passive("Narwhal")
def _passive_narwhal(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Narwhal: On combat win, gain +1 Power (max 3 times, once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_t = card.stats.get("_narwhal_last_turn", -1)
        if last_t != turn:
            buff = card.stats.get("_narwhal_buff", 0)
            if buff < 3:
                card.stats["_narwhal_last_turn"] = turn
                card.stats["_narwhal_buff"] = buff + 1
                if "Power" in card.stats:
                    card.stats["Power"] += 1
                    card.edges = [(s, v+1 if s == "Power" else v) for s, v in card.edges]
    return 0


@passive("Sirius")
def _passive_sirius(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Sirius: On combat win, gain +1 Speed (max 2 times, once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last_t = card.stats.get("_sirius_last_turn", -1)
        if last_t != turn:
            buff = card.stats.get("_sirius_buff", 0)
            if buff < 2:
                card.stats["_sirius_last_turn"] = turn
                card.stats["_sirius_buff"] = buff + 1
                if "Speed" in card.stats:
                    card.stats["Speed"] += 1
                    card.edges = [(s, v+1 if s == "Speed" else v) for s, v in card.edges]
    return 0


@passive("Pulsar")
def _passive_pulsar(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Pulsar: On combat win, award 2 combat points (once per turn)."""
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last = card.stats.get("_pulsar_last_turn", -1)
        if last != turn:
            card.stats["_pulsar_last_turn"] = turn
            return 2
    return 0


@passive("Cerberus")
def _passive_cerberus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cerberus: Every 3 combat wins, award 3 combat points."""
    if trigger == "combat_win" and owner is not None:
        cnt = owner.stats.get("cerberus_win_qty", 0) + 1
        if cnt >= 3:
            owner.stats["cerberus_win_qty"] = 0
            return 3
        owner.stats["cerberus_win_qty"] = cnt
    return 0


@passive("Fibonacci Sequence")
def _passive_fibonacci_sequence(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Fibonacci Sequence: bonus combat points based on win streak.
    
    Since combat_win triggers fire DURING combat (before win_streak is updated
    in combat_phase), we add +1 to reflect the current win that's happening.
    This ensures the first win gives 1 point, second consecutive win gives 2, etc.
    
    Returns: min(3, max(1, streak + 1)) - capped between 1 and 3 points.
    """
    if trigger == "combat_win":
        turn = ctx.get("turn", 1)
        last = card.stats.get("_fib_last_turn", -1)
        if last != turn:
            card.stats["_fib_last_turn"] = turn
            streak = getattr(owner, "win_streak", 0) if owner else 0
            # Add 1 because this win hasn't been counted in win_streak yet
            current_streak = streak + 1
            return min(3, max(1, current_streak))
    return 0


# ===================================================================
# COMBAT LOSE HANDLERS
# ===================================================================

@passive("Guernica")
def _passive_guernica(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Guernica: On combat lose, award 1 combat point (max 3 times per turn)."""
    if trigger == "combat_lose":
        turn = ctx.get("turn", 1)
        last_turn = card.stats.get("_guernica_turn", -1)
        if last_turn != turn:
            card.stats["_guernica_turn"] = turn
            card.stats["_guernica_count"] = 0
        count = card.stats.get("_guernica_count", 0)
        if count < 3:
            card.stats["_guernica_count"] = count + 1
            return 1
    return 0


@passive("Minotaur")
def _passive_minotaur(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Minotaur: On combat lose, gain +1 Power (max 2 times per turn, max +4 total per game)."""
    if trigger == "combat_lose" and owner is not None:
        # Cap total bonus at +4 per card instance per game
        total_buff = card.stats.get("_minotaur_total_buff", 0)
        if total_buff >= 4:
            return 0
        
        turn = ctx.get("turn", 1)
        last_t = owner.stats.get("_minotaur_turn", -1)
        if last_t != turn:
            owner.stats["_minotaur_turn"] = turn
            owner.stats["_minotaur_turn_count"] = 0
        tc = owner.stats.get("_minotaur_turn_count", 0)
        if tc < 2:
            owner.stats["minotaur_buff"] = owner.stats.get("minotaur_buff", 0) + 1
            owner.stats["_minotaur_turn_count"] = tc + 1
            if "Power" in card.stats:
                card.stats["Power"] += 1
                card.edges = [(s, v+1 if s == "Power" else v) for s, v in card.edges]
            # Track total buff applied to this card instance
            card.stats["_minotaur_total_buff"] = total_buff + 1
    return 0


@passive("Code of Hammurabi")
def _passive_code_of_hammurabi(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Code of Hammurabi: On combat lose, increase first non-zero edge by 2 (max +4 total per game)."""
    if trigger == "combat_lose":
        # Cap total bonus at +4 per card instance per game (each application adds +2)
        total_buff = card.stats.get("_hammurabi_total_buff", 0)
        if total_buff >= 4:
            return 0
        
        for i, (s, v) in enumerate(card.edges):
            if v > 0:
                card.edges[i] = (s, v + 2)
                card.stats[s] = v + 2
                # Track total buff applied (each application is +2)
                card.stats["_hammurabi_total_buff"] = total_buff + 2
                break
    return 0


@passive("Frida Kahlo")
def _passive_frida_kahlo(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Frida Kahlo: On combat lose, set first zero edge to 1."""
    if trigger == "combat_lose":
        for i, (s, v) in enumerate(card.edges):
            if v == 0:
                card.edges[i] = (s, 1)
                card.stats[s] = 1
                break
    return 0


# ===================================================================
# CARD KILLED HANDLERS (COMBAT)
# ===================================================================

@passive("Anubis")
def _passive_anubis(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Anubis: When any card is killed, gain +1 Secret (max 2 times)."""
    if trigger == "card_killed":
        buff = card.stats.get("_anubis_buff", 0)
        if buff < 2:
            card.stats["_anubis_buff"] = buff + 1
            if "Secret" in card.stats:
                card.stats["Secret"] += 1
                card.edges = [(s, v+1 if s == "Secret" else v) for s, v in card.edges]
    return 0
