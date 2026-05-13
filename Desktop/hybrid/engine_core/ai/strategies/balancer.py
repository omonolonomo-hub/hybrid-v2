"""
Balancer strategy implementation.
"""

from collections import defaultdict
from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS
from engine_core.ai.base import BaseStrategy
from engine_core.ai.strategies.random import _place_smart_default


def _buy_balancer(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """Balances power and distinct group coverage.
    Phase 1: group_bonus, group_thresh, power_weight parametreleri ai_instance'tan alınır.
    """
    costs = CARD_COSTS
    # Phase 1 param access
    group_bonus  = ai_instance.get_param("balancer", "group_bonus",   5.0) if ai_instance else 5.0
    group_thresh = int(ai_instance.get_param("balancer", "group_thresh", 3.0)) if ai_instance else 3
    pw           = ai_instance.get_param("balancer", "power_weight",  1.0) if ai_instance else 1.0

    board_groups = defaultdict(int)
    for card in player.board.alive_cards():
        board_groups[card.dominant_group()] += 1

    def score(c: Card):
        bonus = group_bonus if board_groups[c.dominant_group()] < group_thresh else 0
        return c.total_power() * pw + bonus

    affordable = sorted(
        [c for c in market if costs[c.rarity] <= player.gold],
        key=score, reverse=True
    )
    for card in affordable[:max_cards]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


class BalancerStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_balancer(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        # Balancer stratejisi için sinerji-delta tabanlı yerleştirme
        # Agresif geç oyun ağırlıkları ile (4.0)
        # Orta lookahead (0.6) — dengeli planlama
        from engine_core.ai.synergy_placement import place_cards_synergy_aware, schedule_for
        schedule = schedule_for("balancer")
        place_cards_synergy_aware(player, schedule=schedule, lookahead_weight=0.6)
