"""
Property-based tests for zero edge stat invisibility.

This test validates that all edges with zero values are NOT rendered
on the board card, ensuring visual clarity by hiding inactive stats.

Feature: board-shop-ui-cleanup-v3
Task: 3.4 Write property test for zero edge stat invisibility
Property 4: Zero Edge Stat Invisibility
Validates: Requirements 2.5
"""

import pytest
import pygame
import sys
import os
import math
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer, _hex_corners, _edge_midpoint, _toward_center, EDGE_LABEL_INSET
from engine_core.card import Card


# Strategy for generating card data with some zero-value edges
def card_with_zero_edges_strategy():
    """Generate cards with at least one zero-value edge."""
    # Define stat names (must match the 6 stats used in the game)
    stat_names = ["Power", "Durability", "Size", "Speed", "Meaning", "Secret"]
    
    # Generate stat values ensuring at least one zero
    # We'll use a strategy that creates a mix but guarantees at least one zero
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


def extract_rendered_stat_colors(surface: pygame.Surface, cx: int, cy: int, r: int, 
                                  edges: List[Tuple[str, int]]) -> Dict[int, bool]:
    """
    Extract which edge positions have rendered stat values by checking for colored pixels.
    
    Returns a dict mapping edge_index -> is_rendered (bool)
    """
    corners = _hex_corners(cx, cy, r - 6)
    rendered_stats = {}
    
    for index, (stat_name, value) in enumerate(edges[:6]):
        # Calculate where the stat should be rendered
        mp = _edge_midpoint(corners, index)
        lp = _toward_center(mp[0], mp[1], cx, cy, EDGE_LABEL_INSET)
        
        # Sample pixels in a small region around the stat position
        # to detect if text was rendered there
        sample_radius = 10  # pixels around the stat position
        non_black_pixels = 0
        total_samples = 0
        
        for dx in range(-sample_radius, sample_radius + 1, 1):
            for dy in range(-sample_radius, sample_radius + 1, 1):
                x = int(lp[0] + dx)
                y = int(lp[1] + dy)
                
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    pixel = surface.get_at((x, y))[:3]
                    total_samples += 1
                    
                    # Check if pixel is not black (background)
                    # Text rendering includes the stat color plus shadows
                    if pixel != (0, 0, 0):
                        non_black_pixels += 1
        
        # If we found enough non-black pixels in the region, the stat is rendered
        # Use a threshold to account for the text being rendered
        # Text should occupy a reasonable portion of the sample area
        is_rendered = non_black_pixels > 10 and total_samples > 0
        rendered_stats[index] = is_rendered
    
    return rendered_stats


