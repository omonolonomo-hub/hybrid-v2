
# <<< TRAINED_PARAMS_START >>>
# Bu blok train_strategies.py tarafından otomatik oluşturuldu.
# Kullanım: from engine_core.ai import TRAINED_PARAMS
#           ai = ParameterizedAI(TRAINED_PARAMS)
#
# Phase 1: Tüm stratejiler için varsayılan parametreler.
# train_strategies.py --apply ile bu blok güncellenir.
TRAINED_PARAMS = {
    "economist": {
        # Backward compat params
        "thresh_high":          27.012525825899594,
        "thresh_mid":            5.887870123764179,
        "thresh_low":           11.572130722067811,
        "buy_2_thresh":         15.0,
        # Phase params
        "greed_turn_end":        6.556475060280888,
        "spike_turn_end":       14.773731014667712,
        "greed_gold_thresh":    15.0,
        "spike_r4_thresh":      42.07452062733782,
        "convert_r5_thresh":    80.0,
        "spike_buy_count":       3.1891953600814538,
        "convert_buy_count":     3.6086842743641023,
    },
    "warrior": {
        "power_weight":  1.0,
        "rarity_weight": 0.0,
    },
    "builder": {
        "combo_weight":         0.5,    # combo/synergy skorunun ana ağırlığı
        "power_weight":         0.4,    # power tie-break / güvenlik ağırlığı
        # Economist economy model copied into builder
        "greed_turn_end":        5.0,
        "spike_turn_end":       14.773731014667712,
        "greed_gold_thresh":     8.0,
        "spike_r4_thresh":      42.07452062733782,
        "convert_r5_thresh":    80.0,
        "spike_buy_count":       2.0,
        "convert_buy_count":     3.0,
    },
    "evolver": {
        "evo_near_bonus":     1000.0,
        "evo_one_bonus":       500.0,
        "rarity_weight_mult":   10.0,
        "power_weight":          1.0,
    },
    "balancer": {
        "group_bonus":  5.0,
        "group_thresh": 3.0,
        "power_weight": 1.0,
    },
    "rare_hunter": {
        "fallback_rarity": 3.0,
    },
    "tempo": {
        "power_center_thresh": 45.0,
        "combo_center_weight":  1.5,
    },
    "random": {},
}
# <<< TRAINED_PARAMS_END >>>


def load_all_strategy_params() -> Dict[str, Dict[str, Any]]:
    """Phase 1: Tüm stratejiler için JSON parametrelerini tek seferde yükle.

    trained_params.json formatı:
        {
            "economist": {"greed_turn_end": 7, ...},
            "warrior":   {"power_weight": 1.2, ...},
            ...
        }

    Crash-proof: herhangi bir hata durumunda {} döner, asla exception fırlatmaz.
    Yükleme sadece ParameterizedAI.__init__() sırasında bir kez yapılır;
    runtime'da JSON'a tekrar erişilmez (zero performance regression).

    File location: project_root/trained_params.json
    """
    try:
        path = Path(__file__).parent.parent / "trained_params.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        return {}


def load_strategy_params() -> Dict[str, Any]:
    """Backward compat: sadece economist parametrelerini döndürür.

    Phase 0'dan kalan eski arayüz. Phase 1'de bu fonksiyonu çağıran
    kod varsa çalışmaya devam eder; ancak yeni kod load_all_strategy_params()
    kullanmalıdır.
    """
    return load_all_strategy_params().get("economist", {})


"""
================================================================
|         AUTOCHESS HYBRID - AI Module                         |
|  AI strategies for card buying and placement                 |
================================================================

This module contains the AI class with various strategies for automated
gameplay including buying cards and placing them on the board.
"""

import random
import json
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

# Import dependencies
try:
    from .card import Card
    from .player import Player
    from .constants import (
        CARD_COSTS, HEX_DIRS, OPP_DIR, STAT_TO_GROUP, PLACE_PER_TURN
    )
    from .strategy_logger import get_strategy_logger
