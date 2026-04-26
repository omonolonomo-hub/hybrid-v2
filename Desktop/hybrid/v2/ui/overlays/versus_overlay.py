import pygame
from v2.constants import Screen, Layout, Colors
from v2.ui import font_cache

class VersusOverlay:
    def __init__(self, player_name: str, opp_name: str, duration_ms: int = 3000):
        self.player_name = player_name
        self.opp_name = opp_name
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        self.is_finished = False

        self.overlay_surf = pygame.Surface((Screen.W, Screen.H), pygame.SRCALPHA)
        self.overlay_surf.fill((10, 10, 15, 230))  # Koyu yarı saydam arkaplan

        self.center_rect = pygame.Rect(0, 0, 800, 200)
        self.center_rect.center = (Screen.W // 2, Screen.H // 2)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.is_finished:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_finished = True
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.is_finished = True
            return True
        return False

    def update(self, dt: float):
        if self.is_finished:
            return
        
        self.elapsed_ms += dt
        if self.elapsed_ms >= self.duration_ms:
            self.is_finished = True

    def render(self, surface: pygame.Surface):
        # 1. Arkaplanı karart
        surface.blit(self.overlay_surf, (0, 0))

        # 2. Yazılar
        font_large = font_cache.bold(64)
        font_small = font_cache.bold(32)

        # Player (Sol)
        p1_rect = pygame.Rect(self.center_rect.x, self.center_rect.y, 300, 200)
        font_cache.render_text(
            surface, self.player_name, font_small, Colors.MIND,
            p1_rect, align="right", v_align="center"
        )

        # VS (Orta)
        vs_rect = pygame.Rect(self.center_rect.x + 300, self.center_rect.y, 200, 200)
        font_cache.render_text(
            surface, "VS", font_large, Colors.GOLD_TEXT,
            vs_rect, align="center", v_align="center"
        )

        # Opponent (Sağ)
        p2_rect = pygame.Rect(self.center_rect.x + 500, self.center_rect.y, 300, 200)
        font_cache.render_text(
            surface, self.opp_name, font_small, Colors.EXISTENCE,
            p2_rect, align="left", v_align="center"
        )
