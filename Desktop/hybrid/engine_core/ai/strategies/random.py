"""
Random strategy implementation.
"""

import random
from typing import List

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS, HEX_DIRS, PLACE_PER_TURN
from engine_core.strategy_logger import get_strategy_logger
from engine_core.ai.base import BaseStrategy


def _buy_random(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    if rng is None:
        rng = random.Random()
    budget = player.gold
    affordable = [c for c in market if CARD_COSTS[c.rarity] <= budget]
    rng.shuffle(affordable)
    for card in affordable[:max_cards]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


def _place_smart_default(player: Player, rng=None):
    """Tüm diğer stratejiler için akıllı yerleştirme.

    Her strateji için combo score hesaplanır ve en iyi koordinat seçilir.
    Strateji kimliklerini korumak için küçük ağırlık farkları uygulanır:
      - warrior/rare_hunter : power ağırlığı yüksek → güçlü kartı en iyi combo
        konumuna koyar ama koordinat seçiminde power'ı da gözetir
      - evolver              : evolved kartları önceliklendirir
      - economist            : combo'ya göre saf akıllı yerleşim
      - balancer             : combo + group diversity dengesi
      - random               : %50 combo akıllı, %50 rastgele (kimlik korunur)

    Tüm stratejiler strategy logger'a bağlıdır.

    v0.6: PLACE_PER_TURN kadar kart yerleştirir.
    """
    if rng is None:
        rng = random.Random()

    free = player.board.free_coords()
    if not free:
        return

    _slogger = get_strategy_logger()
    strategy  = player.strategy
    grid      = player.board.grid

    def _combo_score_at(coord: tuple, card) -> int:
        """Kendi boardundaki komşularla grup uyumunu say."""
        card_group = card.dominant_group()
        q, r = coord
        score = 0
        for dq, dr in HEX_DIRS:
            nbr = grid.get((q + dq, r + dr))
            if nbr is not None and nbr.dominant_group() == card_group:
                score += 1
        return score

    # Filter out None values from hand (positional integrity placeholders)
    valid_hand = [c for c in player.hand if c is not None]
    
    # Strateji bazlı kart sıralama
    if strategy in ("warrior", "rare_hunter"):
        sorted_cards = sorted(valid_hand,
                              key=lambda c: c.total_power(), reverse=True)
    elif strategy == "evolver":
        # Evolved kartları öne al, sonra power sırası
        sorted_cards = sorted(
            valid_hand,
            key=lambda c: (1 if c.rarity == "E" else 0, c.total_power()),
            reverse=True
        )
    else:
        # economist, balancer, random — power sırasıyla
        sorted_cards = sorted(valid_hand,
                              key=lambda c: c.total_power(), reverse=True)

    placed = 0
    for card in sorted_cards:
        if placed >= PLACE_PER_TURN or not free:
            break

        # random stratejisi: %50 ihtimalle rastgele koordinat seç
        if strategy == "random" and rng.random() < 0.5:
            target      = rng.choice(free)
            final_combo = _combo_score_at(target, card)
        else:
            # Tüm boş koordinatları combo score'a göre değerlendir
            best_coord = None
            best_score = -1

            if strategy in ("warrior", "rare_hunter"):
                # Power yüksekse merkeze yakın koordinatları hafifçe tercih et
                center_coords = {(0, 0)}
                for dq, dr in HEX_DIRS:
                    center_coords.add((dq, dr))
                power = card.total_power()
                for coord in free:
                    cs = _combo_score_at(coord, card)
                    # Güçlü kart (r4+) → merkeze yakınlık bonus +0.5
                    center_bonus = 0.5 if (power >= 42 and coord in center_coords) else 0
                    score = cs + center_bonus
                    if score > best_score:
                        best_score = score
                        best_coord = coord
            else:
                for coord in free:
                    cs = _combo_score_at(coord, card)
                    if cs > best_score:
                        best_score = cs
                        best_coord = coord

            target      = best_coord if best_coord else free[-1]
            final_combo = _combo_score_at(target, card)

        player.board.place(target, card)
        free.remove(target)
        
        # Remove card from hand (handle None-slot system)
        for i, hand_card in enumerate(player.hand):
            if hand_card is card:
                player.hand[i] = None
                break
        
        placed += 1

        # ── Strategy Logger hook ─────────────────────────────────────
        if _slogger is not None:
            _slogger.log_placement(player, card, target,
                                   combo_score=final_combo)


class RandomStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_smart_default(player, rng)
