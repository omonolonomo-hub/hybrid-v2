import logging
import pygame
import math
from dataclasses import dataclass
from v2.constants import Layout, Colors
from v2.ui import font_cache

logger = logging.getLogger(__name__)


@dataclass
class PlayerHubData:
    """PlayerHub'a dışardan itilen veri sözleşmesi.
    Panel bu nesneyi alır, GameState'e hiç dokunmaz.
    """
    hp:          int
    gold:        int
    win_streak:  int
    total_pts:   int
    turn:        int
    next_gold:   int
    board_used:  int = 0


def build_hub_data(state) -> PlayerHubData:
    """Pure function: state → PlayerHubData dönüşümü.
    
    GameState'den PlayerHub için gerekli verileri çıkarır.
    Hiç state tutmaz, sadece dönüşüm yapar.
    
    Args:
        state: PublicState snapshot (active_player, turn, vb. içerir)
        
    Returns:
        PlayerHubData: PlayerHub paneli için veri sözleşmesi
    """
    hud = state.active_player.hud
    return PlayerHubData(
        hp=hud.hp,
        gold=hud.gold,
        win_streak=hud.win_streak,
        total_pts=hud.total_pts,
        turn=state.turn,
        next_gold=hud.next_gold,
        board_used=len(state.active_player.board_cards),
    )


class PlayerHub:
    """SOL PANEL: DCI-REFIT (Digital Combat Interface) Oyuncu Merkezi."""

    _MAX_HP: int      = 150
    # DCI Renk Paleti (Karbon-Mor Tonları)
    _C_VOID_BG   = (16, 13, 20, 255)  # Koyu mor-karbon base
    _C_RIM_TOP   = (140, 120, 160, 180)  # Mor-gri cam parlaması
    _C_SCANLINE  = (255, 255, 255, 8)
    _C_TITLE     = (160, 140, 200)  # Mor-gri title
    _C_GOLD_GLOW = (255, 180, 50, 40)
    _C_HP_GLOW   = (255, 50, 50, 30)

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, Layout.SIDEBAR_LEFT_W, Layout.PLAYER_HUB_H)
        # İç panel rect (padding ile - 20px Kırpıldı)
        self.inner_rect = pygame.Rect(10, 8, Layout.SIDEBAR_LEFT_W - 20, 114)
        
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
        self._board_used = 0
        
        self._time = 0.0
        self._flashes = {}

        # Önbelleğe alınmış yüzey
        self._panel_surf = pygame.Surface(self.inner_rect.size, pygame.SRCALPHA)
        from v2.ui.ui_utils import UIUtils
        self._bg_surf = UIUtils.create_gradient_panel(
            self.inner_rect.w, self.inner_rect.h, 
            (28, 24, 35, 255), (16, 13, 20, 255),  # Karbon-mor gradient
            border_radius=8, border_color=(50, 41, 61, 180)  # Karbon-mor border
        )

    def update_view(self, data: PlayerHubData) -> None:
        """ShopScene tarafından çağrılır. Panel GameState'e dokunmaz.
        Değişim takibi ve DCI feedback bu metod içinde kalır.
        """
        if data.hp < self._hp:
            self._trigger_flash("hp", (255, 50, 50))
        if data.gold > self._gold:
            self._trigger_flash("gold", (255, 210, 60))
        if data.gold < self._gold:
            self._trigger_flash("gold", (220, 60, 60))

        self._hp        = data.hp
        self._gold      = data.gold
        self._streak    = data.win_streak
        self._total_pts = data.total_pts
        self._turn      = data.turn
        self._next_gold = data.next_gold
        self._board_used = data.board_used

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
        self._panel_surf.fill((0, 0, 0, 0))
        panel_surf = self._panel_surf

        # 1. Synergy Stili Gradient Arka Plan
        panel_surf.blit(self._bg_surf, (0, 0))

        # ── Element Çizimleri ──────────────────────────────────────────
        self._render_header(panel_surf)
        self._render_hp_cell(panel_surf)
        self._render_economy_row(panel_surf)
        self._render_pts_footer(panel_surf)

        # Nihai blit
        surface.blit(panel_surf, self.inner_rect.topleft)

    def _render_header(self, surf):
        # Synergy stili ortalanmış "SYSTEM HUB" başlığı (Mor-gri ton)
        font_cache.render_text(surf, "SYSTEM HUB", font_cache.bold(10), (160, 140, 200), pygame.Rect(0, 4, surf.get_width(), 14), align="center")
        # Döngü Sayısı (Sağa dayalı ufak bilgi - Mor-gri ton)
        font_cache.render_text(surf, f"CYCLE {self._turn}", font_cache.mono(9), (180, 170, 200), pygame.Rect(0, 4, surf.get_width()-10, 14), align="right")

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
        font_cache.render_text(surf, txt, font_cache.bold(11), (200, 190, 220), 
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
        font_cache.render_icon(surf, "GEAR", 10, (160, 140, 200), (p_r.x + 6, p_r.y + 5))
        
        font_cache.render_text(surf, f"STRAT_SCORE: {int(self._display_pts)}", font_cache.mono(10), (160, 140, 200), p_r, align="center", v_align="center")
