"""
screens/game_over.py
--------------------
Oyun sonu ekranı. Yeniden oyna veya çıkış.
"""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from core.game_state import GameState

C_BG    = (10, 11, 18)
C_CYAN  = (0, 242, 255)
C_GOLD  = (255, 200, 50)
C_RED   = (220, 60, 60)
C_TEXT  = (220, 228, 248)
C_DIM   = (100, 110, 140)


class GameOverScreen:
    def __init__(self, state: GameState, manager: pygame_gui.UIManager):
        self.state   = state
        self.manager = manager
        self.W, self.H = manager.get_root_container().get_size()
        self._build_ui()

    def _build_ui(self):
        W, H = self.W, self.H
        cx = W // 2
        self.btn_restart = UIButton(
            relative_rect=pygame.Rect(cx - 120, H // 2 + 60, 240, 50),
            text="🔄  YENİDEN OYNA",
            manager=self.manager,
        )
        self.btn_quit = UIButton(
            relative_rect=pygame.Rect(cx - 120, H // 2 + 124, 240, 50),
            text="✕  ÇIKIŞ",
            manager=self.manager,
        )

    def destroy(self):
        self.btn_restart.kill()
        self.btn_quit.kill()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_restart:
                return "restart"
            if event.ui_element == self.btn_quit:
                return "quit"
        return None

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        W, H = self.W, self.H
        screen.fill(C_BG)

        won = self.state.hp > 0
        title_col  = C_CYAN if won else C_RED
        title_text = "ZAFER!" if won else "OYUN BİTTİ"

        title_font = pygame.font.SysFont("segoeui", 64, bold=True)
        sub_font   = pygame.font.SysFont("segoeui", 20)
        stat_font  = pygame.font.SysFont("segoeui", 16)

        ts = title_font.render(title_text, True, title_col)
        screen.blit(ts, (W // 2 - ts.get_width() // 2, H // 2 - 130))

        sub = "Hayatta kaldın! Tüm turları atlattın." if won else "HP tükendi, oyun bitti."
        ss = sub_font.render(sub, True, C_TEXT)
        screen.blit(ss, (W // 2 - ss.get_width() // 2, H // 2 - 56))

        stats = [
            f"Son HP      : {self.state.hp}",
            f"Kalan Altın : {self.state.gold}",
            f"Tur         : {self.state.round} / {self.state.max_rounds}",
            f"Strateji    : {self.state.player_strategy}",
        ]
        for i, s in enumerate(stats):
            st = stat_font.render(s, True, C_GOLD)
            screen.blit(st, (W // 2 - st.get_width() // 2, H // 2 - 8 + i * 24))
