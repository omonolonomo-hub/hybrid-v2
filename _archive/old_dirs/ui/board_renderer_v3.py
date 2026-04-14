"""
Board Renderer V3 - Clean Implementation
Board and Shop UI Cleanup v3

This is a clean board renderer without legacy code.

UPDATED: Now uses HexSystem for all coordinate conversions with cube rounding.
"""

import pygame
import math
from typing import Optional, Tuple, Set

try:
    from ui.renderer_v3 import CyberRendererV3, HEX_SIZE, _hex_corners
    from ui.card_meta import get_passive_desc
    from engine_core.constants import STAT_TO_GROUP
    from core.hex_system import HexSystem
except ImportError:
    from .renderer_v3 import CyberRendererV3, HEX_SIZE, _hex_corners
    from .card_meta import get_passive_desc
    from ..engine_core.constants import STAT_TO_GROUP
    from ..core.hex_system import HexSystem

# Colors
C_WHITE = (245, 245, 255)
C_DIM = (130, 140, 170)
C_ACCENT = (0, 242, 255)
C_LOCKED = (255, 180, 40)

GROUP_COLORS = {
    "EXISTENCE": (255, 60, 50),
    "MIND": (50, 130, 255),
    "CONNECTION": (40, 230, 130),
}


# Legacy module-level functions for backward compatibility
# These now delegate to HexSystem with cube rounding
def hex_to_pixel(q: int, r: int, origin_x: int, origin_y: int) -> Tuple[int, int]:
    """Convert hex coordinates to pixel position.
    
    UPDATED: Now uses HexSystem for consistent coordinate conversion.
    
    Args:
        q, r: Hex coordinates
        origin_x, origin_y: Screen origin coordinates
    
    Returns:
        (px, py) screen pixel coordinates
    """
    hex_sys = HexSystem(hex_size=HEX_SIZE, origin=(origin_x, origin_y))
    return hex_sys.hex_to_pixel(q, r)


def pixel_to_hex(px: int, py: int, origin_x: int, origin_y: int) -> Tuple[int, int]:
    """Convert pixel position to hex coordinates.
    
    UPDATED: Now uses HexSystem with CUBE ROUNDING (not simple round).
    This fixes coordinate conversion bugs.
    
    Args:
        px, py: Screen pixel coordinates
        origin_x, origin_y: Screen origin coordinates
    
    Returns:
        (q, r) hex coordinates
    """
    hex_sys = HexSystem(hex_size=HEX_SIZE, origin=(origin_x, origin_y))
    return hex_sys.pixel_to_hex(px, py)


