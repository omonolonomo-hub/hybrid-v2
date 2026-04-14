"""
Economy Passive Handlers

This module contains passive handlers that trigger during economy phases:
- income: Triggers during the income phase at the start of each turn
- market_refresh: Triggers when the player refreshes the market
- card_buy: Triggers when the player buys a card
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
# INCOME HANDLERS
# ===================================================================

@passive("Industrial Revolution")
def _passive_industrial_revolution(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Industrial Revolution: Gain +1 gold during income phase."""
    if trigger == "income" and owner is not None:
        owner.gold += 1
        owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


@passive("Ottoman Empire")
def _passive_ottoman_empire(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Ottoman Empire: Gain +1 gold during income phase."""
    return _passive_industrial_revolution(card, trigger, owner, opponent, ctx)


@passive("Babylon")
def _passive_babylon(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Babylon: Gain +1 gold during income phase."""
    return _passive_industrial_revolution(card, trigger, owner, opponent, ctx)


@passive("Printing Press")
def _passive_printing_press(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Printing Press: Gain +1 gold during income phase."""
    return _passive_industrial_revolution(card, trigger, owner, opponent, ctx)


@passive("Midas", "Midas Dokunuşu")
def _passive_midas(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Midas: Gain +1 gold during income phase if win streak >= 2."""
    if trigger == "income" and owner is not None:
        if getattr(owner, "win_streak", 0) >= 2:
            owner.gold += 1
            owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


@passive("Silk Road")
def _passive_silk_road(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Silk Road: Gain +1 gold during income phase if bought 2+ cards this turn."""
    if trigger == "income" and owner is not None:
        if owner.stats.get("cards_bought_this_turn", 0) >= 2:
            owner.gold += 1
            owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


@passive("Exoplanet")
def _passive_exoplanet(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Exoplanet: Gain +1 gold during income phase if market has rarity 4 or 5 card."""
    if trigger == "income" and owner is not None:
        market = getattr(owner, "market", [])
        if any(c.rarity in ("4", "5") for c in market):
            owner.gold += 1
            owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


@passive("Moon Landing")
def _passive_moon_landing(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Moon Landing: Gain +1 gold during income phase on even turns."""
    if trigger == "income" and owner is not None:
        turn = ctx.get("turn", 1)
        if turn % 2 == 0:
            owner.gold += 1
            owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


# ===================================================================
# MARKET REFRESH HANDLERS
# ===================================================================

@passive("Algorithm")
def _passive_algorithm(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Algorithm: Gain +1 gold when refreshing the market."""
    if trigger == "market_refresh" and owner is not None:
        owner.gold += 1
        owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 1
    return 0


# ===================================================================
# CARD BUY HANDLERS
# ===================================================================

@passive("Age of Discovery")
def _passive_age_of_discovery(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Age of Discovery: Gain +2 gold when buying a card from a new category."""
    if trigger == "card_buy" and owner is not None:
        bought = ctx.get("bought_card")
        if bought is not None:
            seen = owner.stats.setdefault("seen_categories", set())
            if bought.category not in seen:
                seen.add(bought.category)
                owner.gold += 2
                owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + 2
    return 0
