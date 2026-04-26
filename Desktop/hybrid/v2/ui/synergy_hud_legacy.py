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
from v2.core.exceptions import AutochessException
from v2.ui import font_cache
from collections import defaultdict

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

    # ── Canonical 6 Kategorileri (Mapping & Styling) ──────────────────
    _CAT_LIST = [
        # (ID/Key, Display Name, Icon, Color)
        ("MYTHOLOGY", "MYTHOLOGY",       "⚡", (248, 222, 34)),
        ("ART",       "ART & CULTURE",   "♪", (240, 60, 110)),
        ("NATURE",    "NATURE",          "♣", (60, 255, 80)),
        ("COSMOS",    "COSMOS",          "★", (140, 80, 255)),
        ("SCIENCE",   "SCIENCE",         "⊕", (3, 190, 240)),
        ("HISTORY",   "HISTORY",         "⚜", (255, 120, 40)),
    ]
    
    _CAT_MAPPING = {
        "Mythology & Gods":     "MYTHOLOGY",
        "Art & Culture":        "ART",
        "Nature & Biology":     "NATURE",
        "Nature & Creatures":   "NATURE",
        "Cosmos & Space":       "COSMOS",
        "Cosmos":               "COSMOS",
        "Science":              "SCIENCE",
        "Science & Technology": "SCIENCE",
        "History":              "HISTORY",
        "History & Civilizations": "HISTORY",
    }

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

        # ── Kategori HUD (Eski Score Box + Combat Box alanı) ────────
        # 6 satır (her biri ~34px) + başlık için ~216px alan ayırıyoruz
        self.category_hud_rect = pygame.Rect(x0, self.groups_rect.bottom + 10, inner_w, 216)

        # ── Pasif akış kutusu ────────────────────────────────────────
        # Synergy ve Category kutuları orantılandığında kalan tüm alanı pasif feed alır
        feed_h = self.rect.bottom - self.category_hud_rect.bottom - 18
        self.passive_feed_rect = pygame.Rect(x0, self.category_hud_rect.bottom + 10, inner_w, feed_h)

        # Önbelleklenmiş yüzeyler
        from v2.ui.ui_utils import UIUtils
        _bdr = (42, 58, 92, 180)
        _top = (36, 42, 62, 255)
        _bot = (16, 22, 42, 255)
        def _panel(w, h):
            return UIUtils.create_gradient_panel(w, h, _top, _bot, border_radius=8, border_color=_bdr)

        self._grp_surf      = _panel(inner_w, self.groups_rect.h)
        self._cat_surf      = _panel(inner_w, self.category_hud_rect.h)
        self._feed_surf     = _panel(inner_w, self.passive_feed_rect.h)

        # ── Animasyon durumu ─────────────────────────────────────────
        self._last_tiers:   dict[str, int]   = {g[0]: 0 for g in self._GROUPS}
        self._bursts:       list[dict]       = [] # [{"x", "y", "color", "progress"}]
        self._flash_timers: dict[str, float] = {}

        # ── Pasif akış: gösterilen son N kayıt ───────────────────────
        self._feed_seen_count: int = 0   # passive_buff_log'dan kaç kayıt gördük
        self._board_cards: dict = {}
        self._passive_feed: list[dict] = []

    # ── Public API ───────────────────────────────────────────────────

    def add_log(self, line: str) -> None:
        """Geriye uyumluluk stub'ı — artık pasif feed kullanılıyor."""
        pass

    def update(self, dt_ms: float, board_cards: dict | None = None, passive_feed: list | None = None) -> None:
        if board_cards is not None:
            self._board_cards = board_cards
        if passive_feed is not None:
            self._passive_feed = list(passive_feed)
        for k in list(self._flash_timers):
            self._flash_timers[k] -= dt_ms
            if self._flash_timers[k] <= 0:
                del self._flash_timers[k]
        
        # ── Patlama (Burst) animasyonları
        for b in self._bursts[:]:
            b["progress"] += dt_ms / 500.0 # 500ms sürer
            if b["progress"] >= 1.0:
                self._bursts.remove(b)

    # ── Synergy hesabı ───────────────────────────────────────────────

    def _get_tier(self, n: int) -> int:
        if n < 2: return 0
        if n == 2: return 1
        if n == 3: return 2
        if n <= 5: return 3
        return 4

    def _compute_state(self) -> dict:
        from v2.core.synergy_calculator import SynergyCalculator
        from v2.core.card_database import CardDatabase
        from v2.core.exceptions import AutochessException
        try:
            db  = CardDatabase.get()
            res = SynergyCalculator.compute(self._board_cards, db)
        except AutochessException:
            return self._empty_state()

        combo_pts  = self._compute_combo_pts(self._board_cards, db)
        cat_counts = self._build_cat_counts(self._board_cards, db)

        return {
            "group_counts": res.group_counts,
            "group_bonus":  res.group_bonuses,
            "total":        res.total,
            "combo_pts":    combo_pts,
            "cat_counts":   cat_counts,
        }

    def _trigger_burst(self, group_name: str):
        idx = 0
        for i, (k, *_) in enumerate(self._GROUPS):
            if k == group_name: idx = i; break
        # Icon position (Left sidebar sidebar_left_w)
        bx = self.groups_rect.x + 20
        by = self.groups_rect.y + 18 + idx * 62 + 28
        color = next(g[1] for g in self._GROUPS if g[0] == group_name)
        self._bursts.append({"x": bx, "y": by, "color": color, "progress": 0.0})

    def _build_cat_counts(self, board: dict, db) -> dict:
        """Canonical Category Tracking (Master Refit Mapping)"""
        cat_counts = {c[0]: 0 for c in self._CAT_LIST}
        for item in board.values():
            c_name = item.get("name") if isinstance(item, dict) else item
            c_data = db.lookup(c_name)
            if c_data:
                canon_key = self._CAT_MAPPING.get(c_data.category)
                if canon_key:
                    cat_counts[canon_key] += 1
        return cat_counts

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
        return combo_pts

    @staticmethod
    def _empty_state() -> dict:
        return {
            "group_counts":  {"MIND": 0, "CONNECTION": 0, "EXISTENCE": 0},
            "group_bonus":   {"MIND": 0, "CONNECTION": 0, "EXISTENCE": 0},
            "total": 0,
            "combo_pts": 0,
            "cat_counts": {},
        }

    # ── Ana render ───────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        state = self._compute_state()
        t     = pygame.time.get_ticks() / 1000.0
        self._render_groups_box(surface, state, t)
        self._render_category_hud(surface, state, t)
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
            max_n  = state["group_counts"].get(key, 0)
            bonus  = state["group_bonus"].get(key, 0)
            active = max_n >= 2
            flash  = self._flash_timers.get(key, 0) > 0

            row_bg = pygame.Rect(gx + pad, row_y, inner_w, row_h - 4)
            if active:
                bg_col = tuple(c * (50 if flash else 28) // 255 for c in color)
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
            pts_txt = f"+{bonus}" if bonus > 0 else "–"
            font_cache.render_text(
                surface, pts_txt, font_cache.bold(13), color if bonus > 0 else self._C_TEXT_DIM,
                pygame.Rect(gx + pad, row_y + 2, inner_w - 6, 15),
                align="right",
            )

            # Pip bar (Cluster size)
            pip_y  = row_y + 22
            pip_x0 = gx + pad + 6
            pip_r  = 5
            pip_gap= 14

            for i in range(6):
                pip_cx = pip_x0 + i * pip_gap + pip_r
                pip_cy = pip_y + pip_r
                filled = i < max_n

                if filled:
                    pulse = (0.8 + 0.2 * math.sin(t * 6)) if flash else 1.0
                    rc    = tuple(min(255, int(c * pulse)) for c in color)
                    pygame.draw.circle(surface, rc, (pip_cx, pip_cy), pip_r)
                    pygame.draw.circle(surface, (255, 255, 255), (pip_cx, pip_cy), 2)
                else:
                    pygame.draw.circle(surface, self._C_PIP_OFF, (pip_cx, pip_cy), pip_r)
                    pygame.draw.circle(surface, (60, 65, 95), (pip_cx, pip_cy), pip_r, 1)

            # Subtext
            sub = f"En büyük küme: {max_n}" if active else "bağlantı yok"
            font_cache.render_text(
                surface, sub, font_cache.mono(8),
                (160, 165, 195) if active else self._C_TEXT_DIM,
                pygame.Rect(gx + pad + 5, pip_y + pip_r * 2 + 5, inner_w - 10, 12),
            )
            row_y += row_h

        # ── Render Bursts
        for b in self._bursts:
            alpha = int(255 * (1.0 - b["progress"]))
            radius = int(10 + 50 * b["progress"])
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*b["color"], alpha), (radius, radius), radius, 2)
            surface.blit(surf, (b["x"] - radius, b["y"] - radius))

        # ── Kategori Takip HUD (Master Refit: Synergy Style Rows) ────────

    def _render_category_hud(self, surface: pygame.Surface, state: dict, t: float) -> None:
        gx, gy = self.category_hud_rect.x, self.category_hud_rect.y
        surface.blit(self._cat_surf, (gx, gy))

        font_cache.render_text(
            surface, "BOARD KATEGORİ TAKİBİ", font_cache.bold(10), self._C_TITLE,
            pygame.Rect(gx, gy + 4, self.category_hud_rect.w, 14),
            align="center",
        )

        row_h   = 32
        row_y   = gy + 20
        pad     = 6
        inner_w = self.category_hud_rect.w - pad * 2
        cat_counts = state.get("cat_counts", {})

        for cat_id, display_name, icon, color in self._CAT_LIST:
            count = cat_counts.get(cat_id, 0)
            active = count > 0

            # Satır Arka Planı (Synergy style rounded row)
            row_bg = pygame.Rect(gx + pad, row_y, inner_w, row_h - 4)
            if active:
                bg_col = tuple(c * 28 // 255 for c in color)
            else:
                bg_col = (20, 24, 40)
            
            pygame.draw.rect(surface, bg_col, row_bg, border_radius=4)
            if active:
                dim_c = tuple(max(0, c - 100) for c in color)
                pygame.draw.rect(surface, dim_c, row_bg, width=1, border_radius=4)

            # İkon ve İsim
            name_col = color if active else self._C_TEXT_DIM
            font_cache.render_text(
                surface, icon, font_cache.bold(12), color if active else (50, 55, 75),
                pygame.Rect(gx + pad + 8, row_y + 4, 20, 15)
            )
            font_cache.render_text(
                surface, display_name, font_cache.bold(9), name_col,
                pygame.Rect(gx + pad + 28, row_y + 5, inner_w - 60, 13),
            )

            # Adet (Sağ)
            pts_txt = str(count)
            font_cache.render_text(
                surface, pts_txt, font_cache.bold(12), color if active else self._C_TEXT_DIM,
                pygame.Rect(gx + pad, row_y + 4, inner_w - 8, 15),
                align="right",
            )

            row_y += row_h

    # ── Pasif akış kutusu ────────────────────────────────────────────

    def _render_passive_feed(self, surface: pygame.Surface) -> None:
        px, py = self.passive_feed_rect.x, self.passive_feed_rect.y
        surface.blit(self._feed_surf, (px, py))
        font_cache.render_text(surface, "PASİF AKIŞI", font_cache.bold(10), self._C_TITLE, pygame.Rect(px, py + 4, self.passive_feed_rect.w, 14), align="center")
        
        try:
            log = list(self._passive_feed)
            if not log:
                font_cache.render_text(
                    surface, "— pasif kaydı yok —", font_cache.mono(9), self._C_TEXT_DIM,
                    pygame.Rect(px + 8, py + 28, self.passive_feed_rect.w - 16, 12),
                    align="center",
                )
                return

            line_h    = 18
            max_lines = (self.passive_feed_rect.h - 28) // (line_h + 4)
            entries   = log[-max_lines:]
            
            fnt   = font_cache.mono(9)
            fnt_b = font_cache.bold(9)
            ly    = py + 24

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
                
                # Trigger kısa etiketi (alt satır)
                trig_short = trigger.replace("_", " ")
                t_surf = fnt.render(f"T{turn_n} · {trig_short}", True, self._C_TEXT_DIM)
                surface.blit(t_surf, (px + 20, ly + 9))

                ly += line_h + 4
                if ly + line_h > self.passive_feed_rect.bottom - 4:
                    break
        except AutochessException:
            pass
