#!/usr/bin/env python3
"""
================================================================
  AUTOCHESS HYBRID — AI Strateji Eğitici
  Genetik Algoritma ile Parametre Optimizasyonu

  Her strateji için en iyi parametreleri arar.
  Sonuçlar: output/training/trained_params.json

  Kullanım:
    python train_strategies.py                      # tam eğitim (composite fitness)
    python train_strategies.py --quick              # hızlı test (5 gen, 30 oyun)
    python train_strategies.py --strategy evolver   # tek strateji
    python train_strategies.py --fitness win        # sadece win_rate (eski mod)
    python train_strategies.py --apply              # öğrenilen parametreleri ai.py'e yazar
    python train_strategies.py --validate           # doğrulama koşusu
================================================================
"""

import sys, os, json, random, time, argparse
from collections import defaultdict
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool, Card
from engine_core.constants import (
    STRATEGIES, STARTING_HP, CARD_COSTS,
    PLACE_PER_TURN, HEX_DIRS, OPP_DIR, STAT_TO_GROUP
)
from engine_core.player import Player
from engine_core.game import Game
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log

OUT_DIR = os.path.join(ROOT, "output", "training")
os.makedirs(OUT_DIR, exist_ok=True)

# ================================================================
# FITNESS AĞIRLIKLARI
# ================================================================
#
# Composite fitness, AI'ın sadece "kısa vadeli agresif" oynamasını
# önler. Tek başına win_rate kullanan bir fitness şu sorunu yaşar:
#
#   Yalnızca win_rate → AI ilk birkaç turda agresif saldırır,
#   erken elendiğinde bile zaman zaman kazanır. Ama uzun vadeli
#   strateji (sinerji, ekonomi) öğrenilemez.
#
# Composite çözümü:
#   fitness = 0.60 * win_rate            ← birincil hedef (kazanmak)
#           + 0.20 * hayatta_kalma_oranı ← uzun oyun ödülü
#           + 0.15 * sinerji_oranı       ← sinerji kullanımı
#           + 0.05 * final_hp_oranı      ← ne kadar sağlıklı bitti
#
# "--fitness win" ile eski davranışa geçilebilir.

FITNESS_WEIGHTS = {
    "win_rate":    0.60,
    "survival":    0.20,   # turns_played / 50 (max tur limiti)
    "synergy":     0.15,   # avg sinerji/tur, normalize edilmiş
    "final_hp":    0.05,   # player.hp / STARTING_HP
}

# Sinerji normalizasyonu: simülasyonlarda gözlemlenen ~0-20 aralığı
SYNERGY_NORM = 20.0


# ================================================================
# PARAMETRELİ AI
# ================================================================

