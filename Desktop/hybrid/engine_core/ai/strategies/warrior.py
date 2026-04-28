"""
Warrior strategy implementation.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS
from engine_core.ai.base import BaseStrategy
from engine_core.ai.strategies.random import _place_smart_default


def _buy_warrior(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """Prefers cards with high total_power.
    Phase 1: power_weight ve rarity_weight parametreleri ai_instance'tan alınır.
    """
    costs = CARD_COSTS
    # Phase 1 param access
    strat = player.strategy  # "warrior" veya "tempo"
    pw = ai_instance.get_param(strat, "power_weight",  1.0) if ai_instance else 1.0
    rw = ai_instance.get_param(strat, "rarity_weight", 0.0) if ai_instance else 0.0
    rmap = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "E": 6}
    affordable = sorted(
        [c for c in market if costs[c.rarity] <= player.gold],
        key=lambda c: c.total_power() * pw + rmap.get(c.rarity, 0) * rw,
        reverse=True
    )
    for card in affordable[:max_cards]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


class WarriorStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_smart_default(player, rng)
