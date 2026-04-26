"""Cyber-synthwave lobby scene for choosing AI strategies before a run."""

import math
from typing import List
import pygame

from core.scene import Scene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState

try:
    from engine_core.constants import STRATEGIES
except ImportError:
    from ..engine_core.constants import STRATEGIES

try:
    from ui.renderer import STRATEGY_COLORS
except ImportError:
    try:
        from ..ui.renderer import STRATEGY_COLORS
    except ImportError:
        STRATEGY_COLORS = {}


# Color palette
C = {
    "bg": (10, 11, 18),
    "panel": (18, 20, 32),
    "panel2": (26, 29, 46),
    "border": (44, 48, 72),
    "border_hi": (80, 100, 160),
    "accent": (0, 242, 255),
    "pink": (255, 0, 255),
    "gold": (255, 200, 50),
    "text": (220, 225, 240),
    "text_dim": (100, 105, 135),
    "text_hi": (255, 255, 255),
    "ok": (60, 210, 110),
}

STRAT_LIST: List[str] = list(STRATEGIES)

STRAT_DESC = {
    "random": "Unscripted chaos.",
    "warrior": "Buys the strongest units first.",
    "builder": "Chases combos and synergy webs.",
    "evolver": "Stacks copies for evolution spikes.",
    "economist": "Preserves gold and interest.",
    "balancer": "Keeps group coverage even.",
    "rare_hunter": "Pushes toward high rarity finds.",
    "tempo": "Stabilizes board power early.",
}


