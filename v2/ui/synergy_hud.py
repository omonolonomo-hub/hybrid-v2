"""
SynergyHud — Sol sidebar grup synergy + son savaş + pasif akış.
DCI Refit: Digital Combat Interface.
"""
from __future__ import annotations
import math
import pygame
import random
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache
from collections import defaultdict

_TIER_THRESHOLDS = [2, 3, 4, 5, 6]
_TIER_BONUSES    = [3, 7, 11, 16, 18]

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
    "combo":          (255, 215,  50),
}
_TRIGGER_ICONS: dict[str, str] = {
    "copy_2":         "STAR",
    "copy_3":         "STAR",
    "copy_strengthen":"STAR",
    "income":         "GOLD",
    "market_refresh": "SYNC",
    "card_buy":       "SHOP",
    "combat_win":     "SWORD",
    "combat_lose":    "SKULL",
    "card_killed":    "SKULL",
    "pre_combat":     "BOLT",
    "combo":          "FIRE",
}

class SynergyHud:
    _C_TITLE    = (100, 140, 220)
    _C_DIM      = (55,  60,  85)
    _C_PIP_OFF  = (42,  48,  72)
    _C_TEXT_DIM = (80,  85, 110)
    _C_WHITE    = (220, 224, 240)
    _C_GOLD     = (255, 210,  60)
    
    # ── DCI Estetik Renkleri
    _C_DCI_GRID   = (80, 100, 160, 160)
    _C_DCI_GLOW   = (100, 150, 255, 60)
    _C_DCI_SCAN   = (255, 255, 255, 15)

    _GROUPS = [
        ("MIND",       Colors.MIND,       "MIND"),
        ("CONNECTION", Colors.CONNECTION, "CONN"),
        ("EXISTENCE",  Colors.EXISTENCE,  "EXST"),
    ]

    _CAT_LIST = [
        # (ID/Key, Display Name, Icon, Color, Abbr)
        ("MYTHOLOGY", "MYTHOLOGY",       "⚡", (248, 222, 34),  "MYTH"),
        ("ART",       "ART & CULTURE",   "♪", (240, 60, 110),  "ARTS"),
        ("NATURE",    "NATURE",          "♣", (60, 255, 80),   "NATR"),
        ("COSMOS",    "COSMOS",          "★", (140, 80, 255),  "COSM"),
        ("SCIENCE",   "SCIENCE",         "⊕", (3, 190, 240),   "SCIE"),
        ("HISTORY",   "HISTORY",         "⚜", (255, 120, 40),   "HIST"),
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
        # 🎯 [FIX] Minimap ile tam bitişik olması için (boşluksuz) yükseklik ayarlandı
        # Minimap y=700'de başlıyor (1080 - 340 - 40).
        self.rect = pygame.Rect(
            0, Layout.SYNERGY_HUD_Y,
            Layout.SIDEBAR_LEFT_W,
            700 - Layout.SYNERGY_HUD_Y,
        )
        # hud_h = self.rect.h # legacy calc

        pad      = 10
        inner_w  = self.rect.w - pad * 2
        x0       = self.rect.x + pad
        y0       = self.rect.y

        # ── Animasyon durumu ve DCI Materyalleri ─────────────────────
        self._last_tiers:   dict[str, int]   = {g[0]: 0 for g in self._GROUPS}
        self._bursts:       list[dict]       = [] # [{"x", "y", "color", "progress"}]
        self._flash_timers: dict[str, float] = {}

        # Kinematik state (Lerp için)
        self._curr_cat_vals: dict[str, float] = {c[0]: 0.0 for c in self._CAT_LIST}
        self._total_units:   float            = 0.0

        # ── DCI Materyalleri (Noise / Grain)
        self._noise_surf = self._create_noise_surf(128, 128)
        self._scanline_y = 0.0

        # Boxes
        # Groups: PlayerHub'ın hemen altına (Y=5 local -> 155 screen)
        self.groups_rect = pygame.Rect(x0, 5, inner_w, 204)
        
        # Category HUD (PETEK) KALDIRILDI - Yerine Minimap gelecek (ShopScene seviyesinde)
        self.category_hud_rect = pygame.Rect(0, 0, 0, 0) 

        # Passive Feed: Orta alan (Minimap'e daha fazla yer açmak için 320 -> 240px)
        feed_h = 240  # 80px kısaltıldı
        self.passive_feed_rect = pygame.Rect(x0, 215, inner_w, feed_h)

        # Pre-render panels
        from v2.ui.ui_utils import UIUtils
        _bdr = (42, 58, 92, 220)
        _top = (12, 16, 24, 255) # Opaque Deep Void
        _bot = (8, 10, 16, 255)   # Opaque Deep Void
        def _panel(w, h):
            p = UIUtils.create_gradient_panel(w, h, _top, _bot, border_radius=8, border_color=_bdr)
            self._apply_noise(p)
            return p

        self._grp_surf  = _panel(inner_w, self.groups_rect.h)
        self._cat_surf  = _panel(inner_w, self.category_hud_rect.h)
        self._feed_surf = _panel(inner_w, self.passive_feed_rect.h)
        
        # ── Yeni Log Sistemi Verileri ─────────────────────────────────
        self._logs: list[dict] = [] # Animated logs
        
        # [FIX] Başlangıçta mevcut log sayısını eşitle ki geçmişi tekrar okumasın
        try:
            from v2.core.game_state import GameState
            self._feed_seen_count: int = len(GameState.get().get_passive_buff_log(0))
        except:
            self._feed_seen_count: int = 0
            
        self._feed_scroll_y:   float = 0.0

    def _create_noise_surf(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h))
        for x in range(w):
            for y in range(h):
                val = random.randint(220, 255)
                surf.set_at((x, y), (val, val, val))
        return surf

    def _apply_noise(self, target_surf: pygame.Surface):
        tw, th = target_surf.get_size()
        nw, nh = self._noise_surf.get_size()
        for x in range(0, tw, nw):
            for y in range(0, th, nh):
                target_surf.blit(self._noise_surf, (x, y), special_flags=pygame.BLEND_RGBA_MULT)

    def add_log(self, trigger: str, card_name: str, delta: int = 0, res: int = 0):
        """Dışarıdan veya GS'den gelen logları listeye animasyonlu ekler.
        Mükerrer kaydı önlemek için 'Duplicate Guard' içerir.
        """
        now = pygame.time.get_ticks()
        
        # ── Duplicate Guard ───────────────────────────────────────────
        # Eğer son log aynıysa ve son 100ms içinde eklendiyse es geç
        if self._logs:
            last = self._logs[0]
            if (last["trigger"] == trigger and 
                last["card"] == card_name and 
                last["delta"] == delta and 
                last["res"] == res and
                now - last["time"] < 100):
                return

        entry = {
            "trigger": trigger,
            "card": card_name,
            "delta": delta,
            "res": res,
            "time": now,
            "alpha": 0.0,
            "offset_y": 10.0
        }
        self._logs.insert(0, entry)
        if len(self._logs) > 20: # 15 -> 20 (Artan yer sayesinde)
            self._logs.pop()

    def update(self, dt_ms: float) -> None:
        # Animasyon güncelleme (Lerp)
        for log in self._logs:
            log["alpha"] += (1.0 - log["alpha"]) * 0.1
            log["offset_y"] += (0.0 - log["offset_y"]) * 0.1

        for k in list(self._flash_timers):
            self._flash_timers[k] -= dt_ms
            if self._flash_timers[k] <= 0: del self._flash_timers[k]
        
        for b in self._bursts[:]:
            b["progress"] += dt_ms / 500.0
            if b["progress"] >= 1.0: self._bursts.remove(b)

        # 🧪 Akıllı Log Takibi: GameState'ten yeni gelenleri yakala
        from v2.core.game_state import GameState
        try:
            gs_log = GameState.get().get_passive_buff_log(0)
            
            # [FIX] Eğer log temizlendiyse (yeni tur), sayacı sıfırla
            if len(gs_log) < self._feed_seen_count:
                self._feed_seen_count = 0
                
            if len(gs_log) > self._feed_seen_count:
                for i in range(self._feed_seen_count, len(gs_log)):
                    e = gs_log[i]
                    self.add_log(e.get("trigger",""), e.get("card",""), e.get("delta",0), e.get("res",0))
                self._feed_seen_count = len(gs_log)
        except Exception:
            pass

        # Kinematic Lerp
        state = self._compute_state()
        lf = 0.15
        t_tot = float(sum(state["cat_counts"].values()))
        self._total_units += (t_tot - self._total_units) * lf
        for cid, val in state["cat_counts"].items():
            if cid in self._curr_cat_vals:
                self._curr_cat_vals[cid] += (float(val) - self._curr_cat_vals[cid]) * lf

    def _get_tier(self, n: int) -> int:
        if n < 2: return 0
        if n == 2: return 1
        if n == 3: return 2
        if n <= 5: return 3
        return 4

    def _compute_state(self) -> dict:
        from v2.core.game_state import GameState
        from v2.core.card_database import CardDatabase
        from v2.constants import STAT_TO_GROUP, ENGINE_HEX_DIRS, OPP_DIR
        try:
            gs = GameState.get(); board = gs.get_board_cards(); db = CardDatabase.get()
        except:
            return {"group_counts":{}, "group_bonus":{}, "total":0, "cat_counts":{}}

        group_bonus = {g[0]: 0 for g in self._GROUPS}
        group_max_n = {g[0]: 0 for g in self._GROUPS}
        
        for g_name, _, _ in self._GROUPS:
            visited = set()
            for coord in board:
                if coord in visited: continue
                cluster = {coord}; queue = [coord]; c_vis = {coord}; matches = 0; match_p = set()
                while queue:
                    curr = queue.pop(0)
                    cdat = db.lookup(board[curr]["name"])
                    if not cdat: continue
                    edges = list(cdat.stats.items())
                    rot = board[curr].get("rotation", 0)
                    for d_i, (dq, dr) in enumerate(ENGINE_HEX_DIRS):
                        nb = (curr[0]+dq, curr[1]+dr)
                        if nb not in board: continue
                        nb_dat = db.lookup(board[nb]["name"])
                        if not nb_dat: continue
                        nb_rot = board[nb].get("rotation", 0)
                        idx_a = (d_i - rot)%6; idx_b = (OPP_DIR[d_i] - nb_rot)%6
                        ga = STAT_TO_GROUP.get(edges[idx_a][0]); gb = STAT_TO_GROUP.get(list(nb_dat.stats.items())[idx_b][0])
                        if ga == g_name and gb == g_name:
                            p = tuple(sorted((curr, nb)))
                            if p not in match_p: matches += 1; match_p.add(p)
                            if nb not in c_vis: c_vis.add(nb); cluster.add(nb); queue.append(nb)
                visited.update(cluster); n = len(cluster)
                if n >= 2:
                    if n == 2: tp = 3
                    elif n == 3: tp = 9
                    elif n <= 5: tp = 16
                    else: tp = 25 + (n - 6) * 3
                    group_bonus[g_name] += (tp + matches*2); group_max_n[g_name] = max(group_max_n[g_name], n)

        for g in group_max_n:
            nt = self._get_tier(group_max_n[g])
            if nt > self._last_tiers.get(g, 0):
                self._trigger_burst(g)
                # ── [NEW] Combo Log Tetikle
                self.add_log("combo", f"{g} UPGRADED", res=nt)
            self._last_tiers[g] = nt

        cat_counts = {c[0]: 0 for c in self._CAT_LIST}
        for it in board.values():
            c_dat = db.lookup(it["name"])
            if c_dat:
                ck = self._CAT_MAPPING.get(c_dat.category)
                if ck: cat_counts[ck] += 1
        return {"group_counts":group_max_n, "group_bonus":group_bonus, "total":sum(group_bonus.values()), "cat_counts":cat_counts}

    def _trigger_burst(self, g_name: str):
        idx = next(i for i, g in enumerate(self._GROUPS) if g[0] == g_name)
        bx = self.groups_rect.x + 20; by = self.groups_rect.y + 18 + idx * 62 + 28
        col = next(g[1] for g in self._GROUPS if g[0] == g_name)
        self._bursts.append({"x": bx, "y": by, "color": col, "progress": 0.0})

    def _render_groups_box(self, surface, state, t):
        gx, gy = self.groups_rect.x, self.groups_rect.y
        surface.blit(self._grp_surf, (gx, gy))
        font_cache.render_text(surface, "SYNERGY BOARD", font_cache.bold(10), self._C_TITLE, pygame.Rect(gx, gy + 4, self.groups_rect.w, 14), align="center")
        
        row_h = 62; row_y = gy + 18; pad = 6; inner_w = self.groups_rect.w - pad*2
        for key, color, short in self._GROUPS:
            max_n = state["group_counts"].get(key, 0); bonus = state["group_bonus"].get(key, 0)
            active = max_n >= 2; flash = self._flash_timers.get(key, 0) > 0
            row_bg = pygame.Rect(gx + pad, row_y, inner_w, row_h - 4)
            bg_col = tuple(c * (50 if flash else 28)//255 for c in color) if active else (22, 26, 42)
            pygame.draw.rect(surface, bg_col, row_bg, border_radius=5)
            if active: pygame.draw.rect(surface, tuple(max(0, c-80) for c in color), row_bg, 1, 5)
            
            font_cache.render_text(surface, key, font_cache.bold(11), color if active else self._C_TEXT_DIM, pygame.Rect(gx+pad+6, row_y+4, 90, 13))
            pts_t = f"+{bonus}" if bonus > 0 else "–"
            font_cache.render_text(surface, pts_t, font_cache.bold(13), color if bonus>0 else self._C_TEXT_DIM, pygame.Rect(gx+pad, row_y+2, inner_w-6, 15), align="right")
            
            # Pip Bar
            p_y = row_y + 22; p_x0 = gx+pad+6; p_r=5; p_g=14
            for i in range(6):
                p_cx = p_x0 + i*p_g + p_r; p_cy = p_y + p_r
                filled = i < max_n
                if filled:
                    p = (0.8+0.2*math.sin(t*6)) if flash else 1.0
                    pygame.draw.circle(surface, tuple(min(255, int(c*p)) for c in color), (p_cx, p_cy), p_r)
                    pygame.draw.circle(surface, (255,255,255), (p_cx, p_cy), 2)
                else:
                    pygame.draw.circle(surface, self._C_PIP_OFF, (p_cx, p_cy), p_r)
                    pygame.draw.circle(surface, (60,65,95), (p_cx, p_cy), p_r, 1)
            
            sub = f"En büyük küme: {max_n}" if active else "bağlantı yok"
            font_cache.render_text(surface, sub, font_cache.mono(8), (160,165,195) if active else self._C_TEXT_DIM, pygame.Rect(gx+pad+5, p_y+p_r*2+5, inner_w-10, 12))
            row_y += row_h

        for b in self._bursts:
            alpha = int(255*(1.0-b["progress"]))
            radius = int(10+50*b["progress"])
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*b["color"], alpha), (radius, radius), radius, 2)
            surface.blit(s, (b["x"]-radius, b["y"]-radius))

    # ── Kategori Takip HUD (DCI: Honeycomb Tactical Array) ───────────

    def _draw_hex_cell(self, surface, cx, cy, radius, color, ratio, active_count):
        """Kenarlardan içeri doğru dolan altıgen hücresi (Bloating korumalı)."""
        # 1. Köşe Koordinatları (Sabit Dış Sınır)
        outer_pts = []
        for i in range(6):
            a = math.radians(i * 60 - 30)
            outer_pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
        
        # 2. Arka Plan (Soluk Izgara)
        base_color = (60, 70, 90, 80)
        pygame.draw.polygon(surface, base_color, outer_pts, 1)

        if ratio > 0:
            # 3. İçeri Doğru Dolum (Hole-Masking Mantığı)
            # İsteğe göre: Kenarlardan merkeze doğru dolacak. 
            # Dış sınır (outer_pts) sabit kalmalı.
            
            # Kategori rengi + glow
            alpha = int(100 + 155 * ratio)
            f_col = (*color, alpha)
            
            if active_count >= 6:
                # Tam dolu: Solid
                pygame.draw.polygon(surface, color, outer_pts)
            else:
                # İçeri doğru dolum: Dıştan içe katmanlı çizim
                # Önce tüm altıgeni boyayalım
                pygame.draw.polygon(surface, f_col, outer_pts)
                
                # Sonra ortada bir "delik" açalım (içeri dolma hissi için)
                # ratio arttıkça içteki delik küçülür.
                hole_ratio = 1.0 - ratio
                hole_radius = radius * hole_ratio
                inner_pts = []
                for i in range(6):
                    a = math.radians(i * 60 - 30)
                    inner_pts.append((cx + hole_radius * math.cos(a), cy + hole_radius * math.sin(a)))
                
                # Deliği panelin arka plan rengiyle (veya siyahla) boyayarak 'içeri dolma' illüzyonu yaratıyoruz
                # Not: Panel rengi (16, 22, 42) civarıdır.
                pygame.draw.polygon(surface, (16, 22, 42), inner_pts)

            # 4. Parlak Kenar (DCI Frame)
            pygame.draw.polygon(surface, color, outer_pts, 1)

    def _render_category_hud(self, surface, state, t):
        gx, gy = self.category_hud_rect.x, self.category_hud_rect.y
        surface.blit(self._cat_surf, (gx, gy))
        font_cache.render_text(surface, "HONEYCOMB TACTICAL ARRAY", font_cache.bold(10), self._C_TITLE, pygame.Rect(gx, gy+4, self.category_hud_rect.w, 14), align="center")
        
        # Geometri: 6 Hex (Merkezi boş bırakıp etrafına diziyoruz)
        cx, cy = gx + self.category_hud_rect.w // 2, gy + self.category_hud_rect.h // 2 + 10
        hex_r  = 30
        dist   = 68 # Merkezden hücre merkezlerine uzaklık
        max_val = 6.0

        for i, (cid, d_n, icon, color, abbr) in enumerate(self._CAT_LIST):
            # Hex konumu (60 derece açılarla)
            ang = math.radians(i * 60 - 90)
            hx = cx + dist * math.cos(ang)
            hy = cy + dist * math.sin(ang)
            
            # Veri & Lerp
            v = self._curr_cat_vals.get(cid, 0.0)
            ratio = min(v, max_val) / max_val
            act_n = state["cat_counts"].get(cid, 0)
            act = act_n > 0
            
            # Hücreyi çiz
            self._draw_hex_cell(surface, hx, hy, hex_r, color, ratio, act_n)
            
            # Etiketler (Hex'in dış tarafına, merkeze uzak köşeye yerleştiriyoruz)
            # hx, hy merkezden dist uzaklıktaydı. Etiketleri biraz daha dışarı itiyoruz.
            label_dist = dist + hex_r + 18
            lx = cx + label_dist * math.cos(ang)
            ly = cy + label_dist * math.sin(ang)
            
            label_col = color if act else self._C_DIM
            # Kısaltma ve Sayı dikey bir blok olarak
            font_cache.render_text(surface, abbr, font_cache.bold(9), label_col, pygame.Rect(lx-15, ly-10, 30, 10), align="center")
            font_cache.render_text(surface, f"{act_n}", font_cache.bold(12), label_col, pygame.Rect(lx-10, ly+2, 20, 12), align="center")

        # 4. Merkezi Toplam Sayacı (Hex silindi, sadece işlevsel sayı)
        total_txt = f"{int(self._total_units+0.5)}"
        font_cache.render_text(surface, total_txt, font_cache.bold(22), self._C_WHITE, pygame.Rect(cx-25, cy-12, 50, 24), align="center")
        font_cache.render_text(surface, "TOTAL UNITS", font_cache.mono(7), self._C_TITLE, pygame.Rect(cx-30, cy+10, 60, 10), align="center")

    def _render_passive_feed(self, surface):
        px, py = self.passive_feed_rect.x, self.passive_feed_rect.y
        surface.blit(self._feed_surf, (px, py))
        
        # Header (Cyberpunk Scanline effect)
        header_r = pygame.Rect(px, py + 4, self.passive_feed_rect.w, 14)
        font_cache.render_text(surface, "PASSIVE COM-LOG", font_cache.bold(10), self._C_TITLE, header_r, align="center")
        
        # Clipping area for smooth scrolling
        clip_r = pygame.Rect(px + 4, py + 22, self.passive_feed_rect.w - 8, self.passive_feed_rect.h - 26)
        log_surf = pygame.Surface((clip_r.w, clip_r.h), pygame.SRCALPHA)
        
        y_cursor = 2
        entry_h  = 22
        spacing  = 4
        
        for i, log in enumerate(self._logs):
            if y_cursor + entry_h > clip_r.h: break
            
            tr = log["trigger"]
            col = _TRIGGER_COLORS.get(tr, (160, 165, 195))
            alpha = int(255 * log["alpha"])
            
            # ── Entry Background (Pill Design) ─────────────────────
            row_r = pygame.Rect(2, y_cursor + log["offset_y"], clip_r.w - 4, entry_h)
            
            # Base Pill
            pygame.draw.rect(log_surf, (25, 30, 45, int(alpha * 0.6)), row_r, border_radius=4)
            # Left Accent
            pygame.draw.rect(log_surf, (*col, int(alpha * 0.4)), (row_r.x, row_r.y, 22, entry_h), border_radius=4)
            # Rim Glow
            pygame.draw.rect(log_surf, (*col, int(alpha * 0.2)), row_r, width=1, border_radius=4)

            # 🧪 [ICON] Tactical Trigger Icon
            icon_key = _TRIGGER_ICONS.get(tr, "GEAR")
            icon_x = row_r.x + 11
            icon_y = row_r.y + (entry_h - 10) // 2
            font_cache.render_icon(log_surf, icon_key, 10, (*col, alpha), (icon_x - 5, icon_y), shadow=True)

            # ── Content ───────────────────────────────────────────
            name_txt = log["card"].upper()
            if tr == "combo" and "UPGRADED" in name_txt:
                # Özel combo mesajı (Tier vurgulu)
                name_txt = name_txt.replace("UPGRADED", "").strip()
                font_cache.render_text(log_surf, name_txt, font_cache.bold(9), col, 
                                       pygame.Rect(row_r.x + 28, row_r.y, row_r.w - 60, entry_h), align="left", v_align="center")
                tier_txt = f"TIER {log['res']}"
                font_cache.render_text(log_surf, tier_txt, font_cache.mono(8), (200, 205, 225), 
                                       pygame.Rect(row_r.x + 28 + 65, row_r.y, 50, entry_h), align="left", v_align="center")
            else:
                font_cache.render_text(log_surf, name_txt[:18], font_cache.mono(9), (220, 225, 240), 
                                       pygame.Rect(row_r.x + 28, row_r.y, row_r.w - 60, entry_h), align="left", v_align="center")
            
            # Delta / Value (+N)
            val = log["delta"] if log["delta"] != 0 else log["res"]
            if val != 0 and tr != "combo": 
                v_str = f"+{val}" if val > 0 else str(val)
                font_cache.render_text(log_surf, v_str, font_cache.bold(11), col, 
                                       pygame.Rect(row_r.x, row_r.y, row_r.w - 8, entry_h), align="right", v_align="center")
            
            y_cursor += entry_h + spacing

        surface.blit(log_surf, clip_r.topleft)

    def render(self, surface: pygame.Surface) -> None:
        # 1. Base Dark Surface (Opaklık artırma)
        h_s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        h_s.fill((10, 12, 20, 245)) # Arkadaki boardu kapatacak kadar opak
        
        state = self._compute_state()
        t = pygame.time.get_ticks()/1000.0
        self._render_groups_box(h_s, state, t)
        # self._render_category_hud(h_s, state, t) # PETEK KALDIRILDI
        self._render_passive_feed(h_s)
        
        # 2. Atmospheric Layer (Mavi blok kaldırıldı)

        # 3. Final Blit (Normal blit for unified look)
        surface.blit(h_s, self.rect.topleft)
