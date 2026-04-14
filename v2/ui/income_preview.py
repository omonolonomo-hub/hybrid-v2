"""
IncomePreview — Shop sahnesi gelir önizlemesi.

GDD §13.1 formülü:
  base        = 3
  interest    = min(floor(gold / 10), 5)   [economist için multiplier uygulanır]
  streak      = floor(win_streak / 3)       [yalnızca pozitif seriler]
  bailout     = +1 (HP < 75)  veya  +3 (HP < 45)
  total       = base + interest + streak + bailout

Görsel tasarım: SynergyHud score kutusuna paralel — 2 satırlı mini panel.
  Satır 1: "NEXT INCOME" etiketi  ·  sağda  "+{total}G"  (bold, altın)
  Satır 2: Base · +Int · +Streak · +Bail  (mono, renkli)
Arka plan: tam opak koyu navy, ince cyan kenarlık.
"""
from __future__ import annotations
import pygame
from v2.constants import Layout, Colors
from v2.ui import font_cache


# ── Renk paleti ────────────────────────────────────────────────────────────
_C_TITLE    = (100, 140, 220)        # panel başlık mavisi (SynergyHud ile aynı)
_C_BASE     = (180, 190, 215)        # sabit gelir — nötr beyaz-mavi
_C_INTEREST = (70,  210, 130)        # faiz — yeşil (kâr)
_C_STREAK   = (255, 200,  50)        # seri bonusu — altın
_C_BAILOUT  = (230, 120,  60)        # kurtarma — turuncu (HP tehlikesi)
_C_SEP      = (70,   80, 110)        # ayraç " · "
_C_ARROW    = (90,  100, 135)        # "→"
_C_TOTAL    = Colors.GOLD_TEXT       # toplam — parlak altın
_C_ZERO     = (70,   80, 110)        # sıfır değerler — soluk


class IncomePreview:
    # Panel boyutu
    _W = 440
    _H = 44

    def __init__(self):
        self.rect = pygame.Rect(
            Layout.CENTER_ORIGIN_X + 16,
            Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 10,
            self._W,
            self._H,
        )
        self._bg: pygame.Surface | None = None   # geç oluştur (pygame.init sonrası)

    # ── Arka plan yüzeyi ──────────────────────────────────────────────────

    def _get_bg(self) -> pygame.Surface:
        if self._bg is not None:
            return self._bg
        from v2.ui.ui_utils import UIUtils
        self._bg = UIUtils.create_gradient_panel(
            self._W, self._H,
            color_top    = (28, 34, 52, 255),
            color_bottom = (16, 20, 36, 255),
            border_radius = 6,
            border_color  = (55, 90, 150, 220),
        )
        # Üst ince neon çizgi (SynergyHud stili)
        pygame.draw.line(self._bg, (55, 90, 150, 140), (10, 1), (self._W - 10, 1), 1)
        return self._bg

    # ── Formül hesabı ─────────────────────────────────────────────────────

    @staticmethod
    def _compute(gold: int, hp: int, win_streak: int,
                 interest_multiplier: float = 1.0) -> dict:
        base    = 3
        raw_int = min(5, gold // 10)
        if interest_multiplier > 1.0:
            interest = min(8, int(raw_int * interest_multiplier) + 1)
        else:
            interest = raw_int
        streak  = max(0, win_streak) // 3
        bailout = (3 if hp < 45 else 1 if hp < 75 else 0)
        total   = base + interest + streak + bailout
        return {"base": base, "interest": interest,
                "streak": streak, "bailout": bailout, "total": total}

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, pid: int = 0) -> None:
        # Veri çek
        try:
            from v2.core.game_state import GameState
            gs         = GameState.get()
            gold       = gs.get_gold(pid)
            hp         = gs.get_hp(pid)
            streak     = gs.get_win_streak(pid)
            multiplier = gs.get_interest_multiplier(pid)
        except Exception:
            gold, hp, streak, multiplier = 10, 150, 0, 1.0

        t = self._compute(gold, hp, streak, multiplier)

        rx, ry = self.rect.x, self.rect.y

        # 1. Panel zemini
        surface.blit(self._get_bg(), (rx, ry))

        # 2. Satır 1 — başlık (sol) + toplam (sağ)
        fnt_bold  = font_cache.bold(10)
        fnt_total = font_cache.bold(14)

        # Sol: "NEXT INCOME"
        title_surf = fnt_bold.render("NEXT INCOME", True, _C_TITLE)
        surface.blit(title_surf, (rx + 10, ry + 6))

        # Sağ: "+{total}G"
        total_txt   = f"+{t['total']}G"
        total_surf  = fnt_total.render(total_txt, True, _C_TOTAL)
        surface.blit(total_surf, (rx + self._W - total_surf.get_width() - 10, ry + 4))

        # İnce ayraç çizgisi (başlık altı)
        sep_y = ry + 22
        pygame.draw.line(surface, (42, 58, 92), (rx + 8, sep_y), (rx + self._W - 8, sep_y), 1)

        # 3. Satır 2 — renkli formül parçaları
        fnt_mono = font_cache.mono(10)

        def _col(val: int, color: tuple) -> tuple:
            """Sıfır değerler için soluk renk döndür."""
            return color if val > 0 else _C_ZERO

        parts = [
            (f"Base {t['base']}",     _C_BASE),
            ("  ·  ",                  _C_SEP),
            (f"+Int {t['interest']}",  _col(t['interest'], _C_INTEREST)),
            ("  ·  ",                  _C_SEP),
            (f"+Streak {t['streak']}", _col(t['streak'],   _C_STREAK)),
            ("  ·  ",                  _C_SEP),
            (f"+Bail {t['bailout']}",  _col(t['bailout'],  _C_BAILOUT)),
        ]

        x = rx + 10
        y = ry + 26
        for text, color in parts:
            try:
                s = fnt_mono.render(text, True, color)
                surface.blit(s, (x, y))
                x += s.get_width()
            except pygame.error:
                pass