class ParameterizedAI:
    """
    Standart AI mantığının parametre-enjeksiyonlu versiyonu.
    Genetik algoritmanın keşfettiği float parametrelerle çalışır.
    game.py'deki `ai_override` hook'u üzerinden enjekte edilir.
    """

    def __init__(self, all_params: Dict[str, Dict[str, float]]):
        self.all_params = all_params

    def buy_cards(self, player: Player, market: List[Card], max_cards: int = 1,
                  market_obj=None, rng=None, trigger_passive_fn=None):
        if rng is None:
            rng = random.Random()
        s = player.strategy
        p = self.all_params.get(s, {})
        dispatch = {
            "random":      self._buy_random,
            "warrior":     self._buy_warrior,
            "builder":     self._buy_builder,
            "evolver":     self._buy_evolver,
            "economist":   self._buy_economist,
            "balancer":    self._buy_balancer,
            "rare_hunter": self._buy_rare_hunter,
            "tempo":       self._buy_warrior,
        }
        dispatch.get(s, self._buy_random)(
            player, market, max_cards, market_obj, rng, trigger_passive_fn, p
        )

    def place_cards(self, player: Player, rng=None):
        s = player.strategy
        p = self.all_params.get(s, {})
        if s == "builder":
            self._place_combo_optimized(player, p)
        elif s == "tempo":
            self._place_aggressive(
                player, p,
                power_center_thresh=p.get("power_center_thresh", 45.0),
                combo_center_weight=p.get("combo_center_weight", 1.5),
            )
        else:
            player.place_cards(rng=rng)

    # ── Satın alma ────────────────────────────────────────────

    def _buy_random(self, player, market, max_cards, market_obj, rng, fn, p):
        affordable = [c for c in market if CARD_COSTS[c.rarity] <= player.gold]
        rng.shuffle(affordable)
        for c in affordable[:max_cards]:
            player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    def _buy_warrior(self, player, market, max_cards, market_obj, rng, fn, p):
        pw  = p.get("power_weight",  1.0)
        rw  = p.get("rarity_weight", 0.0)
        rm  = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "E": 6}
        aff = sorted(
            [c for c in market if CARD_COSTS[c.rarity] <= player.gold],
            key=lambda c: c.total_power() * pw + rm.get(c.rarity, 0) * rw,
            reverse=True
        )
        for c in aff[:max_cards]:
            player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    def _buy_builder(self, player, market, max_cards, market_obj, rng, fn, p):
        """
        Gold- ve tur-bazlı dinamik ağırlık sistemi.

        Builder'in mevcut sorunu: erken oyun kombo yaparken yüksek sinerji
        puanı üretiyor ama bunu galibiyete dönüşttüremıyor.
        Sebep: tüm oyun boyunca sinerji ağırlıklı alım yaparak düşuk rarity
        kartlarla takılı kalıyor.

        Çözüm: Altın artıkça VE tur ilerledikçe saf güç (rarity) ağırlığı yüksek,
        sinerji ağırlığı düşüyor. Hem ekonomi hem geç oyun agóresyonu körülmüş olur.
        """
        gw   = p.get("group_weight", 1.0)
        pw   = p.get("power_weight", 0.0)
        gold = player.gold
        turn = player.turns_played
        rm   = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "E": 6}

        # ── Dinamik ağırlık belirleme ──────────────────────────────────
        if gold >= 30 and turn >= 20:          # Geç oyun + zengin: tam agóresyon
            syn_w, pow_w = 0.10, 0.90
        elif gold >= 30 or turn >= 20:         # Ya geç tur ya yüksek altın
            syn_w, pow_w = 0.20, 0.80
        elif gold >= 15:                       # Orta ekonomi: dengeli
            syn_w, pow_w = 0.40, 0.60
        else:                                  # Erken oyun: sinerji odaklı
            syn_w = max(0.70, gw * 0.70)
            pow_w = 0.30

        # ── Hedef grup hesapla ───────────────────────────────────────
        dom = defaultdict(int)
        for card in player.board.alive_cards():
            dom[card.dominant_group()] += 1
        target = max(dom, key=dom.get) if dom else "CONNECTION"

        def score(c):
            # Sinerji: dominant grubu ile örtüşen stat sayısı
            gs = sum(1 for stat in c.stats if STAT_TO_GROUP.get(stat) == target)
            synergy_score = gs * syn_w
            # Güç: normalize total_power + rarity katılımı
            power_score   = (c.total_power() * 0.01 + rm.get(c.rarity, 0)) * pow_w
            return synergy_score + power_score

        aff = sorted(
            [c for c in market if CARD_COSTS[c.rarity] <= player.gold],
            key=score, reverse=True
        )
        for c in aff[:max_cards]:
            player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    def _buy_evolver(self, player, market, max_cards, market_obj, rng, fn, p):
        evo_near = p.get("evo_near_bonus",    1000.0)
        evo_one  = p.get("evo_one_bonus",      500.0)
        rm       = p.get("rarity_weight_mult",  10.0)
        pw       = p.get("power_weight",          1.0)
        owned = player.copies
        gold  = player.gold
        rmap  = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
        def affordable(c):
            return CARD_COSTS[c.rarity] <= gold and c.rarity != "E"
        pool = [c for c in market if affordable(c)]
        if not pool:
            return
        def focus(c):
            cnt = owned.get(c.name, 0)
            if owned.get(f"Evolved {c.name}", 0) > 0:
                return -1.0
            rw = rmap.get(c.rarity, 0) * rm
            if cnt == 2:   return evo_near + rw + c.total_power() * pw
            elif cnt == 1: return evo_one  + rw + c.total_power() * pw
            return rw + c.total_power() * pw
        best = max(pool, key=focus)
        if focus(best) < 0:
            best = max(pool, key=lambda c: c.total_power())
        player.buy_card(best, market=market_obj, trigger_passive_fn=fn)
        if max_cards > 1 and player.gold >= 4:
            rest = [c for c in pool if c.name != best.name
                    and owned.get(c.name, 0) >= 1
                    and not owned.get(f"Evolved {c.name}", 0)]
            if rest:
                player.buy_card(max(rest, key=focus), market=market_obj, trigger_passive_fn=fn)

    def _buy_economist(self, player, market, max_cards, market_obj, rng, fn, p):
        """
        Phase-aware economist strategy with trainable thresholds.

        Parametreler (GA tarafından optimize edilecek):
          - greed_turn_end: When to end greed phase (default 8)
          - spike_turn_end: When to end spike phase (default 18)
          - greed_gold_thresh: Min gold to buy in greed phase
          - spike_r4_thresh: Gold needed for rarity-4 in spike
          - convert_gold_thresh: Gold needed to start legendary buying
          - spike_buy_count: Cards to buy per turn in spike
          - convert_buy_count: Cards to buy per turn in convert
        """
        gold = player.gold
        hp = player.hp
        turn = player.turns_played

        # Parametreler (defaults + GA optimized)
        greed_turn_end = int(p.get("greed_turn_end", 8.0))
        spike_turn_end = int(p.get("spike_turn_end", 18.0))
        greed_gold_thresh = p.get("greed_gold_thresh", 12.0)
        spike_r4_thresh = p.get("spike_r4_thresh", 40.0)
        convert_r5_thresh = p.get("convert_r5_thresh", 60.0)
        spike_buy_count = max(1, int(p.get("spike_buy_count", 2.0)))
        convert_buy_count = max(1, int(p.get("convert_buy_count", 3.0)))

        # ════════════════════════════════════════════════════════════
        # EMERGENCY
        # ════════════════════════════════════════════════════════════
        if hp < 35:
            aff = sorted(
                [c for c in market if CARD_COSTS[c.rarity] <= gold],
                key=lambda c: c.total_power(),
                reverse=True
            )
            for c in aff[:min(max_cards, 3)]:
                player.buy_card(c, market=market_obj, trigger_passive_fn=fn)
            return

        # ════════════════════════════════════════════════════════════
        # PHASE 1: GREED
        # ════════════════════════════════════════════════════════════
        if turn <= greed_turn_end:
            if gold < greed_gold_thresh:
                return  # Wait for more income

            # Buy cheap high-value cards only
            cheap = sorted(
                [c for c in market if CARD_COSTS[c.rarity] in [CARD_COSTS["1"], CARD_COSTS["2"]]],
                key=lambda c: c.total_power() / CARD_COSTS[c.rarity],
                reverse=True
            )

            if cheap and cheap[0].total_power() / CARD_COSTS[cheap[0].rarity] > 3.0:
                player.buy_card(cheap[0], market=market_obj, trigger_passive_fn=fn)
            return

        # ════════════════════════════════════════════════════════════
        # PHASE 2: SPIKE
        # ════════════════════════════════════════════════════════════
        elif turn <= spike_turn_end:
            if gold >= spike_r4_thresh:
                max_cost = CARD_COSTS["4"]
            elif gold >= 25:
                max_cost = CARD_COSTS["3"]
            elif gold >= 12:
                max_cost = CARD_COSTS["2"]
            else:
                max_cost = CARD_COSTS["1"]

            aff = sorted(
                [c for c in market if CARD_COSTS[c.rarity] <= max_cost],
                key=lambda c: c.total_power(),
                reverse=True
            )

            cnt = spike_buy_count if gold >= 25 else min(spike_buy_count, 1)
            for c in aff[:min(max_cards, cnt)]:
                player.buy_card(c, market=market_obj, trigger_passive_fn=fn)
            return

        # ════════════════════════════════════════════════════════════
        # PHASE 3: CONVERT
        # ════════════════════════════════════════════════════════════
        else:
            if gold >= convert_r5_thresh:
                max_cost = CARD_COSTS["5"]
            elif gold >= 40:
                max_cost = CARD_COSTS["4"]
            elif gold >= 20:
                max_cost = CARD_COSTS["3"]
            else:
                max_cost = CARD_COSTS["2"]

            aff = sorted(
                [c for c in market if CARD_COSTS[c.rarity] <= max_cost],
                key=lambda c: c.total_power(),
                reverse=True
            )

            for c in aff[:min(max_cards, convert_buy_count)]:
                player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    def _buy_balancer(self, player, market, max_cards, market_obj, rng, fn, p):
        gb  = p.get("group_bonus",  5.0)
        gt  = int(p.get("group_thresh", 3))
        pw  = p.get("power_weight", 1.0)
        bg  = defaultdict(int)
        for card in player.board.alive_cards():
            bg[card.dominant_group()] += 1
        def score(c):
            return c.total_power() * pw + (gb if bg[c.dominant_group()] < gt else 0)
        aff = sorted(
            [c for c in market if CARD_COSTS[c.rarity] <= player.gold],
            key=score, reverse=True
        )
        for c in aff[:max_cards]:
            player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    def _buy_rare_hunter(self, player, market, max_cards, market_obj, rng, fn, p):
        fr   = str(max(1, min(4, int(round(p.get("fallback_rarity", 3.0))))))
        gold = player.gold
        if gold >= CARD_COSTS["5"]:
            r5 = [c for c in market if c.rarity == "5"]
            if r5:
                player.buy_card(max(r5, key=lambda c: c.total_power()),
                                market=market_obj, trigger_passive_fn=fn)
                return
        if gold >= CARD_COSTS["4"]:
            r4 = sorted([c for c in market if c.rarity == "4"],
                        key=lambda c: c.total_power(), reverse=True)
            for c in r4[:max_cards]:
                player.buy_card(c, market=market_obj, trigger_passive_fn=fn)
            if r4:
                return
        rfb = sorted(
            [c for c in market if c.rarity == fr and CARD_COSTS[c.rarity] <= gold],
            key=lambda c: c.total_power(), reverse=True
        )
        for c in rfb[:1]:
            player.buy_card(c, market=market_obj, trigger_passive_fn=fn)

    # ── Yerleştirme ───────────────────────────────────────────

    def _place_combo_optimized(self, player, p):
        free = player.board.free_coords()
        if not free:
            return
        cw = p.get("combo_weight", 1.0)
        placed = 0
        for card in list(player.hand):
            if placed >= PLACE_PER_TURN or not free:
                break
            best_coord, best_score = None, -1
            for coord in free:
                score = 0
                q, r = coord
                for d, (dq, dr) in enumerate(HEX_DIRS):
                    nc = (q + dq, r + dr)
                    if nc in player.board.grid:
                        nbr = player.board.grid[nc]
                        opp = OPP_DIR[d]
                        g1 = STAT_TO_GROUP.get(card.edges[d][0]) if d < len(card.edges) else None
                        g2 = STAT_TO_GROUP.get(nbr.edges[opp][0]) if opp < len(nbr.edges) else None
                        if g1 and g2 and g1 == g2:
                            score += cw
                if score > best_score:
                    best_score, best_coord = score, coord
            if best_coord:
                player.board.place(best_coord, card)
                free.remove(best_coord)
                player.hand.remove(card)
                placed += 1

    def _place_aggressive(self, player, p,
                           power_center_thresh: float = 45.0,
                           combo_center_weight: float = 1.5):
        free = player.board.free_coords()
        if not free:
            return
        thresh = p.get("power_center_thresh", power_center_thresh)
        ccw    = p.get("combo_center_weight", combo_center_weight)
        center = {(0, 0)} | {(dq, dr) for (dq, dr) in HEX_DIRS}
        grid   = player.board.grid

        def _combo_score_at(coord, card):
            card_group = card.dominant_group()
            q, r = coord
            s = 0
            for dq, dr in HEX_DIRS:
                nbr = grid.get((q + dq, r + dr))
                if nbr is not None and nbr.dominant_group() == card_group:
                    s += 1
            return s

        sorted_hand = sorted(list(player.hand), key=lambda c: c.total_power(), reverse=True)
        placed = 0
        for card in sorted_hand:
            if placed >= PLACE_PER_TURN or not free:
                break
            if card.total_power() >= thresh:
                center_free = [c for c in free if c in center]
                rim_free    = [c for c in free if c not in center]
                best_center = center_free[0] if center_free else None
                cc = _combo_score_at(best_center, card) if best_center else -1
                best_rim, best_rc = None, -1
                for rc in rim_free:
                    cs = _combo_score_at(rc, card)
                    if cs > best_rc:
                        best_rc, best_rim = cs, rc
                if best_rim is not None and best_rc > cc * ccw:
                    target = best_rim
                elif best_center is not None:
                    target = best_center
                else:
                    target = free[-1]
            else:
                best_coord, best_cs = None, -1
                for rc in free:
                    cs = _combo_score_at(rc, card)
                    if cs > best_cs:
                        best_cs, best_coord = cs, rc
                target = best_coord if best_coord else free[-1]
            player.board.place(target, card)
            free.remove(target)
            player.hand.remove(card)
            placed += 1


