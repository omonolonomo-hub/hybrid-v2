"""
Builder strategy implementation with synergy matrix.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import CARD_COSTS, HEX_DIRS, STAT_TO_GROUP, RARITY_TAVAN, PLACE_PER_TURN
from engine_core.strategy_logger import get_strategy_logger
from engine_core.ai.base import BaseStrategy
from engine_core.ai.utils import _economy_phase_controls, _get_param_with_fallback, MAX_COORD_CHECK, PLACEMENT_TIME_BUDGET_S


# ===================================================================
# BUILDER SYNERGY MATRIX  (C önerisi — session-level adjacency memory)
# ===================================================================

class BuilderSynergyMatrix:
    """Session-level synergy memory for builder AI.

    Her oyun için ayrı bir instance oluşturulur (game-scope).
    game.py veya simulation.py builder player'ı oluştururken
    player.synergy_matrix = BuilderSynergyMatrix() ataması yapılabilir;
    yoksa _buy_builder ve _place_combo_optimized kendi içinde boş
    bir fallback kullanır.

    Neden cross-game sızıntı riski yok:
    • Her oyun Player() yeniden oluşturulur.
    • Matrix player'a bağlı → oyun bitince GC tarafından temizlenir.
    • Global state yok; rng seed bağımsız.
    """

    def __init__(self):
        # synergy_weight[card_a_name][card_b_name] → float
        # İki kart aynı combo zincirinde birlikte combo puan üretirse artar.
        self._weights: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._decay = 0.97          # Her turn sonunda hafifçe unutur (uzun vadeli öğrenme)
        self._reward_per_combo = 1.0
        self._penalty_per_miss  = 0.3

    def record_combo(self, card_a_name: str, card_b_name: str):
        """Bu iki kartın combo ürettiğini kaydet."""
        self._weights[card_a_name][card_b_name] += self._reward_per_combo
        self._weights[card_b_name][card_a_name] += self._reward_per_combo

    def record_miss(self, card_a_name: str, card_b_name: str):
        """Komşu oldukları halde combo üretemeyen çiftleri kaydet."""
        self._weights[card_a_name][card_b_name] = max(
            0.0, self._weights[card_a_name][card_b_name] - self._penalty_per_miss
        )
        self._weights[card_b_name][card_a_name] = max(
            0.0, self._weights[card_b_name][card_a_name] - self._penalty_per_miss
        )

    def decay(self):
        """Her tur sonunda ağırlıkları biraz unuttur."""
        for a in self._weights:
            for b in self._weights[a]:
                self._weights[a][b] *= self._decay

    def synergy_score(self, card_name: str, board_card_names: List[str]) -> float:
        """Bu kartın tahtadaki kartlarla geçmiş synergy skorunu döndür."""
        total = 0.0
        for bn in board_card_names:
            total += self._weights[card_name].get(bn, 0.0)
        return total

    def update_from_board(self, board):
        """Mevcut tahta combo'larını okuyarak matrix'i güncelle.
        find_combos'u çağırmadan, sadece dominant_group eşleşmesine bakar.
        """
        grid = board.grid
        counted = set()
        for coord, card in grid.items():
            cg = card.dominant_group()
            q, r = coord
            for dq, dr in HEX_DIRS:
                nc = (q + dq, r + dr)
                if nc not in grid:
                    continue
                pair = (min(coord, nc), max(coord, nc))
                if pair in counted:
                    continue
                counted.add(pair)
                neighbor = grid[nc]
                ng = neighbor.dominant_group()
                if cg == ng:
                    self.record_combo(card.name, neighbor.name)
                else:
                    self.record_miss(card.name, neighbor.name)


def _buy_builder(player: Player, market: List[Card], max_cards: int,
                market_obj=None, rng=None, trigger_passive_fn=None,
                ai_instance=None, next_uid_fn=None, game_ref=None):
    """Builder v4: combo-first card scoring + economist economy controls.

    Builder now reuses economist's phase economy model so spending/hoarding
    stays stable, but ranks cards by combo potential rather than raw power.
    Previous builder tuner params were:
      - group_weight
      - power_weight
      - gold_spend_threshold
    New builder model uses:
      - combo_weight
      - power_weight
      - greed_gold_thresh / spike_buy_count / convert_buy_count
        and the rest of economist-style phase controls.
    """
    costs = CARD_COSTS
    # Backward compat: if combo_weight missing, old group_weight still works.
    cw = _get_param_with_fallback(ai_instance, "builder", "combo_weight", None)
    if cw is None:
        cw = _get_param_with_fallback(ai_instance, "builder", "group_weight", 1.0)
    pw = _get_param_with_fallback(ai_instance, "builder", "power_weight", 0.4)

    econ = _economy_phase_controls(
        player, market, max_cards,
        market_obj=market_obj,
        trigger_passive_fn=trigger_passive_fn,
        ai_instance=ai_instance,
        strategy="builder",
    )
    candidate_cards = econ["candidates"]
    if not candidate_cards or econ["buy_count"] <= 0:
        return

    # Tahtadaki dominant grup dağılımı
    dom_count: Dict[str, int] = defaultdict(int)
    board_cards = player.board.alive_cards()
    board_card_names = [c.name for c in board_cards]
    board_categories = set(c.category for c in board_cards)

    for card in board_cards:
        dom_count[card.dominant_group()] += 1

    if dom_count:
        target_group = max(dom_count, key=dom_count.get)
    else:
        # Early-game: tahta boş — marketteki en yaygın combo grubunu hedef al.
        # Bu olmadan combo_weight erken turda sıfıra çarpar ve sweep anlamsızlaşır.
        _market_groups: Dict[str, int] = defaultdict(int)
        for _mc in candidate_cards:
            for _s in _mc.stats:
                if not str(_s).startswith("_"):
                    _g = STAT_TO_GROUP.get(_s)
                    if _g:
                        _market_groups[_g] += 1
        target_group = (
            max(_market_groups, key=_market_groups.get)
            if _market_groups else "CONNECTION"
        )

    # Synergy matrix (opsiyonel — player'da yoksa None)
    sm: Optional[BuilderSynergyMatrix] = getattr(player, "synergy_matrix", None)

    def score(c: Card) -> float:
        # 1) Grup eşleşmesi: hedef gruptaki stat sayısı
        group_match = sum(
            1 for s in c.stats
            if not str(s).startswith("_") and STAT_TO_GROUP.get(s) == target_group
        ) * 4.0

        # 2) Passive uyum bonusu: kart kategorisi tahtadaki kategorilerle
        #    eşleşiyorsa combo passive'ler daha kolay tetiklenir
        passive_compat = 2.0 if c.category in board_categories else 0.0

        # 3) Synergy matrix bonusu (normalize: max 3.0)
        if sm is not None:
            raw_matrix = sm.synergy_score(c.name, board_card_names)
            matrix_score = min(3.0, raw_matrix * 0.5)
        else:
            matrix_score = 0.0

        # 4) Power tiebreak (normalize 0-1)
        tavan = RARITY_TAVAN.get(c.rarity, 36)
        power_norm = (c.total_power() / tavan if tavan > 0 else 0.0) * max(0.0, pw)
        combo_score = group_match + passive_compat + matrix_score
        return combo_score * cw + power_norm

    affordable = sorted(
        [c for c in candidate_cards if costs.get(str(c.rarity), float("inf")) <= player.gold],
        key=score, reverse=True
    )

    if econ["ratio_floor"] is not None:
        affordable = [
            c for c in affordable
            if CARD_COSTS[c.rarity] > 0
            and (c.total_power() / CARD_COSTS[c.rarity]) >= econ["ratio_floor"]
        ]

    for card in affordable[:econ["buy_count"]]:
        player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0, game_ref=game_ref)


def _place_fast_synergy(player: Player):
    """Fast builder placement for tuning runs.

    Preserves builder identity with local synergy scoring, but skips
    expensive multi-card lookahead to avoid combinatorial blow-ups.
    """
    free = player.board.free_coords()
    if not free:
        return

    _slogger  = get_strategy_logger()
    grid      = player.board.grid
    
    # Filter out None values from hand (positional integrity placeholders)
    hand_list = [c for c in player.hand if c is not None]
    
    start_ts  = time.perf_counter()

    sm: Optional[BuilderSynergyMatrix] = getattr(player, "synergy_matrix", None)

    center_ring = {(0, 0)}
    for dq, dr in HEX_DIRS:
        center_ring.add((dq, dr))

    def _group_combo_score(coord: Tuple[int, int], card: Card) -> int:
        cg = card.dominant_group()
        q, r = coord
        s = 0
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None and nb.dominant_group() == cg:
                s += 1
        return s

    def _passive_neighbor_score(coord: Tuple[int, int], card: Card) -> int:
        q, r = coord
        s = 0
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None and nb.category == card.category:
                s += 1
        return s

    def _matrix_score(coord: Tuple[int, int], card: Card) -> float:
        if sm is None:
            return 0.0
        q, r = coord
        neighbor_names = []
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None:
                neighbor_names.append(nb.name)
        return sm.synergy_score(card.name, neighbor_names) * 0.5

    def placement_score(coord: Tuple[int, int], card: Card) -> float:
        combo   = _group_combo_score(coord, card) * 5.0
        passive = _passive_neighbor_score(coord, card) * 4.0
        center  = 2.0 if coord in center_ring else 0.0
        matrix  = _matrix_score(coord, card)
        return combo + passive + center + matrix

    placed = 0
    for card in hand_list:
        if placed >= PLACE_PER_TURN or not free:
            break
        if time.perf_counter() - start_ts > PLACEMENT_TIME_BUDGET_S:
            break

        best_coord = None
        best_sc = -1.0
        for coord in free[:MAX_COORD_CHECK]:
            sc = placement_score(coord, card)
            if sc > best_sc:
                best_sc = sc
                best_coord = coord

        target = best_coord if best_coord is not None else free[-1]
        final_combo = _group_combo_score(target, card)

        player.board.place(target, card)
        free.remove(target)
        
        # Remove card from hand (handle None-slot system)
        for i, hand_card in enumerate(player.hand):
            if hand_card is card:
                player.hand[i] = None
                break
        
        placed += 1

        if sm is not None:
            sm.update_from_board(player.board)

        if _slogger is not None:
            _slogger.log_placement(player, card, target,
                                   combo_score=final_combo)


def _place_combo_optimized(player: Player):
    """Builder placement engine v2 — A + B + C entegre.

    Skor bileşenleri (her koordinat için):
      combo_neighbors  : mevcut tahtadaki grup-eşleşen komşu sayısı  ×5
      passive_neighbors: aynı kategorili komşu sayısı (passive zincir) ×4
      center_bonus     : 37-hex board'da merkez ring (radius≤1)        ×2
      lookahead_bonus  : bu yerleşimden sonra eldeki diğer kartların
                         alabileceği ek combo puanı (2-adım)           ×1
      matrix_bonus     : synergy_matrix'ten gelen geçmiş uyum skoru    ×0.5

    Önem sırası: combo_neighbors > passive_neighbors > lookahead > center > matrix
    Bu ağırlıklar boş tahta sorununu çözer: board boşken bile
    lookahead ve center_bonus skor üretir, sıralama anlamlı olur.
    """
    from engine_core.ai.utils import MAX_LOOKAHEAD_CARDS
    
    free = player.board.free_coords()
    if not free:
        return

    start_ts = time.perf_counter()
    _slogger  = get_strategy_logger()
    grid      = player.board.grid
    
    # Filter out None values from hand (positional integrity placeholders)
    hand_list = [c for c in player.hand if c is not None]

    # Synergy matrix (opsiyonel)
    sm: Optional[BuilderSynergyMatrix] = getattr(player, "synergy_matrix", None)

    # Merkez ring koordinatları (radius ≤ 1)
    center_ring = {(0, 0)}
    for dq, dr in HEX_DIRS:
        center_ring.add((dq, dr))

    def _group_combo_score(coord: Tuple[int, int], card: Card) -> int:
        """Kaç komşu bu kartla grup eşleşmesi yapıyor (mevcut tahta)."""
        cg = card.dominant_group()
        q, r = coord
        s = 0
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None and nb.dominant_group() == cg:
                s += 1
        return s

    def _passive_neighbor_score(coord: Tuple[int, int], card: Card) -> int:
        """Aynı kategori komşu sayısı — passive zincir potansiyeli."""
        q, r = coord
        s = 0
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None and nb.category == card.category:
                s += 1
        return s

    def _lookahead_score(coord: Tuple[int, int], placed_card: Card,
                         remaining_hand: List[Card]) -> float:
        """2-adım lookahead: bu kartı coord'a koyarsak eldeki
        diğer kartların en iyi konumdaki combo puanı ne olur?
        Gerçek simulate etmek yerine hafif bir tahmin yaparız:
        her kalan kart için free_coords üzerinde max combo_score bak
        (placed_card'ı grid'de geçici say).
        """
        if not remaining_hand:
            return 0.0

        # Geçici yerleştirme — sadece lookahead için, state değiştirmez
        fake_grid = dict(grid)
        fake_grid[coord] = placed_card
        limited_hand = remaining_hand[:MAX_LOOKAHEAD_CARDS]
        remaining_free = [c for c in free if c != coord][:MAX_COORD_CHECK]
        if not remaining_free:
            return 0.0

        total = 0.0
        for rc in limited_hand:
            if time.perf_counter() - start_ts > PLACEMENT_TIME_BUDGET_S:
                break
            rc_group = rc.dominant_group()
            best = 0
            for fc in remaining_free:
                fq, fr = fc
                s = 0
                for dq2, dr2 in HEX_DIRS:
                    nb2 = fake_grid.get((fq + dq2, fr + dr2))
                    if nb2 is not None and nb2.dominant_group() == rc_group:
                        s += 1
                if s > best:
                    best = s
            total += best
        return total / max(1, len(limited_hand))  # ortalama

    def _matrix_score(coord: Tuple[int, int], card: Card) -> float:
        if sm is None:
            return 0.0
        q, r = coord
        neighbor_names = []
        for dq, dr in HEX_DIRS:
            nb = grid.get((q + dq, r + dr))
            if nb is not None:
                neighbor_names.append(nb.name)
        return sm.synergy_score(card.name, neighbor_names) * 0.5

    def placement_score(coord: Tuple[int, int], card: Card,
                        remaining: List[Card]) -> float:
        combo    = _group_combo_score(coord, card)    * 5.0
        passive  = _passive_neighbor_score(coord, card) * 4.0
        center   = 2.0 if coord in center_ring else 0.0
        look     = _lookahead_score(coord, card, remaining) * 1.0
        matrix   = _matrix_score(coord, card)
        return combo + passive + center + look + matrix

    placed = 0
    remaining_hand = list(hand_list)  # lookahead için kalan el takibi

    for card in hand_list:
        if placed >= PLACE_PER_TURN or not free:
            break
        if time.perf_counter() - start_ts > PLACEMENT_TIME_BUDGET_S:
            break

        other_cards = [c for c in remaining_hand if c is not card]

        best_coord = None
        best_sc    = -1.0
        for coord in free[:MAX_COORD_CHECK]:
            if time.perf_counter() - start_ts > PLACEMENT_TIME_BUDGET_S:
                break
            sc = placement_score(coord, card, other_cards)
            if sc > best_sc:
                best_sc    = sc
                best_coord = coord

        target = best_coord if best_coord is not None else free[-1]
        final_combo = _group_combo_score(target, card)

        player.board.place(target, card)
        free.remove(target)
        
        # Remove card from hand (handle None-slot system)
        for i, hand_card in enumerate(player.hand):
            if hand_card is card:
                player.hand[i] = None
                break
        
        remaining_hand.remove(card)
        placed += 1

        # Synergy matrix güncelle
        if sm is not None:
            sm.update_from_board(player.board)

        # ── Strategy Logger hook ──────────────────────────────────
        if _slogger is not None:
            _slogger.log_placement(player, card, target,
                                   combo_score=final_combo)


class BuilderStrategy(BaseStrategy):
    def buy_cards(self, player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref=None):
        _buy_builder(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn, game_ref)
    
    def place_cards(self, player, rng=None, **kwargs):
        _place_fast_synergy(player)
