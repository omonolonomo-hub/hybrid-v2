"""
screens/lobby.py
----------------
Oyun öncesi Lobby ekranı.
Strateji seçimi + Başlat butonu.
Tamamen pygame_gui üzerine kurulu, sıfır el yapımı buton kodu.
"""

import math
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UIPanel, UIDropDownMenu

from core.game_state import GameState

# ─── Renk paleti ─────────────────────────────────────────────────────────────
C_BG      = (10, 11, 18)
C_PANEL   = (18, 20, 32)
C_ACCENT  = (0, 242, 255)
C_PINK    = (255, 0, 255)
C_GOLD    = (255, 200, 50)
C_TEXT    = (220, 225, 240)
C_DIM     = (100, 105, 135)

STRATEGIES = [
    "random", "warrior", "builder", "evolver",
    "economist", "balancer", "rare_hunter", "tempo"
]

STRAT_DESC = {
    "random":      "Rastgele kaos — tahmin edilemez.",
    "warrior":     "En güçlü birimleri önce alır.",
    "builder":     "Kombo ve sinerji ağlarını kovalar.",
    "evolver":     "Kopyalar toplayarak evrim ateşler.",
    "economist":   "Altın ve faizi korur.",
    "balancer":    "Grup kapsamını dengede tutar.",
    "rare_hunter": "Yüksek rarity kartları ister.",
    "tempo":       "Tahta gücünü erken stabilize eder.",
}


class LobbyScreen:
    """
    Lobby ekranı.
    handle_event(event) → str|None  ("shop" geçmek için "shop" döner)
    update(dt)
    draw(screen)
    """

    def __init__(self, state: GameState, manager: pygame_gui.UIManager):
        self.state   = state
        self.manager = manager
        self.W, self.H = manager.get_root_container().get_size()

        self._anim_t = 0.0
        self._build_ui()

    def _build_ui(self):
        W, H = self.W, self.H

        # ── Strateji dropdown ──
        dd_w, dd_h = 280, 46
        dd_x = W // 2 - dd_w // 2
        dd_y = H // 2 - 60
        self.dd_strategy = UIDropDownMenu(
            options_list=STRATEGIES,
            starting_option=self.state.player_strategy,
            relative_rect=pygame.Rect(dd_x, dd_y, dd_w, dd_h),
            manager=self.manager,
        )

        # ── Başlat butonu ──
        btn_w, btn_h = 220, 56
        self.btn_start = UIButton(
            relative_rect=pygame.Rect(W // 2 - btn_w // 2, dd_y + dd_h + 24, btn_w, btn_h),
            text="▶  OYUNU BAŞLAT",
            manager=self.manager,
        )

        # ── Açıklama etiketi ──
        self.lbl_desc = UILabel(
            relative_rect=pygame.Rect(W // 2 - 260, dd_y - 50, 520, 38),
            text=STRAT_DESC.get(self.state.player_strategy, ""),
            manager=self.manager,
        )

    def destroy(self):
        """Ekrandan çıkarken UI elemanlarını temizle."""
        self.dd_strategy.kill()
        self.btn_start.kill()
        self.lbl_desc.kill()

    def handle_event(self, event: pygame.event.Event):
        """
        None → devam et
        "shop" → lobby bitti, shop'a geç
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_start:
                self.state.player_strategy = self.dd_strategy.selected_option
                self.state.current_screen  = "shop"
                return "shop"

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.dd_strategy:
                sel = event.text
                self.state.player_strategy = sel
                self.lbl_desc.set_text(STRAT_DESC.get(sel, ""))

        return None

    def update(self, dt: float):
        self.state.tick(dt)
        self._anim_t += dt

    def draw(self, screen: pygame.Surface):
        W, H = self.W, self.H
        screen.fill(C_BG)

        # ── Animasyonlu arka plan ızgarası ──
        grid_alpha = pygame.Surface((W, H), pygame.SRCALPHA)
        spacing = 48
        shift = (self._anim_t * 12) % spacing
        for x in range(0, W + spacing, spacing):
            pygame.draw.line(grid_alpha, (30, 40, 70, 60), (x - shift, 0), (x - shift, H))
        for y in range(0, H + spacing, spacing):
            pygame.draw.line(grid_alpha, (30, 40, 70, 60), (0, y - shift), (W, y - shift))
        screen.blit(grid_alpha, (0, 0))

        # ── Başlık ──
        pulse = 0.5 + 0.5 * math.sin(self._anim_t * 1.8)
        title_col = (
            int(C_ACCENT[0] * pulse + 180 * (1 - pulse)),
            int(C_ACCENT[1] * pulse + 180 * (1 - pulse)),
            int(C_ACCENT[2] * pulse + 180 * (1 - pulse)),
        )
        title_font = pygame.font.SysFont("segoeui", 52, bold=True)
        sub_font   = pygame.font.SysFont("segoeui", 18)

        t_surf = title_font.render("HYBRID", True, title_col)
        screen.blit(t_surf, (W // 2 - t_surf.get_width() // 2, H // 4 - 20))

        s_surf = sub_font.render("Strateji Kartları Autochess", True, C_DIM)
        screen.blit(s_surf, (W // 2 - s_surf.get_width() // 2, H // 4 + 44))

        # ── Strateji başlık etiketi ──
        lbl_font = pygame.font.SysFont("segoeui", 14)
        lbl_s = lbl_font.render("STRATEJİ SEÇ", True, C_DIM)
        screen.blit(lbl_s, (W // 2 - lbl_s.get_width() // 2, self.H // 2 - 92))

        # ── Tur / altın bilgisi ──
        info_font = pygame.font.SysFont("segoeui", 15)
        info_s = info_font.render(
            f"Tur: {self.state.round}/{self.state.max_rounds}   "
            f"Altın: {self.state.gold}   HP: {self.state.hp}",
            True, C_GOLD
        )
        screen.blit(info_s, (W // 2 - info_s.get_width() // 2, H - 40))

        # ── Durum mesajı ──
        if self.state.message:
            msg_font = pygame.font.SysFont("segoeui", 16)
            msg_s = msg_font.render(self.state.message, True, (255, 80, 80))
            screen.blit(msg_s, (W // 2 - msg_s.get_width() // 2, H - 70))
