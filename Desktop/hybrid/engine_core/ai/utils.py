"""
Shared utilities for AI strategies.
"""

from typing import Dict, List, Any, Optional

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS

# Constants
MAX_LOOKAHEAD_CARDS = 4
MAX_COORD_CHECK = 8
PLACEMENT_TIME_BUDGET_S = 0.05


def _get_param_with_fallback(ai_instance, strategy: str, key: str,
                             default: Any,
                             fallback_strategy: Optional[str] = None) -> Any:
    """Read strategy param; optionally fall back to another strategy bucket."""
    if ai_instance is None:
        return default

    primary = ai_instance.get_param(strategy, key, None)
    if primary is not None:
        return primary

    if fallback_strategy is not None:
        fallback = ai_instance.get_param(fallback_strategy, key, None)
        if fallback is not None:
            return fallback

    return default


def _economy_phase_controls(player: Player, market: List[Card], max_cards: int,
                            market_obj=None, trigger_passive_fn=None,
                            ai_instance=None, strategy: str = "economist") -> Dict[str, Any]:
    """Shared phase economy engine used by economist and builder."""
    fallback = "economist" if strategy != "economist" else None

    def get_param(key, default):
        return _get_param_with_fallback(ai_instance, strategy, key, default, fallback)

    gold = player.gold
    hp = player.hp
    turn = player.turns_played

    if hp < 35:
        affordable = [c for c in market if CARD_COSTS[c.rarity] <= gold]
        return {
            "phase": "emergency",
            "candidates": affordable,
            "buy_count": min(max_cards, 3),
            "cheap_only": False,
            "ratio_floor": None,
        }

    greed_turn_end = get_param("greed_turn_end", 8)
    greed_gold_thresh = get_param("greed_gold_thresh", 12)
    spike_turn_end = get_param("spike_turn_end", 18)
    spike_r4_thresh = get_param("spike_r4_thresh", 40)
    thresh_high = get_param("thresh_high", 25)
    buy_2_thresh = get_param("buy_2_thresh", 15)
    spike_buy_count = max(1, int(get_param("spike_buy_count", 3)))
    convert_r5_thresh = get_param("convert_r5_thresh", 60)
    convert_buy_count = max(1, int(get_param("convert_buy_count", 4)))

    if turn <= greed_turn_end:
        if gold < 8:
            return {
                "phase": "greed_hold",
                "candidates": [],
                "buy_count": 0,
                "cheap_only": True,
                "ratio_floor": 3.0,
            }

        if gold >= greed_gold_thresh:
            cheap = [
                c for c in market
                if CARD_COSTS[c.rarity] in (CARD_COSTS["1"], CARD_COSTS["2"])
            ]
            return {
                "phase": "greed_buy",
                "candidates": cheap,
                "buy_count": min(max_cards, 1),
                "cheap_only": True,
                "ratio_floor": 3.0,
            }

        return {
            "phase": "greed_hold",
            "candidates": [],
            "buy_count": 0,
            "cheap_only": True,
            "ratio_floor": 3.0,
        }

    if turn <= spike_turn_end:
        if gold >= spike_r4_thresh:
            max_cost = CARD_COSTS["4"]
        elif gold >= thresh_high:
            max_cost = CARD_COSTS["3"]
        elif gold >= 12:
            max_cost = CARD_COSTS["2"]
        else:
            max_cost = CARD_COSTS["1"]

        candidates = [c for c in market if CARD_COSTS[c.rarity] <= max_cost]
        if gold >= thresh_high:
            cnt = min(max_cards, spike_buy_count)
        elif gold >= buy_2_thresh:
            cnt = min(max_cards, 2)
        else:
            cnt = min(max_cards, 1)

        return {
            "phase": "spike",
            "candidates": candidates,
            "buy_count": cnt,
            "cheap_only": False,
            "ratio_floor": None,
        }

    if gold >= convert_r5_thresh:
        max_cost = CARD_COSTS["5"]
    elif gold >= 40:
        max_cost = CARD_COSTS["4"]
    elif gold >= 20:
        max_cost = CARD_COSTS["3"]
    else:
        max_cost = CARD_COSTS["2"]

    candidates = [c for c in market if CARD_COSTS[c.rarity] <= max_cost]
    if gold >= 50:
        cnt = min(max_cards, convert_buy_count)
    elif gold >= 30:
        cnt = min(max_cards, 3)
    else:
        cnt = min(max_cards, 2)

    return {
        "phase": "convert",
        "candidates": candidates,
        "buy_count": cnt,
        "cheap_only": False,
        "ratio_floor": None,
    }
