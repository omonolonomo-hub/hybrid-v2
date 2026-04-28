"""
Evolver strategy implementation.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS
from engine_core.ai.base import BaseStrategy
from engine_core.ai.strategies.random import _place_smart_default


def _buy_evolver(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """v0.7 Evolution-aware buying strategy.
    Priority: cards with 2 copies (one away from evolving) >
    cards with 1 copy > new cards (highest rarity first).
    After evolving a card, picks a new focus target.

    Phase 1: evo_near_bonus, evo_one_bonus, rarity_weight_mult, power_weight
    parametreleri ai_instance'tan alınır.
    """
    owned = player.copies
    gold = player.gold
    # Phase 1 param access
    evo_near = ai_instance.get_param("evolver", "evo_near_bonus",    1000.0) if ai_instance else 1000.0
    evo_one  = ai_instance.get_param("evolver", "evo_one_bonus",      500.0) if ai_instance else  500.0
    rw_mult  = ai_instance.get_param("evolver", "rarity_weight_mult",  10.0) if ai_instance else   10.0
    pw       = ai_instance.get_param("evolver", "power_weight",         1.0) if ai_instance else    1.0

    def affordable(c: Card) -> bool:
        return CARD_COSTS[c.rarity] <= gold and c.rarity != "E"

    market_base = [c for c in market if affordable(c)]
    if not market_base:
        return

    def focus_score(c: Card) -> float:
        count = owned.get(c.name, 0)
        evolved_exists = owned.get(f"Evolved {c.name}", 0) > 0
        if evolved_exists:
            return -1.0
        rarity_weight = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}.get(c.rarity, 0)
        if count == 2:
            return evo_near + rarity_weight * rw_mult + c.total_power() * pw
        elif count == 1:
            return evo_one  + rarity_weight * rw_mult + c.total_power() * pw
        else:
            return rarity_weight * rw_mult + c.total_power() * pw

    best = max(market_base, key=focus_score)
    if focus_score(best) < 0:
        best = max(market_base, key=lambda c: c.total_power())
    player.buy_card(best, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)

    if max_cards > 1 and player.gold >= 4:
        remaining = [c for c in market if affordable(c) and c.name != best.name]
        second_candidates = [c for c in remaining
                             if owned.get(c.name, 0) >= 1
                             and not owned.get(f"Evolved {c.name}", 0)]
        if second_candidates:
            second = max(second_candidates, key=focus_score)
            player.buy_card(second, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


class EvolverStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_evolver(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_smart_default(player, rng)