# ================================================================
# PARAMETRE UZAYI VE VARSAYILANLAR
# ================================================================

PARAM_SPACE: Dict[str, Dict[str, Tuple[float, float]]] = {
    "warrior":     {"power_weight": (0.3, 3.0), "rarity_weight": (0.0, 8.0)},
    "builder":     {"group_weight": (0.3, 6.0), "power_weight":  (0.0, 3.0)},
    "evolver":     {
        "evo_near_bonus":     (100.0, 3000.0),
        "evo_one_bonus":      ( 50.0, 1500.0),
        "rarity_weight_mult": (  1.0,   40.0),
        "power_weight":       (  0.3,    3.0),
    },
    "economist":   {
        # Old parameters (backward compat)
        "thresh_high":          (10.0, 60.0),
        "thresh_mid":           ( 4.0, 25.0),
        "thresh_low":           ( 2.0, 12.0),
        "buy_2_thresh":         ( 3.0, 30.0),
        
        # NEW: Phase parameters
        "greed_turn_end":       ( 6.0, 12.0),        # When greed phase ends
        "spike_turn_end":       (14.0, 22.0),        # When spike phase ends
        "greed_gold_thresh":    ( 8.0, 15.0),        # Min gold to buy in greed
        "spike_r4_thresh":      (30.0, 50.0),        # Gold for rarity-4 in spike
        "convert_r5_thresh":    (50.0, 80.0),        # Gold for legendary conversion
        "spike_buy_count":      ( 1.0,  4.0),        # Cards to buy per turn in spike
        "convert_buy_count":    ( 2.0,  5.0),        # Cards to buy per turn in convert
    },
    "balancer":    {
        "group_bonus":  ( 0.0, 25.0),
        "group_thresh": ( 1.0,  6.0),
        "power_weight": ( 0.3,  3.0),
    },
    "rare_hunter": {"fallback_rarity":      (1.0,  4.0)},
    "tempo":       {"power_center_thresh":  (30.0, 65.0),
                    "combo_center_weight":  (0.5,  4.0)},
    "random":      {},
}

