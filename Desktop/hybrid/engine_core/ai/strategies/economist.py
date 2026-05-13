"""
Economist strategy implementation.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS
from engine_core.ai.base import BaseStrategy
from engine_core.ai.utils import _economy_phase_controls
from engine_core.ai.strategies.random import _place_smart_default


def _buy_economist(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """
    Phase-aware economist strategy: GREED → SPIKE → CONVERT

    v0.6: Three phases with distinct objectives:
      - GREED (Turn 1-8):   Minimize spending, maximize interest stacking
      - SPIKE (Turn 9-18):  Build board power, selective rolling
      - CONVERT (Turn 19+): Hard spend, legendary chase

    Args:
        ai_instance: ParameterizedAI instance for parameter access (optional).
                     If None, uses hardcoded defaults (backward compatibility).
    """
    econ = _economy_phase_controls(
        player, market, max_cards,
        market_obj=market_obj,
        trigger_passive_fn=trigger_passive_fn,
        ai_instance=ai_instance,
        strategy="economist",
    )
    if not econ["candidates"] or econ["buy_count"] <= 0:
        return

    affordable = sorted(
        [c for c in econ["candidates"] if CARD_COSTS[c.rarity] <= player.gold],
        key=lambda c: c.total_power(),
        reverse=True
    )

    if econ["ratio_floor"] is not None:
        affordable = [
            c for c in affordable
            if CARD_COSTS[c.rarity] > 0
            and (c.total_power() / CARD_COSTS[c.rarity]) >= econ["ratio_floor"]
        ]

    for card in affordable[:econ["buy_count"]]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


class EconomistStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_economist(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        # Economist stratejisi için sinerji-delta tabanlı yerleştirme
        # Orta seviye ağırlıklar (2.5) — dengeli yaklaşım
        from engine_core.ai.synergy_placement import place_cards_synergy_aware, schedule_for
        schedule = schedule_for("economist")
        place_cards_synergy_aware(player, schedule=schedule)
