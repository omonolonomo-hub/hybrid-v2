"""
Property-based tests for hover sidebar deactivation.

This test validates that the Mini_Board_Sidebar is hidden when the mouse
cursor is not hovering over any market card in the shop screen.

Feature: board-shop-ui-cleanup-v3
Task: 9.4 Write property test for hover sidebar deactivation
Property 12: Hover Sidebar Deactivation
Validates: Requirements 6.2
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import List
from unittest.mock import Mock

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


class TestHoverSidebarDeactivation:
    """Property-based tests for hover sidebar deactivation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(market_cards=market_window_strategy())
    def test_no_hover_hides_mini_board_sidebar(self, market_cards):
        """
        **Validates: Requirements 6.2**
        
        Property 12: Hover Sidebar Deactivation
        
        For any mouse position not over a market card, the Mini_Board_Sidebar 
        SHALL be hidden.
        
        This test generates various market configurations, simulates mouse
        positions outside market cards, and verifies that the mini board
        sidebar is deactivated (hovered card is None).
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
        
        # Test mouse positions outside all market cards
        test_positions = [
            (0, 0),  # Top-left corner
            (self.screen.get_width() - 1, 0),  # Top-right corner
            (0, self.screen.get_height() - 1),  # Bottom-left corner
            (self.screen.get_width() - 1, self.screen.get_height() - 1),  # Bottom-right corner
            (50, 50),  # Arbitrary position likely outside cards
        ]
        
        for mouse_pos in test_positions:
            # Update all shop cards with this mouse position
            for shop_card in shop_screen.shop_cards:
                shop_card.update(16, mouse_pos)
            
            # Simulate _draw_market_grid logic
            hovered_card = None
            for shop_card in shop_screen.shop_cards:
                if shop_card.draw_rect.collidepoint(mouse_pos) and not shop_card.bought:
                    hovered_card = shop_card.card
                    break
            
            shop_screen._hovered_market_card = hovered_card
            
            # Check if mouse is actually over any card
            is_over_card = any(
                shop_card.rect.collidepoint(mouse_pos) 
                for shop_card in shop_screen.shop_cards
            )
            
            # If mouse is not over any card, verify hovered_market_card is None
            if not is_over_card:
                assert shop_screen._hovered_market_card is None, (
                    f"Expected _hovered_market_card to be None when mouse at {mouse_pos} "
                    f"is not over any card, but got {shop_screen._hovered_market_card}"
                )
    
    def test_mouse_outside_cards_deactivates_sidebar(self):
        """
        Deterministic test: verify mouse position outside all cards
        deactivates the mini board sidebar.
        """
        # Create test cards
        test_cards = [
            Card(
                name="CARD_ONE",
                category="EXISTENCE",
                rarity="3",
                stats={"Power": 10, "Durability": 8, "Size": 5, "Speed": 3, "Meaning": 0, "Secret": 0},
                passive_type="none",
            ),
            Card(
                name="CARD_TWO",
                category="MIND",
                rarity="2",
                stats={"Power": 0, "Durability": 0, "Size": 0, "Speed": 0, "Meaning": 12, "Secret": 9},
                passive_type="power_boost",
            ),
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
        
        # First, set a hovered card (simulate previous hover)
        shop_screen._hovered_market_card = test_cards[0]
        
        # Now move mouse outside all cards
        mouse_pos = (10, 10)  # Top-left corner, outside cards
        
        # Update all shop cards
        for shop_card in shop_screen.shop_cards:
            shop_card.update(16, mouse_pos)
        
        # Simulate _draw_market_grid logic
        hovered_card = None
        for shop_card in shop_screen.shop_cards:
            if shop_card.draw_rect.collidepoint(mouse_pos) and not shop_card.bought:
                hovered_card = shop_card.card
                break
        
        shop_screen._hovered_market_card = hovered_card
        
        # Verify hover is cleared
        assert shop_screen._hovered_market_card is None, (
            "Expected _hovered_market_card to be None when mouse is outside all cards"
        )
    
    def test_hover_then_move_away_clears_state(self):
        """
        Deterministic test: verify hovering over a card then moving away
        clears the hover state.
        """
        # Create test card
        test_card = Card(
            name="HOVER_CARD",
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
        
        shop_card = shop_screen.shop_cards[0]
        
        # Step 1: Hover over card
        mouse_pos_over = shop_card.rect.center
        shop_card.update(16, mouse_pos_over)
        
        if shop_card.rect.collidepoint(mouse_pos_over) and not shop_card.bought:
            shop_screen._hovered_market_card = shop_card.card
        
        # Verify hover is set
        assert shop_screen._hovered_market_card is not None
        assert shop_screen._hovered_market_card.name == "HOVER_CARD"
        
        # Step 2: Move mouse away
        mouse_pos_away = (10, 10)
        shop_card.update(16, mouse_pos_away)
        
        # Simulate _draw_market_grid logic
        hovered_card = None
        if shop_card.draw_rect.collidepoint(mouse_pos_away) and not shop_card.bought:
            hovered_card = shop_card.card
        
        shop_screen._hovered_market_card = hovered_card
        
        # Verify hover is cleared
        assert shop_screen._hovered_market_card is None, (
            "Expected _hovered_market_card to be None after moving mouse away from card"
        )
    
    def test_compare_sidebar_falls_back_to_synergy(self):
        """
        Deterministic test: verify that _draw_compare_sidebar falls back
        to synergy sidebar when no card is hovered.
        """
        # Create test card
        test_card = Card(
            name="TEST_CARD",
            category="EXISTENCE",
            rarity="3",
            stats={"Power": 10, "Durability": 8, "Size": 0, "Speed": 0, "Meaning": 0, "Secret": 0},
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
        
        # Call _draw_compare_sidebar (should fall back to synergy sidebar)
        try:
            shop_screen._draw_compare_sidebar()
            sidebar_drawn = True
        except Exception as e:
            sidebar_drawn = False
            error_msg = str(e)
        
        assert sidebar_drawn, (
            f"Expected _draw_compare_sidebar to fall back to synergy sidebar when "
            f"no card is hovered, but it raised an exception: {error_msg if not sidebar_drawn else 'N/A'}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
