"""
Synergy Field Passive Handlers

This module contains passive handlers that create synergy field effects during pre_combat.
These handlers typically buff friendly cards or debuff enemy cards based on board state,
category synergies, or adjacency conditions.

All synergy_field handlers:
- Trigger on "pre_combat"
- Return 1 combat point
- Track "_sf_pc" counter for pre_combat invocations
- Some track "_sf_stacks" to cap total stat bonuses at 6 per card
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
# MYTHOLOGY & GODS SYNERGY HANDLERS
# ===================================================================

@passive("Odin")
def _passive_odin(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Odin: Buff neighboring Mythology & Gods cards' Meaning by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        
        # Cap synergy_field stacks at 6 total stat points per card
        stacks = card.stats.get("_sf_stacks", 0)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for nc_card in _neighbor_cards(owner.board, coord):
                if nc_card.category == "Mythology & Gods":
                    nc_card.edges = [(s, v+1 if s == "Meaning" else v) for s, v in nc_card.edges]
                    if "Meaning" in nc_card.stats:
                        nc_card.stats["Meaning"] += 1
                    buffed = True
            # Track stacks applied only if we buffed something
            if buffed:
                card.stats["_sf_stacks"] = stacks + 1
        return 1
    return 0


@passive("Olympus")
def _passive_olympus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Olympus: If 2+ neighboring Mythology & Gods cards, buff all their Prestige by +1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        coord = _find_coord(owner.board, card)
        mito_neighbors = []
        if coord:
            mito_neighbors = [c for c in _neighbor_cards(owner.board, coord)
                              if c.category == "Mythology & Gods"]
        if len(mito_neighbors) >= 2:
            for nc_card in mito_neighbors:
                nc_card.edges = [(s, v+1 if s == "Prestige" else v) for s, v in nc_card.edges]
                if "Prestige" in nc_card.stats:
                    nc_card.stats["Prestige"] += 1
        return 1
    return 0


# ===================================================================
# COSMOS SYNERGY HANDLERS
# ===================================================================

@passive("Medusa")
def _passive_medusa(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Medusa: Reduce all enemy cards' Speed by -1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        if opponent:
            for c in opponent.board.alive_cards():
                if "Speed" in c.stats:
                    c.stats["Speed"] = max(0, c.stats["Speed"] - 1)
                    c.edges = [(s, max(0, v-1) if s == "Speed" else v) for s, v in c.edges]
        return 1
    return 0


@passive("Black Hole")
def _passive_black_hole(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Hole: Reduce enemy center card's Gravity by -1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        if opponent:
            center = opponent.board.grid.get((0, 0))
            if center and "Gravity" in center.stats:
                center.stats["Gravity"] = max(0, center.stats["Gravity"] - 1)
                center.edges = [(s, max(0, v-1) if s == "Gravity" else v) for s, v in center.edges]
        return 1
    return 0


@passive("Entropy")
def _passive_entropy(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Entropy: Every 3rd turn, all neighbors lose their highest edge."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        turn = ctx.get("turn", 1)
        if turn % 3 == 0:
            coord = _find_coord(owner.board, card)
            if coord:
                for nc_card in _neighbor_cards(owner.board, coord):
                    nc_card.lose_highest_edge()
        return 1
    return 0


@passive("Gravity")
def _passive_gravity(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Gravity: Reduce all neighbors' Speed by -1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        coord = _find_coord(owner.board, card)
        if coord:
            for nb in _neighbor_cards(owner.board, coord):
                if "Speed" in nb.stats:
                    nb.stats["Speed"] = max(0, nb.stats["Speed"] - 1)
                    nb.edges = [(s, max(0, v - 1) if s == "Speed" else v) for s, v in nb.edges]
        return 1
    return 0


# ===================================================================
# SCIENCE SYNERGY HANDLERS
# ===================================================================

@passive("Isaac Newton")
def _passive_isaac_newton(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Isaac Newton: If 3+ Science cards on board, buff all their Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        
        # Cap synergy_field stacks at 6 total stat points per card
        stacks = card.stats.get("_sf_stacks", 0)
        if stacks >= 6:
            return 1
        
        science_cards = [c for c in owner.board.alive_cards() if c.category == "Science"]
        if len(science_cards) >= 3:
            for sc in science_cards:
                if "Intelligence" in sc.stats:
                    sc.stats["Intelligence"] += 1
                    sc.edges = [(s, v + 1 if s == "Intelligence" else v) for s, v in sc.edges]
            # Track stacks applied (count all science cards buffed as 1 stack per turn)
            card.stats["_sf_stacks"] = stacks + 1
        return 1
    return 0


@passive("Nikola Tesla")
def _passive_nikola_tesla(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Nikola Tesla: Buff neighboring Science cards' Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        
        # Cap synergy_field stacks at 6 total stat points per card
        stacks = card.stats.get("_sf_stacks", 0)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for nb in _neighbor_cards(owner.board, coord):
                if nb.category == "Science" and "Intelligence" in nb.stats:
                    nb.stats["Intelligence"] += 1
                    nb.edges = [(s, v + 1 if s == "Intelligence" else v) for s, v in nb.edges]
                    buffed = True
            # Track stacks applied only if we buffed something
            if buffed:
                card.stats["_sf_stacks"] = stacks + 1
        return 1
    return 0


# ===================================================================
# HISTORY & CIVILIZATIONS SYNERGY HANDLERS
# ===================================================================

@passive("Black Death")
def _passive_black_death(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Death: Reduce all enemy cards' Spread by -1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        if opponent:
            for oc in opponent.board.alive_cards():
                if "Spread" in oc.stats:
                    oc.stats["Spread"] = max(0, oc.stats["Spread"] - 1)
                    oc.edges = [(s, max(0, v - 1) if s == "Spread" else v) for s, v in oc.edges]
        return 1
    return 0


@passive("French Revolution")
def _passive_french_revolution(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """French Revolution: If 3+ History & Civilizations cards, reduce enemy's highest stat by -1."""
    if trigger == "pre_combat" and owner is not None:
        card.stats["_sf_pc"] = card.stats.get("_sf_pc", 0) + 1
        hist_count = sum(
            1 for c in owner.board.alive_cards()
            if c.category == "History & Civilizations"
        )
        if hist_count >= 3 and opponent:
            best_oc = None
            best_stat = None
            best_val = -1
            for oc in opponent.board.alive_cards():
                for s, v in oc.stats.items():
                    if str(s).startswith("_"):
                        continue
                    if v > best_val:
                        best_val = v
                        best_oc = oc
                        best_stat = s
            if best_oc is not None and best_stat is not None:
                best_oc.stats[best_stat] = max(0, best_oc.stats[best_stat] - 1)
                best_oc.edges = [
                    (sn, max(0, v - 1) if sn == best_stat else v)
                    for sn, v in best_oc.edges
                ]
        return 1
    return 0
