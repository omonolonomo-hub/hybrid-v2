"""
Property-based tests for sidebar mutual exclusivity.

This test validates that the synergy sidebar and mini board sidebar are
never visible simultaneously in the shop screen.

Feature: board-shop-ui-cleanup-v3
Task: 9.5 Write property test for sidebar mutual exclusivity
Property 13: Sidebar Mutual Exclusivity
Validates: Requirements 6.3
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import List
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.screens.shop_screen import ShopScreen
from engine_core.card import Card
from engine_core.player import Player


def card_strategy():
    """Generate random cards for testing."""
    stat_names = ["Power", "Durability", "Size", "Speed", "Meaning", "Secret"]
    
    stats_dict = st.fixed_dictionaries({
        stat_names[0]: st.integers(min_value=0, max_value=15),
        stat_names[1]: st.integers(min_value=0, max_value=15),
        stat_names[2]: st.integers(min_value=0, max_value=15),
        stat_names[3]: st.integers(min_value=0, max_value=15),
        stat_names[4]: st.integers(min_value=0, max_value=15),
        stat_names[5]: st.integers(min_value=0, max_value=15),
    })
    
    return st.builds(
        Card,
        name=st.text(min_size=3, max_size=12, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=stats_dict,
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    )


def market_window_strategy():
    """Generate a list of cards for the market window."""
    return st.lists(card_strategy(), min_size=1, max_size=5)


class TestSidebarMutualExclusivity:
    """Property-based tests for sidebar mutual exclusivity."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(market_cards=market_window_strategy())
    def test_sidebars_never_visible_simultaneously(self, market_cards):
        """
        **Validates: Requirements 6.3**
        
        Property 13: Sidebar Mutual Exclusivity
        
        For any UI state, the synergy sidebar and mini board sidebar SHALL NOT 
        be visible simultaneously.
        
        This test generates various market configurations, tests both hover
        and non-hover states, and verifies that only one sidebar type is
        active at any time.
        """
        # Create mock game and player
        mock_game = Mock()
        mock_game.turn = 1
        
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=market_cards,
        )
        
        # Verify shop cards were created
        assume(len(shop_screen.shop_cards) > 0)
        
        # Track which sidebar methods are called
        synergy_called = False
        mini_board_called = False
        
        # Test Case 1: No hover (should show synergy sidebar)
        shop_screen._hovered_market_card = None
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                synergy_called = mock_synergy.called
                mini_board_called = mock_mini_board.called
        
        # When no hover, synergy should be called, mini board should NOT
        assert synergy_called, (
            "Expected _draw_synergy_sidebar to be called when no card is hovered"
        )
        assert not mini_board_called, (
            "Expected _draw_mini_board to NOT be called when no card is hovered"
        )
        
        # Test Case 2: With hover (should show mini board, NOT synergy)
        if len(shop_screen.shop_cards) > 0:
            shop_screen._hovered_market_card = shop_screen.shop_cards[0].card
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    synergy_called = mock_synergy.called
                    mini_board_called = mock_mini_board.called
            
            # When hovering, synergy should NOT be called, mini board should be called
            assert not synergy_called, (
                "Expected _draw_synergy_sidebar to NOT be called when a card is hovered"
            )
            assert mini_board_called, (
                "Expected _draw_mini_board to be called when a card is hovered"
            )
    
    def test_no_hover_shows_only_synergy_sidebar(self):
        """
        Deterministic test: verify that when no card is hovered,
        only the synergy sidebar is shown.
        """
        # Create test card
        test_card = Card(
            name="TEST_CARD",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 8, "Size": 5, "Speed": 3, "Meaning": 0, "Secret": 0},
            passive_type="none",
        )
        
        # Create mock game and player
        mock_game = Mock()
        mock_game.turn = 1
        
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=[test_card],
        )
        
        # Ensure no card is hovered
        shop_screen._hovered_market_card = None
        
        # Track which methods are called
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                # Verify only synergy sidebar is called
                assert mock_synergy.called, (
                    "Expected _draw_synergy_sidebar to be called when no card is hovered"
                )
                assert not mock_mini_board.called, (
                    "Expected _draw_mini_board to NOT be called when no card is hovered"
                )
    
    def test_hover_shows_only_mini_board_sidebar(self):
        """
        Deterministic test: verify that when a card is hovered,
        only the mini board sidebar is shown.
        """
        # Create test card
        test_card = Card(
            name="HOVER_CARD",
            category="MIND",
            rarity="4",
            stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 9},
            passive_type="power_boost",
        )
        
        # Create mock game and player
        mock_game = Mock()
        mock_game.turn = 1
        
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=[test_card],
        )
        
        # Set hovered card
        shop_screen._hovered_market_card = test_card
        
        # Track which methods are called
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                # Verify only mini board is called
                assert not mock_synergy.called, (
                    "Expected _draw_synergy_sidebar to NOT be called when a card is hovered"
                )
                assert mock_mini_board.called, (
                    "Expected _draw_mini_board to be called when a card is hovered"
                )
    
    def test_transition_from_synergy_to_mini_board(self):
        """
        Deterministic test: verify transition from synergy sidebar to
        mini board sidebar when hover state changes.
        """
        # Create test card
        test_card = Card(
            name="TRANSITION_CARD",
            category="CONNECTION",
            rarity="2",
            stats={"Power": 5, "Durability": 5, "Size": 5, "Speed": 5, "Meaning": 5, "Secret": 5},
            passive_type="shield",
        )
        
        # Create mock game and player
        mock_game = Mock()
        mock_game.turn = 1
        
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=[test_card],
        )
        
        # State 1: No hover (synergy sidebar)
        shop_screen._hovered_market_card = None
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                assert mock_synergy.called
                assert not mock_mini_board.called
        
        # State 2: Hover (mini board sidebar)
        shop_screen._hovered_market_card = test_card
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                assert not mock_synergy.called
                assert mock_mini_board.called
        
        # State 3: No hover again (back to synergy sidebar)
        shop_screen._hovered_market_card = None
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                
                assert mock_synergy.called
                assert not mock_mini_board.called
    
    def test_multiple_hover_transitions(self):
        """
        Deterministic test: verify multiple transitions between hover states
        maintain mutual exclusivity.
        """
        # Create test cards
        test_cards = [
            Card(
                name=f"CARD_{i}",
                category="EXISTENCE",
                rarity="3",
                stats={"Power": i, "Durability": i, "Size": i, "Speed": i, "Meaning": i, "Secret": i},
                passive_type="none",
            )
            for i in range(1, 4)
        ]
        
        # Create mock game and player
        mock_game = Mock()
        mock_game.turn = 1
        
        player = Player(pid=1, strategy="random")
        player.gold = 100
        
        # Create shop screen
        shop_screen = ShopScreen(
            screen=self.screen,
            game=mock_game,
            player=player,
            market_window=test_cards,
        )
        
        # Test multiple transitions
        for i in range(5):
            # Alternate between hover and no hover
            if i % 2 == 0:
                shop_screen._hovered_market_card = None
                expected_synergy = True
                expected_mini_board = False
            else:
                shop_screen._hovered_market_card = test_cards[i % len(test_cards)]
                expected_synergy = False
                expected_mini_board = True
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    assert mock_synergy.called == expected_synergy, (
                        f"Iteration {i}: Expected synergy sidebar called={expected_synergy}, "
                        f"got {mock_synergy.called}"
                    )
                    assert mock_mini_board.called == expected_mini_board, (
                        f"Iteration {i}: Expected mini board called={expected_mini_board}, "
                        f"got {mock_mini_board.called}"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
