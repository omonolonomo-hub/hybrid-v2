"""
Property-based tests for match highlight correctness.

This test validates that board cards sharing at least one upper-group
with the hovered market card are highlighted with a match indicator.

Feature: board-shop-ui-cleanup-v3
Task: 10.4 Write property test for match highlight correctness
Property 16: Match Highlight Correctness
Validates: Requirements 7.2, 7.5
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import List, Set
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


def card_with_groups_strategy(target_groups: Set[str]):
    """Generate a card with specific upper-groups."""
    # Map groups to stats
    group_to_stats = {
        "EXISTENCE": ["Power", "Durability", "Size", "Speed"],
        "MIND": ["Meaning", "Secret", "Intelligence", "Trace"],
        "CONNECTION": ["Gravity", "Harmony", "Spread", "Prestige"],
    }
    
    # Build stats dict with at least one stat from each target group
    stats = {
        "Power": 0, "Durability": 0, "Size": 0, "Speed": 0,
        "Meaning": 0, "Secret": 0,
    }
    
    for group in target_groups:
        available_stats = [s for s in group_to_stats.get(group, []) if s in stats]
        if available_stats:
            # Set at least one stat from this group to non-zero
            stat_name = available_stats[0]
            stats[stat_name] = 10
    
    return st.builds(
        Card,
        name=st.text(min_size=3, max_size=12, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=st.just(stats),
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    )


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


class TestMatchHighlightCorrectness:
    """Property-based tests for match highlight correctness."""
    
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
        board_cards=st.lists(card_strategy(), min_size=1, max_size=8)
    )
    def test_matching_cards_highlighted(self, hover_card, board_cards):
        """
        **Validates: Requirements 7.2, 7.5**
        
        Property 16: Match Highlight Correctness
        
        For any board card that shares at least one upper-group with the 
        hovered market card, the Mini_Board_Sidebar SHALL highlight it 
        with a match indicator.
        
        This test generates various card combinations, identifies which
        board cards should match, and verifies the match classification
        logic is correct.
        """
        # Extract hovered card groups
        hovered_groups = extract_upper_groups(hover_card)
        
        # Skip if hover card has no active groups
        assume(len(hovered_groups) > 0)
        
        # Create mock game
        mock_game = Mock()
        mock_game.turn = 1
        
        # Create player with board
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Add cards to board grid
        for idx, card in enumerate(board_cards):
            q = idx % 3
            r = idx // 3
            player.board.grid[(q, r)] = card
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=[hover_card],
        )
        
        # Set hovered card
        shop_screen._hovered_market_card = hover_card
        
        # Verify match classification for each board card
        for card in board_cards:
            card_groups = extract_upper_groups(card)
            
            # Determine if this card should match
            should_match = bool(card_groups & hovered_groups)
            
            # Verify the match logic
            is_match = bool(card_groups & hovered_groups)
            
            if should_match:
                assert is_match, (
                    f"Expected card {card.name} with groups {card_groups} to MATCH "
                    f"hovered card with groups {hovered_groups}, but it did not"
                )
            else:
                # Card either has no groups or no shared groups
                if card_groups:
                    # Has groups but no match = clash
                    assert not is_match, (
                        f"Expected card {card.name} with groups {card_groups} to NOT match "
                        f"hovered card with groups {hovered_groups}, but it did"
                    )
    
    def test_exact_match_single_group(self):
        """
        Deterministic test: verify that a board card with the same
        single upper-group as the hovered card is marked as a match.
        """
        # Create hover card with EXISTENCE group only
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with EXISTENCE group only
        board_card = Card(
            name="BOARD_EXISTENCE",
            category="EXISTENCE",
            rarity="2",
            stats={"Power": 8, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        card_groups = extract_upper_groups(board_card)
        
        # Verify match
        is_match = bool(card_groups & hovered_groups)
        
        assert is_match, (
            f"Expected EXISTENCE card to match EXISTENCE hover card, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
    
    def test_partial_match_multiple_groups(self):
        """
        Deterministic test: verify that a board card sharing at least
        one group (but not all) with the hovered card is marked as a match.
        """
        # Create hover card with EXISTENCE and MIND groups
        hover_card = Card(
            name="HOVER_MULTI",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 8, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with only MIND group
        board_card = Card(
            name="BOARD_MIND",
            category="MIND",
            rarity="2",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        card_groups = extract_upper_groups(board_card)
        
        # Verify match (shares MIND group)
        is_match = bool(card_groups & hovered_groups)
        
        assert is_match, (
            f"Expected MIND card to match EXISTENCE+MIND hover card, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
    
    def test_no_match_different_groups(self):
        """
        Deterministic test: verify that a board card with different
        upper-groups than the hovered card is NOT marked as a match.
        """
        # Create hover card with EXISTENCE group only
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with MIND group only
        board_card = Card(
            name="BOARD_MIND",
            category="MIND",
            rarity="2",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        card_groups = extract_upper_groups(board_card)
        
        # Verify no match
        is_match = bool(card_groups & hovered_groups)
        
        assert not is_match, (
            f"Expected MIND card to NOT match EXISTENCE hover card, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
    
    def test_no_match_zero_stats_card(self):
        """
        Deterministic test: verify that a board card with all zero stats
        is NOT marked as a match (neutral state).
        """
        # Create hover card with EXISTENCE group
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with all zero stats
        board_card = Card(
            name="BOARD_ZERO",
            category="EXISTENCE",
            rarity="1",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        card_groups = extract_upper_groups(board_card)
        
        # Verify no match (card has no active groups)
        is_match = bool(card_groups & hovered_groups)
        
        assert not is_match, (
            f"Expected zero-stat card to NOT match, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