def _rnd(surf, color, rect, radius, width=0):
    """Draw rounded rectangle."""
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def _lerp(a, b, t):
    """Linear interpolation between two colors."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class LobbyScene(Scene):
    """Lobby scene for strategy selection.
    
    Refactored from LobbyScreen to use Scene architecture:
    - No while loop (controlled by SceneManager)
    - Uses InputState for intent-based input
    - Stores UI state in self.ui_state (THROWAWAY)
    - Stores game state in self.core_game_state (SAVEABLE)
    """
    
    N_PLAYERS = 8
    COLS = 2
    SLOT_W = 440
    SLOT_H = 108
    GAP_X = 40
    GAP_Y = 18
    BTN_W = 260
    BTN_H = 58

    def __init__(self, core_game_state: CoreGameState):
        """Initialize lobby scene.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes
        """
        super().__init__(core_game_state)
        self._init_fonts()
        
        # Screen dimensions (will be set in on_enter when we have access to screen)
        self.W = 1600
        self.H = 960

    def _init_fonts(self):
        """Initialize pygame fonts."""
        def f(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                return pygame.font.SysFont("segoeui", size, bold=bold)

        self.f_hero = f("bahnschrift", 54, bold=True)
        self.f_title = f("bahnschrift", 24, bold=True)
        self.f_sub = f("segoeui", 15)
        self.f_slot = f("segoeui", 15, bold=True)
        self.f_desc = f("segoeui", 13)
        self.f_btn = f("segoeui", 17, bold=True)
        self.f_hint = f("segoeui", 12)

    def on_enter(self) -> None:
        """Called when scene becomes active. Create fresh UIState."""
        # Create fresh THROWAWAY state
        self.ui_state = UIState()
        
        # Initialize lobby-specific UI state
        self.ui_state.strategies = [
            STRAT_LIST[i % len(STRAT_LIST)] for i in range(self.N_PLAYERS)
        ]
        self.ui_state.hover_left = [False] * self.N_PLAYERS
        self.ui_state.hover_right = [False] * self.N_PLAYERS
        self.ui_state.hover_start = False
        self.ui_state.hover_rand = False
        self.ui_state.flash = [0] * self.N_PLAYERS
        self.ui_state.time = 0.0

    def on_exit(self) -> None:
        """Called when scene is deactivated. Discard UIState."""
        # Explicitly discard THROWAWAY state
        self.ui_state = None

    def handle_input(self, input_state: InputState) -> None:
        """Process input intents for lobby scene.
        
        Args:
            input_state: Intent-based input abstraction (not raw events)
        """
        # Update hover state based on mouse position
        self._update_hover(input_state.mouse_pos)
        
        # Handle confirm intent (Enter key or left click on start button)
        if input_state.intent_confirm:
            rand_r, start_r = self._btn_rects()
            if self.ui_state.hover_start or input_state.was_key_pressed_this_frame(pygame.K_RETURN):
                # T1.10: Transition to game_loop (not shop) with selected strategies
                # GameLoopScene will build the game and initialize CoreGameState
                self.scene_manager.request_transition("game_loop", strategies=list(self.ui_state.strategies))
                return
        
        # Handle mouse clicks
        if input_state.mouse_clicked:
            self._handle_click(input_state.mouse_pos)

    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        Args:
            dt: Delta time in milliseconds since last frame
        """
        # Update time for animations
        self.ui_state.time += dt / 1000.0
        
        # Update flash effects (decay over time)
        for i in range(self.N_PLAYERS):
            if self.ui_state.flash[i] > 0:
                self.ui_state.flash[i] = max(0, self.ui_state.flash[i] - dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Render lobby scene to screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        # Update screen dimensions if needed
        self.W, self.H = screen.get_size()
        
        # Draw all lobby elements
        screen.fill(C["bg"])
        self._draw_grid_bg(screen)
        self._draw_header(screen)
        
        for i in range(self.N_PLAYERS):
            self._draw_slot(screen, i)
        
        self._draw_buttons(screen)
        self._draw_hint(screen)

    # ========== Helper Methods (UI Logic) ==========

    def _grid_origin(self):
        """Calculate grid origin for centered layout."""
        rows = math.ceil(self.N_PLAYERS / self.COLS)
        total_w = self.COLS * self.SLOT_W + (self.COLS - 1) * self.GAP_X
        total_h = rows * self.SLOT_H + (rows - 1) * self.GAP_Y
        ox = (self.W - total_w) // 2
        oy = (self.H - total_h) // 2 + 20
        return ox, oy

    def _slot_rect(self, idx: int) -> pygame.Rect:
        """Get rect for player slot at index."""
        ox, oy = self._grid_origin()
        col = idx % self.COLS
        row = idx // self.COLS
        x = ox + col * (self.SLOT_W + self.GAP_X)
        y = oy + row * (self.SLOT_H + self.GAP_Y)
        return pygame.Rect(x, y, self.SLOT_W, self.SLOT_H)

    def _arrow_rects(self, slot: pygame.Rect):
        """Get left/right arrow rects for a slot."""
        aw, ah = 32, 32
        left = pygame.Rect(slot.x + 56, slot.centery - ah // 2, aw, ah)
        right = pygame.Rect(slot.right - 56 - aw, slot.centery - ah // 2, aw, ah)
        return left, right

    def _btn_rects(self):
        """Get button rects for randomize and start buttons."""
        ox, oy = self._grid_origin()
        rows = math.ceil(self.N_PLAYERS / self.COLS)
        grid_bottom = oy + rows * self.SLOT_H + (rows - 1) * self.GAP_Y
        by = grid_bottom + 32
        cx = self.W // 2
        rand_r = pygame.Rect(cx - self.BTN_W - 16, by, self.BTN_W, self.BTN_H)
        start_r = pygame.Rect(cx + 16, by, self.BTN_W, self.BTN_H)
        return rand_r, start_r

    def _update_hover(self, mouse):
        """Update hover states based on mouse position."""
        rand_r, start_r = self._btn_rects()
        self.ui_state.hover_start = start_r.collidepoint(mouse)
        self.ui_state.hover_rand = rand_r.collidepoint(mouse)
        
        for i in range(self.N_PLAYERS):
            sl = self._slot_rect(i)
            lr, rr = self._arrow_rects(sl)
            self.ui_state.hover_left[i] = lr.collidepoint(mouse)
            self.ui_state.hover_right[i] = rr.collidepoint(mouse)

    def _handle_click(self, pos):
        """Handle mouse click at position."""
        import random as rnd
        
        rand_r, start_r = self._btn_rects()
        
        # Start button - T1.10: Transition to game_loop (not shop)
        if start_r.collidepoint(pos):
            self.scene_manager.request_transition("game_loop", strategies=list(self.ui_state.strategies))
            return
        
        # Randomize button
        if rand_r.collidepoint(pos):
            pool = STRAT_LIST * 2
            self.ui_state.strategies = rnd.sample(pool, self.N_PLAYERS)
            return
        
        # Arrow buttons
        for i in range(self.N_PLAYERS):
            sl = self._slot_rect(i)
            lr, rr = self._arrow_rects(sl)
            
            if lr.collidepoint(pos):
                idx = STRAT_LIST.index(self.ui_state.strategies[i])
                self.ui_state.strategies[i] = STRAT_LIST[(idx - 1) % len(STRAT_LIST)]
                self.ui_state.flash[i] = 250
                return
            
            if rr.collidepoint(pos):
                idx = STRAT_LIST.index(self.ui_state.strategies[i])
                self.ui_state.strategies[i] = STRAT_LIST[(idx + 1) % len(STRAT_LIST)]
                self.ui_state.flash[i] = 250
                return

    # ========== Drawing Methods ==========

    def _draw_grid_bg(self, surf):
        """Draw cyberpunk grid background."""
        horizon_y = 180
        center_x = self.W // 2

        # Gradient background
        gradient = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(self.H):
            t = y / max(1, self.H - 1)
            col = _lerp((8, 8, 14), (14, 18, 34), t)
            pygame.draw.line(gradient, (*col, 255), (0, y), (self.W, y))
        surf.blit(gradient, (0, 0))

        # Grid lines
        grid = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for x in range(0, self.W, 80):
            pygame.draw.line(grid, (18, 26, 50, 65), (x, 0), (x, self.H), 1)
        for y in range(0, self.H, 80):
            pygame.draw.line(grid, (18, 26, 50, 55), (0, y), (self.W, y), 1)

        # Perspective lines
        for lane in range(-12, 13):
            start_x = center_x + lane * 92
            end_x = center_x + lane * 450
            pygame.draw.line(grid, (0, 180, 255, 48), (start_x, horizon_y), (end_x, self.H), 1)

        # Horizontal scan lines
        for i in range(18):
            y = self.H - int((i ** 1.78) * 7)
            alpha = max(10, 170 - i * 9)
            pygame.draw.line(grid, (255, 0, 255, alpha), (0, y), (self.W, y), 1)

        surf.blit(grid, (0, 0))

        # Scanline effect
        scan = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, 4):
            pygame.draw.line(scan, (0, 0, 0, 22), (0, y), (self.W, y), 1)
        surf.blit(scan, (0, 0))

    def _draw_header(self, surf):
        """Draw header with title and subtitle."""
        panel = pygame.Surface((self.W, 128), pygame.SRCALPHA)
        panel.fill((8, 10, 18, 170))
        surf.blit(panel, (0, 0))
        pygame.draw.line(surf, C["accent"], (0, 120), (self.W, 120), 1)

        title_y = 18 + int(math.sin(self.ui_state.time * 2.2) * 4)
        shadow = self.f_hero.render("CORE_OS : HYBRID", True, (0, 80, 90))
        hero = self.f_hero.render("CORE_OS : HYBRID", True, C["text_hi"])
        surf.blit(shadow, (self.W // 2 - shadow.get_width() // 2 + 3, title_y + 3))
        surf.blit(hero, (self.W // 2 - hero.get_width() // 2, title_y))

        sub_title = self.f_title.render("NEURAL LOBBY", True, C["accent"])
        surf.blit(sub_title, (self.W // 2 - sub_title.get_width() // 2, 78))

        desc = self.f_sub.render(
            "Configure every pilot, then initialize the simulation.",
            True,
            C["text_dim"],
        )
        surf.blit(desc, (self.W // 2 - desc.get_width() // 2, 102))

    def _draw_slot(self, surf, idx: int):
        """Draw player strategy slot."""
        strat = self.ui_state.strategies[idx]
        sl = self._slot_rect(idx)
        t = self.ui_state.flash[idx] / 250.0
        col = STRATEGY_COLORS.get(strat, (120, 120, 160))

        # Glow effect when flashing
        if t > 0:
            glow = pygame.Surface((sl.width + 22, sl.height + 22), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*col, 34), glow.get_rect(), border_radius=16, width=2)
            surf.blit(glow, (sl.x - 11, sl.y - 11), special_flags=pygame.BLEND_ADD)

        # Slot background
        bg = _lerp(C["panel"], col, 0.18 * t) if t > 0 else (*C["panel"],)
        _rnd(surf, bg, sl, 10)
        _rnd(surf, col if t > 0 else C["border"], sl, 10, 2)

        # Side accent bar
        pygame.draw.rect(surf, col, (sl.x, sl.y + 12, 4, sl.height - 24), border_radius=2)

        # Player label
        ps = self.f_slot.render(f"P{idx + 1}", True, C["text_hi"])
        surf.blit(ps, (sl.x + 12, sl.centery - ps.get_height() // 2))

        # Status indicator
        pygame.draw.circle(surf, col, (sl.x + 48, sl.centery), 8)
        pygame.draw.circle(surf, C["bg"], (sl.x + 48, sl.centery), 4)

        # Arrow buttons
        lr, rr = self._arrow_rects(sl)
        self._draw_arrow(surf, lr, "<", self.ui_state.hover_left[idx], col)
        self._draw_arrow(surf, rr, ">", self.ui_state.hover_right[idx], col)

        # Strategy name and description
        label_x = lr.right + 6
        label_w = rr.left - 6 - label_x
        ns = self.f_slot.render(strat.upper(), True, col)
        surf.blit(ns, (label_x + (label_w - ns.get_width()) // 2, sl.centery - ns.get_height() // 2 - 9))
        ds = self.f_desc.render(STRAT_DESC.get(strat, ""), True, C["text_dim"])
        surf.blit(ds, (label_x + (label_w - ds.get_width()) // 2, sl.centery + 5))

    def _draw_arrow(self, surf, rect, label, hovered, col):
        """Draw arrow button."""
        bg = _lerp(C["panel2"], col, 0.28) if hovered else C["panel2"]
        bc = col if hovered else C["border"]
        _rnd(surf, bg, rect, 6)
        _rnd(surf, bc, rect, 6, 2 if hovered else 1)
        s = self.f_btn.render(label, True, col if hovered else C["text_dim"])
        surf.blit(s, (rect.centerx - s.get_width() // 2, rect.centery - s.get_height() // 2))

    def _draw_cyber_button(self, surf, rect, label, hovered, text_color, glow_color):
        """Draw cyberpunk-styled button with glow effects."""
        draw_rect = rect.copy()
        
        # Hover animation
        if hovered:
            draw_rect.x += int(math.sin(self.ui_state.time * 36) * 2)
            glow = pygame.Surface((rect.width + 28, rect.height + 28), pygame.SRCALPHA)
            for inset in range(0, 10, 2):
                alpha = max(10, 42 - inset * 3)
                pygame.draw.rect(
                    glow,
                    (*glow_color, alpha),
                    pygame.Rect(14 - inset // 2, 14 - inset // 2, rect.width + inset, rect.height + inset),
                    border_radius=14,
                    width=2,
                )
            surf.blit(glow, (draw_rect.x - 14, draw_rect.y - 14), special_flags=pygame.BLEND_ADD)

        # Button background
        bg = _lerp(C["panel2"], glow_color, 0.16 if hovered else 0.08)
        _rnd(surf, bg, draw_rect, 12)
        _rnd(surf, glow_color if hovered else C["border_hi"], draw_rect, 12, 2)

        # Text with glitch effect
        glitch_x = int(math.sin(self.ui_state.time * 44) * 2) if hovered else 0
        text_shadow = self.f_btn.render(label, True, C["accent"])
        text_main = self.f_btn.render(label, True, text_color)
        surf.blit(
            text_shadow,
            (
                draw_rect.centerx - text_shadow.get_width() // 2 + glitch_x,
                draw_rect.centery - text_shadow.get_height() // 2 + 1,
            ),
        )
        surf.blit(
            text_main,
            (
                draw_rect.centerx - text_main.get_width() // 2,
                draw_rect.centery - text_main.get_height() // 2 - 1,
            ),
        )

    def _draw_buttons(self, surf):
        """Draw randomize and start buttons."""
        rand_r, start_r = self._btn_rects()
        self._draw_cyber_button(
            surf,
            rand_r,
            "REMIX LOBBY",
            self.ui_state.hover_rand,
            C["gold"],
            C["accent"],
        )
        self._draw_cyber_button(
            surf,
            start_r,
            "INITIALIZE  [ENTER]",
            self.ui_state.hover_start,
            C["pink"],
            C["accent"],
        )

    def _draw_hint(self, surf):
        """Draw hint text at bottom."""
        h = self.f_hint.render(
            "Use < > to swap strategies. REMIX LOBBY shuffles all. ENTER launches the match. ESC exits.",
            True,
            C["text_dim"],
        )
        surf.blit(h, (self.W // 2 - h.get_width() // 2, self.H - 26))
