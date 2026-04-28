"""
v2/ui/ui_feedback_manager.py
============================
UIFeedbackManager — Floating text feedback'lerini merkezi olarak yönetir.

ShopScene'den taşınan sorumluluklar:
  - FloatingTextManager yaşam döngüsü (update / render)
  - Kart yerleştirme float'u  (_spawn_placement_float → spawn_placement)
  - Milestone float'u         (_on_milestone_reached  → on_milestone)

ShopScene'de kalan:
  - Sinyal bağlantıları (connect / disconnect)
  - Reroll / buy inline spawn çağrıları (koordinat bilgisi orada)
  - Doğrudan ft_manager.spawn() çağrıları (reroll, buy)
"""
from __future__ import annotations

from collections import defaultdict

import pygame

from v2.constants import Colors, GridMath, STAT_TO_GROUP
from v2.core.exceptions import AutochessException
from v2.ui.widgets import FloatingTextManager


class UIFeedbackManager:
    """Floating text feedback'lerini yönetir.

    ShopScene bu sınıfı oluşturur ve şu üç görevi delege eder:
      1. update(dt_ms)  — her frame
      2. render(surface) — her frame
      3. spawn_placement(coord, card_name, synergy_total, cam_state)
      4. on_milestone(cam_state, **kwargs)

    Reroll / buy gibi koordinat bilgisi ShopScene'de olan spawn'lar
    doğrudan ``self._feedback.ft_manager.spawn(...)`` ile yapılabilir
    ya da ShopScene'de kalabilir; bu sınıf onlara karışmaz.
    """

    def __init__(self) -> None:
        self.ft_manager = FloatingTextManager()
        self._prev_synergy: int = 0

    # ── Yaşam döngüsü ────────────────────────────────────────────────────

    def update(self, dt_ms: float) -> None:
        self.ft_manager.update(dt_ms)

    def render(self, surface: pygame.Surface) -> None:
        self.ft_manager.render(surface)

    # ── Kart yerleştirme ─────────────────────────────────────────────────

    def spawn_placement(
        self,
        coord: tuple[int, int],
        card_name: str,
        synergy_total: int,
        cam_state,
    ) -> None:
        """Kart yerleştirildiğinde sinerji delta'sını göster.

        Args:
            coord:         Axial hex koordinatı (q, r).
            card_name:     Yerleştirilen kartın adı.
            synergy_total: Yerleştirme sonrası güncel sinerji toplamı.
            cam_state:     CameraState — axial_to_pixel için gerekli.
        """
        from v2.core.engine_adapter import EngineAdapter
        from v2.ui.hex_math import axial_to_pixel

        # Kartın baskın grubunu bul
        dom_grp = "EXISTENCE"
        try:
            card_data = EngineAdapter.get_card_info(card_name)
            if card_data:
                counts: dict[str, int] = defaultdict(int)
                for stat, value in card_data.stats.items():
                    if value > 0:
                        group = STAT_TO_GROUP.get(stat)
                        if group:
                            counts[group] += 1
                if counts:
                    dom_grp = max(counts, key=counts.get)
        except AutochessException:
            pass

        color = {
            "MIND":       Colors.MIND,
            "CONNECTION": Colors.CONNECTION,
            "EXISTENCE":  Colors.EXISTENCE,
        }.get(dom_grp, Colors.GOLD_TEXT)

        delta = synergy_total - self._prev_synergy
        self._prev_synergy = synergy_total
        text = f"+{delta} SYN" if delta > 0 else "PLACED"

        cx, cy = axial_to_pixel(*coord, cam_state)
        self.ft_manager.spawn(text, cx, cy - 50, color, font_size=14, coord_key=coord)

    # ── Milestone ────────────────────────────────────────────────────────

    def on_milestone(self, cam_state, **kwargs) -> None:
        """Milestone sinyali geldiğinde uygun floating text'i spawn et.

        Args:
            cam_state: CameraController.get_state() sonucu.
            **kwargs:  Sinyal tarafından iletilen milestone verisi.
        """
        milestone_type = kwargs.get("milestone_type")

        if milestone_type == "tier":
            tier_short = kwargs.get("tier_short", kwargs.get("group"))
            bonus      = kwargs.get("bonus")
            tier_color = kwargs.get("tier_color", "GOLD")

            color = {
                "MIND":       Colors.MIND,
                "CONNECTION": Colors.CONNECTION,
                "EXISTENCE":  Colors.EXISTENCE,
            }.get(tier_color, Colors.GOLD_TEXT)

            text = f"{tier_short} +{bonus}pts UP"
            x = GridMath.ORIGIN_X + cam_state.offset_x
            y = GridMath.ORIGIN_Y + cam_state.offset_y - 120
            self.ft_manager.spawn(text, x, y, color, font_size=13, coord_key=("board_center",))

        elif milestone_type == "copy":
            trigger = kwargs.get("trigger")
            card    = kwargs.get("card")

            title = "3-COPY POWER UP" if trigger == "copy_3" else "2-COPY POWER UP"
            x = GridMath.ORIGIN_X + cam_state.offset_x
            y = GridMath.ORIGIN_Y + cam_state.offset_y - 90
            self.ft_manager.spawn(
                title, x, y, Colors.PLATINUM,
                font_size=15, coord_key=("copy_strengthen", card),
            )
