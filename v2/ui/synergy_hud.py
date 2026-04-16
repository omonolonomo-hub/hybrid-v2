"""
SynergyHud — Sol sidebar grup synergy + son savaş + pasif akış.

GDD §8 formülü:
  group_bonus(n) = min(18, floor(3 * (n-1)^1.25))  n>=2, n=1 → 0
  diversity_bonus = min(5, kaç farklı grup aktif)
  total = Σ group_bonus + diversity_bonus

Layout (y=SYNERGY_HUD_Y=150 → y=1080):
  ┌─ SYNERGY BOARD ─────────────────┐  h=204  (3 grup × 62px + 18px başlık)
  ├─ SKOR KUTUSU ───────────────────┤  h=118  (KILL/COMBO/SYN satır × 3 + TOPLAM)
  ├─ SON SAVAŞ ─────────────────────┤  h=68   (kazandı/kaybetti/berabere + hasar)
  ├─ PASİF AKIŞI ───────────────────┤  h=kalan (son pasif olaylar)
  └─────────────────────────────────┘
"""
from __future__ import annotations
import math
import pygame
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache

_TIER_THRESHOLDS = [2, 3, 4, 5, 6]
_TIER_BONUSES    = [3, 7, 11, 16, 18]

def _group_bonus(n: int) -> int:
    if n < 2:
        return 0
    return min(18, int(3 * (n - 1) ** 1.25))

def _next_tier(n: int):
    for thresh, pts in zip(_TIER_THRESHOLDS, _TIER_BONUSES):
        if n < thresh:
            return thresh, pts
    return None

# ── Pasif trigger renk paleti ──────────────────────────────────────────
_TRIGGER_COLORS: dict[str, tuple] = {
    "copy_2":         (255, 200,  55),
    "copy_3":         (255, 160,  20),
    "copy_strengthen":(255, 200,  55),
    "income":         (70,  210, 130),
    "market_refresh": (70,  200, 120),
    "card_buy":       (100, 180, 255),
    "combat_win":     (100, 220, 120),
    "combat_lose":    (220,  80,  80),
    "card_killed":    (255, 120,  40),
    "pre_combat":     (160, 100, 255),
}
_TRIGGER_ICONS: dict[str, str] = {
    "copy_2":         "★",
    "copy_3":         "★★",
    "copy_strengthen":"★",
    "income":         "◈",
    "market_refresh": "◈",
    "card_buy":       "▸",
    "combat_win":     "▲",
    "combat_lose":    "▼",
    "card_killed":    "✕",
    "pre_combat":     "⬡",
}


