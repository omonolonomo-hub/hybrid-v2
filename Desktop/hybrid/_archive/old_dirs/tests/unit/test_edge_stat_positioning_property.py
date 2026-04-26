"""
Property-based tests for edge stat positioning accuracy.

This test validates that edge stats are positioned accurately near their
corresponding edge midpoints, ensuring clear and consistent stat display.

Feature: board-shop-ui-cleanup-v3
Task: 3.2 Write property test for edge stat positioning accuracy
Property 2: Edge Stat Positioning Accuracy
Validates: Requirements 2.1
"""

import pytest
import pygame
import sys
import os
import math
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer, _hex_corners, _edge_midpoint, _toward_center, EDGE_LABEL_INSET
from engine_core.card import Card


# Strategy for generating card data
def card_strategy():
    """Generate cards with various edge configurations."""
    # Define stat names (must match the 6 stats used in the game)
    stat_names = ["Power", "Durability", "Size", "Speed", "Meaning", "Secret"]
    
    # Generate stat values (0-15 range, with some zeros)
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


def calculate_edge_midpoint_distance(cx: int, cy: int, r: int, edge_index: int) -> float:
    """
    Calculate the distance from center to edge midpoint.
    This is used to verify positioning accuracy.
    """
    corners = _hex_corners(cx, cy, r - 6)
    mp = _edge_midpoint(corners, edge_index)
    return math.hypot(mp[0] - cx, mp[1] - cy)


def calculate_stat_position_distance_from_midpoint(cx: int, cy: int, r: int, edge_index: int) -> float:
    """
    Calculate the distance between the stat position and the edge midpoint.
    This should be approximately equal to EDGE_LABEL_INSET.
    """
    corners = _hex_corners(cx, cy, r - 6)
    mp = _edge_midpoint(corners, edge_index)
    lp = _toward_center(mp[0], mp[1], cx, cy, EDGE_LABEL_INSET)
    return math.hypot(lp[0] - mp[0], lp[1] - mp[1])


