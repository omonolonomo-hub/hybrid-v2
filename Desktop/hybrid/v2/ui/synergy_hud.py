from __future__ import annotations

import math
import pygame

from v2.constants import Layout, Screen
from v2.core.public_state import EffectViewState, PassiveFeedEntryViewState, SynergyGroupViewState, SynergyViewState
from v2.ui import font_cache
from v2.ui.ui_utils import UIUtils


def _empty_view_model() -> SynergyViewState:
    return SynergyViewState(groups=[], total=0, passive_feed=[], active_effects=[])


class SynergyHud:
    _C_TITLE = (100, 140, 220)
    _C_WHITE = (220, 224, 240)
    _C_DIM = (80, 85, 110)
    _C_PANEL = (10, 12, 20, 235)
    _C_BORDER = (42, 58, 92, 180)
    _C_OFF = (42, 48, 72)

    # Gradient panel renkleri
    _C_PANEL_TOP = (36, 42, 62, 255)
    _C_PANEL_BOT = (16, 22, 42, 255)
    _C_BORDER    = (42, 58, 92, 180)

    def __init__(self):
        self.rect = pygame.Rect(
            0,
            Layout.SYNERGY_HUD_Y,
            Layout.SIDEBAR_LEFT_W,
            Layout.SYNERGY_HUD_H,
        )

        pad = 10
        inner_w = self.rect.w - pad * 2
        x0 = self.rect.x + pad
        y0 = self.rect.y
        usable_h = self.rect.h - 16 - 20  # 16px top/bottom margin, 20px gaps
        phi = 1.618
        
        # 3-Way Golden Ratio Progression:
        # A + B + C = usable_h
        # A = B * phi, B = C * phi => A = C * phi^2
        # We assign A (largest) to Groups, B to Passives, C to Effects
        c = usable_h / (phi**2 + phi + 1)
        b = c * phi
        a = b * phi
        
        groups_h = int(a)
        feed_h = int(b)
        effects_h = usable_h - groups_h - feed_h
        
        self.groups_rect = pygame.Rect(x0, y0 + 8, inner_w, groups_h)
        self.effects_rect = pygame.Rect(x0, self.groups_rect.bottom + 10, inner_w, effects_h)
        self.passive_feed_rect = pygame.Rect(x0, self.effects_rect.bottom + 10, inner_w, feed_h)

        # Önceden hazırlanan gradient yüzeyleri (her frame yeniden çizilmez)
        self._grp_surf  = UIUtils.create_gradient_panel(
            inner_w, self.groups_rect.h, self._C_PANEL_TOP, self._C_PANEL_BOT,
            border_radius=8, border_color=self._C_BORDER)
        self._eff_surf  = UIUtils.create_gradient_panel(
            inner_w, self.effects_rect.h, self._C_PANEL_TOP, self._C_PANEL_BOT,
            border_radius=8, border_color=self._C_BORDER)
        self._feed_surf = UIUtils.create_gradient_panel(
            inner_w, self.passive_feed_rect.h, self._C_PANEL_TOP, self._C_PANEL_BOT,
            border_radius=8, border_color=self._C_BORDER)

        self._view_model = _empty_view_model()
        self._display_counts: dict[str, float] = {}
        self._flash_timers: dict[str, float] = {}
        self._t: float = 0.0   # animasyon zamanı (saniye)

    @property
    def view_model(self) -> SynergyViewState:
        return self._view_model

    def set_view_model(self, view_model: SynergyViewState | None) -> None:
        self._view_model = view_model or _empty_view_model()

    def update(self, dt_ms: float, view_model: SynergyViewState | None = None) -> None:
        if view_model is not None:
            self.set_view_model(view_model)

        self._t += dt_ms / 1000.0

        for group in self._view_model.groups:
            current = self._display_counts.get(group.key, 0.0)
            target = float(group.count)
            self._display_counts[group.key] = current + (target - current) * 0.2
            if int(round(current)) < group.count:
                self._flash_timers[group.key] = 300.0

        for key in list(self._flash_timers):
            self._flash_timers[key] -= dt_ms
            if self._flash_timers[key] <= 0:
                del self._flash_timers[key]

    def render(self, surface: pygame.Surface) -> None:
        self._render_groups(surface)
        self._render_effects(surface)
        self._render_passive_feed(surface)

    def _draw_panel(self, surface: pygame.Surface, cached_surf: pygame.Surface, rect: pygame.Rect, title: str) -> None:
        # Gradient yüzey önce blit edilir
        surface.blit(cached_surf, rect.topleft)
        font_cache.render_text(
            surface,
            title,
            font_cache.bold(10),
            self._C_TITLE,
            pygame.Rect(rect.x, rect.y + 4, rect.w, 14),
            align="center",
        )

    def _render_groups(self, surface: pygame.Surface) -> None:
        self._draw_panel(surface, self._grp_surf, self.groups_rect, "SYNERGY BOARD")
        header_h = 18
        available_h = self.groups_rect.h - header_h - 4
        row_h = available_h // 3
        row_y = self.groups_rect.y + header_h + 2
        
        for group in self._view_model.groups:
            active = group.count >= 2
            flash  = self._flash_timers.get(group.key, 0) > 0

            # Altın oran dengesi için uyumlu boşluk
            row_rect = pygame.Rect(self.groups_rect.x + 6, row_y + 4, self.groups_rect.w - 12, row_h - 8)

            # Arka plan
            if active:
                bg_col = tuple(c * (50 if flash else 28) // 255 for c in group.color)
            else:
                bg_col = (22, 26, 42)
            pygame.draw.rect(surface, bg_col, row_rect, border_radius=5)
            if active:
                dim_c = tuple(max(0, c - 80) for c in group.color)
                pygame.draw.rect(surface, dim_c, row_rect, width=1, border_radius=5)

            # Orantılı Yerleşim Değerleri (Altın Oran ve Yüzdesel Dağılım)
            pad_x    = int(row_rect.w * 0.04)
            top_y    = row_rect.y + int(row_rect.h * 0.15)
            next_y   = row_rect.y + int(row_rect.h * 0.40)
            pip_y    = row_rect.y + int(row_rect.h * 0.55)

            # Grup adı (Sol Üst)
            font_cache.render_text(
                surface, group.label, font_cache.bold(11),
                group.color if active else self._C_DIM,
                pygame.Rect(row_rect.x + pad_x, top_y, int(row_rect.w * 0.5), 14),
            )
            # Bonus (Sağ Üst)
            pts_txt = f"+{group.bonus}" if group.bonus > 0 else "–"
            font_cache.render_text(
                surface, pts_txt, font_cache.bold(13),
                group.color if group.bonus > 0 else self._C_DIM,
                pygame.Rect(row_rect.x, top_y - 1, row_rect.w - pad_x, 15),
                align="right",
            )
            
            # Alt metin (Next Tier) -> Net puanın tam altında sağa dayalı
            next_tier = "maxed"
            if group.next_tier_count is not None and group.next_tier_bonus is not None:
                next_tier = f"next {group.next_tier_count} → +{group.next_tier_bonus}"
            font_cache.render_text(
                surface, next_tier, font_cache.mono(8),
                (160, 165, 195) if active else self._C_DIM,
                pygame.Rect(row_rect.x, next_y, row_rect.w - pad_x, 12),
                align="right",
            )

            # Pip bar — Altıgen (Hexagonal) Pipler
            pip_r   = max(6, int(row_rect.h * 0.16)) # Boyutları daha büyük
            pip_x0  = row_rect.x + pad_x
            pip_gap = int((row_rect.w * 0.55) / 5)  # Genişliğin %55'ine yay

            filled_count = int(round(self._display_counts.get(group.key, 0.0)))
            for idx in range(6):
                pip_cx = pip_x0 + idx * pip_gap + pip_r
                pip_cy = pip_y + pip_r
                
                # Altıgen noktalarını hesapla
                hex_points = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    px = pip_cx + pip_r * math.cos(angle)
                    py = pip_cy + pip_r * math.sin(angle)
                    hex_points.append((px, py))
                    
                if idx < filled_count:
                    pulse = (0.8 + 0.2 * math.sin(self._t * 6)) if flash else 1.0
                    rc = tuple(min(255, int(c * pulse)) for c in group.color)
                    pygame.draw.polygon(surface, rc, hex_points)
                    
                    # İç highlight (rim light) için daha küçük altıgen
                    inner_r = max(2, pip_r - 2)
                    inner_points = []
                    for i in range(6):
                        angle = math.radians(60 * i - 30)
                        px = pip_cx + inner_r * math.cos(angle)
                        py = pip_cy + inner_r * math.sin(angle)
                        inner_points.append((px, py))
                    pygame.draw.polygon(surface, (255, 255, 255, 180), inner_points, 1)
                else:
                    pygame.draw.polygon(surface, self._C_OFF, hex_points)
                    pygame.draw.polygon(surface, (60, 65, 95), hex_points, 1)
            row_y += row_h

    def _render_effects(self, surface: pygame.Surface) -> None:
        self._draw_panel(surface, self._eff_surf, self.effects_rect, "TOTAL / EFFECTS")
        font_cache.render_text(
            surface,
            f"TOTAL {self._view_model.total}",
            font_cache.bold(16),
            self._C_WHITE,
            pygame.Rect(self.effects_rect.x, self.effects_rect.y + 18, self.effects_rect.w, 18),
            align="center",
        )
        row_y = self.effects_rect.y + 40
        effects = self._view_model.active_effects[:3]
        if not effects:
            font_cache.render_text(
                surface,
                "No active effects",
                font_cache.mono(8),
                self._C_DIM,
                pygame.Rect(self.effects_rect.x, row_y + 10, self.effects_rect.w, 12),
                align="center",
            )
            return
        for effect in effects:
            self._render_effect_row(surface, effect, row_y)
            row_y += 14

    def _render_effect_row(self, surface: pygame.Surface, effect: EffectViewState, y: int) -> None:
        color = effect.color
        font_cache.render_text(
            surface,
            effect.label,
            font_cache.mono(8),
            color,
            pygame.Rect(self.effects_rect.x + 10, y, self.effects_rect.w - 20, 12),
        )
        if effect.value:
            font_cache.render_text(
                surface,
                effect.value,
                font_cache.bold(9),
                self._C_WHITE,
                pygame.Rect(self.effects_rect.x + 10, y, self.effects_rect.w - 20, 12),
                align="right",
            )

    def _render_passive_feed(self, surface: pygame.Surface) -> None:
        self._draw_panel(surface, self._feed_surf, self.passive_feed_rect, "PASSIVES")
        if not self._view_model.passive_feed:
            font_cache.render_text(
                surface,
                "No passive feed",
                font_cache.mono(8),
                self._C_DIM,
                pygame.Rect(self.passive_feed_rect.x, self.passive_feed_rect.y + 28, self.passive_feed_rect.w, 12),
                align="center",
            )
            return

        row_y = self.passive_feed_rect.y + 24
        row_h = 20
        max_rows = max(1, (self.passive_feed_rect.h - 28) // row_h)
        for entry in self._view_model.passive_feed[-max_rows:]:
            self._render_passive_row(surface, entry, row_y)
            row_y += row_h

    def _render_passive_row(self, surface: pygame.Surface, entry: PassiveFeedEntryViewState, y: int) -> None:
        color = entry.color
        pygame.draw.rect(
            surface,
            (*color, 28),
            pygame.Rect(self.passive_feed_rect.x + 6, y, self.passive_feed_rect.w - 12, 16),
            border_radius=4,
        )
        font_cache.render_text(
            surface,
            f"{entry.trigger.upper()}",
            font_cache.mono(7),
            color,
            pygame.Rect(self.passive_feed_rect.x + 10, y + 2, 70, 12),
        )
        font_cache.render_text(
            surface,
            entry.card[:18],
            font_cache.mono(8),
            self._C_WHITE,
            pygame.Rect(self.passive_feed_rect.x + 74, y + 1, self.passive_feed_rect.w - 150, 12),
        )
        value = entry.delta if entry.delta != 0 else entry.res
        if value:
            label = f"+{value}" if value > 0 else str(value)
            font_cache.render_text(
                surface,
                label,
                font_cache.bold(9),
                color,
                pygame.Rect(self.passive_feed_rect.x + 10, y + 1, self.passive_feed_rect.w - 20, 12),
                align="right",
            )