class SynergyHud:
    _C_TITLE    = (100, 140, 220)
    _C_DIM      = (55,  60,  85)
    _C_PIP_OFF  = (42,  48,  72)
    _C_TEXT_DIM = (80,  85, 110)
    _C_WHITE    = (220, 224, 240)
    _C_GOLD     = (255, 210,  60)

    _GROUPS = [
        ("MIND",       Colors.MIND,       "MIND"),
        ("CONNECTION", Colors.CONNECTION, "CONN"),
        ("EXISTENCE",  Colors.EXISTENCE,  "EXST"),
    ]

    def __init__(self):
        self.rect = pygame.Rect(
            0, Layout.SYNERGY_HUD_Y,
            Layout.SIDEBAR_LEFT_W,
            Screen.H - Layout.SYNERGY_HUD_Y,
        )

        pad      = 10
        inner_w  = self.rect.w - pad * 2
        x0       = self.rect.x + pad
        y0       = self.rect.y

        # ── Grup kutusu ─────────────────────────────────────────────
        self.groups_rect = pygame.Rect(x0, y0 + 10, inner_w, 204)

        # ── Skor kutusu (Kill/Combo/Syn/Toplam) ─────────────────────
        self.score_rect = pygame.Rect(x0, self.groups_rect.bottom + 8, inner_w, 118)

        # ── Son savaş kutusu ─────────────────────────────────────────
        self.last_combat_rect = pygame.Rect(x0, self.score_rect.bottom + 8, inner_w, 68)

        # ── Pasif akış kutusu ────────────────────────────────────────
        feed_h = self.rect.bottom - self.last_combat_rect.bottom - 18
        self.passive_feed_rect = pygame.Rect(x0, self.last_combat_rect.bottom + 8, inner_w, feed_h)

        # Test uyumluluğu alias'ları
        self.passive_tracker_rect = self.score_rect
        self.combat_log_rect      = self.passive_feed_rect
        # log_rect alias (eski testler için)
        self.log_rect             = self.passive_feed_rect

        # ── Önbelleklenmiş yüzeyler ──────────────────────────────────
        from v2.ui.ui_utils import UIUtils
        _bdr = (42, 58, 92, 180)
        _top = (36, 42, 62, 255)
        _bot = (16, 22, 42, 255)
        def _panel(w, h):
            return UIUtils.create_gradient_panel(w, h, _top, _bot, border_radius=8, border_color=_bdr)

        self._grp_surf      = _panel(inner_w, self.groups_rect.h)
        self._score_surf    = _panel(inner_w, self.score_rect.h)
        self._combat_surf   = _panel(inner_w, self.last_combat_rect.h)
        self._feed_surf     = _panel(inner_w, self.passive_feed_rect.h)

        # ── Animasyon durumu ─────────────────────────────────────────
        self._prev_counts:  dict[str, int]   = {}
        self._flash_timers: dict[str, float] = {}

        # ── Pasif akış: gösterilen son N kayıt ───────────────────────
        self._feed_seen_count: int = 0   # passive_buff_log'dan kaç kayıt gördük

    # ── Public API ───────────────────────────────────────────────────

    def add_log(self, line: str) -> None:
        """Geriye uyumluluk stub'ı — artık pasif feed kullanılıyor."""
        pass

    def update(self, dt_ms: float) -> None:
        for k in list(self._flash_timers):
            self._flash_timers[k] -= dt_ms
            if self._flash_timers[k] <= 0:
                del self._flash_timers[k]

    # ── Synergy hesabı ───────────────────────────────────────────────

    def _compute_state(self) -> dict:
        from v2.core.game_state import GameState
        from v2.core.card_database import CardDatabase
        from v2.constants import STAT_TO_GROUP
        try:
            board = GameState.get().get_board_cards()
            db    = CardDatabase.get()
        except Exception:
            return self._empty_state()

        group_counts: dict[str, int] = {g: 0 for g, *_ in self._GROUPS}
        for item in board.values():
            card_name = item.get("name") if isinstance(item, dict) else item
            data = db.lookup(card_name)
            if not data:
                continue
            seen: set[str] = set()
            for stat_name, val in data.stats.items():
                if val > 0:
                    g = STAT_TO_GROUP.get(stat_name, "")
                    if g and g not in seen:
                        seen.add(g)
                        group_counts[g] = group_counts.get(g, 0) + 1

        group_bonus   = {g: _group_bonus(c) for g, c in group_counts.items()}
        unique_active = sum(1 for c in group_counts.values() if c > 0)
        div_bonus     = min(5, unique_active)
        total         = sum(group_bonus.values()) + div_bonus

        for g, cnt in group_counts.items():
            prev = self._prev_counts.get(g, 0)
            if cnt > prev:
                self._flash_timers[g] = 600
            self._prev_counts[g] = cnt

        # Çapraz doğrulama (debug)
        try:
            import os
            if os.environ.get("DEBUG_MODE", "").lower() == "true":
                results = GameState.get().get_last_combat_results()
                if results:
                    eng = results[-1].get("synergy_a", None)
                    if eng is not None and eng != total:
                        print(f"[SYN MISMATCH] ui={total} engine={eng}")
        except Exception:
            pass

        combo_pts = self._compute_combo_pts(board, db)

        return {
            "group_counts":  group_counts,
            "group_bonus":   group_bonus,
            "div_bonus":     div_bonus,
            "total":         total,
            "unique_active": unique_active,
            "combo_pts":     combo_pts,
        }

    # ── Canlı combo hesabı (engine find_combos() ile aynı mantık) ────

    @staticmethod
    def _compute_combo_pts(board: dict, db) -> int:
        """
        Komşu kart çiftlerinde dominant_group eşleşmesi → +1 combo/çift.
        engine_core.board.find_combos() ile birebir aynı algoritma,
        CardDatabase üzerinden UI tarafında canlı hesaplanır.
        """
        from v2.constants import STAT_TO_GROUP, ENGINE_HEX_DIRS
        from collections import defaultdict

        if len(board) < 2:
            return 0

        # Her koordinat için dominant_group hesapla
        dominant: dict = {}
        for coord, item in board.items():
            card_name = item.get("name") if isinstance(item, dict) else item
            data = db.lookup(card_name)
            if not data:
                continue
            cnt: dict = defaultdict(int)
            for stat_name, val in data.stats.items():
                if val > 0:
                    g = STAT_TO_GROUP.get(stat_name)
                    if g:
                        cnt[g] += 1
            dominant[coord] = max(cnt, key=cnt.get) if cnt else "EXISTENCE"

        # Komşu çiftlerini tara — her çift bir kez sayılır
        combo_pts = 0
        counted: set = set()
        for coord, grp in dominant.items():
            q, r = coord
            for dq, dr in ENGINE_HEX_DIRS:
                nb = (q + dq, r + dr)
                if nb not in dominant:
                    continue
                pair = (min(coord, nb), max(coord, nb))
                if pair in counted:
                    continue
                counted.add(pair)
                if dominant[nb] == grp:
                    combo_pts += 1

        return combo_pts

    @staticmethod
    def _empty_state() -> dict:
        return {
            "group_counts":  {"MIND": 0, "CONNECTION": 0, "EXISTENCE": 0},
            "group_bonus":   {"MIND": 0, "CONNECTION": 0, "EXISTENCE": 0},
            "div_bonus": 0, "total": 0, "unique_active": 0, "combo_pts": 0,
        }

    # ── Ana render ───────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        state = self._compute_state()
        t     = pygame.time.get_ticks() / 1000.0
        self._render_groups_box(surface, state, t)
        self._render_score_box(surface, state, t)
        self._render_last_combat_box(surface)
        self._render_passive_feed(surface)

    # ── Grup kutusu ──────────────────────────────────────────────────

    def _render_groups_box(self, surface: pygame.Surface, state: dict, t: float) -> None:
        gx, gy = self.groups_rect.x, self.groups_rect.y
        surface.blit(self._grp_surf, (gx, gy))

        font_cache.render_text(
            surface, "SYNERGY BOARD", font_cache.bold(10),
            self._C_TITLE,
            pygame.Rect(gx, gy + 4, self.groups_rect.w, 14),
            align="center",
        )

        row_h   = 62
        row_y   = gy + 18
        pad     = 6
        inner_w = self.groups_rect.w - pad * 2

        for key, color, short in self._GROUPS:
            count  = state["group_counts"].get(key, 0)
            bonus  = state["group_bonus"].get(key, 0)
            active = count >= 2
            flash  = self._flash_timers.get(key, 0) > 0

            row_bg = pygame.Rect(gx + pad, row_y, inner_w, row_h - 4)
            if active:
                bg_a   = 50 if flash else 28
                bg_col = tuple(c * bg_a // 255 for c in color)
            else:
                bg_col = (22, 26, 42)
            pygame.draw.rect(surface, bg_col, row_bg, border_radius=5)
            if active:
                dim_c = tuple(max(0, c - 80) for c in color)
                pygame.draw.rect(surface, dim_c, row_bg, width=1, border_radius=5)

            # Grup adı
            name_col = color if active else self._C_TEXT_DIM
            font_cache.render_text(
                surface, key, font_cache.bold(11), name_col,
                pygame.Rect(gx + pad + 6, row_y + 4, 90, 13),
            )

            # Bonus (sağ)
            if bonus > 0:
                bright  = tuple(min(255, int(c * 1.3)) for c in color)
                pts_txt = f"+{bonus}"
            else:
                bright  = self._C_TEXT_DIM
                pts_txt = "–"
            font_cache.render_text(
                surface, pts_txt, font_cache.bold(13), bright,
                pygame.Rect(gx + pad, row_y + 2, inner_w - 6, 15),
                align="right",
            )

            # Pip bar
            pip_y  = row_y + 22
            pip_x0 = gx + pad + 6
            pip_r  = 5
            pip_gap= 14

            for i in range(6):
                pip_cx = pip_x0 + i * pip_gap + pip_r
                pip_cy = pip_y + pip_r
                filled = i < count

                if filled:
                    pulse = (0.8 + 0.2 * math.sin(t * 6)) if flash else 1.0
                    rc    = tuple(min(255, int(c * pulse)) for c in color)
                    pygame.draw.circle(surface, rc, (pip_cx, pip_cy), pip_r)
                    pygame.draw.circle(surface, tuple(min(255, int(c * 1.5)) for c in color),
                                       (pip_cx, pip_cy), 2)
                else:
                    pygame.draw.circle(surface, self._C_PIP_OFF, (pip_cx, pip_cy), pip_r)
                    pygame.draw.circle(surface, (60, 65, 95), (pip_cx, pip_cy), pip_r, 1)

                if (i + 1) in (2, 3, 4, 5, 6):
                    tick_x   = pip_cx + pip_gap // 2
                    tick_col = (70, 80, 110) if not filled else tuple(max(0, c - 100) for c in color)
                    pygame.draw.line(surface, tick_col,
                                     (tick_x, pip_cy - 3), (tick_x, pip_cy + 3), 1)

            # Sonraki tier metni
            nxt = _next_tier(count)
            if nxt:
                need, nxt_pts = nxt
                sub = f"{count} kart  →  {need - count} daha → +{nxt_pts}pts"
            else:
                sub = f"{count} kart  ·  MAX  · +{bonus}pts"

            font_cache.render_text(
                surface, sub, font_cache.mono(8),
                (160, 165, 195) if active else self._C_TEXT_DIM,
                pygame.Rect(gx + pad + 5, pip_y + pip_r * 2 + 5, inner_w - 10, 12),
            )

            row_y += row_h

    # ── Skor kutusu ──────────────────────────────────────────────────

    # Bileşen başına sabit renk & arka plan tablosu (synergy group satırlarıyla aynı dil)
    _SCORE_ROWS = [
        # (anahtar, etiket, accent rengi, aktif bg tint, aktif label rengi, aktif değer rengi)
        ("kill",  "KILL",  (100, 180, 220), (18,  50,  75, 60),  (140, 195, 225), (170, 210, 235)),
        ("combo", "COMBO", (225, 175,  55), (75,  55,  15, 60),  (225, 175,  55), (240, 195,  80)),
        ("syn",   "SYN",   (255, 210,  60), (65,  50,  10, 50),  (255, 200,  50), (255, 215,  70)),
    ]

    def _render_score_box(self, surface: pygame.Surface, state: dict, t: float) -> None:
        sx, sy = self.score_rect.x, self.score_rect.y
        surface.blit(self._score_surf, (sx, sy))

        # ── Başlık ───────────────────────────────────────────────────
        font_cache.render_text(
            surface, "SKOR TABLOSU", font_cache.bold(10), self._C_TITLE,
            pygame.Rect(sx, sy + 4, self.score_rect.w, 14),
            align="center",
        )
        pygame.draw.line(surface, (42, 58, 92),
                         (sx + 8, sy + 20), (sx + self.score_rect.w - 8, sy + 20), 1)

        # ── Veri hazırla ─────────────────────────────────────────────
        total     = state["total"]
        div       = state["div_bonus"]
        group_sum = total - div
        # Combo: board'dan canlı hesaplanır (synergy ile aynı yaklaşım)
        combo_pts = state.get("combo_pts", 0)

        # Kill: yalnızca gerçekleşmiş savaştan gelir (last_combat_results)
        kill_pts = 0
        try:
            from v2.core.game_state import GameState
            for r in GameState.get().get_last_combat_results():
                if r.get("pid_a") == 0:
                    kill_pts = r.get("kill_a", 0)
                    break
                elif r.get("pid_b") == 0:
                    kill_pts = r.get("kill_b", 0)
                    break
        except Exception:
            pass

        grand_total = kill_pts + combo_pts + total
        values      = {"kill": kill_pts, "combo": combo_pts, "syn": total}
        sub_texts   = {
            "kill":  f"{kill_pts // 8} kart yok edildi" if kill_pts >= 8 else "henüz kill yok",
            "combo": f"komşu grup eşleşmesi",
            "syn":   f"Grp +{group_sum}  ·  Div +{div}",
        }

        # ── 3 bileşen satırı (synergy group row stilinde) ─────────────
        pad     = 6
        inner_w = self.score_rect.w - pad * 2
        row_h   = 22
        row_y   = sy + 24

        for key, lbl, accent, bg_tint, lbl_col_on, val_col_on in self._SCORE_ROWS:
            val    = values[key]
            active = val > 0

            # Satır zemin
            row_bg = pygame.Rect(sx + pad, row_y, inner_w, row_h)
            bg_col = bg_tint[:3] if active else (20, 24, 40)
            pygame.draw.rect(surface, bg_col, row_bg, border_radius=4)

            # Sol accent çizgisi (3 px, sadece aktifse)
            if active:
                pygame.draw.rect(
                    surface, accent,
                    pygame.Rect(sx + pad, row_y + 2, 3, row_h - 4),
                    border_radius=2,
                )
                # Satır kenar çizgisi
                dim_accent = tuple(max(0, c - 80) for c in accent)
                pygame.draw.rect(surface, dim_accent, row_bg, width=1, border_radius=4)

            # Etiket
            lbl_c = lbl_col_on if active else self._C_TEXT_DIM
            font_cache.render_text(
                surface, lbl, font_cache.bold(10), lbl_c,
                pygame.Rect(sx + pad + 8, row_y + 3, 60, 14),
            )

            # Alt açıklama (küçük, soluk)
            font_cache.render_text(
                surface, sub_texts[key], font_cache.mono(7),
                (110, 120, 150) if active else (55, 62, 85),
                pygame.Rect(sx + pad + 8, row_y + 13, inner_w - 60, 10),
            )

            # Değer (sağ, büyük)
            val_c   = val_col_on if active else self._C_DIM
            val_txt = f"+{val}"
            font_cache.render_text(
                surface, val_txt, font_cache.bold(13), val_c,
                pygame.Rect(sx + pad, row_y + 2, inner_w - 6, 17),
                align="right",
            )

            row_y += row_h + 2

        # ── TOPLAM satırı ────────────────────────────────────────────
        pygame.draw.line(surface, (42, 58, 92),
                         (sx + 8, row_y), (sx + self.score_rect.w - 8, row_y), 1)
        row_y += 3

        pulse     = 0.85 + 0.15 * math.sin(t * 2.2)
        total_col = tuple(min(255, int(c * pulse)) for c in self._C_GOLD)
        font_cache.render_text(
            surface, "TOPLAM", font_cache.bold(10), (140, 148, 175),
            pygame.Rect(sx + 10, row_y, 80, 13),
        )
        font_cache.render_text(
            surface, f"+{grand_total}", font_cache.bold(14), total_col,
            pygame.Rect(sx + 8, row_y - 1, self.score_rect.w - 16, 15),
            align="right",
        )

    # ── Son savaş kutusu ─────────────────────────────────────────────

    def _render_last_combat_box(self, surface: pygame.Surface) -> None:
        cx, cy = self.last_combat_rect.x, self.last_combat_rect.y
        surface.blit(self._combat_surf, (cx, cy))

        font_cache.render_text(
            surface, "SON SAVAŞ", font_cache.bold(10), self._C_TITLE,
            pygame.Rect(cx, cy + 4, self.last_combat_rect.w, 14),
            align="center",
        )

        try:
            from v2.core.game_state import GameState
            results = GameState.get().get_last_combat_results()
            our = None
            for r in results:
                if r.get("pid_a") == 0 or r.get("pid_b") == 0:
                    our = r
                    break
        except Exception:
            our = None

        sep_y = cy + 20
        pygame.draw.line(surface, (42, 58, 92),
                         (cx + 8, sep_y), (cx + self.last_combat_rect.w - 8, sep_y), 1)

        if our is None:
            font_cache.render_text(
                surface, "— savaş bekleniyor —", font_cache.mono(9), self._C_TEXT_DIM,
                pygame.Rect(cx + 8, cy + 26, self.last_combat_rect.w - 16, 12),
                align="center",
            )
            return

        pid_a   = our.get("pid_a", -1)
        winner  = our.get("winner_pid", -1)
        dmg     = our.get("dmg", 0)
        hp_after_opp = our.get("hp_after_b" if pid_a == 0 else "hp_after_a", "?")
        hp_before_opp= our.get("hp_before_b" if pid_a == 0 else "hp_before_a", "?")
        opp_pid = our.get("pid_b" if pid_a == 0 else "pid_a", "?")

        if winner == 0:
            result_txt = "▲ KAZANDIN"
            result_col = (80, 220, 120)
        elif winner == -1:
            result_txt = "— BERABERE"
            result_col = (160, 160, 180)
        else:
            result_txt = "▼ KAYBETTİN"
            result_col = (220, 80, 80)

        font_cache.render_text(
            surface, result_txt, font_cache.bold(12), result_col,
            pygame.Rect(cx + 8, cy + 24, self.last_combat_rect.w - 16, 16),
        )
        if dmg > 0:
            dmg_txt = f"P{opp_pid} → -{dmg} HP  ({hp_after_opp}/150)"
            font_cache.render_text(
                surface, dmg_txt, font_cache.mono(9), (180, 185, 210),
                pygame.Rect(cx + 8, cy + 24, self.last_combat_rect.w - 16, 14),
                align="right",
            )

        # Draws info
        draws = our.get("draws", 0)
        if draws > 0:
            font_cache.render_text(
                surface, f"{draws} hex berabere", font_cache.mono(8), self._C_TEXT_DIM,
                pygame.Rect(cx + 8, cy + 44, self.last_combat_rect.w - 16, 12),
            )

    # ── Pasif akış kutusu ────────────────────────────────────────────

    def _render_passive_feed(self, surface: pygame.Surface) -> None:
        px, py = self.passive_feed_rect.x, self.passive_feed_rect.y
        surface.blit(self._feed_surf, (px, py))

        font_cache.render_text(
            surface, "PASİF AKIŞI", font_cache.bold(10), self._C_TITLE,
            pygame.Rect(px, py + 4, self.passive_feed_rect.w, 14),
            align="center",
        )

        pygame.draw.line(surface, (42, 58, 92),
                         (px + 8, py + 20), (px + self.passive_feed_rect.w - 8, py + 20), 1)

        try:
            from v2.core.game_state import GameState
            log = GameState.get().get_passive_buff_log(0)
        except Exception:
            log = []

        line_h    = 17
        max_lines = max(3, (self.passive_feed_rect.h - 28) // line_h)
        entries   = log[-max_lines:] if log else []

        if not entries:
            font_cache.render_text(
                surface, "— pasif kaydı yok —", font_cache.mono(9), self._C_TEXT_DIM,
                pygame.Rect(px + 8, py + 28, self.passive_feed_rect.w - 16, 12),
                align="center",
            )
            return

        fnt   = font_cache.mono(9)
        fnt_b = font_cache.bold(9)
        ly    = py + 26

        for entry in reversed(entries):
            trigger = entry.get("trigger", "")
            card    = entry.get("card", "")
            delta   = entry.get("delta", 0)
            turn_n  = entry.get("turn", 0)

            icon     = _TRIGGER_ICONS.get(trigger, "·")
            color    = _TRIGGER_COLORS.get(trigger, (160, 165, 195))

            # İkon
            icon_surf = fnt_b.render(icon, True, color)
            surface.blit(icon_surf, (px + 8, ly))
            # Kart adı (kısaltılmış)
            card_short = card[:20] + "…" if len(card) > 20 else card
            name_surf  = fnt.render(card_short, True, (200, 205, 225))
            surface.blit(name_surf, (px + 20, ly))
            # Delta (varsa)
            if delta > 0:
                d_surf = fnt_b.render(f"+{delta}", True, color)
                surface.blit(d_surf, (px + self.passive_feed_rect.w - d_surf.get_width() - 8, ly))
            # Trigger kısa etiketi (alt satır, küçük)
            trig_short = trigger.replace("_", " ")
            t_surf = fnt.render(f"T{turn_n} · {trig_short}", True, self._C_TEXT_DIM)
            surface.blit(t_surf, (px + 20, ly + 9))

            ly += line_h + 5
            if ly + line_h > self.passive_feed_rect.bottom - 6:
                break