class TestEdgeStatPositioningAccuracy:
    """Property-based tests for edge stat positioning accuracy."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=card_strategy())
    def test_edge_stats_positioned_near_midpoints(self, card):
        """
        **Validates: Requirements 2.1**
        
        Property 2: Edge Stat Positioning Accuracy
        
        For any card with non-zero edge stats, each stat value SHALL be positioned
        within a threshold distance (15 pixels) of its corresponding edge midpoint.
        
        This test verifies the mathematical positioning logic rather than pixel rendering,
        ensuring that the _toward_center calculation places stats correctly.
        """
        # Filter out cards with no non-zero stats (nothing to test)
        non_zero_stats = [(name, val) for name, val in card.rotated_edges() 
                          if val > 0 and not str(name).startswith("_")]
        assume(len(non_zero_stats) > 0)  # Need at least one stat to test
        
        # Render parameters (matching draw_hex_card)
        cx, cy, r = 300, 300, 68
        
        # Calculate corners and verify positioning for each non-zero edge
        corners = _hex_corners(cx, cy, r - 6)
        edges = card.rotated_edges()
        
        positioning_errors = []
        
        for index, (stat_name, value) in enumerate(edges[:6]):
            # Skip zero values and internal stats (same logic as renderer)
            if str(stat_name).startswith("_") or value == 0:
                continue
            
            # Calculate edge midpoint
            mp = _edge_midpoint(corners, index)
            
            # Calculate stat position (where renderer places the stat)
            lp = _toward_center(mp[0], mp[1], cx, cy, EDGE_LABEL_INSET)
            
            # Calculate distance from stat position to edge midpoint
            distance = math.hypot(lp[0] - mp[0], lp[1] - mp[1])
            
            # The stat should be positioned EDGE_LABEL_INSET pixels from the midpoint
            # toward the center. Verify this is within threshold.
            expected_distance = EDGE_LABEL_INSET
            threshold = 15  # pixels (as specified in requirements)
            
            # The distance should be approximately EDGE_LABEL_INSET
            # We allow some tolerance for floating point calculations
            if abs(distance - expected_distance) > 1.0:  # 1 pixel tolerance for rounding
                positioning_errors.append({
                    'edge_index': index,
                    'stat_name': stat_name,
                    'value': value,
                    'midpoint': mp,
                    'stat_position': lp,
                    'distance': distance,
                    'expected_distance': expected_distance,
                })
            
            # Also verify the stat is actually closer to center than the midpoint
            dist_mp_to_center = math.hypot(mp[0] - cx, mp[1] - cy)
            dist_lp_to_center = math.hypot(lp[0] - cx, lp[1] - cy)
            
            if dist_lp_to_center >= dist_mp_to_center:
                positioning_errors.append({
                    'edge_index': index,
                    'stat_name': stat_name,
                    'error': 'Stat not moved toward center',
                    'midpoint_dist': dist_mp_to_center,
                    'stat_dist': dist_lp_to_center,
                })
        
        # Report any positioning errors
        assert len(positioning_errors) == 0, (
            f"Edge stat positioning accuracy failed for card {card.name}.\n"
            f"Card stats: {card.rotated_edges()}\n"
            f"Positioning errors: {positioning_errors}"
        )
    
    def test_positioning_logic_correctness(self):
        """
        Deterministic test: verify the positioning logic is mathematically correct.
        
        This test verifies that _toward_center moves a point exactly EDGE_LABEL_INSET
        pixels toward the center, which is the core requirement for accurate positioning.
        """
        # Test parameters
        cx, cy, r = 300, 300, 68
        
        # Test each edge
        corners = _hex_corners(cx, cy, r - 6)
        
        for edge_index in range(6):
            # Get edge midpoint
            mp = _edge_midpoint(corners, edge_index)
            
            # Calculate stat position
            lp = _toward_center(mp[0], mp[1], cx, cy, EDGE_LABEL_INSET)
            
            # Verify distance from midpoint to stat position
            distance = math.hypot(lp[0] - mp[0], lp[1] - mp[1])
            
            # Should be exactly EDGE_LABEL_INSET (within floating point tolerance)
            assert abs(distance - EDGE_LABEL_INSET) < 0.01, (
                f"Edge {edge_index}: stat position distance {distance:.2f} "
                f"does not match EDGE_LABEL_INSET {EDGE_LABEL_INSET}"
            )
            
            # Verify stat is closer to center than midpoint
            dist_mp_to_center = math.hypot(mp[0] - cx, mp[1] - cy)
            dist_lp_to_center = math.hypot(lp[0] - cx, lp[1] - cy)
            
            assert dist_lp_to_center < dist_mp_to_center, (
                f"Edge {edge_index}: stat position ({dist_lp_to_center:.2f}) "
                f"not closer to center than midpoint ({dist_mp_to_center:.2f})"
            )
            
            # Verify the inset amount is correct
            inset_amount = dist_mp_to_center - dist_lp_to_center
            assert abs(inset_amount - EDGE_LABEL_INSET) < 0.01, (
                f"Edge {edge_index}: inset amount {inset_amount:.2f} "
                f"does not match EDGE_LABEL_INSET {EDGE_LABEL_INSET}"
            )
    
    def test_specific_card_positioning(self):
        """
        Deterministic test: verify a specific card's edge stat positioning.
        This complements the property-based test with a concrete example.
        """
        # Create a card with known stats
        test_card = Card(
            name="TEST_CARD",
            category="EXISTENCE",
            rarity="3",
            stats={
                "Power": 10,
                "Durability": 8,
                "Size": 6,
                "Speed": 4,
                "Meaning": 2,
                "Secret": 0,  # Zero value should not be rendered
            },
            passive_type="none",
        )
        
        # Render parameters
        cx, cy, r = 300, 300, 68
        
        # Calculate corners
        corners = _hex_corners(cx, cy, r - 6)
        edges = test_card.rotated_edges()
        
        # Count non-zero stats
        non_zero_count = sum(1 for name, val in edges if val > 0 and not str(name).startswith("_"))
        assert non_zero_count == 5, f"Expected 5 non-zero stats, got {non_zero_count}"
        
        # Verify positioning for each non-zero stat
        for index, (stat_name, value) in enumerate(edges[:6]):
            if str(stat_name).startswith("_") or value == 0:
                continue
            
            # Calculate positions
            mp = _edge_midpoint(corners, index)
            lp = _toward_center(mp[0], mp[1], cx, cy, EDGE_LABEL_INSET)
            
            # Verify distance
            distance = math.hypot(lp[0] - mp[0], lp[1] - mp[1])
            assert abs(distance - EDGE_LABEL_INSET) < 0.01, (
                f"Stat {stat_name} at edge {index}: distance {distance:.2f} "
                f"does not match EDGE_LABEL_INSET {EDGE_LABEL_INSET}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
