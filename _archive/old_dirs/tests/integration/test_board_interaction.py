"""
Integration test for board interaction with new tarot-style UI.

This test verifies that the new tarot-style hex frames and edge stat rendering
work correctly with the existing game board logic, coordinate system, and interactions.

Feature: board-shop-ui-cleanup-v3
Task: 12.2 Write integration test for board interaction
Requirements: 9.1, 9.2, 9.3, 9.4

Validates:
- Requirement 9.1: Board_Renderer SHALL maintain existing render order
- Requirement 9.2: Board_Renderer SHALL preserve hex-frame alignment with coordinate system
- Requirement 9.3: Board_Renderer SHALL use same BOARD_COORDS structure
- Requirement 9.4: Board_Renderer SHALL maintain compatibility with existing board interaction logic
"""

import pytest
import pygame
import sys
import os
from typing import Tuple, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer, BoardRenderer, hex_to_pixel, pixel_to_hex
from engine_core.card import Card
from engine_core.board import Board, BOARD_COORDS


class TestBoardInteraction:
    """Integration test suite for board interaction with new UI."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instances."""
        pygame.init()
        self.surface = pygame.Surface((1600, 900))
        self.surface.fill((20, 20, 30))  # Dark background
        
        # Create fonts
        fonts = {
            "md": pygame.font.SysFont("consolas", 16),
            "sm": pygame.font.SysFont("consolas", 13),
            "xs": pygame.font.SysFont("consolas", 12),
        }
        
        self.cyber_renderer = CyberRenderer(fonts)
        self.board_renderer = BoardRenderer(
            origin=(800, 450),
            player_strategy="test",
            cyber_renderer=self.cyber_renderer
        )
        self.board_renderer.init_fonts()
        
        yield
        pygame.quit()

    def create_test_card(self, name: str = "Test Card", rarity: str = "3") -> Card:
        """Create a test card with specified properties."""
        return Card(
            name=name,
            category="Test",
            rarity=rarity,
            stats={
                "Power": 5,
                "Durability": 4,
                "Speed": 3,
                "Intelligence": 6,
                "Harmony": 5,
                "Spread": 4
            },
            passive_type="test_passive"
        )

    def test_coordinate_system_compatibility(self):
        """
        Verify that hex_to_pixel and pixel_to_hex conversions work correctly
        with the new tarot-style rendering.
        
        Validates Requirement 9.2: Preserve hex-frame alignment with coordinate system
        """
        origin = (800, 450)
        
        # Test several hex coordinates
        test_coords = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1), (-1, 1)]
        
        for q, r in test_coords:
            # Convert hex to pixel
            px, py = hex_to_pixel(q, r, origin[0], origin[1])
            
            # Convert back to hex
            q2, r2 = pixel_to_hex(px, py, origin[0], origin[1])
            
            # Should round-trip correctly
            assert (q2, r2) == (q, r), \
                f"Coordinate system round-trip failed for ({q}, {r}). " \
                f"Got ({q2}, {r2}) after pixel conversion. " \
                f"Requirement 9.2 violated: hex-frame alignment broken."

    def test_board_coords_structure_preserved(self):
        """
        Verify that BOARD_COORDS structure is still used and compatible.
        
        Validates Requirement 9.3: Use same BOARD_COORDS structure
        """
        # BOARD_COORDS should be a list of (q, r) tuples
        assert isinstance(BOARD_COORDS, list), \
            "BOARD_COORDS should be a list"
        
        # Check that it contains hex coordinate tuples
        for coord in BOARD_COORDS:
            assert isinstance(coord, tuple), \
                f"BOARD_COORDS element {coord} should be a tuple"
            assert len(coord) == 2, \
                f"BOARD_COORDS element {coord} should have 2 elements (q, r)"
        
        # Verify that board renderer can use BOARD_COORDS
        board = Board()
        card = self.create_test_card()
        
        # Place a card at a valid board position
        if BOARD_COORDS:
            first_coord = BOARD_COORDS[0]
            board.place(first_coord, card)
            
            # Render the board - should not raise errors
            try:
                self.board_renderer.draw(
                    self.surface,
                    board,
                    BOARD_COORDS,
                    locked_coords=set(),
                    show_tooltip=False
                )
                success = True
            except Exception as e:
                success = False
                error_msg = str(e)
            
            assert success, \
                f"Board rendering failed with BOARD_COORDS structure. " \
                f"Requirement 9.3 violated: BOARD_COORDS compatibility broken. " \
                f"Error: {error_msg if not success else ''}"

    def test_board_placement_logic_compatibility(self):
        """
        Verify that existing board placement logic works with new rendering.
        
        Validates Requirement 9.4: Maintain compatibility with board interaction logic
        """
        board = Board()
        
        # Create several test cards
        cards = [
            self.create_test_card(f"Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Place cards at various positions
        positions = BOARD_COORDS[:5]
        for card, pos in zip(cards, positions):
            board.place(pos, card)
        
        # Verify cards are placed correctly
        assert len(board.grid) == 5, \
            "Board should contain 5 cards after placement"
        
        # Render the board with placed cards
        try:
            self.board_renderer.draw(
                self.surface,
                board,
                BOARD_COORDS,
                locked_coords=set(),
                show_tooltip=False
            )
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Board rendering failed with placed cards. " \
            f"Requirement 9.4 violated: board placement logic compatibility broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_synergy_line_rendering_compatibility(self):
        """
        Verify that synergy lines render correctly with new edge coloring.
        
        Validates Requirement 9.1: Maintain existing render order
        """
        board = Board()
        
        # Create cards with matching stats for synergy
        card1 = Card(
            name="Card 1",
            category="Test",
            rarity="3",
            stats={"Power": 5, "Durability": 4, "Speed": 3,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test"
        )
        
        card2 = Card(
            name="Card 2",
            category="Test",
            rarity="3",
            stats={"Power": 6, "Durability": 3, "Speed": 4,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test"
        )
        
        # Place cards adjacent to each other
        positions = BOARD_COORDS[:2]
        board.place(positions[0], card1)
        board.place(positions[1], card2)
        
        # Render with synergy lines
        try:
            self.board_renderer.draw(
                self.surface,
                board,
                BOARD_COORDS,
                locked_coords=set(),
                show_tooltip=False
            )
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Board rendering with synergy lines failed. " \
            f"Requirement 9.1 violated: render order broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_tooltip_rendering_compatibility(self):
        """
        Verify that tooltips render correctly with new frame geometry.
        
        Validates Requirement 9.1: Maintain existing render order
        """
        board = Board()
        card = self.create_test_card("Tooltip Test", rarity="4")
        
        # Place card
        position = BOARD_COORDS[0]
        board.place(position, card)
        
        # Simulate hover over the card
        pixel_pos = hex_to_pixel(position[0], position[1], 800, 450)
        self.board_renderer.update_hover(pixel_pos, BOARD_COORDS)
        
        # Render with tooltip enabled
        try:
            self.board_renderer.draw(
                self.surface,
                board,
                BOARD_COORDS,
                locked_coords=set(),
                show_tooltip=True
            )
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Board rendering with tooltip failed. " \
            f"Requirement 9.1 violated: tooltip rendering broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_locked_coords_rendering(self):
        """
        Verify that locked coordinate indicators work with new rendering.
        
        Validates Requirement 9.4: Maintain compatibility with board interaction logic
        """
        board = Board()
        card = self.create_test_card()
        
        # Place card and lock its position
        position = BOARD_COORDS[0]
        board.place(position, card)
        locked_coords = {position}
        
        # Render with locked coordinates
        try:
            self.board_renderer.draw(
                self.surface,
                board,
                BOARD_COORDS,
                locked_coords=locked_coords,
                show_tooltip=False
            )
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Board rendering with locked coordinates failed. " \
            f"Requirement 9.4 violated: locked coords compatibility broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_multiple_rarity_cards_on_board(self):
        """
        Verify that cards of different rarities render correctly together on the board.
        
        Validates Requirements 9.1, 9.2: Render order and alignment preserved
        """
        board = Board()
        
        # Create cards of all rarities
        rarities = ["1", "2", "3", "4", "5", "E"]
        cards = [self.create_test_card(f"Rarity {r}", rarity=r) for r in rarities]
        
        # Place all cards on board
        positions = BOARD_COORDS[:len(cards)]
        for card, pos in zip(cards, positions):
            board.place(pos, card)
        
        # Render the board
        try:
            self.board_renderer.draw(
                self.surface,
                board,
                BOARD_COORDS,
                locked_coords=set(),
                show_tooltip=False
            )
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Board rendering with multiple rarity cards failed. " \
            f"Requirements 9.1, 9.2 violated: render order or alignment broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_board_render_with_rotation(self):
        """
        Verify that card rotation works correctly with new edge stat rendering.
        
        Validates Requirement 9.4: Maintain compatibility with board interaction logic
        """
        board = Board()
        
        # Create card with specific edge values
        card = Card(
            name="Rotated Card",
            category="Test",
            rarity="3",
            stats={"Power": 5, "Durability": 0, "Speed": 3,
                   "Intelligence": 6, "Harmony": 0, "Spread": 4},
            passive_type="test"
        )
        
        # Test different rotations
        for rotation in range(6):
            card.rotation = rotation
            position = BOARD_COORDS[0]
            board.grid.clear()
            board.place(position, card)
            
            # Render with rotation
            try:
                self.board_renderer.draw(
                    self.surface,
                    board,
                    BOARD_COORDS,
                    locked_coords=set(),
                    show_tooltip=False
                )
                render_success = True
            except Exception as e:
                render_success = False
                error_msg = str(e)
                break
        
        assert render_success, \
            f"Board rendering with card rotation failed at rotation {rotation}. " \
            f"Requirement 9.4 violated: rotation compatibility broken. " \
            f"Error: {error_msg if not render_success else ''}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
