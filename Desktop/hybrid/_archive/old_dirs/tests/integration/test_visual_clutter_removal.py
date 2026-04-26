"""
Integration test for visual clutter removal from board card rendering.

This test verifies that deprecated visual effects (glow, aura, medallion, badges)
have been successfully removed from board card rendering across all rarity levels.

Feature: board-shop-ui-cleanup-v3
Task: 2.2 Write integration test for visual clutter removal
Requirements: 1.1, 1.2, 1.3, 1.4

Validates:
- Requirement 1.1: Board_Renderer SHALL remove all glow effects
- Requirement 1.2: Board_Renderer SHALL remove all aura effects
- Requirement 1.3: Board_Renderer SHALL remove all circle-medallion effects
- Requirement 1.4: Board_Renderer SHALL remove all boxed edge badges
"""

import pytest
import pygame
import sys
import os
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer
from engine_core.card import Card


class TestVisualClutterRemoval:
    """Integration test suite for visual clutter removal."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.surface = pygame.Surface((800, 600))
        self.surface.fill((0, 0, 0))  # Black background
        self.renderer = CyberRenderer()
        yield
        pygame.quit()

    def create_test_card(self, rarity: str) -> Card:
        """Create a test card with the specified rarity."""
        return Card(
            name=f"Test Card {rarity}",
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

    def get_pixels_in_ring(self, center: Tuple[int, int], radius: int, 
                          thickness: int = 3) -> List[Tuple[int, int, int]]:
        """
        Get all pixel colors in a ring around the center point.
        Used to detect circular aura/glow effects.
        """
        cx, cy = center
        pixels = []
        for angle in range(0, 360, 5):  # Sample every 5 degrees
            import math
            for r in range(radius - thickness, radius + thickness):
                x = int(cx + r * math.cos(math.radians(angle)))
                y = int(cy + r * math.sin(math.radians(angle)))
                if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                    pixels.append(self.surface.get_at((x, y))[:3])
        return pixels

    def count_non_black_pixels_in_ring(self, center: Tuple[int, int], 
                                       radius: int, thickness: int = 3) -> int:
        """
        Count non-black pixels in a ring. Used to detect glow/aura effects.
        """
        pixels = self.get_pixels_in_ring(center, radius, thickness)
        return sum(1 for p in pixels if p != (0, 0, 0))

    def has_circular_pattern_outside_hex(self, center: Tuple[int, int], 
                                        hex_radius: int) -> bool:
        """
        Detect if there are circular patterns outside the hex boundary.
        This would indicate glow/aura effects that extend beyond the card.
        """
        # Check for pixels in rings outside the hex
        outer_radius = hex_radius + 10
        non_black_count = self.count_non_black_pixels_in_ring(center, outer_radius, 5)
        
        # If more than 20% of sampled pixels are non-black, likely a glow/aura effect
        total_samples = len(self.get_pixels_in_ring(center, outer_radius, 5))
        if total_samples == 0:
            return False
        return (non_black_count / total_samples) > 0.2

    def has_circular_shape_instead_of_hex(self, center: Tuple[int, int], 
                                          test_radius: int = 50) -> bool:
        """
        Detect if the card uses circular shapes instead of hexagonal shapes.
        The legacy renderer used circles (medallion style), the new renderer uses hexagons.
        
        We test this by sampling pixels at the hex corners vs circle edge:
        - Hex shape: corners should be outside the filled area
        - Circle shape: all points at test_radius should be inside the filled area
        """
        cx, cy = center
        import math
        
        # Sample at hex corner positions (30° offset from cardinal directions)
        hex_corner_angles = [30, 90, 150, 210, 270, 330]
        circle_edge_angles = [0, 60, 120, 180, 240, 300]
        
        # For a hex, corners at these angles should be OUTSIDE the fill at radius test_radius
        # For a circle, all points at test_radius should be INSIDE the fill
        
        hex_corner_pixels = []
        for angle in hex_corner_angles:
            x = int(cx + test_radius * math.cos(math.radians(angle)))
            y = int(cy + test_radius * math.sin(math.radians(angle)))
            if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                pixel = self.surface.get_at((x, y))[:3]
                hex_corner_pixels.append(pixel)
        
        circle_edge_pixels = []
        for angle in circle_edge_angles:
            x = int(cx + test_radius * math.cos(math.radians(angle)))
            y = int(cy + test_radius * math.sin(math.radians(angle)))
            if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                pixel = self.surface.get_at((x, y))[:3]
                circle_edge_pixels.append(pixel)
        
        # Count filled pixels (non-black)
        hex_corners_filled = sum(1 for p in hex_corner_pixels if p != (0, 0, 0))
        circle_edges_filled = sum(1 for p in circle_edge_pixels if p != (0, 0, 0))
        
        # If it's a circle: all circle edge points should be filled
        # If it's a hex: hex corners should NOT be filled (or fewer filled)
        # A circular medallion would have >80% of circle edge points filled
        # and >80% of hex corner points filled (since circle encompasses hex corners)
        
        if len(circle_edge_pixels) == 0:
            return False
        
        circle_fill_ratio = circle_edges_filled / len(circle_edge_pixels)
        
        # If most circle edge points are filled, it's likely circular
        # But we need to distinguish from a large hex that also fills these points
        # The key is: a circle would fill ALL points uniformly at a given radius
        # A hex would have gaps at certain angles
        
        # Sample more points around the perimeter to check for uniformity
        perimeter_pixels = []
        for angle in range(0, 360, 10):
            x = int(cx + test_radius * math.cos(math.radians(angle)))
            y = int(cy + test_radius * math.sin(math.radians(angle)))
            if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                pixel = self.surface.get_at((x, y))[:3]
                perimeter_pixels.append(1 if pixel != (0, 0, 0) else 0)
        
        if not perimeter_pixels:
            return False
        
        # A circle would have very uniform fill around the perimeter (>90%)
        # A hex would have gaps (typically <70% at the right radius)
        perimeter_fill_ratio = sum(perimeter_pixels) / len(perimeter_pixels)
        
        # If >90% of perimeter is filled uniformly, it's circular
        return perimeter_fill_ratio > 0.90

    def test_no_glow_effects_all_rarities(self):
        """
        Verify no glow effects are rendered for cards of all rarity levels.
        
        Validates Requirement 1.1: Board_Renderer SHALL remove all glow effects
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            # Clear surface
            self.surface.fill((0, 0, 0))
            
            # Create and render card
            card = self.create_test_card(rarity)
            center = (400, 300)
            hex_radius = 68
            
            self.renderer.draw_hex_card(
                self.surface, card, center, r=hex_radius, 
                is_hovered=False, highlighted=False
            )
            
            # Check for glow effects outside the hex boundary
            has_glow = self.has_circular_pattern_outside_hex(center, hex_radius)
            
            assert not has_glow, \
                f"Glow effect detected for rarity {rarity} card. " \
                f"Requirement 1.1 violated: glow effects should be removed."

    def test_no_aura_effects_all_rarities(self):
        """
        Verify no aura ring effects are rendered for cards of all rarity levels.
        
        Validates Requirement 1.2: Board_Renderer SHALL remove all aura effects
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            # Clear surface
            self.surface.fill((0, 0, 0))
            
            # Create and render card
            card = self.create_test_card(rarity)
            center = (400, 300)
            hex_radius = 68
            
            self.renderer.draw_hex_card(
                self.surface, card, center, r=hex_radius,
                is_hovered=False, highlighted=False
            )
            
            # Check for aura rings at various distances from center
            # Auras typically appear as rings slightly outside the card boundary
            aura_detected = False
            for ring_offset in [8, 12, 16]:
                ring_radius = hex_radius + ring_offset
                non_black = self.count_non_black_pixels_in_ring(center, ring_radius, 2)
                total = len(self.get_pixels_in_ring(center, ring_radius, 2))
                
                if total > 0 and (non_black / total) > 0.15:
                    aura_detected = True
                    break
            
            assert not aura_detected, \
                f"Aura effect detected for rarity {rarity} card. " \
                f"Requirement 1.2 violated: aura effects should be removed."

    def test_no_center_medallion_all_rarities(self):
        """
        Verify no circle-medallion effects are rendered at card center.
        The legacy renderer used circular shapes (medallion style).
        The new renderer should use hexagonal shapes, not circles.
        
        Validates Requirement 1.3: Board_Renderer SHALL remove all circle-medallion effects
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            # Clear surface
            self.surface.fill((0, 0, 0))
            
            # Create and render card
            card = self.create_test_card(rarity)
            center = (400, 300)
            hex_radius = 68
            
            self.renderer.draw_hex_card(
                self.surface, card, center, r=hex_radius,
                is_hovered=False, highlighted=False
            )
            
            # Check if card uses circular shape instead of hexagonal
            # Test at a radius that would distinguish hex from circle
            has_circular = self.has_circular_shape_instead_of_hex(center, test_radius=55)
            
            assert not has_circular, \
                f"Circular medallion shape detected for rarity {rarity} card. " \
                f"Requirement 1.3 violated: circle-medallion effects should be removed. " \
                f"Card should use hexagonal shape, not circular."

    def test_no_boxed_edge_badges_all_rarities(self):
        """
        Verify no boxed edge badges are rendered around edge stats.
        
        Validates Requirement 1.4: Board_Renderer SHALL remove all boxed edge badges
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            # Clear surface
            self.surface.fill((0, 0, 0))
            
            # Create and render card
            card = self.create_test_card(rarity)
            center = (400, 300)
            hex_radius = 68
            
            self.renderer.draw_hex_card(
                self.surface, card, center, r=hex_radius,
                is_hovered=False, highlighted=False
            )
            
            # Check edge positions for boxed badges
            # Edge stats should be plain text without background boxes
            import math
            edge_positions = []
            for i in range(6):
                angle = math.radians(i * 60 - 90)  # Start from top
                edge_x = int(center[0] + (hex_radius - 15) * math.cos(angle))
                edge_y = int(center[1] + (hex_radius - 15) * math.sin(angle))
                edge_positions.append((edge_x, edge_y))
            
            # For each edge position, check if there's a rectangular badge pattern
            # A badge would show as a rectangular region of uniform color
            badges_detected = False
            for edge_pos in edge_positions:
                ex, ey = edge_pos
                
                # Sample a small region around the edge position
                region_colors = []
                for dx in range(-10, 11, 2):
                    for dy in range(-10, 11, 2):
                        x, y = ex + dx, ey + dy
                        if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                            region_colors.append(self.surface.get_at((x, y))[:3])
                
                # Check for uniform color regions (indicating a badge background)
                if region_colors:
                    # Count most common color
                    from collections import Counter
                    color_counts = Counter(region_colors)
                    most_common_color, count = color_counts.most_common(1)[0]
                    
                    # If >70% of pixels are the same non-black color, likely a badge
                    if most_common_color != (0, 0, 0) and count / len(region_colors) > 0.7:
                        badges_detected = True
                        break
            
            assert not badges_detected, \
                f"Boxed edge badges detected for rarity {rarity} card. " \
                f"Requirement 1.4 violated: boxed edge badges should be removed."

    def test_tarot_frame_present_all_rarities(self):
        """
        Verify that tarot-style hex frame IS present (positive test).
        This ensures we're testing the new implementation, not a broken renderer.
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            # Clear surface
            self.surface.fill((0, 0, 0))
            
            # Create and render card
            card = self.create_test_card(rarity)
            center = (400, 300)
            hex_radius = 68
            
            self.renderer.draw_hex_card(
                self.surface, card, center, r=hex_radius,
                is_hovered=False, highlighted=False
            )
            
            # Check that SOMETHING was rendered (not a blank surface)
            non_black_pixels = 0
            for x in range(center[0] - hex_radius, center[0] + hex_radius, 5):
                for y in range(center[1] - hex_radius, center[1] + hex_radius, 5):
                    if 0 <= x < self.surface.get_width() and 0 <= y < self.surface.get_height():
                        if self.surface.get_at((x, y))[:3] != (0, 0, 0):
                            non_black_pixels += 1
            
            assert non_black_pixels > 50, \
                f"Card rendering appears broken for rarity {rarity}. " \
                f"Expected tarot frame and card content to be visible."

    def test_visual_clutter_removal_with_hover(self):
        """
        Verify no deprecated effects are rendered even when card is hovered.
        """
        card = self.create_test_card("4")
        center = (400, 300)
        hex_radius = 68
        
        # Test with hover
        self.surface.fill((0, 0, 0))
        self.renderer.draw_hex_card(
            self.surface, card, center, r=hex_radius,
            is_hovered=True, highlighted=False
        )
        
        # Check for glow/aura effects
        has_glow = self.has_circular_pattern_outside_hex(center, hex_radius)
        assert not has_glow, \
            "Glow effect detected on hovered card. Deprecated effects should not appear on hover."

    def test_visual_clutter_removal_with_highlight(self):
        """
        Verify no deprecated effects are rendered even when card is highlighted.
        """
        card = self.create_test_card("5")
        center = (400, 300)
        hex_radius = 68
        
        # Test with highlight
        self.surface.fill((0, 0, 0))
        self.renderer.draw_hex_card(
            self.surface, card, center, r=hex_radius,
            is_hovered=False, highlighted=True
        )
        
        # Check for glow/aura effects
        has_glow = self.has_circular_pattern_outside_hex(center, hex_radius)
        assert not has_glow, \
            "Glow effect detected on highlighted card. Deprecated effects should not appear on highlight."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
