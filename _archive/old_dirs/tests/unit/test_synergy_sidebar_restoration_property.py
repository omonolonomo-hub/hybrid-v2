"""
Property-based tests for synergy sidebar restoration.

This test validates that the synergy sidebar is restored to visible state
when a hover-end event occurs (mouse moves away from market cards).

Feature: board-shop-ui-cleanup-v3
Task: 9.6 Write property test for synergy sidebar restoration
Property 14: Synergy Sidebar Restoration
Validates: Requirements 6.4
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


class TestSynergySidebarRestoration:
    """Property-based tests for synergy sidebar restoration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(market_cards=market_window_strategy())
    def test_synergy_sidebar_restored_after_hover_end(self, market_cards):
        """
        **Validates: Requirements 6.4**
        
        Property 14: Synergy Sidebar Restoration
        
        For any hover-end event, the synergy sidebar SHALL be restored to 
        visible state.
        
        This test generates various market configurations, simulates hover
        and hover-end events, and verifies that the synergy sidebar is
        restored when hover ends.
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
        
        # Test each card: hover then unhover
        for shop_card in shop_screen.shop_cards:
            # Step 1: Hover over card (mini board should be shown)
            shop_screen._hovered_market_card = shop_card.card
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    # During hover, mini board should be called
                    assert mock_mini_board.called, (
                        f"Expected mini board to be shown during hover of {shop_card.card.name}"
                    )
                    assert not mock_synergy.called, (
                        f"Expected synergy sidebar to NOT be shown during hover of {shop_card.card.name}"
                    )
            
            # Step 2: End hover (synergy sidebar should be restored)
            shop_screen._hovered_market_card = None
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    # After hover ends, synergy sidebar should be restored
                    assert mock_synergy.called, (
                        f"Expected synergy sidebar to be restored after hover end for {shop_card.card.name}"
                    )
                    assert not mock_mini_board.called, (
                        f"Expected mini board to NOT be shown after hover end for {shop_card.card.name}"
                    )
    
    def test_synergy_sidebar_restored_after_single_hover(self):
        """
        Deterministic test: verify synergy sidebar is restored after
        a single hover-end event.
        """
        # Create test card
        test_card = Card(
            name="HOVER_CARD",
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
        
        # Initial state: synergy sidebar visible
        shop_screen._hovered_market_card = None
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            shop_screen._draw_compare_sidebar()
            assert mock_synergy.called, "Expected synergy sidebar initially"
        
        # Hover over card
        shop_screen._hovered_market_card = test_card
        
        with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
            shop_screen._draw_compare_sidebar()
            assert mock_mini_board.called, "Expected mini board during hover"
        
        # End hover
        shop_screen._hovered_market_card = None
        
        with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
            shop_screen._draw_compare_sidebar()
            assert mock_synergy.called, "Expected synergy sidebar restored after hover end"
    
    def test_synergy_sidebar_restored_after_multiple_hovers(self):
        """
        Deterministic test: verify synergy sidebar is restored after
        multiple hover-end events.
        """
        # Create test cards
        test_cards = [
            Card(
                name=f"CARD_{i}",
                category="MIND",
                rarity="2",
                stats={"Power": i, "Durability": i, "Size": i, "Speed": i, "Meaning": i, "Secret": i},
                passive_type="power_boost",
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
        
        # Test multiple hover-unhover cycles
        for card in test_cards:
            # Hover
            shop_screen._hovered_market_card = card
            
            with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                shop_screen._draw_compare_sidebar()
                assert mock_mini_board.called, f"Expected mini board during hover of {card.name}"
            
            # Unhover
            shop_screen._hovered_market_card = None
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                shop_screen._draw_compare_sidebar()
                assert mock_synergy.called, f"Expected synergy sidebar restored after hover end of {card.name}"
    
    def test_synergy_sidebar_state_consistency(self):
        """
        Deterministic test: verify synergy sidebar state remains consistent
        across multiple hover-unhover cycles.
        """
        # Create test card
        test_card = Card(
            name="CONSISTENCY_CARD",
            category="CONNECTION",
            rarity="4",
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
        
        # Perform 10 hover-unhover cycles
        for i in range(10):
            # Hover
            shop_screen._hovered_market_card = test_card
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    assert not mock_synergy.called, f"Cycle {i}: Expected synergy NOT called during hover"
                    assert mock_mini_board.called, f"Cycle {i}: Expected mini board called during hover"
            
            # Unhover
            shop_screen._hovered_market_card = None
            
            with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                with patch.object(shop_screen, '_draw_mini_board') as mock_mini_board:
                    shop_screen._draw_compare_sidebar()
                    
                    assert mock_synergy.called, f"Cycle {i}: Expected synergy called after hover end"
                    assert not mock_mini_board.called, f"Cycle {i}: Expected mini board NOT called after hover end"
    
    def test_rapid_hover_changes_restore_synergy(self):
        """
        Deterministic test: verify synergy sidebar is restored even with
        rapid hover state changes.
        """
        # Create test cards
        test_cards = [
            Card(
                name=f"RAPID_{i}",
                category="EXISTENCE",
                rarity=str((i % 5) + 1),
                stats={"Power": i, "Durability": i, "Size": i, "Speed": i, "Meaning": i, "Secret": i},
                passive_type="none",
            )
            for i in range(5)
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
        
        # Rapidly change hover state
        for i in range(20):
            if i % 3 == 0:
                # Hover over a card
                shop_screen._hovered_market_card = test_cards[i % len(test_cards)]
            else:
                # No hover
                shop_screen._hovered_market_card = None
                
                # Verify synergy sidebar is restored
                with patch.object(shop_screen, '_draw_synergy_sidebar') as mock_synergy:
                    shop_screen._draw_compare_sidebar()
                    assert mock_synergy.called, (
                        f"Iteration {i}: Expected synergy sidebar restored after rapid hover change"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