DEFAULT_PARAMS: Dict[str, Dict[str, float]] = {
    "warrior":     {"power_weight": 1.0,    "rarity_weight": 0.0},
    "builder":     {"group_weight": 1.0,    "power_weight":  0.0},
    "evolver":     {"evo_near_bonus": 1000.0, "evo_one_bonus": 500.0,
                    "rarity_weight_mult": 10.0, "power_weight": 1.0},
    "economist":   {
        # Old defaults (backward compat)
        "thresh_high":      30.0,
        "thresh_mid":        8.0,
        "thresh_low":        4.0,
        "buy_2_thresh":     15.0,
        
        # NEW: Phase defaults
        "greed_turn_end":         8.0,
        "spike_turn_end":        18.0,
        "greed_gold_thresh":     12.0,
        "spike_r4_thresh":       40.0,
        "convert_r5_thresh":     60.0,
        "spike_buy_count":        2.0,
        "convert_buy_count":      3.0,
    },
    "balancer":    {"group_bonus": 5.0, "group_thresh": 3.0, "power_weight": 1.0},
    "rare_hunter": {"fallback_rarity": 3.0},
    "tempo":       {"power_center_thresh": 45.0, "combo_center_weight": 1.5},
    "random":      {},
}


# ================================================================
# FITNESS DEĞERLENDİRME
# ================================================================

