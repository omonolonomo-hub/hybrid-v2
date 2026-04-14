"""
Game Over Scene

Displays winner announcement and final stats after game ends.
Provides restart and quit options.
"""

import sys
import pygame
from typing import Optional

from core.scene import Scene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState
from ui.hud_renderer import draw_game_over


class GameOverScene(Scene):
    """Game over scene for displaying winner and final stats.
    
    Responsibilities:
    - Display winner announcement using HUDRenderer
    - Show final stats (HP, wins, losses, total points, win streak)
    - Handle restart (R key or click) - transitions to lobby
    - Handle quit (ESC key or click) - exits game
    
    Requirements:
    - Req 10: Game Over Detection
    - Req 21: Game Restart Flow
    - Req 28: Visual Consistency
    """
    
    def __init__(self, core_game_state: CoreGameState, **kwargs):
        """Initialize game over scene.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes
            **kwargs: Additional arguments (winner, etc.)
        """
        super().__init__(core_game_state)
        
        # Extract winner from kwargs (passed from GameLoopScene)
        self.winner = kwargs.get('winner', None)
        
        # Initialize fonts
        self._init_fonts()
        
        # Button rects (will be calculated in draw)
        self.restart_rect = None
        self.quit_rect = None
        
        # Hover states
        self.hover_restart = False
        self.hover_quit = False
    
    def _init_fonts(self):
        """Initialize pygame fonts."""
        def f(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                return pygame.font.SysFont("segoeui", size, bold=bold)
        
        self.font_lg = f("bahnschrift", 48, bold=True)
        self.font_md = f("bahnschrift", 24, bold=True)
        self.font_sm = f("segoeui", 16)
    
    def on_enter(self) -> None:
        """Called when scene becomes active. Create fresh UIState."""
        # Create fresh THROWAWAY state
        self.ui_state = UIState()
        
        # If no winner was passed, determine from core_game_state
        if self.winner is None:
            alive_players = self.core_game_state.alive_players
            if alive_players:
                # Winner is player with max HP
                self.winner = max(alive_players, key=lambda p: p.hp)
            else:
                # Fallback: all players dead, pick first player
                if self.core_game_state.game and self.core_game_state.game.players:
                    self.winner = self.core_game_state.game.players[0]
        
        print(f"[GameOverScene] Entered with winner: P{self.winner.pid + 1 if self.winner else '?'}")
    
    def on_exit(self) -> None:
        """Called when scene is deactivated. Discard UIState."""
        # Explicitly discard THROWAWAY state
        self.ui_state = None
        print("[GameOverScene] Exited")
    
    def handle_input(self, input_state: InputState) -> None:
        """Process input intents for game over scene.
        
        Args:
            input_state: Intent-based input abstraction (not raw events)
        """
        # Update hover state based on mouse position
        self._update_hover(input_state.mouse_pos)
        
        # Handle R key - restart
        if input_state.was_key_pressed_this_frame(pygame.K_r):
            print("[GameOverScene] Restart requested (R key)")
            # T1.4: Transition to lobby (LobbyScene will handle strategy selection)
            # New game will be built via Lobby → GameLoop handoff protocol
            self.scene_manager.request_transition("lobby")
            return
        
        # Handle ESC key - quit
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            print("[GameOverScene] Quit requested (ESC key)")
            pygame.quit()
            sys.exit(0)
        
        # Handle mouse clicks
        if input_state.mouse_clicked:
            self._handle_click(input_state.mouse_pos)
    
    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        Args:
            dt: Delta time in milliseconds since last frame
        """
        # No animations or time-based logic in this scene
        pass
    
    def draw(self, screen: pygame.Surface) -> None:
        """Render game over scene to screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        # Draw game over screen using HUDRenderer
        if self.winner:
            draw_game_over(screen, self.winner, self.font_lg, self.font_md)
        
        # Draw additional stats and buttons
        self._draw_stats(screen)
        self._draw_buttons(screen)
    
    # ========== Helper Methods (UI Logic) ==========
    
    def _update_hover(self, mouse_pos):
        """Update hover states based on mouse position."""
        if self.restart_rect:
            self.hover_restart = self.restart_rect.collidepoint(mouse_pos)
        if self.quit_rect:
            self.hover_quit = self.quit_rect.collidepoint(mouse_pos)
    
    def _handle_click(self, pos):
        """Handle mouse click at position."""
        # Restart button
        if self.restart_rect and self.restart_rect.collidepoint(pos):
            print("[GameOverScene] Restart requested (click)")
            # T1.4: Transition to lobby
            self.scene_manager.request_transition("lobby")
            return
        
        # Quit button
        if self.quit_rect and self.quit_rect.collidepoint(pos):
            print("[GameOverScene] Quit requested (click)")
            pygame.quit()
            sys.exit(0)
    
    def _draw_stats(self, screen):
        """Draw final stats below winner announcement."""
        if not self.winner:
            return
        
        W, H = screen.get_size()
        
        # Stats panel position (below winner announcement)
        panel_y = H // 2 + 100
        
        # Collect stats
        stats = [
            ("HP", f"{self.winner.hp}"),
            ("Wins", f"{self.winner.stats.get('wins', 0)}"),
            ("Losses", f"{self.winner.stats.get('losses', 0)}"),
            ("Total Points", f"{self.winner.total_pts}"),
            ("Win Streak", f"{self.winner.win_streak}"),
            ("Max Streak", f"{self.winner.stats.get('win_streak_max', 0)}"),
            ("Gold Earned", f"{self.winner.stats.get('gold_earned', 0)}"),
            ("Damage Dealt", f"{self.winner.stats.get('damage_dealt', 0)}"),
        ]
        
        # Draw stats in two columns
        col_w = 200
        row_h = 24
        col1_x = W // 2 - col_w - 20
        col2_x = W // 2 + 20
        
        for i, (label, value) in enumerate(stats):
            row = i % 4
            col_x = col1_x if i < 4 else col2_x
            y = panel_y + row * row_h
            
            # Draw label and value
            label_surf = self.font_sm.render(label, True, (130, 140, 170))
            value_surf = self.font_sm.render(value, True, (245, 245, 255))
            
            screen.blit(label_surf, (col_x, y))
            screen.blit(value_surf, (col_x + 120, y))
    
    def _draw_buttons(self, screen):
        """Draw restart and quit buttons."""
        W, H = screen.get_size()
        
        # Button dimensions
        btn_w = 200
        btn_h = 50
        btn_gap = 20
        
        # Button positions (centered at bottom)
        buttons_y = H - 120
        restart_x = W // 2 - btn_w - btn_gap // 2
        quit_x = W // 2 + btn_gap // 2
        
        self.restart_rect = pygame.Rect(restart_x, buttons_y, btn_w, btn_h)
        self.quit_rect = pygame.Rect(quit_x, buttons_y, btn_w, btn_h)
        
        # Draw restart button
        self._draw_button(
            screen,
            self.restart_rect,
            "RESTART [R]",
            self.hover_restart,
            (0, 242, 255)  # Cyan accent
        )
        
        # Draw quit button
        self._draw_button(
            screen,
            self.quit_rect,
            "QUIT [ESC]",
            self.hover_quit,
            (255, 50, 150)  # Magenta
        )
    
    def _draw_button(self, screen, rect, label, hovered, color):
        """Draw a button with hover effect.
        
        Args:
            screen: Pygame surface to draw on
            rect: Button rectangle
            label: Button text
            hovered: Whether button is hovered
            color: Button accent color
        """
        # Background
        bg_color = (38, 42, 62) if hovered else (22, 26, 44)
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        
        # Border
        border_width = 2 if hovered else 1
        pygame.draw.rect(screen, color, rect, border_width, border_radius=8)
        
        # Text
        text_color = color if hovered else (245, 245, 255)
        text_surf = self.font_md.render(label, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
