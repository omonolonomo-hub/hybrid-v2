"""
Property-based tests for upper-group color consistency.

This test validates that stats belonging to the same upper-group
are rendered in the same color family in the shop card stat grid.

Feature: board-shop-ui-cleanup-v3
Task: 5.4 Write property test for upper-group color consistency
Property 7: Upper-Group Color Consistency
Validates: Requirements 3.4
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Tuple, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer, GROUP_COLORS
from engine_core.card import Card
from engine_core.constants import STAT_TO_GROUP


# Strategy for generating cards with multiple stats in the same upper-group
def card_with_same_group_stats_strategy():
    """Generate cards with at least 2 non-zero stats in the same upper-group."""
    # Define stat groups
    existence_stats = ["Power", "Durability", "Size", "Speed"]
    mind_stats = ["Meaning", "Secret"]
    
    # We'll ensure at least 2 stats from one group are non-zero
    # Strategy: pick a group and ensure at least 2 stats from it are non-zero
    
    def make_stats_dict(group_choice):
        """Create a stats dict with at least 2 non-zero stats from the chosen group."""
        stats = {}
        
        if group_choice == "EXISTENCE":
            # Ensure at least 2 existence stats are non-zero
            stats["Power"] = st.integers(min_value=1, max_value=15)
            stats["Durability"] = st.integers(min_value=1, max_value=15)
            stats["Size"] = st.integers(min_value=0, max_value=15)
            stats["Speed"] = st.integers(min_value=0, max_value=15)
            stats["Meaning"] = st.integers(min_value=0, max_value=15)
            stats["Secret"] = st.integers(min_value=0, max_value=15)
        elif group_choice == "MIND":
            # Ensure both mind stats are non-zero
            stats["Power"] = st.integers(min_value=0, max_value=15)
            stats["Durability"] = st.integers(min_value=0, max_value=15)
            stats["Size"] = st.integers(min_value=0, max_value=15)
            stats["Speed"] = st.integers(min_value=0, max_value=15)
            stats["Meaning"] = st.integers(min_value=1, max_value=15)
            stats["Secret"] = st.integers(min_value=1, max_value=15)
        
        return st.fixed_dictionaries(stats)
    
    # Choose which group to focus on
    group_choice = st.sampled_from(["EXISTENCE", "MIND"])
    
    return group_choice.flatmap(lambda g: st.builds(
        Card,
        name=st.text(min_size=3, max_size=12, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=make_stats_dict(g),
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    ))


def extract_stat_colors_from_shop_card(surface: pygame.Surface, 
                                       stats_rect: pygame.Rect,
                                       card: Card) -> Dict[str, Tuple[int, int, int]]:
    """
    Extract the dominant color used for each stat in the shop card stat grid.
    
    Returns a dict mapping stat names to their rendered color (RGB tuple).
    """
    # Get the real stats that should be rendered (non-zero, non-internal)
    edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
    real_stats = []
    for stat_name, value in edge_source:
        if str(stat_name).startswith("_") or value <= 0:
            continue
        real_stats.append((stat_name, value))
    
    if not real_stats:
        return {}
    
    # Calculate grid layout (same logic as draw_shop_stat_grid)
    cols = 2
    rows = (len(real_stats) + cols - 1) // cols
    cell_w = (stats_rect.width - 6) // cols
    cell_h = max(28, (stats_rect.height - 6) // max(1, rows))
    
    stat_colors = {}
    
    for idx, (stat_name, value) in enumerate(real_stats):
        col = idx % cols
        row = idx // cols
        cell = pygame.Rect(
            stats_rect.x + col * cell_w,
            stats_rect.y + row * cell_h,
            cell_w - 6, cell_h - 4,
        )
        
        # Sample pixels in the cell to find the dominant non-black color
        color_counts = {}
        sample_radius = 8
        
        # Sample around the center of the cell
        cx = cell.centerx
        cy = cell.centery
        
        for dx in range(-sample_radius, sample_radius + 1, 2):
            for dy in range(-sample_radius, sample_radius + 1, 2):
                x = cx + dx
                y = cy + dy
                
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    pixel = surface.get_at((x, y))[:3]
                    
                    # Skip black (background) and very dark colors
                    if pixel != (0, 0, 0) and sum(pixel) > 30:
                        color_counts[pixel] = color_counts.get(pixel, 0) + 1
        
        # Find the most common non-black color
        if color_counts:
            dominant_color = max(color_counts.items(), key=lambda x: x[1])[0]
            stat_colors[stat_name] = dominant_color
    
    return stat_colors


def colors_are_similar(color1: Tuple[int, int, int], 
                       color2: Tuple[int, int, int], 
                       threshold: int = 50) -> bool:
    """
    Check if two colors are similar (within threshold distance in RGB space).
    """
    r_diff = abs(color1[0] - color2[0])
    g_diff = abs(color1[1] - color2[1])
    b_diff = abs(color1[2] - color2[2])
    
    # Use Euclidean distance
    distance = (r_diff**2 + g_diff**2 + b_diff**2) ** 0.5
    
    return distance <= threshold


class TestUpperGroupColorConsistency:
    """Property-based tests for upper-group color consistency."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=card_with_same_group_stats_strategy())
    def test_same_group_stats_use_same_color(self, card):
        """
        **Validates: Requirements 3.4**
        
        Property 7: Upper-Group Color Consistency
        
        For any card with multiple stats in the same upper-group, 
        those stats SHALL be rendered in the same color family.
        
        This test generates cards with multiple stats in the same upper-group,
        renders them as shop cards, and verifies that stats in the same group
        use the same color.
        """
        # Get all non-zero stats from the card
        edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
        nonzero_stats = [(name, val) for name, val in edge_source 
                         if val > 0 and not str(name).startswith("_")]
        
        # Group stats by upper-group
        stats_by_group = {}
        for stat_name, value in nonzero_stats:
            group = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            if group not in stats_by_group:
                stats_by_group[group] = []
            stats_by_group[group].append(stat_name)
        
        # Skip if no group has at least 2 stats
        has_multiple_in_group = any(len(stats) >= 2 for stats in stats_by_group.values())
        assume(has_multiple_in_group)
        
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
        
        # Extract stat colors
        stat_colors = extract_stat_colors_from_shop_card(surface, stats_rect, card)
        
        # Verify color consistency within each group
        inconsistencies = []
        for group, stat_names in stats_by_group.items():
            if len(stat_names) < 2:
                continue
            
            # Get colors for all stats in this group
            group_colors = []
            for stat_name in stat_names:
                if stat_name in stat_colors:
                    group_colors.append((stat_name, stat_colors[stat_name]))
            
            if len(group_colors) < 2:
                continue
            
            # Check if all colors in this group are similar
            reference_stat, reference_color = group_colors[0]
            for stat_name, color in group_colors[1:]:
                if not colors_are_similar(reference_color, color, threshold=50):
                    inconsistencies.append({
                        'group': group,
                        'reference_stat': reference_stat,
                        'reference_color': reference_color,
                        'inconsistent_stat': stat_name,
                        'inconsistent_color': color,
                    })
        
        # Report any color inconsistencies
        assert len(inconsistencies) == 0, (
            f"Stats in the same upper-group have inconsistent colors for {card.name}.\n"
            f"Card rarity: {card.rarity}\n"
            f"Stats by group: {stats_by_group}\n"
            f"Stat colors: {stat_colors}\n"
            f"Inconsistencies: {inconsistencies}"
        )
    
    def test_existence_group_color_consistency(self):
        """
        Deterministic test: verify EXISTENCE group stats use the same color.
        """
        # Create a card with multiple EXISTENCE stats
        test_card = Card(
            name="EXISTENCE_TEST",
            category="EXISTENCE",
            rarity="3",
            stats={
                "Power": 10,       # EXISTENCE
                "Durability": 8,   # EXISTENCE
                "Size": 6,         # EXISTENCE
                "Speed": 0,        # EXISTENCE (zero, won't be rendered)
                "Meaning": 0,      # MIND (zero)
                "Secret": 0,       # MIND (zero)
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
        
        # Extract stat colors
        stat_colors = extract_stat_colors_from_shop_card(surface, stats_rect, test_card)
        
        # Verify all EXISTENCE stats use similar colors
        existence_stats = ["Power", "Durability", "Size"]
        colors = [stat_colors[stat] for stat in existence_stats if stat in stat_colors]
        
        assert len(colors) >= 2, "Expected at least 2 EXISTENCE stats to be rendered"
        
        reference_color = colors[0]
        for i, color in enumerate(colors[1:], 1):
            assert colors_are_similar(reference_color, color, threshold=50), (
                f"EXISTENCE stats have inconsistent colors: "
                f"{existence_stats[0]}={reference_color}, "
                f"{existence_stats[i]}={color}"
            )
    
    def test_mind_group_color_consistency(self):
        """
        Deterministic test: verify MIND group stats use the same color.
        """
        # Create a card with both MIND stats
        test_card = Card(
            name="MIND_TEST",
            category="MIND",
            rarity="4",
            stats={
                "Power": 0,        # EXISTENCE (zero)
                "Durability": 0,   # EXISTENCE (zero)
                "Size": 0,         # EXISTENCE (zero)
                "Speed": 0,        # EXISTENCE (zero)
                "Meaning": 12,     # MIND
                "Secret": 9,       # MIND
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
        
        # Extract stat colors
        stat_colors = extract_stat_colors_from_shop_card(surface, stats_rect, test_card)
        
        # Verify both MIND stats use similar colors
        mind_stats = ["Meaning", "Secret"]
        colors = [stat_colors[stat] for stat in mind_stats if stat in stat_colors]
        
        assert len(colors) == 2, "Expected both MIND stats to be rendered"
        
        assert colors_are_similar(colors[0], colors[1], threshold=50), (
            f"MIND stats have inconsistent colors: "
            f"Meaning={colors[0]}, Secret={colors[1]}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