def _composite_score(players_of_strategy, winner_strategy, strategy, n_games_run):
    """
    Bir grup oyun için composite fitness hesapla.

    Toplanan ham veriler:
      wins            — kaç oyun kazanıldı
      survival_scores — turns_played / 50.0 (normalize edilmiş hayatta kalma)
      synergy_scores  — ortalama sinerji/tur, [0,1] aralığına sıkıştırılmış
      hp_scores       — final_hp / STARTING_HP
    """
    w   = FITNESS_WEIGHTS
    win_rate = sum(1 for ws in winner_strategy if ws == strategy) / max(1, n_games_run)

    if not players_of_strategy:
        return win_rate  # sadece win_rate'e düş

    survival = sum(p.turns_played / 50.0 for p in players_of_strategy) / len(players_of_strategy)
    syn_raw  = [
        p.stats.get("synergy_sum", 0) / max(1, p.stats.get("synergy_turns", 1))
        for p in players_of_strategy
    ]
    synergy  = sum(min(1.0, v / SYNERGY_NORM) for v in syn_raw) / len(syn_raw)
    hp       = sum(p.hp / STARTING_HP for p in players_of_strategy) / len(players_of_strategy)

    return (w["win_rate"] * win_rate
          + w["survival"] * survival
          + w["synergy"]  * synergy
          + w["final_hp"] * hp)


