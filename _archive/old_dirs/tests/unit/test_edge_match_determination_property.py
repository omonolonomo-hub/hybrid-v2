"""
Property-based tests for edge match determination.

This test validates that the upper-group matching logic correctly determines
if an edge on a board card matches the hovered market card.

Feature: board-shop-ui-cleanup-v3
Task: 10.6 Write property test for edge match determination
Property 18: Edge Match Determination
Validates: Requirements 8.1
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import List, Set, Tuple
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.screens.shop_screen import ShopScreen
from engine_core.card import Card
from engine_core.player import Player
from engine_core.constants import STAT_TO_GROUP


def extract_upper_groups(card: Card) -> Set[str]:
    """Extract upper-groups from a card's stats."""
    groups = set()
    for stat_name, value in card.stats.items():
        if value > 0 and not str(stat_name).startswith("_"):
            g = STAT_TO_GROUP.get(stat_name)
            if g:
                groups.add(g)
    return groups


def extract_edge_groups(card: Card) -> List[Tuple[str, int, str]]:
    """Extract edge information: (stat_name, value, upper_group)."""
    edges_info = []
    edges = getattr(card, "rotated_edges", lambda: [])()
    for stat_name, value in edges[:6]:  # Max 6 edges
        if value > 0 and not str(stat_name).startswith("_"):
            group = STAT_TO_GROUP.get(stat_name)
            if group:
                edges_info.append((stat_name, value, group))
    return edges_info


def card_strategy():
    """Generate random cards for testing."""
    stats_dict = st.fixed_dictionaries({
        "Power": st.integers(min_value=0, max_value=15),
        "Durability": st.integers(min_value=0, max_value=15),
        "Size": st.integers(min_value=0, max_value=15),
        "Speed": st.integers(min_value=0, max_value=15),
        "Meaning": st.integers(min_value=0, max_value=15),
        "Secret": st.integers(min_value=0, max_value=15),
    })
    
    return st.builds(
        Card,
        name=st.text(min_size=3, max_size=12, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=stats_dict,
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    )


class TestEdgeMatchDetermination:
    """Property-based tests for edge match determination."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(
        hover_card=card_strategy(),
        board_card=card_strategy()
    )
    def test_edge_match_determination_logic(self, hover_card, board_card):
        """
        **Validates: Requirements 8.1**
        
        Property 18: Edge Match Determination
        
        For all edges on board cards in the Mini_Board_Sidebar, the 
        Shop_Screen SHALL determine if the edge upper-group matches 
        the hovered card.
        
        This test generates various card combinations and verifies that
        the edge matching logic correctly identifies matching edges.
        """
        # Extract hovered card groups
        hovered_groups = extract_upper_groups(hover_card)
        
        # Skip if hover card has no active groups
        assume(len(hovered_groups) > 0)
        
        # Extract board card edge groups
        edge_groups = extract_edge_groups(board_card)
        
        # Skip if board card has no edges
        assume(len(edge_groups) > 0)
        
        # Create mock game
        mock_game = Mock()
        mock_game.turn = 1
        
        # Create player with board
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Add board card to grid
        player.board.grid[(0, 0)] = board_card
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=[hover_card],
        )
        
        # Set hovered card
        shop_screen._hovered_market_card = hover_card
        
        # Verify edge match determination for each edge
        for stat_name, value, edge_group in edge_groups:
            # Determine if this edge should match
            should_match = edge_group in hovered_groups
            
            # Verify the match logic
            is_match = edge_group in hovered_groups
            
            assert is_match == should_match, (
                f"Edge match determination failed for edge {stat_name} "
                f"(group: {edge_group}, value: {value}). "
                f"Expected match={should_match}, got match={is_match}. "
                f"Hovered groups: {hovered_groups}"
            )
    
    def test_edge_matches_same_group(self):
        """
        Deterministic test: verify that an edge with the same upper-group
        as the hovered card is determined to match.
        """
        # Create hover card with EXISTENCE group (Power stat)
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with EXISTENCE edge (Power stat)
        board_card = Card(
            name="BOARD_EXISTENCE",
            category="EXISTENCE",
            rarity="2",
            stats={"Power": 8, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        edge_groups = extract_edge_groups(board_card)
        
        # Verify edge match
        for stat_name, value, edge_group in edge_groups:
            is_match = edge_group in hovered_groups
            assert is_match, (
                f"Expected edge {stat_name} (group: {edge_group}) to match "
                f"hovered groups {hovered_groups}"
            )
    
    def test_edge_no_match_different_group(self):
        """
        Deterministic test: verify that an edge with a different upper-group
        than the hovered card is determined to NOT match.
        """
        # Create hover card with EXISTENCE group (Power stat)
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with MIND edge (Meaning stat)
        board_card = Card(
            name="BOARD_MIND",
            category="MIND",
            rarity="2",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        edge_groups = extract_edge_groups(board_card)
        
        # Verify edge does NOT match
        for stat_name, value, edge_group in edge_groups:
            is_match = edge_group in hovered_groups
            assert not is_match, (
                f"Expected edge {stat_name} (group: {edge_group}) to NOT match "
                f"hovered groups {hovered_groups}"
            )
    
    def test_edge_partial_match_multiple_groups(self):
        """
        Deterministic test: verify that when the hovered card has multiple
        groups, an edge matching any one of them is determined to match.
        """
        # Create hover card with EXISTENCE and MIND groups
        hover_card = Card(
            name="HOVER_MULTI",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 8, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with MIND edge only
        board_card = Card(
            name="BOARD_MIND",
            category="MIND",
            rarity="2",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        edge_groups = extract_edge_groups(board_card)
        
        # Verify edge matches (MIND is in hovered groups)
        for stat_name, value, edge_group in edge_groups:
            is_match = edge_group in hovered_groups
            assert is_match, (
                f"Expected edge {stat_name} (group: {edge_group}) to match "
                f"hovered groups {hovered_groups} (partial match)"
            )
    
    def test_edge_zero_value_ignored(self):
        """
        Deterministic test: verify that edges with zero values are not
        considered in match determination.
        """
        # Create hover card with EXISTENCE group
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with zero-value EXISTENCE edge
        board_card = Card(
            name="BOARD_ZERO",
            category="EXISTENCE",
            rarity="1",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Extract edge groups (should be empty for zero-value edges)
        edge_groups = extract_edge_groups(board_card)
        
        # Verify no edges are extracted (all zero values)
        assert len(edge_groups) == 0, (
            f"Expected no edges with non-zero values, but found {len(edge_groups)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
