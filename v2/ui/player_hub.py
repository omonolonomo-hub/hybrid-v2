import pygame
import math
from v2.constants import Layout, Colors
from v2.ui import font_cache


class PlayerHub:
    """Sol panel oyuncu durum merkezi (PLAYER_HUB_H = 150 px).

    Layout (tüm y-offset'ler inner_rect.y'ye göredir):
      Row 1  y_off= 8, h=15  — PLAYER HUB (sol) | Tur: N (sağ)
      Sep    y_off=26         — ince ayraç
      Row 2  y_off=30, h=20  — HP bar (segmentli, 5 HP/blok)
      Row 3  y_off=57, h=28  — [Gold %45] [Streak %55]
      Sep    y_off=90         — ince ayraç
      Row 4  y_off=94, h=20  — [★ Pts %50] [Board N/37 %50]
      Row 5  y_off=118, h=14 — → +Ng gelecek tur (sağa hizalı)
    """

    _MAX_HP: int      = 150
    _BOARD_TOTAL: int = 37

    # ── Renk sabitleri ────────────────────────────────────────────────────
    _C_TITLE  = (100, 140, 220)
    _C_TURN   = (140, 160, 200)
    _C_SEP    = ( 50,  70, 110)
    _C_HP_TXT = (210, 225, 255)
    _C_BOX_BG = ( 20,  26,  40)
    _C_BOX_BD = ( 42,  58,  92)
    _C_PTS    = (200, 220, 255)
    _C_INC    = (140, 180, 100)

    def __init__(self) -> None:
        # ── Dış rect (sabit) ──────────────────────────────────────────
        self.rect = pygame.Rect(0, 0, Layout.SIDEBAR_LEFT_W, Layout.PLAYER_HUB_H)

        # ── İç panel rect ─────────────────────────────────────────────
        self.inner_rect = pygame.Rect(10, 8, Layout.SIDEBAR_LEFT_W - 20, 134)
        ix = self.inner_rect.x
        iy = self.inner_rect.y
        iw = self.inner_rect.w

        # Row 2 — HP bar
        self.hp_rect = pygame.Rect(ix, iy + 30, iw, 20)

        # Row 3 — Gold %45 | Streak %55
        gold_w   = int(iw * 0.45)
        streak_w = iw - gold_w - 4
        self.gold_rect   = pygame.Rect(ix,              iy + 57, gold_w,   28)
        self.streak_rect = pygame.Rect(ix + gold_w + 4, iy + 57, streak_w, 28)

        # Row 4 — Pts %50 | Board %50
        pts_w   = iw // 2 - 2
        board_w = iw - pts_w - 4
        self.pts_rect   = pygame.Rect(ix,             iy + 94, pts_w,   20)
        self.board_rect = pygame.Rect(ix + pts_w + 4, iy + 94, board_w, 20)

        # Row 5 — income preview
        self.income_rect = pygame.Rect(ix, iy + 118, iw, 14)

        # ── Canlı değerler (sync() ile güncellenir) ───────────────────
        self._hp: int         = self._MAX_HP
        self._gold: int       = 10
        self._streak: int     = 0
        self._total_pts: int  = 0
        self._turn: int       = 1
        self._board_used: int = 0
        self._next_gold: int  = 3

        # ── Gradient arka plan ────────────────────────────────────────
        from v2.ui.ui_utils import UIUtils
        self.bg_surf = UIUtils.create_gradient_panel(
            self.inner_rect.w, self.inner_rect.h,
            (32, 38, 58, 255), (16, 20, 36, 255),
            border_radius=8, border_color=(50, 70, 110, 200),
        )

    # ── Genel API ─────────────────────────────────────────────────────────

    def sync(self, player_index: int = 0) -> None:
        """GameState'ten güncel değerleri çek."""
        try:
            from v2.core.game_state import GameState
            gs = GameState.get()
            self._hp         = gs.get_hp(player_index)
            self._gold       = gs.get_gold(player_index)
            self._streak     = gs.get_win_streak(player_index)
            self._total_pts  = gs.get_total_pts(player_index)
            self._turn       = gs.get_turn()
            self._board_used = len(gs.get_board_cards())
        except Exception:
            pass

        try:
            from v2.core.game_state import GameState
            from v2.ui.income_preview import IncomePreview
            gs         = GameState.get()
            multiplier = gs.get_interest_multiplier(player_index)
            t          = IncomePreview._compute(
                self._gold, self._hp, self._streak, multiplier
            )
            self._next_gold = t["total"]
        except Exception:
            pass

    def render(self, surface: pygame.Surface) -> None:
        ix = self.inner_rect.x
        iy = self.inner_rect.y
        iw = self.inner_rect.w

        # ── 0. Arka plan ──────────────────────────────────────────────
        surface.blit(self.bg_surf, (ix, iy))

        # ── Row 1: PLAYER HUB (sol bold 11) | Tur: N (sağ mono 10) ──
        row1 = pygame.Rect(ix + 4, iy + 8, iw - 8, 15)
        font_cache.render_text(
            surface, "PLAYER HUB", font_cache.bold(11),
            self._C_TITLE, row1, align="left", v_align="center",
        )
        font_cache.render_text(
            surface, f"Tur: {self._turn}", font_cache.mono(10),
            self._C_TURN, row1, align="right", v_align="center",
        )

        # ── Ayraç — y_off=26 ─────────────────────────────────────────
        pygame.draw.line(
            surface, self._C_SEP,
            (ix + 6, iy + 26), (ix + iw - 6, iy + 26), 1,
        )

        # ── Row 2: HP bar — y_off=30, h=20 ───────────────────────────
        self._draw_hp_bar(surface)

        # ── Row 3: Gold | Streak — y_off=57, h=28 ────────────────────
        self._draw_gold_box(surface)
        self._draw_streak_box(surface)

        # ── Ayraç — y_off=90 ─────────────────────────────────────────
        pygame.draw.line(
            surface, self._C_SEP,
            (ix + 6, iy + 90), (ix + iw - 6, iy + 90), 1,
        )

        # ── Row 4: Pts | Board — y_off=94, h=20 ──────────────────────
        self._draw_pts_box(surface)
        self._draw_board_box(surface)

        # ── Row 5: income preview sağa hizalı — y_off=118, h=14 ──────
        font_cache.render_text(
            surface, f"→ +{self._next_gold}G gelecek tur",
            font_cache.mono(9), self._C_INC,
            self.income_rect, align="right", v_align="center",
        )

    # ── Özel çizim yardımcıları ───────────────────────────────────────────

    def _draw_hp_bar(self, surface: pygame.Surface) -> None:
        bar    = self.hp_rect
        hp     = self._hp
        max_hp = self._MAX_HP

        # Zemin
        pygame.draw.rect(surface, (22, 28, 42), bar, border_radius=3)

        # Dolu kısım
        hp_ratio = max(0.0, min(1.0, hp / max(1, max_hp)))
        fill_w   = int(bar.w * hp_ratio)
        if fill_w > 0:
            hp_color = Colors.HP_FULL if hp_ratio > 0.4 else Colors.HP_LOW
            pygame.draw.rect(
                surface, hp_color,
                pygame.Rect(bar.x, bar.y, fill_w, bar.h),
                border_radius=3,
            )

        # Segment çizgileri — 5 HP/blok → 30 segment
        n_segs = max_hp // 5
        seg_w  = bar.w / max(1, n_segs)
        for i in range(1, n_segs):
            sx = bar.x + int(i * seg_w)
            pygame.draw.line(
                surface, (22, 28, 42),
                (sx, bar.y + 2), (sx, bar.bottom - 3), 1,
            )

        # Kenarlık
        pygame.draw.rect(surface, self._C_BOX_BD, bar, width=1, border_radius=3)

        # HP metni — bar üstüne ortalanmış: "N / 150"
        font_cache.render_text(
            surface, f"{hp} / {max_hp}",
            font_cache.bold(11), self._C_HP_TXT,
            bar, align="center", v_align="center", shadow=True,
        )

    def _draw_gold_box(self, surface: pygame.Surface) -> None:
        gr = self.gold_rect
        # Zemin: (28, 24, 10)  |  Kenar: (140, 110, 20)  |  Metin: GOLD_TEXT
        pygame.draw.rect(surface, (28, 24, 10), gr, border_radius=6)
        pygame.draw.rect(surface, (140, 110, 20), gr, width=1, border_radius=6)
        font_cache.render_text(
            surface, f"◈ {self._gold}G", font_cache.bold(12),
            Colors.GOLD_TEXT, gr,
            align="center", v_align="center", shadow=True,
        )

    def _draw_streak_box(self, surface: pygame.Surface) -> None:
        streak = self._streak
        sr     = self.streak_rect

        if streak >= 3:
            # 🔥 +Nw — turuncu, ateş parıltısı alfa arka planı
            label  = f"🔥 +{streak}w"
            color  = (255, 140, 30)
            tmp = pygame.Surface((sr.w, sr.h), pygame.SRCALPHA)
            pygame.draw.rect(tmp, (60, 30, 5, 200), tmp.get_rect(), border_radius=6)
            surface.blit(tmp, (sr.x, sr.y))
            pygame.draw.rect(surface, (140, 80, 10), sr, width=1, border_radius=6)

        elif streak == 2:
            label = "▲ +2w"
            color = (220, 160, 60)
            pygame.draw.rect(surface, (24, 26, 14), sr, border_radius=6)
            pygame.draw.rect(surface, (80, 70, 20), sr, width=1, border_radius=6)

        elif streak == 1:
            label = "▲ +1w"
            color = (80, 200, 100)
            pygame.draw.rect(surface, (14, 26, 18), sr, border_radius=6)
            pygame.draw.rect(surface, (30, 80, 50), sr, width=1, border_radius=6)

        elif streak == 0:
            label = "— nötr —"
            color = (90, 100, 120)
            pygame.draw.rect(surface, (16, 22, 34), sr, border_radius=6)
            pygame.draw.rect(surface, self._C_BOX_BD, sr, width=1, border_radius=6)

        else:  # kayıp serisi (negatif)
            nl    = abs(streak)
            arrow = "▼▼" if streak <= -2 else "▼"
            label = f"{arrow} -{nl}l"
            color = (200, 70, 70)
            pygame.draw.rect(surface, (28, 12, 12), sr, border_radius=6)
            pygame.draw.rect(surface, (90, 30, 30), sr, width=1, border_radius=6)

        font_cache.render_text(
            surface, label, font_cache.bold(11),
            color, sr, align="center", v_align="center",
        )

    def _draw_pts_box(self, surface: pygame.Surface) -> None:
        pr = self.pts_rect
        pygame.draw.rect(surface, self._C_BOX_BG, pr, border_radius=4)
        pygame.draw.rect(surface, self._C_BOX_BD, pr, width=1, border_radius=4)
        font_cache.render_text(
            surface, f"★ Pts: {self._total_pts}", font_cache.bold(10),
            self._C_PTS, pr, align="center", v_align="center",
        )

    def _draw_board_box(self, surface: pygame.Surface) -> None:
        br          = self.board_rect
        board_ratio = max(0.0, min(1.0, self._board_used / self._BOARD_TOTAL))

        # Kutu zemini
        pygame.draw.rect(surface, self._C_BOX_BG, br, border_radius=4)

        # Kapasite mini barı (h=6) — kutunun alt kısmı
        bar_h = 6
        pad   = 2
        cap_bar = pygame.Rect(
            br.x  + pad,
            br.bottom - bar_h - pad,
            br.w  - pad * 2,
            bar_h,
        )
        pygame.draw.rect(surface, (12, 16, 28), cap_bar, border_radius=2)

        fill_w = int(cap_bar.w * board_ratio)
        if fill_w > 0:
            if board_ratio > 0.6:
                bar_color = Colors.HP_FULL
            elif board_ratio > 0.3:
                bar_color = Colors.GOLD_TEXT
            else:
                bar_color = Colors.HP_LOW
            pygame.draw.rect(
                surface, bar_color,
                pygame.Rect(cap_bar.x, cap_bar.y, fill_w, bar_h),
                border_radius=2,
            )

        # Kutu kenarlığı
        pygame.draw.rect(surface, self._C_BOX_BD, br, width=1, border_radius=4)

        # "Board: N/37" metni — mini barın üstünde
        txt_rect = pygame.Rect(br.x, br.y, br.w, br.h - bar_h - pad)
        font_cache.render_text(
            surface, f"Board: {self._board_used}/37",
            font_cache.bold(10), self._C_PTS,
            txt_rect, align="center", v_align="center",
        )
