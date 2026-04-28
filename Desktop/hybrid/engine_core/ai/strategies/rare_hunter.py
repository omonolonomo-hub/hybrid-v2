"""
Rare hunter strategy implementation.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS
from engine_core.ai.base import BaseStrategy
from engine_core.ai.strategies.random import _place_smart_default


def _buy_rare_hunter(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """
    Chases high-rarity cards (4+ pip).
    BUG FIX: rarity-3 fallback until 8 gold fixes early-game stall.
    Phase 1: fallback_rarity parametresi ai_instance'tan alınır.
    """
    gold = player.gold
    # Phase 1 param access — fallback_rarity: kaçıncı rarity'e düşüleceği
    fb_rarity = str(max(1, min(4, int(round(
        ai_instance.get_param("rare_hunter", "fallback_rarity", 3.0)
        if ai_instance else 3.0
    )))))

    # Try 5-pip first
    if gold >= CARD_COSTS["5"]:
        rare5 = [c for c in market if c.rarity == "5"]
        if rare5:
            player.buy_card(max(rare5, key=lambda c: c.total_power()), market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)
            return

    # Then 4-pip
    if gold >= CARD_COSTS["4"]:
        rare4 = sorted(
            [c for c in market if c.rarity == "4"],
            key=lambda c: c.total_power(), reverse=True
        )
        for card in rare4[:max_cards]:
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)
        if rare4:
            return

    # Fallback: parameterized rarity — keep banking gold
    rfb = sorted(
        [c for c in market if c.rarity == fb_rarity and CARD_COSTS[c.rarity] <= gold],
        key=lambda c: c.total_power(), reverse=True
    )
    for card in rfb[:1]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


class RareHunterStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_rare_hunter(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_smart_default(player, rng)
