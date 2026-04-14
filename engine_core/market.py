"""
================================================================
|         AUTOCHESS HYBRID - Market Module                     |
|  Market class for card pool management                       |
================================================================

This module contains the Market class which manages the shared card pool,
player-specific market windows, and card availability tracking.
"""

import random
from typing import Dict, List

# Import dependencies
try:
    from .card import Card
    from .constants import MARKET_REFRESH_COST
    from .strategy_logger import get_strategy_logger
except ImportError:
    from card import Card
    from constants import MARKET_REFRESH_COST
    try:
        from strategy_logger import get_strategy_logger
    except ImportError:
        def get_strategy_logger(): return None


# ===================================================================
# MARKET
# ===================================================================

# Rarity availability weights by turn range.
# Each entry: (min_turn, weight_multiplier)
# Lower weight = less likely to appear in market window (not excluded).
# This creates organic rarity curves without hard cutoffs.
RARITY_WEIGHT: dict = {
    "1": [(1,  1.0)],                          # always full weight
    "2": [(1,  1.0)],                          # always full weight
    "3": [(1,  0.3), (5,  0.7), (9,  1.0)],   # scarce early, normal mid+
    "4": [(1,  0.0), (5,  0.2), (10, 0.6), (14, 1.0)],  # absent early, gradual
    "5": [(1,  0.0), (8,  0.1), (13, 0.5), (18, 1.0)],  # very late
    "E": [(1,  1.0)],                          # evolution cards: always
}


def _rarity_weight(rarity: str, turn: int) -> float:
    """Return sampling weight for a rarity at a given turn.
    Steps are (min_turn, weight) pairs in ascending order.
    The last step whose min_turn <= turn applies.
    """
    steps = RARITY_WEIGHT.get(rarity, [(1, 1.0)])
    w = steps[0][1]  # default: first step
    for min_turn, weight in steps:
        if turn >= min_turn:
            w = weight
    return w


class Market:
    def __init__(self, pool: List[Card], rng=None):
        self.pool = pool
        self.pool_copies: Dict[str, int] = {c.name: 3 for c in pool}  # 3 copies each in pool
        self._player_windows: Dict[int, List[Card]] = {}  # pid -> open window
        self.rng = rng if rng is not None else random.Random()
        self._current_turn: int = 1  # updated externally if needed

    def _available_weighted(self, turn: int) -> tuple:
        """Return (cards, weights) for weighted sampling at given turn."""
        cards, weights = [], []
        for c in self.pool:
            if self.pool_copies.get(c.name, 0) <= 0:
                continue
            w = _rarity_weight(c.rarity, turn)
            if w > 0.0:
                cards.append(c)
                weights.append(w)
        return cards, weights

    def _weighted_sample(self, cards: list, weights: list, k: int) -> list:
        """Sample k unique items from cards according to weights (no replacement)."""
        if not cards:
            return []
        k = min(k, len(cards))
        result, remaining_cards, remaining_weights = [], list(cards), list(weights)
        for _ in range(k):
            total = sum(remaining_weights)
            if total <= 0:
                break
            r = self.rng.random() * total
            cumulative = 0.0
            chosen_idx = len(remaining_cards) - 1
            for i, w in enumerate(remaining_weights):
                cumulative += w
                if r <= cumulative:
                    chosen_idx = i
                    break
            result.append(remaining_cards.pop(chosen_idx))
            remaining_weights.pop(chosen_idx)
        return result

    def deal_market_window(self, player, n: int = 5) -> list:
        """Open a player-specific market window using weighted rarity sampling."""
        pid = player.pid if hasattr(player, "pid") else player
        if hasattr(player, "_window_bought"):
            player._window_bought = []
        if hasattr(player, "stats"):
            player.stats["market_rolls"] += 1
        self._return_window(pid)
        # Use game turn (turns_played is already incremented by income() before buy phase)
        turn = getattr(player, "turns_played", self._current_turn)
        cards, weights = self._available_weighted(turn)
        if not cards:
            # Ultimate fallback: use all available cards unweighted
            cards = [c for c in self.pool if self.pool_copies.get(c.name, 0) > 0] or self.pool
            weights = [1.0] * len(cards)
        window = self._weighted_sample(cards, weights, n)
        for card in window:
            self.pool_copies[card.name] = max(0, self.pool_copies.get(card.name, 0) - 1)
        self._player_windows[pid] = window

        # ── Strategy Logger hook ──────────────────────────────────────────
        _slogger = get_strategy_logger()
        if _slogger is not None:
            _slogger.log_market_window(player, turn, window)

        return window

    def _return_window(self, pid):
        """Return player's open window cards to the pool."""
        for card in self._player_windows.pop(pid, []):
            self.pool_copies[card.name] = self.pool_copies.get(card.name, 0) + 1

    def return_unsold(self, player, bought: List[Card] = None):
        """Return unpurchased window cards to the pool."""
        pid = player.pid if hasattr(player, "pid") else player
        # Count bought names to avoid card identity mismatch when clones are used.
        bought_counts: Dict[str, int] = {}
        if bought is None:
            for name in getattr(player, "_window_bought", []):
                bought_counts[name] = bought_counts.get(name, 0) + 1
        else:
            for card in bought:
                bought_counts[card.name] = bought_counts.get(card.name, 0) + 1

        window = self._player_windows.pop(pid, [])
        for card in window:
            if bought_counts.get(card.name, 0) > 0:
                bought_counts[card.name] -= 1
                continue
            self.pool_copies[card.name] = self.pool_copies.get(card.name, 0) + 1  # patched edge-case

    def get_cards_for_player(self, n: int = 5, turn: int = 1) -> list:
        """Legacy API - sample window without tracking returns."""
        cards, weights = self._available_weighted(turn)
        if not cards:
            cards = [c for c in self.pool if self.pool_copies.get(c.name, 0) > 0] or self.pool
            weights = [1.0] * len(cards)
        window = self._weighted_sample(cards, weights, n)
        for card in window:
            self.pool_copies[card.name] = max(0, self.pool_copies.get(card.name, 0) - 1)
        return window

    def refresh_cost(self) -> int:
        """Refresh cost (fixed)."""
        return MARKET_REFRESH_COST