class BoardRendererV3:
    """Clean board renderer for tarot-style UI.
    
    UPDATED: Now uses HexSystem for all coordinate conversions with cube rounding.
    """
    
    def __init__(self, origin, strategy="tempo", cyber_renderer=None):
        self.origin = origin
        self.strategy = strategy
        self.cyber = cyber_renderer or CyberRendererV3()
        self.hovered_coord = None
        self.hovered_card = None
        self.highlight_group = None
        self.fonts = {}
        
        # Initialize HexSystem for coordinate conversions
        self.hex_system = HexSystem(hex_size=HEX_SIZE, origin=origin)
    
    def init_fonts(self):
        """Initialize fonts."""
        def _font(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except:
                return pygame.font.SysFont("consolas", size, bold=bold)
        
        self.fonts = {
            "xs": _font("consolas", 11),
            "xs_bold": _font("consolas", 11, bold=True),
            "sm": _font("consolas", 13),
            "sm_bold": _font("consolas", 13, bold=True),
        }
        self.cyber.fonts = self.fonts
    
    def update_hover(self, mouse_pos, board_coords):
        """Update hover state from mouse position.
        
        UPDATED: Now uses self.hex_system with cube rounding.
        """
        q, r = self.hex_system.pixel_to_hex(mouse_pos[0], mouse_pos[1])
        coord = (q, r)
        if coord in board_coords:
            self.hovered_coord = coord
        else:
            self.hovered_coord = None
    
    def draw(self, surface, board, board_coords, locked_coords=None, show_tooltip=True):
        """Draw the board with all cards.
        
        UPDATED: Now uses self.hex_system for coordinate conversions.
        
        Args:
            surface: pygame surface to draw on
            board: Board object with grid dict
            board_coords: list of valid (q,r) coordinates
            locked_coords: set of locked (q,r) coordinates
            show_tooltip: whether to show hover tooltip
        """
        locked_coords = locked_coords or set()
        self.hovered_card = None
        
        # Draw empty hexes first
        for q, r in board_coords:
            if (q, r) not in board.grid:
                cx, cy = self.hex_system.hex_to_pixel(q, r)
                self._draw_empty_hex(surface, cx, cy, (q, r) == self.hovered_coord)
        
        # Draw cards
        for (q, r), card in board.grid.items():
            cx, cy = self.hex_system.hex_to_pixel(q, r)
            is_hovered = (q, r) == self.hovered_coord
            is_locked = (q, r) in locked_coords
            
            if is_hovered:
                self.hovered_card = card
            
            # Draw card using V3 renderer
            self.cyber.draw_hex_card(
                surface, card, (cx, cy),
                r=HEX_SIZE,
                is_hovered=is_hovered,
                highlighted=False
            )
            
            # Draw locked indicator
            if is_locked:
                corners = _hex_corners(cx, cy, HEX_SIZE - 2)
                pts = [(int(x), int(y)) for x, y in corners]
                pygame.draw.polygon(surface, C_LOCKED, pts, 2)
    
    def _draw_empty_hex(self, surface, cx, cy, hovered):
        """Draw empty hex slot."""
        corners = _hex_corners(cx, cy, HEX_SIZE - 6)
        pts = [(int(x), int(y)) for x, y in corners]
        
        if hovered:
            pygame.draw.polygon(surface, (30, 35, 50), pts)
            pygame.draw.polygon(surface, C_ACCENT, pts, 2)
        else:
            pygame.draw.polygon(surface, (20, 24, 38), pts)
            pygame.draw.polygon(surface, (40, 52, 84), pts, 1)
    
    def draw_placement_preview(self, surface, cx, cy, card, rotation):
        """Draw card placement preview with rotation."""
        # Get rotated edges
        rotated = self._rotate_edges(card, rotation)
        
        # Create simple preview card object
        class PreviewCard:
            def __init__(self, name, rarity, rotation, edges, passive_type, dominant_group):
                self.name = name
                self.rarity = rarity
                self.rotation = rotation
                self._edges = edges
                self.passive_type = passive_type
                self.dominant_group = dominant_group
            
            def rotated_edges(self):
                return self._edges
        
        preview_card = PreviewCard(
            card.name,
            card.rarity,
            rotation,
            rotated,
            card.passive_type,
            card.dominant_group
        )
        
        # Draw with semi-transparency
        preview_surf = pygame.Surface((HEX_SIZE * 3, HEX_SIZE * 3), pygame.SRCALPHA)
        self.cyber.draw_hex_card(
            preview_surf, preview_card,
            (HEX_SIZE * 1.5, HEX_SIZE * 1.5),
            r=HEX_SIZE - 6,
            is_hovered=False,
            highlighted=True
        )
        preview_surf.set_alpha(180)
        surface.blit(preview_surf, (cx - HEX_SIZE * 1.5, cy - HEX_SIZE * 1.5))
    
    def _rotate_edges(self, card, rotation):
        """Get edges with specified rotation."""
        edges = list(getattr(card, 'edges', []))
        if not edges or len(edges) < 6:
            return []
        # Rotate by shifting indices
        rotated = []
        for i in range(6):
            src_idx = (i - rotation) % 6
            if src_idx < len(edges):
                rotated.append(edges[src_idx])
            else:
                rotated.append(("", 0))
        return rotated


# Export coordinate conversion functions
__all__ = ['BoardRendererV3', 'hex_to_pixel', 'pixel_to_hex', 'HEX_SIZE']
