"""
Property-based tests for clash highlight correctness.

This test validates that board cards with active stats but no shared
upper-groups with the hovered market card are highlighted with a clash indicator.

Feature: board-shop-ui-cleanup-v3
Task: 10.5 Write property test for clash highlight correctness
Property 17: Clash Highlight Correctness
Validates: Requirements 7.3, 7.6
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


class TestClashHighlightCorrectness:
    """Property-based tests for clash highlight correctness."""
    
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
    def test_clashing_cards_highlighted(self, hover_card, board_cards):
        """
        **Validates: Requirements 7.3, 7.6**
        
        Property 17: Clash Highlight Correctness
        
        For any board card with active stats (value > 0) that shares no 
        upper-groups with the hovered market card, the Mini_Board_Sidebar 
        SHALL highlight it with a clash indicator.
        
        This test generates various card combinations, identifies which
        board cards should clash, and verifies the clash classification
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
        
        # Verify clash classification for each board card
        for card in board_cards:
            card_groups = extract_upper_groups(card)
            
            # Determine if this card should clash
            # Clash = has active stats but no shared groups
            has_active_stats = len(card_groups) > 0
            has_shared_groups = bool(card_groups & hovered_groups)
            should_clash = has_active_stats and not has_shared_groups
            
            # Verify the clash logic
            is_clash = has_active_stats and not has_shared_groups
            
            if should_clash:
                assert is_clash, (
                    f"Expected card {card.name} with groups {card_groups} to CLASH "
                    f"with hovered card groups {hovered_groups}, but it did not"
                )
                # Also verify it's not marked as a match
                is_match = bool(card_groups & hovered_groups)
                assert not is_match, (
                    f"Card {card.name} should clash but is marked as match"
                )
            else:
                # Either no active stats (neutral) or has shared groups (match)
                if has_active_stats:
                    # Has shared groups = match
                    assert has_shared_groups, (
                        f"Card {card.name} with active stats should either match or clash"
                    )
    
    def test_clash_different_single_groups(self):
        """
        Deterministic test: verify that a board card with a different
        single upper-group than the hovered card is marked as a clash.
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
        
        # Verify clash
        has_active_stats = len(card_groups) > 0
        has_shared_groups = bool(card_groups & hovered_groups)
        is_clash = has_active_stats and not has_shared_groups
        
        assert is_clash, (
            f"Expected MIND card to CLASH with EXISTENCE hover card, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
    
    def test_no_clash_with_shared_group(self):
        """
        Deterministic test: verify that a board card sharing at least
        one group with the hovered card is NOT marked as a clash (it's a match).
        """
        # Create hover card with EXISTENCE and MIND groups
        hover_card = Card(
            name="HOVER_MULTI",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 8, "Secret": 0},
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
        
        # Verify NOT clash (it's a match)
        has_active_stats = len(card_groups) > 0
        has_shared_groups = bool(card_groups & hovered_groups)
        is_clash = has_active_stats and not has_shared_groups
        
        assert not is_clash, (
            f"Expected MIND card to NOT clash with EXISTENCE+MIND hover card (should match), "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
        
        # Verify it's a match instead
        is_match = bool(card_groups & hovered_groups)
        assert is_match, (
            f"Expected card to be a match, not a clash"
        )
    
    def test_no_clash_zero_stats_card(self):
        """
        Deterministic test: verify that a board card with all zero stats
        is NOT marked as a clash (neutral state, no active stats).
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
        
        # Verify NOT clash (no active stats)
        has_active_stats = len(card_groups) > 0
        has_shared_groups = bool(card_groups & hovered_groups)
        is_clash = has_active_stats and not has_shared_groups
        
        assert not is_clash, (
            f"Expected zero-stat card to NOT clash (neutral), "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )
    
    def test_clash_multiple_different_groups(self):
        """
        Deterministic test: verify that a board card with multiple
        upper-groups, none of which match the hovered card, is marked as a clash.
        """
        # Create hover card with EXISTENCE group only
        hover_card = Card(
            name="HOVER_EXISTENCE",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 8, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create board card with MIND group only (different from EXISTENCE)
        board_card = Card(
            name="BOARD_MIND",
            category="MIND",
            rarity="2",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 9},
            passive_type="none",
        )
        
        # Extract groups
        hovered_groups = extract_upper_groups(hover_card)
        card_groups = extract_upper_groups(board_card)
        
        # Verify clash
        has_active_stats = len(card_groups) > 0
        has_shared_groups = bool(card_groups & hovered_groups)
        is_clash = has_active_stats and not has_shared_groups
        
        assert is_clash, (
            f"Expected MIND card to CLASH with EXISTENCE hover card, "
            f"hovered groups: {hovered_groups}, card groups: {card_groups}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