def evaluate_fitness(strategy: str,
                     params: Dict[str, float],
                     card_pool: list,
                     rng: random.Random,
                     n_games: int,
                     fitness_mode: str = "composite") -> float:
    """
    Verilen parametrelerle n_games oyun boyunca stratejiyi dene.

    fitness_mode:
      "composite" → win_rate + survival + synergy + hp (önerilen)
      "win"       → sadece win_rate (eski davranış)

    Her oyunda 1 eğitilen + 7 farklı strateji player bulunur;
    bu sayede eğitilen strateji gerçek çeşitlilikle test edilir.
    """
    ai = ParameterizedAI({strategy: params})
    others = [s for s in STRATEGIES if s != strategy]
    eval_rng = random.Random(rng.randint(0, 2**31))

    winner_strategies = []
    all_trained_players = []
    played = 0

    for _ in range(n_games):
        try:
            clear_passive_trigger_log()
            pool = [strategy] + eval_rng.choices(others, k=7)
            eval_rng.shuffle(pool)
            players = [Player(pid=i, strategy=s) for i, s in enumerate(pool)]

            game = Game(
                players,
                verbose=False,
                rng=eval_rng,
                trigger_passive_fn=trigger_passive,
                combat_phase_fn=combat_phase,
                card_pool=card_pool,
                ai_override=ai,
            )
            winner = game.run()
            played += 1
            winner_strategies.append(winner.strategy)

            # Eğitilen stratejinin oyuncularını topla (fitness hesabı için)
            for p in players:
                if p.strategy == strategy:
                    all_trained_players.append(p)

        except Exception:
            continue

    if played == 0:
        return 0.0

    if fitness_mode == "win":
        return sum(1 for ws in winner_strategies if ws == strategy) / played

    return _composite_score(all_trained_players, winner_strategies, strategy, played)


# ================================================================
# GENETİK ALGORİTMA
# ================================================================

def _random_ind(strategy: str, rng: random.Random) -> Dict[str, float]:
    return {k: rng.uniform(lo, hi)
            for k, (lo, hi) in PARAM_SPACE.get(strategy, {}).items()}


def _clamp(strategy: str, ind: Dict[str, float]) -> Dict[str, float]:
    return {k: max(lo, min(hi, ind.get(k, (lo + hi) / 2)))
            for k, (lo, hi) in PARAM_SPACE.get(strategy, {}).items()}


def _mutate(strategy, ind, rng, rate, strength):
    new = dict(ind)
    for k, (lo, hi) in PARAM_SPACE.get(strategy, {}).items():
        if rng.random() < rate:
            new[k] += rng.gauss(0, (hi - lo) * strength)
    return _clamp(strategy, new)


def _crossover(a, b, rng):
    return {k: (a[k] if rng.random() < 0.5 else b[k]) for k in a}


def _tournament(pop, fits, k, rng):
    idx = rng.sample(range(len(pop)), min(k, len(pop)))
    return max(idx, key=lambda i: fits[i])


def evolve_strategy(strategy: str, card_pool: list,
                    rng: random.Random, cfg: dict) -> dict:
    POP   = cfg["pop_size"]
    GENS  = cfg["n_gens"]
    EVAL  = cfg["eval_games"]
    ELITE = cfg["elitism"]
    MRATE = cfg["mutation_rate"]
    MSTR  = cfg["mutation_strength"]
    TOURN = cfg["tournament_k"]
    FMODE = cfg.get("fitness_mode", "composite")

    space = PARAM_SPACE.get(strategy, {})
    if not space:
        print(f"    [{strategy}] Parametre yok — atlanıyor.")
        return {"strategy": strategy, "params": {}, "fitness": 0.0, "history": []}

    bar = "─" * (50 - len(strategy))
    print(f"\n  ── {strategy.upper()} {bar}")
    print(f"     Pop={POP} | Gen={GENS} | Eval={EVAL} oyun/birey | Fitness={FMODE}")

    population = [_random_ind(strategy, rng) for _ in range(POP)]
    population[0] = dict(DEFAULT_PARAMS.get(strategy, {}))

    history = []
    best_ind, best_fit = None, -1.0

    for gen in range(GENS):
        t0 = time.time()
        fits = [evaluate_fitness(strategy, ind, card_pool, rng, EVAL, FMODE)
                for ind in population]

        gen_best = max(fits)
        gen_avg  = sum(fits) / len(fits)
        best_idx = fits.index(gen_best)

        if gen_best > best_fit:
            best_fit = gen_best
            best_ind = dict(population[best_idx])

        elapsed = time.time() - t0
        print(f"     Gen {gen+1:>2}/{GENS}  "
              f"best={gen_best:.4f}  avg={gen_avg:.4f}  [{elapsed:.0f}s]")

        history.append({
            "gen": gen + 1,
            "best": round(gen_best, 4),
            "avg":  round(gen_avg,  4),
            "best_params": dict(population[best_idx]),
        })

        # Sonraki nesil
        sorted_idx = sorted(range(POP), key=lambda i: fits[i], reverse=True)
        next_pop   = [dict(population[i]) for i in sorted_idx[:ELITE]]
        while len(next_pop) < POP:
            p1 = _tournament(population, fits, TOURN, rng)
            p2 = _tournament(population, fits, TOURN, rng)
            child = _crossover(population[p1], population[p2], rng)
            child = _mutate(strategy, child, rng, MRATE, MSTR)
            next_pop.append(child)
        population = next_pop

    print(f"     ✓ En iyi fitness: {best_fit:.4f}")
    return {
        "strategy": strategy,
        "params":   best_ind or {},
        "fitness":  round(best_fit, 4),
        "history":  history,
    }


