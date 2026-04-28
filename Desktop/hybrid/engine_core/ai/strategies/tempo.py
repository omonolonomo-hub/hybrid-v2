"""
Tempo strategy implementation.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS, HEX_DIRS, PLACE_PER_TURN
from engine_core.strategy_logger import get_strategy_logger
from engine_core.ai.base import BaseStrategy
from engine_core.ai.strategies.warrior import _buy_warrior


def _place_aggressive(player: Player, power_center_thresh: float = 45.0,
                      combo_center_weight: float = 1.5):
    """Tempo strategy: put strongest card toward center, but prefer a rim
    position when it yields significantly higher combo synergy than center.

    Katman 1: power_center_thresh=45  – only rarity-4/5 auto-centre.
    Katman 3: combo_center_weight     – centre stays preferred unless a rim
      coord has combo_score > power_score * combo_center_weight, keeping
      Tempo aggressive while rewarding board awareness.

    v0.6: places up to PLACE_PER_TURN cards (default 1).
    """
    free = player.board.free_coords()
    if not free:
        return

    _slogger = get_strategy_logger()

    # Filter out None values from hand (positional integrity placeholders)
    valid_hand = [c for c in player.hand if c is not None]
    
    # Sort hand by power (strongest first) — Tempo character preserved
    sorted_cards = sorted(valid_hand, key=lambda c: c.total_power(), reverse=True)

    # Center coords: (0,0) and ring-1 neighbours
    center_coords = {(0, 0)}
    for dq, dr in HEX_DIRS:
        center_coords.add((dq, dr))

    grid = player.board.grid

    def _combo_score_at(coord: tuple, card) -> int:
        """Count how many existing board neighbours share the card's dominant group."""
        card_group = card.dominant_group()
        q, r = coord
        score = 0
        for dq, dr in HEX_DIRS:
            nbr = grid.get((q + dq, r + dr))
            if nbr is not None and nbr.dominant_group() == card_group:
                score += 1
        return score

    placed = 0
    for card in sorted_cards:
        if placed >= PLACE_PER_TURN or not free:
            break

        power = card.total_power()

        if power >= power_center_thresh:
            # Strong enough to go centre — but check if a rim coord offers
            # a meaningfully higher combo score (Katman 3 check).
            center_free   = [c for c in free if c in center_coords]
            rim_free      = [c for c in free if c not in center_coords]

            best_center_coord = center_free[0] if center_free else None
            center_combo = _combo_score_at(best_center_coord, card) if best_center_coord else -1

            # Find best rim coord by combo score
            best_rim_coord  = None
            best_rim_combo  = -1
            for rc in rim_free:
                cs = _combo_score_at(rc, card)
                if cs > best_rim_combo:
                    best_rim_combo = cs
                    best_rim_coord = rc

            # Prefer rim only when its combo score beats centre * weight
            # This keeps Tempo's aggressive identity intact in most cases.
            if (best_rim_coord is not None
                    and best_rim_combo > center_combo * combo_center_weight):
                target = best_rim_coord
                final_combo = best_rim_combo
            elif best_center_coord is not None:
                target = best_center_coord
                final_combo = center_combo
            else:
                target = free[-1]  # fallback: any free coord
                final_combo = 0
        else:
            # Weaker card: place at best combo rim coord, or any free coord
            best_coord = None
            best_cs    = -1
            for rc in free:
                cs = _combo_score_at(rc, card)
                if cs > best_cs:
                    best_cs   = cs
                    best_coord = rc
            target = best_coord if best_coord else free[-1]
            final_combo = best_cs if best_cs >= 0 else 0

        player.board.place(target, card)
        free.remove(target)
        
        # Remove card from hand (handle None-slot system)
        for i, hand_card in enumerate(player.hand):
            if hand_card is card:
                player.hand[i] = None
                break
        
        placed += 1

        # ── Strategy Logger hook ──────────────────────────────────────
        if _slogger is not None:
            _slogger.log_placement(player, card, target,
                                   combo_score=final_combo)


class TempoStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_aggressive(player, **kwargs)