class TestZeroEdgeStatInvisibility:
    """Property-based tests for zero edge stat invisibility."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=card_with_zero_edges_strategy())
    def test_all_zero_edges_are_not_rendered(self, card):
        """
        **Validates: Requirements 2.5**
        
        Property 4: Zero Edge Stat Invisibility
        
        For any card, all edges with value == 0 SHALL NOT be rendered.
        
        This test generates cards with some zero-value edges, renders them,
        and verifies that no zero-value edges have visible stat text rendered.
        """
        # Get edges
        edges = card.rotated_edges()
        zero_edges = [(idx, name, val) for idx, (name, val) in enumerate(edges[:6])
                      if val == 0 and not str(name).startswith("_")]
        
        # Skip cards with no zero stats (nothing to test)
        assume(len(zero_edges) > 0)
        
        # Create a surface and render the card
        surface = pygame.Surface((600, 600))
        surface.fill((0, 0, 0))  # Black background
        
        cx, cy, r = 300, 300, 68
        
        # Render the card
        self.renderer.draw_hex_card(surface, card, (cx, cy), r, is_hovered=False, highlighted=False)
        
        # Extract which stats are rendered
        rendered_stats = extract_rendered_stat_colors(surface, cx, cy, r, edges)
        
        # Verify all zero edges are NOT rendered
        incorrectly_rendered = []
        for idx, stat_name, value in zero_edges:
            if rendered_stats.get(idx, False):
                incorrectly_rendered.append({
                    'edge_index': idx,
                    'stat_name': stat_name,
                    'value': value,
                })
        
        # Report any incorrectly rendered zero stats
        assert len(incorrectly_rendered) == 0, (
            f"Zero-value edge stats were incorrectly rendered for card {card.name}.\n"
            f"Card rarity: {card.rarity}\n"
            f"Card rotation: {card.rotation}\n"
            f"All edges: {edges}\n"
            f"Zero edges: {zero_edges}\n"
            f"Rendered stats: {rendered_stats}\n"
            f"Incorrectly rendered: {incorrectly_rendered}"
        )
    
    def test_specific_card_with_all_zeros(self):
        """
        Deterministic test: verify a card with all zero edges.
        This complements the property-based test with a concrete example.
        """
        # Create a card with all zero stats
        test_card = Card(
            name="ALL_ZERO",
            category="EXISTENCE",
            rarity="3",
            stats={
                "Power": 0,
                "Durability": 0,
                "Size": 0,
                "Speed": 0,
                "Meaning": 0,
                "Secret": 0,
            },
            passive_type="none",
        )
        
        # Create surface and render
        surface = pygame.Surface((600, 600))
        surface.fill((0, 0, 0))
        
        cx, cy, r = 300, 300, 68
        self.renderer.draw_hex_card(surface, test_card, (cx, cy), r)
        
        # Get edges
        edges = test_card.rotated_edges()
        
        # Extract rendered stats
        rendered_stats = extract_rendered_stat_colors(surface, cx, cy, r, edges)
        
        # Verify no stats are rendered
        for idx in range(6):
            stat_name, value = edges[idx]
            assert not rendered_stats.get(idx, False), (
                f"Expected stat {stat_name} (value={value}) at edge {idx} to NOT be rendered, "
                f"but it was detected. Rendered stats: {rendered_stats}"
            )
    
    def test_mixed_card_zero_edges_not_rendered(self):
        """
        Deterministic test: verify a card with mixed zero/non-zero edges.
        Focus on verifying zero edges are not rendered.
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
        surface = pygame.Surface((600, 600))
        surface.fill((0, 0, 0))
        
        cx, cy, r = 300, 300, 68
        self.renderer.draw_hex_card(surface, test_card, (cx, cy), r)
        
        # Get edges
        edges = test_card.rotated_edges()
        
        # Extract rendered stats
        rendered_stats = extract_rendered_stat_colors(surface, cx, cy, r, edges)
        
        # Verify zero stats are NOT rendered
        expected_not_rendered = [1, 3, 5]  # Indices of zero stats
        
        for idx in expected_not_rendered:
            stat_name, value = edges[idx]
            assert not rendered_stats.get(idx, False), (
                f"Expected stat {stat_name} (value={value}) at edge {idx} to NOT be rendered, "
                f"but it was detected. Rendered stats: {rendered_stats}"
            )
    
    def test_single_zero_edge(self):
        """
        Deterministic test: verify a card with only one zero edge.
        """
        # Create a card with only one zero stat
        test_card = Card(
            name="SINGLE_ZERO",
            category="CONNECTION",
            rarity="2",
            stats={
                "Power": 5,
                "Durability": 7,
                "Size": 3,
                "Speed": 9,
                "Meaning": 11,
                "Secret": 0,  # Only this one is zero
            },
            passive_type="shield",
        )
        
        # Create surface and render
        surface = pygame.Surface((600, 600))
        surface.fill((0, 0, 0))
        
        cx, cy, r = 300, 300, 68
        self.renderer.draw_hex_card(surface, test_card, (cx, cy), r)
        
        # Get edges
        edges = test_card.rotated_edges()
        
        # Extract rendered stats
        rendered_stats = extract_rendered_stat_colors(surface, cx, cy, r, edges)
        
        # Only edge 5 (Secret) should NOT be rendered
        stat_name, value = edges[5]
        assert not rendered_stats.get(5, False), (
            f"Expected stat {stat_name} (value={value}) at edge 5 to NOT be rendered, "
            f"but it was detected. Rendered stats: {rendered_stats}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