# ================================================================
# KAYIT VE RAPORLAMA
# ================================================================

def save_results(all_results: dict, cfg: dict):
    best_params = {s: r["params"] for s, r in all_results.items()}
    full = {
        "config":      cfg,
        "best_params": best_params,
        "details": {s: {"fitness": r["fitness"], "history": r["history"]}
                    for s, r in all_results.items()},
    }
    full_path   = os.path.join(OUT_DIR, "training_results.json")
    simple_path = os.path.join(OUT_DIR, "trained_params.json")
    with open(full_path,   "w", encoding="utf-8") as f:
        json.dump(full,        f, indent=2, ensure_ascii=False)
    with open(simple_path, "w", encoding="utf-8") as f:
        json.dump(best_params, f, indent=2, ensure_ascii=False)
    return simple_path, full_path


def print_summary(all_results: dict, fitness_mode: str):
    print()
    print("=" * 65)
    print(f"  SONUÇLAR — Öğrenilen En İyi Parametreler  [{fitness_mode} fitness]")
    print("=" * 65)

    rows = []
    for s, r in all_results.items():
        hist     = r.get("history", [])
        baseline = hist[0]["best"] if hist else r["fitness"]
        final    = r["fitness"]
        imp      = (final - baseline) / max(0.001, baseline) * 100
        rows.append((s, baseline, final, imp, r["params"]))
    rows.sort(key=lambda x: x[2], reverse=True)

    for s, base, final, imp, params in rows:
        print(f"\n  {s.upper()}")
        print(f"    Fitness : {base:.4f} → {final:.4f}  ({imp:+.1f}%)")
        for k, v in params.items():
            dv = DEFAULT_PARAMS.get(s, {}).get(k, "?")
            arrow = ("↑" if isinstance(dv, float) and v > dv
                     else "↓" if isinstance(dv, float) and v < dv else "·")
            print(f"      {k:<28} {v:>8.3f}  {arrow}  (varsayılan: {dv})")
    print()


