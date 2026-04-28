"""
BoardRenderer — Centralized Board Card Rendering
=================================================
Manages the lifecycle of CardFlip instances for all board cards:
  - Syncs flip dict with current board state (add/remove)
  - Updates all flip animations per frame
  - Renders all flips in sorted order (hover_progress for z-order)
  - Provides hover coordinate detection

This extracts ~40 lines from ShopScene.update() and simplifies draw().

Usage:
    renderer = BoardRenderer()
    # Each frame:
    renderer.sync(board_cards, state, cam_state)
    renderer.update(dt_ms, cam_state, mouse_pos)
    renderer.draw(surface)
    # For hover detection:
    coord = renderer.get_hover_coord(mouse_pos)
"""

import pygame
from typing import Optional

from v2.constants import Colors, GridMath, Paths
from v2.core.exceptions import AutochessException
from v2.ui.card_flip import CardFlip
from v2.ui.hex_math import axial_to_pixel
from v2.assets.loader import AssetLoader


class BoardRenderer:
    """Manages CardFlip instances for all board cards."""

    def __init__(self):
        """Initialize empty board renderer."""
        self._flips: dict[tuple[int, int], CardFlip] = {}

    def sync(
        self,
        board_cards: dict[tuple[int, int], dict],
        state,
        cam_state,
    ) -> None:
        """Synchronize flip dict with current board state.
        
        Removes stale flips (cards no longer on board) and adds missing ones.
        
        Args:
            board_cards: Current board cards dict {coord: card_data}
            state: PublicState snapshot (for card info lookup)
            cam_state: Current camera state for positioning
        """
        # Remove stale flips
        stale_coords = [coord for coord in self._flips if coord not in board_cards]
        for coord in stale_coords:
            del self._flips[coord]

        # Add missing flips
        for coord in board_cards:
            if coord not in self._flips:
                self._add_board_flip(coord, board_cards, state, cam_state)

    def update(self, dt_ms: float, cam_state, mouse_pos: tuple[int, int]) -> None:
        """Update all flip animations and hover states.
        
        Args:
            dt_ms: Delta time in milliseconds
            cam_state: Current camera state for positioning
            mouse_pos: Current mouse position for hover detection
        """
        if not self._flips:
            return

        for coord, flip in self._flips.items():
            # Update dest_rect based on camera state
            cx, cy = axial_to_pixel(*coord, cam_state)
            w = int(GridMath.HEX_SIZE * cam_state.zoom * 1.55)
            h = int(GridMath.HEX_SIZE * cam_state.zoom * 1.85)
            flip.dest_rect.update(int(cx - w // 2), int(cy - h // 2), w, h)

            # Update hover state
            if flip.dest_rect.collidepoint(mouse_pos):
                flip.hover_start()
            else:
                flip.hover_end()

            # Update animation
            flip.update(dt_ms)

    def draw(self, surface: pygame.Surface) -> None:
        """Render all flips in sorted order (hover_progress for z-order).
        
        Args:
            surface: Target surface to render to
        """
        if not self._flips:
            return

        # Sort by hover_progress to ensure hovered cards render on top
        for _, flip in sorted(self._flips.items(), key=lambda item: item[1].hover_progress):
            flip.render(surface)

    def get_hover_coord(self, pos: tuple[int, int]) -> Optional[tuple[int, int]]:
        """Get the coordinate of the card at the given position.
        
        Args:
            pos: Mouse position to check
            
        Returns:
            Coordinate tuple if a card is at that position, else None
        """
        return next(
            (coord for coord, flip in self._flips.items() if flip.dest_rect.collidepoint(pos)),
            None
        )

    def clear(self) -> None:
        """Clear all flips (useful for view sync)."""
        self._flips.clear()

    def remove(self, coord: tuple[int, int]) -> None:
        """Remove a specific flip by coordinate.
        
        Args:
            coord: Board coordinate to remove
        """
        self._flips.pop(coord, None)

    def _add_board_flip(
        self,
        coord: tuple[int, int],
        board_cards: dict,
        state,
        cam_state,
    ) -> None:
        """Create and add a CardFlip for the given coordinate.
        
        Args:
            coord: Board coordinate
            board_cards: Current board cards dict
            state: PublicState snapshot
            cam_state: Current camera state
        """
        item = board_cards.get(coord)
        if not item:
            return

        card_name = item["name"]
        
        # Get card data from state snapshot
        card_data = state.active_player.board_card_info.get(coord) if state else None

        # Calculate position and size
        cx, cy = axial_to_pixel(*coord, cam_state)
        w = int(GridMath.HEX_SIZE * cam_state.zoom * 1.55)
        h = int(GridMath.HEX_SIZE * cam_state.zoom * 1.85)
        rect = pygame.Rect(int(cx - w // 2), int(cy - h // 2), w, h)

        # Load card surfaces
        try:
            loader = AssetLoader.get()
            back = loader.get_card_back(card_name)
            front = loader.get_card_front(card_name)
            
            # Check if card is evolved
            evolved = bool(card_data and str(getattr(card_data, "rarity", "")).upper() == "E")
            
            # Fallback if card_data is missing (shouldn't happen in normal flow)
            if not evolved and card_data is None:
                from v2.core.engine_adapter import EngineAdapter
                snap = EngineAdapter.get_card_info(card_name)
                evolved = bool(snap and str(getattr(snap, "rarity", "")).upper() == "E")
        except AutochessException:
            # Fallback to simple colored surfaces
            back = self._fallback_card_surface((38, 42, 62), w, h)
            front = self._fallback_card_surface((20, 60, 100), w, h)
            evolved = False

        self._flips[coord] = CardFlip(
            back,
            front,
            rect,
            evolved=evolved,
            evolved_color=Colors.PLATINUM
        )

    @staticmethod
    def _fallback_card_surface(color: tuple[int, int, int], w: int, h: int) -> pygame.Surface:
        """Create a fallback hexagonal surface when assets fail to load.
        
        Args:
            color: RGB color tuple
            w: Width in pixels
            h: Height in pixels
            
        Returns:
            Pygame surface with hexagonal shape
        """
        import math

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        points = [
            (
                cx + h / 2 * math.cos(math.radians(60 * i - 30)),
                cy + h / 2 * math.sin(math.radians(60 * i - 30)),
            )
            for i in range(6)
        ]
        pygame.draw.polygon(surf, color, points)
        return surf.convert_alpha()
