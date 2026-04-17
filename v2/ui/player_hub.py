import pygame
import math
import pytweening
from v2.constants import Layout, Colors
from v2.ui import font_cache

class PlayerHub:
    """SOL PANEL: DCI-REFIT (Digital Combat Interface) Oyuncu Merkezi."""

    _MAX_HP: int      = 150
    # DCI Renk Paleti (Deep Carbon Glass)
    _C_VOID_BG   = (10, 12, 18, 255) # Deep Carbon base
    _C_RIM_TOP   = (120, 140, 180, 180) # Üst cam parlaması
    _C_SCANLINE  = (255, 255, 255, 8)
    _C_TITLE     = (100, 150, 255)
    _C_GOLD_GLOW = (255, 180, 50, 40)
    _C_HP_GLOW   = (255, 50, 50, 30)

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, Layout.SIDEBAR_LEFT_W, Layout.PLAYER_HUB_H)
        # İç panel rect (padding ile)
        self.inner_rect = pygame.Rect(10, 8, Layout.SIDEBAR_LEFT_W - 20, 134)
        
        # Element Yerleşimleri (Tüm y-offset'ler panel_surf içindeki 0,0'a göredir)
        self.hp_rect     = pygame.Rect(0, 30, self.inner_rect.w, 20)
        gold_w           = int(self.inner_rect.w * 0.45)
        self.gold_rect   = pygame.Rect(0, 57, gold_w, 28)
        self.streak_rect = pygame.Rect(gold_w + 4, 57, self.inner_rect.w - gold_w - 4, 28)
        self.pts_rect    = pygame.Rect(0, 94, self.inner_rect.w, 20)
        self.income_rect = pygame.Rect(0, 118, self.inner_rect.w, 14)

        # State & Animasyon
        self._hp = self._MAX_HP
        self._gold = 10
        self._display_hp = float(self._MAX_HP)
        self._ghost_hp = float(self._MAX_HP)
        self._display_gold = 10.0
        self._display_pts = 0.0
        self._total_pts = 0
        self._turn = 1
        self._streak = 0
        self._next_gold = 3
        
        self._time = 0.0
        self._last_tick = pygame.time.get_ticks()
        self._flashes = {}

    def sync(self, player_index: int = 0) -> None:
        """GameState'ten güncel engine verilerini çek ve DCI state'ini güncelle."""
        try:
            from v2.core.game_state import GameState
            gs = GameState.get()
            nh, ng = gs.get_hp(player_index), gs.get_gold(player_index)
            
            # Değişim takibi (DCI Feedback)
            if nh < self._hp: self._trigger_flash("hp", (255, 50, 50))
            if ng > self._gold: self._trigger_flash("gold", (255, 210, 60))
            if ng < self._gold: self._trigger_flash("gold", (220, 60, 60))

            self._hp, self._gold = nh, ng
            self._streak, self._total_pts, self._turn = gs.get_win_streak(player_index), gs.get_total_pts(player_index), gs.get_turn()
            
            from v2.ui.income_preview import IncomePreview
            self._next_gold = IncomePreview._compute(self._gold, self._hp, self._streak, gs.get_interest_multiplier(player_index))["total"]
        except: 
            pass

    def _trigger_flash(self, key: str, color: tuple):
        """DCI paneline geçici bir ışık patlaması (feedback) ekler."""
        self._flashes[key] = [list(color), 1.0] # 1.0 sn ömür

    def update(self, dt_ms: float):
        dt = dt_ms / 1000.0
        self._time += dt
        
        # Flash sönümleme
        for k in list(self._flashes):
            self._flashes[k][1] -= dt * 3.0 # Hızlı sönüm
            if self._flashes[k][1] <= 0: del self._flashes[k]
        
        # Kinematik Rolling Numbers (Yaylı animasyon)
        # pytweening.easeInOutQuad etkisini lerp hızına yedirerek daha akışkan bir his veriyoruz
        # 🧪 [NEW] Hayalet Bar Takibi (Yavaş süzülme)
        self._display_hp += (self._hp - self._display_hp) * 15 * dt
        self._ghost_hp += (self._display_hp - self._ghost_hp) * 3 * dt
        
        self._display_gold += (self._gold - self._display_gold) * 12 * dt
        self._display_pts += (self._total_pts - self._display_pts) * 10 * dt
        
        # 🧪 [NEW] Kritik HP Titreme Efekti (Tactical Glitch)
        self._hp_shake_x = 0
        if self._display_hp < 30:
            # Can azaldıkça titreme şiddeti artar (1px -> 3px)
            intensity = 1.0 + (30 - self._display_hp) / 10.0
            # pytweening.easeInOutSine yerine doğrudan hızlı sinüs osilasyonu kullanıyoruz
            # ancak şiddeti yumuşatmak için pytweening mantığıyla bir progress çarpanı ekleyebiliriz
            self._hp_shake_x = math.sin(self._time * 25) * intensity

    def render(self, surface: pygame.Surface):
        now = pygame.time.get_ticks()
        self.update(now - self._last_tick)
        self._last_tick = now

        # 1. Ana DCI Konteyner (Angled Tactical Plate)
        # Minimap ile aynı dilde olması için köşeleri kırılmış octagon yapısı
        panel_surf = pygame.Surface(self.inner_rect.size, pygame.SRCALPHA)
        w, h = self.inner_rect.size
        cut  = 12 # Köşe kesme payı
        points = [
            (cut, 0), (w - cut, 0), (w, cut), 
            (w, h - cut), (w - cut, h), (cut, h), 
            (0, h - cut), (0, cut)
        ]
        
        # Arka Plan (Void)
        pygame.draw.polygon(panel_surf, self._C_VOID_BG, points)
        
        # Kenarlık (Static)
        pygame.draw.polygon(panel_surf, (42, 58, 92, 255), points, width=2)
        
        # 2. Holographic Pulse (Minimap ile senkronize ışıma)
        pulse = math.sin(self._time * 3) * 30 + 30
        pygame.draw.polygon(panel_surf, (100, 150, 255, int(pulse)), points, width=3)

        # 3. Dynamic Scanline
        scan_y = int((self._time * 30) % self.inner_rect.h)
        # Scanline'ın polygon dışına taşmaması için maske kullanmak yerine basit padding verelim
        pygame.draw.line(panel_surf, self._C_SCANLINE, (cut, scan_y), (self.inner_rect.w - cut, scan_y), 1)

        # ── Element Çizimleri ──────────────────────────────────────────
        self._render_header(panel_surf)
        self._render_hp_cell(panel_surf)
        self._render_economy_row(panel_surf)
        self._render_pts_footer(panel_surf)

        # Nihai blit
        surface.blit(panel_surf, self.inner_rect.topleft)

    def _render_header(self, surf):
        # "SYSTEM.HUB" ve Döngü Sayısı
        font_cache.render_text(surf, "SYSTEM.HUB", font_cache.bold(10), self._C_TITLE, pygame.Rect(6, 6, 120, 15))
        font_cache.render_text(surf, f"CYCLE: {self._turn}", font_cache.mono(10), (140, 160, 200), pygame.Rect(surf.get_width()-80, 6, 75, 15), align="right")
        pygame.draw.line(surf, (40, 50, 80), (6, 22), (surf.get_width()-6, 22), 1)

    def _render_hp_cell(self, surf):
        # HP Bar - DCI Tactical Energy Cells
        r = self.hp_rect.copy() # Orijinal rect'i bozma (titreme için kopya)
        r.x += getattr(self, "_hp_shake_x", 0)
        
        pygame.draw.rect(surf, (15, 18, 28), r, border_radius=4)
        
        # 🧪 [ICON] Heart (Can) - Sol tarafa sabit yerleşim (Her zaman Kırmızı)
        icon_x = r.x + 8
        icon_y = r.y + (r.h - 14) // 2
        ratio = max(0.0, min(1.0, self._display_hp / self._MAX_HP))
        ratio_ghost = max(0.0, min(1.0, self._ghost_hp / self._MAX_HP))
        
        hp_col = Colors.HP_FULL if ratio > 0.3 else (255, 80, 80)
        ghost_col = (180, 60, 40) # Hasar izi rengi (Koyu Kırmızı/Turuncu)
        
        font_cache.render_icon(surf, "HEART", 14, (255, 60, 60), (icon_x, icon_y), shadow=True)

        # Hex Hücreleri - İkonun yanından başlar (DCI Full Array: 18 adet)
        n_cells = 18
        start_x = r.x + 32
        
        # Hex boyutu (Tam orantılı dizilim)
        radius = 5.7
        hex_step = 11.0 
        
        for i in range(n_cells):
            cx = start_x + i * hex_step
            cy = r.centery
            
            threshold = (i + 1) / n_cells
            is_active = ratio >= threshold - 0.025 # 18 hücre için daha hassas eşik
            is_ghost  = ratio_ghost >= threshold - 0.025
            
            pts = []
            for ang_deg in range(30, 390, 60):
                ang_rad = math.radians(ang_deg)
                pts.append((cx + radius * math.cos(ang_rad), 
                            cy + radius * math.sin(ang_rad)))
            
            if is_active:
                pygame.draw.polygon(surf, hp_col, pts)
                # Rim Light
                pygame.draw.line(surf, (255, 255, 255, 120), pts[4], pts[5], 1)
            elif is_ghost:
                # 🧪 [GHOST] Hasar izi çizerken daha sönük ama belirgin bir renk
                pygame.draw.polygon(surf, ghost_col, pts)
                # Hafif bir kenarlık ekleyelim ki hücre formu belli olsun
                pygame.draw.polygon(surf, (220, 100, 80, 100), pts, 1)
            else:
                pygame.draw.polygon(surf, (35, 40, 55), pts, width=1)

        # HP Metni - En sağa hizalı
        txt = f"{int(self._display_hp)}/{self._MAX_HP}"
        font_cache.render_text(surf, txt, font_cache.bold(11), (220, 230, 255), 
                                pygame.Rect(r.right - 80, r.y, 75, r.h), align="right", v_align="center", shadow=True)

    def _render_economy_row(self, surf):
        # Gold Box (Carbon Refit)
        g_r = self.gold_rect
        pygame.draw.rect(surf, (25, 22, 12), g_r, border_radius=6)
        pygame.draw.rect(surf, (140, 110, 20, 150), g_r, width=1, border_radius=6)
        
        # Feedback Flash
        if "gold" in self._flashes:
            col, timer = self._flashes["gold"]
            pygame.draw.rect(surf, (*col, int(120 * timer)), g_r, width=2, border_radius=6)

        # 🧪 [ICON] Gold (Para)
        font_cache.render_icon(surf, "GOLD", 14, Colors.GOLD_TEXT, (g_r.x + 8, g_r.y + 6), shadow=True)
        
        font_cache.render_text(surf, f"{int(self._display_gold)}", font_cache.bold(13), Colors.GOLD_TEXT, g_r, align="center", v_align="center")

        # Streak Box (Status Indicator)
        s_r = self.streak_rect
        s_col = (80, 200, 100) if self._streak > 0 else (200, 70, 70) if self._streak < 0 else (100, 110, 130)
        pygame.draw.rect(surf, (15, 20, 30), s_r, border_radius=6)
        pygame.draw.rect(surf, (*s_col, 100), s_r, width=1, border_radius=6)
        
        # 🧪 [ICON] Streak Indicator
        streak_icon = "FIRE" if self._streak > 0 else "BOLT" if self._streak < 0 else "GEAR"
        font_cache.render_icon(surf, streak_icon, 12, s_col, (s_r.x + 8, s_r.y + 8), shadow=True)
        
        label = f"{'+' if self._streak>0 else ''}{self._streak} {'WIN' if self._streak>=0 else 'LOSS'}"
        font_cache.render_text(surf, label, font_cache.bold(9), s_col, s_r, align="center", v_align="center")

    def _render_pts_footer(self, surf):
        # Strateji Skoru (Digital Counter)
        p_r = self.pts_rect
        pygame.draw.rect(surf, (18, 22, 35), p_r, border_radius=4)
        # 🧪 [ICON] Strategy (Gear)
        font_cache.render_icon(surf, "GEAR", 10, (180, 200, 255), (p_r.x + 6, p_r.y + 5))
        
        font_cache.render_text(surf, f"STRAT_SCORE: {int(self._display_pts)}", font_cache.mono(10), (180, 200, 255), p_r, align="center", v_align="center")
        
        # Projection (Income)
        i_r = self.income_rect
        font_cache.render_text(surf, f"PROJECTION: +{self._next_gold}G", font_cache.mono(9), (140, 180, 100), i_r, align="right")
