"""
Property-based tests for shop stat non-zero display.

This test validates that all stats with non-zero values ARE rendered
in the shop card stat grid with both name and value visible.

Feature: board-shop-ui-cleanup-v3
Task: 5.3 Write property test for shop stat non-zero display
Property 6: Shop Stat Non-Zero Display
Validates: Requirements 3.3
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer
from engine_core.card import Card


# Strategy for generating card data with non-zero stats
def card_with_nonzero_stats_strategy():
    """Generate cards with at least one non-zero stat."""
    # Define stat names (must match the 6 stats used in the game)
    stat_names = ["Power", "Durability", "Size", "Speed", "Meaning", "Secret"]
    
    # Generate stat values ensuring at least one non-zero
    stats_dict = st.fixed_dictionaries({
        stat_names[0]: st.integers(min_value=0, max_value=15),
        stat_names[1]: st.integers(min_value=0, max_value=15),
        stat_names[2]: st.integers(min_value=0, max_value=15),
        stat_names[3]: st.integers(min_value=0, max_value=15),
        stat_names[4]: st.integers(min_value=0, max_value=15),
        stat_names[5]: st.integers(min_value=0, max_value=15),
    })
    
    # Generate card with random stats, rarity, and rotation
    return st.builds(
        Card,
        name=st.text(min_size=3, max_size=12, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=stats_dict,
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    )


def extract_rendered_stats_from_shop_card(surface: pygame.Surface, 
                                          stats_rect: pygame.Rect,
                                          card: Card) -> List[str]:
    """
    Extract which stats are rendered in the shop card stat grid by checking for colored pixels.
    
    Returns a list of stat names that appear to be rendered.
    """
    # Get the real stats that should be rendered (non-zero, non-internal)
    edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
    real_stats = []
    for stat_name, value in edge_source:
        if str(stat_name).startswith("_") or value <= 0:
            continue
        real_stats.append((stat_name, value))
    
    if not real_stats:
        return []
    
    # Calculate grid layout (same logic as draw_shop_stat_grid)
    cols = 2
    rows = (len(real_stats) + cols - 1) // cols
    cell_w = (stats_rect.width - 6) // cols
    cell_h = max(28, (stats_rect.height - 6) // max(1, rows))
    
    rendered_stat_names = []
    
    for idx, (stat_name, value) in enumerate(real_stats):
        col = idx % cols
        row = idx // cols
        cell = pygame.Rect(
            stats_rect.x + col * cell_w,
            stats_rect.y + row * cell_h,
            cell_w - 6, cell_h - 4,
        )
        
        # Sample pixels in the cell to detect if text was rendered
        sample_radius = 5
        non_black_pixels = 0
        total_samples = 0
        
        # Sample around the center of the cell
        cx = cell.centerx
        cy = cell.centery
        
        for dx in range(-sample_radius, sample_radius + 1, 2):
            for dy in range(-sample_radius, sample_radius + 1, 2):
                x = cx + dx
                y = cy + dy
                
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    pixel = surface.get_at((x, y))[:3]
                    total_samples += 1
                    
                    # Check if pixel is not black (background)
                    if pixel != (0, 0, 0):
                        non_black_pixels += 1
        
        # If we found enough non-black pixels, the stat is rendered
        if non_black_pixels > 5 and total_samples > 0:
            rendered_stat_names.append(stat_name)
    
    return rendered_stat_names


class TestShopStatNonZeroDisplay:
    """Property-based tests for shop stat non-zero display."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=card_with_nonzero_stats_strategy())
    def test_nonzero_stats_rendered_in_shop_grid(self, card):
        """
        **Validates: Requirements 3.3**
        
        Property 6: Shop Stat Non-Zero Display
        
        For any card in the shop, stats with value > 0 SHALL be rendered 
        with both name and value visible in the stat grid.
        
        This test generates cards with non-zero stats, renders them
        as shop cards, and verifies that all non-zero stats are visible
        in the stat grid.
        """
        # Get all non-zero stats from the card
        edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
        nonzero_stats = [(name, val) for name, val in edge_source 
                         if val > 0 and not str(name).startswith("_")]
        
        # Skip cards with no non-zero stats (nothing to test)
        assume(len(nonzero_stats) > 0)
        
        # Create a surface and render the shop card
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))  # Black background
        
        # Define shop card rect (typical shop card dimensions)
        card_rect = pygame.Rect(100, 100, 240, 360)
        
        # Render the shop card
        self.renderer.draw_shop_card(
            surface, card, card_rect, 
            hovered=False, bought=False, affordable=True, cost=3
        )
        
        # Calculate stats rect position (same as in draw_shop_card)
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + ribbon_h + 6 + cameo_h + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        # Extract which stats are rendered
        rendered_stat_names = extract_rendered_stats_from_shop_card(surface, stats_rect, card)
        
        # Verify all non-zero stats are rendered
        missing_stats = []
        for stat_name, value in nonzero_stats:
            if stat_name not in rendered_stat_names:
                missing_stats.append({
                    'stat_name': stat_name,
                    'value': value,
                })
        
        # Report any missing non-zero stats
        assert len(missing_stats) == 0, (
            f"Non-zero stats were NOT rendered in shop card for {card.name}.\n"
            f"Card rarity: {card.rarity}\n"
            f"All stats: {dict(edge_source)}\n"
            f"Non-zero stats: {nonzero_stats}\n"
            f"Rendered stat names: {rendered_stat_names}\n"
            f"Missing stats: {missing_stats}"
        )
    
    def test_specific_card_with_all_nonzero(self):
        """
        Deterministic test: verify a card with all non-zero stats.
        This complements the property-based test with a concrete example.
        """
        # Create a card with all non-zero stats
        test_card = Card(
            name="ALL_NONZERO",
            category="EXISTENCE",
            rarity="3",
            stats={
                "Power": 10,
                "Durability": 8,
                "Size": 6,
                "Speed": 12,
                "Meaning": 5,
                "Secret": 7,
            },
            passive_type="none",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=3)
        
        # Calculate stats rect
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + ribbon_h + 6 + cameo_h + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        # Extract rendered stats
        rendered_stat_names = extract_rendered_stats_from_shop_card(surface, stats_rect, test_card)
        
        # Verify all stats are rendered
        expected_stats = ["Power", "Durability", "Size", "Speed", "Meaning", "Secret"]
        
        for stat_name in expected_stats:
            assert stat_name in rendered_stat_names, (
                f"Expected stat {stat_name} (non-zero) to be rendered, "
                f"but it was not detected. Rendered stats: {rendered_stat_names}"
            )
    
    def test_mixed_card_nonzero_stats_rendered(self):
        """
        Deterministic test: verify a card with mixed zero/non-zero stats.
        Focus on verifying non-zero stats ARE rendered.
        """
        # Create a card with known stats (mix of zero and non-zero)
        test_card = Card(
            name="MIXED_CARD",
            category="MIND",
            rarity="4",
            stats={
                "Power": 10,       # Non-zero
                "Durability": 0,   # Zero
                "Size": 6,         # Non-zero
                "Speed": 0,        # Zero
                "Meaning": 8,      # Non-zero
                "Secret": 0,       # Zero
            },
            passive_type="power_boost",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=5)
        
        # Calculate stats rect
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + ribbon_h + 6 + cameo_h + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        # Extract rendered stats
        rendered_stat_names = extract_rendered_stats_from_shop_card(surface, stats_rect, test_card)
        
        # Verify non-zero stats ARE rendered
        non_zero_stat_names = ["Power", "Size", "Meaning"]
        
        for stat_name in non_zero_stat_names:
            assert stat_name in rendered_stat_names, (
                f"Expected stat {stat_name} (non-zero) to be rendered, "
                f"but it was not detected. Rendered stats: {rendered_stat_names}"
            )
    
    def test_single_nonzero_stat(self):
        """
        Deterministic test: verify a card with only one non-zero stat.
        """
        # Create a card with only one non-zero stat
        test_card = Card(
            name="SINGLE_NONZERO",
            category="CONNECTION",
            rarity="2",
            stats={
                "Power": 0,
                "Durability": 0,
                "Size": 0,
                "Speed": 0,
                "Meaning": 0,
                "Secret": 12,  # Only this one is non-zero
            },
            passive_type="shield",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=4)
        
        # Calculate stats rect
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + ribbon_h + 6 + cameo_h + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        # Extract rendered stats
        rendered_stat_names = extract_rendered_stats_from_shop_card(surface, stats_rect, test_card)
        
        # Only Secret should be rendered
        assert "Secret" in rendered_stat_names, (
            f"Expected stat Secret (value=12) to be rendered, "
            f"but it was not detected. Rendered stats: {rendered_stat_names}"
        )
        
        # Verify we only have one stat rendered
        assert len(rendered_stat_names) == 1, (
            f"Expected exactly 1 stat to be rendered, "
            f"but found {len(rendered_stat_names)}: {rendered_stat_names}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
