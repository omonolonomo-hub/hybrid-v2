"""
Parameterized AI wrapper for multi-strategy parameter system.
"""

import logging
from typing import Dict, List, Optional, Any

from engine_core.card import Card
from engine_core.player import Player
from engine_core.ai.base import AI
from engine_core.ai.config import TRAINED_PARAMS, load_all_strategy_params

logger = logging.getLogger(__name__)


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
        if not loaded:
            logger.info("ParameterizedAI(%s): no JSON overrides loaded — using hardcoded defaults",
                        strategy)
        else:
            logger.debug("ParameterizedAI(%s): loaded %d strategy overrides from JSON",
                         strategy, len(loaded))

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
                  market_obj=None, rng=None, trigger_passive_fn=None, next_uid_fn=None):
        """Tüm stratejiler için parametre enjeksiyonlu buy dispatcher."""
        AI.buy_cards(player, market, max_cards, next_uid_fn, market_obj, rng,
                     trigger_passive_fn, ai_instance=self)

    def place_cards(self, player: Player, rng=None,
                    power_center_thresh: float = 45.0,
                    combo_center_weight: float = 1.5):
        """Yerleştirme: tempo parametreleri self.p'den okunur."""
        # Tempo'nun place parametrelerini self.p'den al
        pct = self.get_param("tempo", "power_center_thresh", power_center_thresh)
        ccw = self.get_param("tempo", "combo_center_weight", combo_center_weight)
        AI.place_cards(player, rng, power_center_thresh=pct, combo_center_weight=ccw)