except ImportError:
    from card import Card
    from player import Player
    from constants import (
        CARD_COSTS, HEX_DIRS, OPP_DIR, STAT_TO_GROUP, PLACE_PER_TURN
    )
    try:
        from strategy_logger import get_strategy_logger
    except ImportError:
        def get_strategy_logger(): return None


MAX_LOOKAHEAD_CARDS = 4
MAX_COORD_CHECK = 8
PLACEMENT_TIME_BUDGET_S = 0.05


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
        try:
            from .constants import HEX_DIRS
        except ImportError:
            from constants import HEX_DIRS

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


# ===================================================================
# AI STRATEGIES
# ===================================================================

class AI:
    @staticmethod
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

    @staticmethod
    def _economy_phase_controls(player: Player, market: List[Card], max_cards: int,
                                market_obj=None, trigger_passive_fn=None,
                                ai_instance=None, strategy: str = "economist") -> Dict[str, Any]:
        """Shared phase economy engine used by economist and builder."""
        fallback = "economist" if strategy != "economist" else None

        def get_param(key, default):
            return AI._get_param_with_fallback(ai_instance, strategy, key, default, fallback)

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

    @staticmethod
    def buy_cards(player: Player, market: List[Card], max_cards: int = 1,
                  market_obj=None, rng=None, trigger_passive_fn=None,
                  ai_instance=None):
        """Buy from market according to player.strategy.
        market_obj: Market instance for hand-overflow pool returns (optional).
        trigger_passive_fn: Function to trigger passive abilities (injected dependency).
        ai_instance: ParameterizedAI instance for parameter access (optional).
                     Phase 1: tüm stratejiler ai_instance alır.
        """
        if rng is None:
            rng = random.Random()
        if player.strategy == "random":
            AI._buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "warrior":
            AI._buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "builder":
            AI._buy_builder(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "evolver":
            AI._buy_evolver(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "economist":
            AI._buy_economist(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "balancer":
            AI._buy_balancer(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "rare_hunter":
            AI._buy_rare_hunter(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        elif player.strategy == "tempo":
            AI._buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
        else:
            AI._buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)

    @staticmethod
    def _buy_random(player: Player, market: List[Card], max_cards: int,
                    market_obj=None, rng=None, trigger_passive_fn=None,
                    ai_instance=None):
        if rng is None:
            rng = random.Random()
        budget = player.gold
        affordable = [c for c in market if CARD_COSTS[c.rarity] <= budget]
        rng.shuffle(affordable)
        for card in affordable[:max_cards]:
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_warrior(player: Player, market: List[Card], max_cards: int,
                     market_obj=None, rng=None, trigger_passive_fn=None,
                     ai_instance=None):
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
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_builder(player: Player, market: List[Card], max_cards: int,
                    market_obj=None, rng=None, trigger_passive_fn=None,
                    ai_instance=None):
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
        cw = AI._get_param_with_fallback(ai_instance, "builder", "combo_weight", None)
        if cw is None:
            cw = AI._get_param_with_fallback(ai_instance, "builder", "group_weight", 1.0)
        pw = AI._get_param_with_fallback(ai_instance, "builder", "power_weight", 0.4)

        econ = AI._economy_phase_controls(
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

        # Rarity power normalization için
        try:
            from .constants import RARITY_TAVAN
        except ImportError:
            from constants import RARITY_TAVAN

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
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_evolver(player: Player, market: List[Card], max_cards: int,
                     market_obj=None, rng=None, trigger_passive_fn=None,
                     ai_instance=None):
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
        player.buy_card(best, market=market_obj, trigger_passive_fn=trigger_passive_fn)

        if max_cards > 1 and player.gold >= 4:
            remaining = [c for c in market if affordable(c) and c.name != best.name]
            second_candidates = [c for c in remaining
                                 if owned.get(c.name, 0) >= 1
                                 and not owned.get(f"Evolved {c.name}", 0)]
            if second_candidates:
                second = max(second_candidates, key=focus_score)
                player.buy_card(second, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_economist(player: Player, market: List[Card], max_cards: int,
                       market_obj=None, rng=None, trigger_passive_fn=None,
                       ai_instance=None):
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
        econ = AI._economy_phase_controls(
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
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_balancer(player: Player, market: List[Card], max_cards: int,
                      market_obj=None, rng=None, trigger_passive_fn=None,
                      ai_instance=None):
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
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def _buy_rare_hunter(player: Player, market: List[Card], max_cards: int,
                        market_obj=None, rng=None, trigger_passive_fn=None,
                        ai_instance=None):
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
                player.buy_card(max(rare5, key=lambda c: c.total_power()), market=market_obj, trigger_passive_fn=trigger_passive_fn)
                return

        # Then 4-pip
        if gold >= CARD_COSTS["4"]:
            rare4 = sorted(
                [c for c in market if c.rarity == "4"],
                key=lambda c: c.total_power(), reverse=True
            )
            for card in rare4[:max_cards]:
                player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)
            if rare4:
                return

        # Fallback: parameterized rarity — keep banking gold
        rfb = sorted(
            [c for c in market if c.rarity == fb_rarity and CARD_COSTS[c.rarity] <= gold],
            key=lambda c: c.total_power(), reverse=True
        )
        for card in rfb[:1]:
            player.buy_card(card, market=market_obj, trigger_passive_fn=trigger_passive_fn)

    @staticmethod
    def place_cards(player: Player, rng=None,
                    power_center_thresh: float = 45.0,
                    combo_center_weight: float = 1.5):
        """Place hand cards onto the board per strategy."""
        if player.strategy == "builder":
            AI._place_fast_synergy(player)
        elif player.strategy == "tempo":
            AI._place_aggressive(player,
                                 power_center_thresh=power_center_thresh,
                                 combo_center_weight=combo_center_weight)
        else:
            AI._place_smart_default(player, rng=rng)

    @staticmethod
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

        # Strateji bazlı kart sıralama
        if strategy in ("warrior", "rare_hunter"):
            sorted_cards = sorted(list(player.hand),
                                  key=lambda c: c.total_power(), reverse=True)
        elif strategy == "evolver":
            # Evolved kartları öne al, sonra power sırası
            sorted_cards = sorted(
                list(player.hand),
                key=lambda c: (1 if c.rarity == "E" else 0, c.total_power()),
                reverse=True
            )
        else:
            # economist, balancer, random — power sırasıyla
            sorted_cards = sorted(list(player.hand),
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
            player.hand.remove(card)
            placed += 1

            # ── Strategy Logger hook ─────────────────────────────────────
            if _slogger is not None:
                _slogger.log_placement(player, card, target,
                                       combo_score=final_combo)

    @staticmethod
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
        free = player.board.free_coords()
        if not free:
            return

        start_ts = time.perf_counter()
        _slogger  = get_strategy_logger()
        grid      = player.board.grid
        hand_list = list(player.hand)

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
            player.hand.remove(card)
            remaining_hand.remove(card)
            placed += 1

            # Synergy matrix güncelle
            if sm is not None:
                sm.update_from_board(player.board)

            # ── Strategy Logger hook ──────────────────────────────────
            if _slogger is not None:
                _slogger.log_placement(player, card, target,
                                       combo_score=final_combo)

    @staticmethod
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
        hand_list = list(player.hand)
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
            player.hand.remove(card)
            placed += 1

            if sm is not None:
                sm.update_from_board(player.board)

            if _slogger is not None:
                _slogger.log_placement(player, card, target,
                                       combo_score=final_combo)

    @staticmethod
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

        # Sort hand by power (strongest first) — Tempo character preserved
        sorted_cards = sorted(list(player.hand), key=lambda c: c.total_power(), reverse=True)

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
            player.hand.remove(card)
            placed += 1

            # ── Strategy Logger hook ──────────────────────────────────────
            if _slogger is not None:
                _slogger.log_placement(player, card, target,
                                       combo_score=final_combo)


# ===================================================================
# PARAMETERIZED AI - Phase 1: Multi-Strategy Parameter System
# ===================================================================

class ParameterizedAI:
    """Phase 1: Tüm stratejiler için parametre enjeksiyonlu AI wrapper.

    Üç katmanlı parametre öncelik sistemi (düşükten yükseğe):
        1. TRAINED_PARAMS hardcoded defaults   (her strateji için)
        2. trained_params.json dosyası          (override, partial OK)
        3. Manuel constructor params            (en yüksek öncelik)

    self.p yapısı:
        self.p["economist"]["greed_turn_end"] = 6.55   # JSON'dan
        self.p["warrior"]["power_weight"]     = 1.0    # default
        self.p["builder"]["combo_weight"]     = 0.6    # default

    Performans: JSON yüklemesi sadece __init__'te bir kez yapılır.
    Runtime'da dict lookup O(1) — zero performance regression.

    Phase 1: Tüm 8 strateji desteklenir.
    Phase 2: self-play learning bu altyapı üzerine inşa edilir.
    """

    def __init__(self,
                 strategy: str = "economist",
                 params: Optional[Dict[str, Any]] = None):
        """Parametre çözümleme ve merge engine.

        Args:
            strategy: Birincil strateji adı (override için referans noktası).
                      Tüm stratejiler yine de yüklenir ve merge edilir.
            params:   Belirli bir strateji için manuel override dict'i.
                      {"greed_turn_end": 7, "spike_turn_end": 16, ...} formatı.
                      Sadece `strategy` için uygulanır.
        """
        self.strategy = strategy

        # ── Step 1: JSON'dan tüm stratejileri yükle (init-only, crash-proof) ──
        loaded = load_all_strategy_params()

        # ── Step 2: Her strateji için merge engine ─────────────────────────────
        # Priority: TRAINED_PARAMS defaults < JSON file < manual params
        # Partial JSON desteği: eksik anahtarlar default'a düşer.
        # Eksik strateji: tamamen default kullanılır.
        self.p: Dict[str, Dict[str, Any]] = {}
        for strat, defaults in TRAINED_PARAMS.items():
            self.p[strat] = {
                **defaults,                   # hardcoded defaults (en düşük öncelik)
                **loaded.get(strat, {}),      # JSON overrides (orta öncelik)
            }

        # ── Step 3: Manuel override (en yüksek öncelik, sadece `strategy` için) ─
        if params is not None:
            self.p[strategy] = {
                **self.p.get(strategy, {}),
                **params,
            }

    def get_param(self, strategy: str, key: str, default: Any) -> Any:
        """Strateji bazlı güvenli parametre erişimi.

        Phase 1 API — tüm _buy_* metodları bu helper'ı kullanır.

        Args:
            strategy: Strateji adı ("economist", "warrior", ...)
            key:      Parametre anahtarı ("greed_turn_end", ...)
            default:  Anahtar bulunamazsa dönülecek değer

        Returns:
            self.p[strategy][key] ya da default.
        """
        return self.p.get(strategy, {}).get(key, default)

    def buy_cards(self, player: Player, market: List[Card], max_cards: int = 1,
                  market_obj=None, rng=None, trigger_passive_fn=None):
        """Tüm stratejiler için parametre enjeksiyonlu buy dispatcher."""
        AI.buy_cards(player, market, max_cards, market_obj, rng,
                     trigger_passive_fn, ai_instance=self)

    def place_cards(self, player: Player, rng=None,
                    power_center_thresh: float = 45.0,
                    combo_center_weight: float = 1.5):
        """Yerleştirme: tempo parametreleri self.p'den okunur."""
        # Tempo'nun place parametrelerini self.p'den al
        pct = self.get_param("tempo", "power_center_thresh", power_center_thresh)
        ccw = self.get_param("tempo", "combo_center_weight", combo_center_weight)
        AI.place_cards(player, rng, pct, ccw)