def apply_to_ai(trained_params_path: str):
    ai_path = os.path.join(ROOT, "engine_core", "ai.py")
    with open(ai_path,            "r", encoding="utf-8") as f: content = f.read()
    with open(trained_params_path,"r", encoding="utf-8") as f: params  = json.load(f)

    ms = "# <<< TRAINED_PARAMS_START >>>"
    me = "# <<< TRAINED_PARAMS_END >>>"
    block = (
        f"\n{ms}\n"
        f"# Bu blok train_strategies.py tarafından otomatik oluşturuldu.\n"
        f"# Kullanım: from engine_core.ai import TRAINED_PARAMS\n"
        f"#           ai = ParameterizedAI(TRAINED_PARAMS)\n"
        f"TRAINED_PARAMS = {json.dumps(params, indent=4, ensure_ascii=False)}\n"
        f"{me}\n"
    )
    if ms in content:
        start = content.index(ms)
        end   = content.index(me) + len(me)
        content = content[:start] + block.strip() + content[end:]
    else:
        content = block + content

    with open(ai_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  ✓ TRAINED_PARAMS bloğu ai.py'e eklendi.")
    print("    Kullanım:")
    print("      from engine_core.ai import TRAINED_PARAMS")
    print("      from train_strategies import ParameterizedAI")
    print("      ai = ParameterizedAI(TRAINED_PARAMS)")
    print("      # game = Game(..., ai_override=ai)")


def validate(strategy: str = None, fitness_mode: str = "composite"):
    params_path = os.path.join(OUT_DIR, "trained_params.json")
    if not os.path.exists(params_path):
        print("  Eğitilmiş parametre dosyası bulunamadı. Önce eğitim yapın.")
        return
    with open(params_path, "r", encoding="utf-8") as f:
        trained = json.load(f)

    card_pool = get_card_pool()
    rng = random.Random(9999)
    targets = [strategy] if strategy else list(trained.keys())

    print(f"\n  Doğrulama (100 oyun/strateji, fitness={fitness_mode})...")
    print(f"  {'Strateji':<14}  {'Varsayılan':>12}  {'Eğitilmiş':>12}  {'İyileşme':>10}")
    print(f"  {'-'*55}")
    for s in targets:
        params = trained.get(s, {})
        if not params:
            continue
        df = evaluate_fitness(s, DEFAULT_PARAMS.get(s, {}), card_pool, rng, 100, fitness_mode)
        tf = evaluate_fitness(s, params,                     card_pool, rng, 100, fitness_mode)
        imp = (tf - df) / max(0.001, df) * 100
        print(f"  {s:<14}  {df:>11.4f}  {tf:>11.4f}  {imp:>+9.1f}%")


# ================================================================
# MAIN
# ================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Autochess Hybrid AI Eğitici")
    p.add_argument("--quick",    action="store_true",
                   help="Hızlı test: pop=10, gen=5, eval=30")
    p.add_argument("--strategy", type=str, default=None,
                   help="Sadece bu stratejiyi eğit (örn. evolver)")
    p.add_argument("--apply",    action="store_true",
                   help="Mevcut trained_params.json'u ai.py'e ekle")
    p.add_argument("--validate", action="store_true",
                   help="Mevcut trained_params.json'u doğrula")
    p.add_argument("--fitness",  type=str, default="composite",
                   choices=["composite", "win"],
                   help="Fitness modu: composite (önerilen) veya win")
    p.add_argument("--pop",  type=int, default=None)
    p.add_argument("--gens", type=int, default=None)
    p.add_argument("--eval", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()

    if args.apply:
        p = os.path.join(OUT_DIR, "trained_params.json")
        if not os.path.exists(p):
            print("  Önce eğitim yapın: python train_strategies.py")
            return
        apply_to_ai(p)
        return

    if args.validate:
        validate(args.strategy, args.fitness)
        return

    if args.quick:
        cfg = dict(pop_size=10, n_gens=5, eval_games=30,
                   elitism=2, mutation_rate=0.3, mutation_strength=0.25,
                   tournament_k=3, seed=args.seed, fitness_mode=args.fitness)
    else:
        cfg = dict(pop_size=args.pop  or 20,
                   n_gens  =args.gens or 15,
                   eval_games=args.eval or 80,
                   elitism=3, mutation_rate=0.3, mutation_strength=0.2,
                   tournament_k=3, seed=args.seed, fitness_mode=args.fitness)

    print("=" * 65)
    print("  AUTOCHESS HYBRID — AI Strateji Eğitici")
    print("=" * 65)
    print(f"  Fitness modu : {cfg['fitness_mode']}")
    if cfg["fitness_mode"] == "composite":
        w = FITNESS_WEIGHTS
        print(f"  Ağırlıklar   : win={w['win_rate']:.0%}  "
              f"survival={w['survival']:.0%}  "
              f"synergy={w['synergy']:.0%}  "
              f"hp={w['final_hp']:.0%}")
    print(f"  Pop={cfg['pop_size']} | Gen={cfg['n_gens']} | "
          f"Eval={cfg['eval_games']} oyun/birey | Seed={cfg['seed']}")

    targets = [args.strategy] if args.strategy else \
              [s for s in STRATEGIES if PARAM_SPACE.get(s)]
    print(f"  Hedef : {', '.join(targets)}")
    total = cfg["pop_size"] * cfg["n_gens"] * cfg["eval_games"] * len(targets)
    print(f"  Tahmin toplam oyun: ~{total:,}")
    print()

    card_pool    = get_card_pool()
    rng          = random.Random(cfg["seed"])
    all_results  = {}
    t0           = time.time()

    for strategy in targets:
        result = evolve_strategy(strategy, card_pool, rng, cfg)
        all_results[strategy] = result
        save_results(all_results, cfg)   # ara kayıt

    elapsed = time.time() - t0
    print(f"\n  Toplam süre: {elapsed:.1f}s  ({elapsed/60:.1f} dakika)")

    print_summary(all_results, cfg["fitness_mode"])

    sp, fp = save_results(all_results, cfg)
    print(f"  Kaydedildi:")
    print(f"    {sp}")
    print(f"    {fp}")
    print()
    print("  Sonraki adımlar:")
    print("    python train_strategies.py --validate")
    print("    python train_strategies.py --apply")
    print()


if __name__ == "__main__":
    main()
