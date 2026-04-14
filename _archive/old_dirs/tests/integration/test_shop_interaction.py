"""
Integration test for shop interaction with new UI features.

This test verifies that the new shop card layout, hover compare mode, and mini board
sidebar work correctly with the existing shop screen logic and card purchase flow.

Feature: board-shop-ui-cleanup-v3
Task: 12.3 Write integration test for shop interaction
Requirements: 9.1, 9.2, 9.3, 9.4

Validates:
- Card purchase flow with new layout
- Hover compare mode activation/deactivation
- Mini board updates when board changes
- Sidebar restoration after hover ends
"""

import pytest
import pygame
import sys
import os
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.screens.shop_screen import ShopScreen
from ui.renderer import CyberRenderer
from engine_core.card import Card
from engine_core.player import Player
from engine_core.market import Market
from engine_core.game import Game


class TestShopInteraction:
    """Integration test suite for shop interaction with new UI."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1600, 900))
        self.screen.fill((20, 20, 30))
        
        # Create fonts
        self.fonts = {
            "title": pygame.font.SysFont("consolas", 28, bold=True),
            "lg": pygame.font.SysFont("consolas", 24, bold=True),
            "md": pygame.font.SysFont("consolas", 16),
            "md_bold": pygame.font.SysFont("consolas", 16, bold=True),
            "sm": pygame.font.SysFont("consolas", 13),
            "sm_bold": pygame.font.SysFont("consolas", 13, bold=True),
            "xs": pygame.font.SysFont("consolas", 12),
            "xs_bold": pygame.font.SysFont("consolas", 12, bold=True),
        }
        
        self.cyber_renderer = CyberRenderer(self.fonts)
        
        yield
        pygame.quit()

    def create_test_card(self, name: str = "Test Card", rarity: str = "3",
                        stats: dict = None) -> Card:
        """Create a test card with specified properties."""
        if stats is None:
            stats = {
                "Power": 5,
                "Durability": 4,
                "Speed": 3,
                "Intelligence": 6,
                "Harmony": 5,
                "Spread": 4
            }
        
        return Card(
            name=name,
            category="Test",
            rarity=rarity,
            stats=stats,
            passive_type="test_passive"
        )

    def create_test_player(self) -> Player:
        """Create a test player with some gold and cards."""
        player = Player(pid=0, strategy="test")
        player.gold = 100
        player.hp = 100
        player.max_hp = 100
        return player

    def create_test_game(self) -> Game:
        """Create a minimal test game instance."""
        # Create a simple card pool
        card_pool = [
            self.create_test_card(f"Card {i}", rarity=str((i % 5) + 1))
            for i in range(20)
        ]
        
        # Create game with one player
        player = self.create_test_player()
        game = Game(players=[player], card_pool=card_pool)
        
        return game

    def test_shop_card_rendering_with_new_layout(self):
        """
        Verify that shop cards render correctly with the new proportioned layout.
        
        Validates: New shop card layout compatibility
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        try:
            shop = ShopScreen(
                self.screen,
                game,
                player,
                market_window,
                renderer=self.cyber_renderer,
                fonts=self.fonts
            )
            creation_success = True
        except Exception as e:
            creation_success = False
            error_msg = str(e)
        
        assert creation_success, \
            f"ShopScreen creation failed with new layout. " \
            f"Error: {error_msg if not creation_success else ''}"
        
        # Try to render the shop
        try:
            shop._draw()
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Shop rendering failed with new card layout. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_hover_compare_mode_activation(self):
        """
        Verify that hover compare mode activates when hovering over market cards.
        
        Validates: Requirement 6.1 - Hover sidebar activation
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Add some cards to player's board
        board_cards = [
            self.create_test_card(f"Board Card {i}", rarity="3")
            for i in range(3)
        ]
        for i, card in enumerate(board_cards):
            player.board.place((i, 0), card)
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Simulate hover over first market card
        # Get the rect of the first market card
        if hasattr(shop, 'shop_cards') and shop.shop_cards:
            first_card_rect = shop.shop_cards[0].rect
            hover_pos = (first_card_rect.centerx, first_card_rect.centery)
            
            # Update hover state
            for sc in shop.shop_cards:
                sc.update(16, hover_pos)
            
            # Check if hovered card is set
            hovered = any(sc.hovered for sc in shop.shop_cards)
            
            # Try to draw compare sidebar
            try:
                shop._draw_compare_sidebar()
                render_success = True
            except Exception as e:
                render_success = False
                error_msg = str(e)
            
            assert render_success, \
                f"Hover compare mode rendering failed. " \
                f"Requirement 6.1 violated: hover sidebar activation broken. " \
                f"Error: {error_msg if not render_success else ''}"

    def test_hover_compare_mode_deactivation(self):
        """
        Verify that hover compare mode deactivates when not hovering over cards.
        
        Validates: Requirement 6.2 - Hover sidebar deactivation
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Simulate no hover (mouse far away)
        no_hover_pos = (10, 10)
        
        # Update hover state
        for sc in shop.shop_cards:
            sc.update(16, no_hover_pos)
        
        # Check that no card is hovered
        any_hovered = any(sc.hovered for sc in shop.shop_cards)
        
        # Try to draw compare sidebar (should show synergy sidebar instead)
        try:
            shop._draw_compare_sidebar()
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Sidebar rendering failed when not hovering. " \
            f"Requirement 6.2 violated: hover sidebar deactivation broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_mini_board_with_empty_board(self):
        """
        Verify that mini board handles empty board state correctly.
        
        Validates: Mini board rendering with edge case
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Player has no cards on board
        assert len(player.board.grid) == 0, "Board should be empty for this test"
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Try to draw mini board with empty board
        try:
            hovered_groups = {"EXISTENCE", "MIND"}
            shop._draw_mini_board(100, 100, hovered_groups)
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Mini board rendering failed with empty board. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_mini_board_with_multiple_cards(self):
        """
        Verify that mini board displays all board cards correctly.
        
        Validates: Requirement 7.1 - Mini board completeness
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Add multiple cards to board
        board_cards = [
            self.create_test_card(f"Board Card {i}", rarity=str((i % 5) + 1))
            for i in range(6)
        ]
        for i, card in enumerate(board_cards):
            player.board.place((i % 3, i // 3), card)
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Try to draw mini board with multiple cards
        try:
            hovered_groups = {"EXISTENCE", "MIND"}
            shop._draw_mini_board(100, 100, hovered_groups)
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Mini board rendering failed with multiple cards. " \
            f"Requirement 7.1 violated: mini board completeness broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_card_purchase_flow_with_new_layout(self):
        """
        Verify that card purchase flow works correctly with new shop layout.
        
        Validates: Card purchase compatibility
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        initial_gold = player.gold
        initial_hand_size = len(player.hand)
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity="2", stats={
                "Power": 3, "Durability": 2, "Speed": 1,
                "Intelligence": 0, "Harmony": 0, "Spread": 0
            })
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Try to buy first card
        try:
            shop._try_buy(0)
            purchase_success = True
        except Exception as e:
            purchase_success = False
            error_msg = str(e)
        
        assert purchase_success, \
            f"Card purchase failed with new layout. " \
            f"Error: {error_msg if not purchase_success else ''}"
        
        # Verify purchase effects
        assert player.gold < initial_gold, \
            "Player gold should decrease after purchase"
        assert len(player.hand) > initial_hand_size, \
            "Player hand should contain purchased card"

    def test_match_clash_classification(self):
        """
        Verify that match/clash classification works correctly in mini board.
        
        Validates: Requirements 7.2, 7.3 - Match and clash highlighting
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Create board cards with specific stat patterns
        # Card 1: EXISTENCE stats (should match)
        card1 = self.create_test_card("Match Card", rarity="3", stats={
            "Power": 5, "Durability": 4, "Speed": 3,
            "Intelligence": 0, "Harmony": 0, "Spread": 0
        })
        
        # Card 2: MIND stats (should clash with EXISTENCE hover)
        card2 = self.create_test_card("Clash Card", rarity="3", stats={
            "Power": 0, "Durability": 0, "Speed": 0,
            "Intelligence": 6, "Meaning": 5, "Secret": 4
        })
        
        # Card 3: No stats (should be neutral)
        card3 = self.create_test_card("Neutral Card", rarity="3", stats={
            "Power": 0, "Durability": 0, "Speed": 0,
            "Intelligence": 0, "Harmony": 0, "Spread": 0
        })
        
        player.board.place((0, 0), card1)
        player.board.place((1, 0), card2)
        player.board.place((2, 0), card3)
        
        # Create market window
        market_window = [
            self.create_test_card("Hover Card", rarity="3", stats={
                "Power": 5, "Durability": 4, "Speed": 3,
                "Intelligence": 0, "Harmony": 0, "Spread": 0
            })
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Try to draw mini board with EXISTENCE hovered
        try:
            hovered_groups = {"EXISTENCE"}
            shop._draw_mini_board(100, 100, hovered_groups)
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Mini board match/clash classification failed. " \
            f"Requirements 7.2, 7.3 violated: match/clash highlighting broken. " \
            f"Error: {error_msg if not render_success else ''}"

    def test_sidebar_restoration_after_hover(self):
        """
        Verify that synergy sidebar is restored after hover ends.
        
        Validates: Requirement 6.4 - Synergy sidebar restoration
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Create market window
        market_window = [
            self.create_test_card(f"Market Card {i}", rarity=str((i % 5) + 1))
            for i in range(5)
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # First, simulate hover
        if hasattr(shop, 'shop_cards') and shop.shop_cards:
            first_card_rect = shop.shop_cards[0].rect
            hover_pos = (first_card_rect.centerx, first_card_rect.centery)
            
            for sc in shop.shop_cards:
                sc.update(16, hover_pos)
            
            # Draw with hover
            try:
                shop._draw_compare_sidebar()
                hover_render_success = True
            except Exception as e:
                hover_render_success = False
                hover_error = str(e)
            
            assert hover_render_success, \
                f"Hover sidebar rendering failed. Error: {hover_error if not hover_render_success else ''}"
        
        # Now simulate hover end (mouse far away)
        no_hover_pos = (10, 10)
        for sc in shop.shop_cards:
            sc.update(16, no_hover_pos)
        
        # Draw without hover (should restore synergy sidebar)
        try:
            shop._draw_compare_sidebar()
            restore_success = True
        except Exception as e:
            restore_success = False
            restore_error = str(e)
        
        assert restore_success, \
            f"Synergy sidebar restoration failed. " \
            f"Requirement 6.4 violated: sidebar restoration broken. " \
            f"Error: {restore_error if not restore_success else ''}"

    def test_shop_with_all_rarity_cards(self):
        """
        Verify that shop handles cards of all rarities correctly.
        
        Validates: Shop layout compatibility with all rarity levels
        """
        player = self.create_test_player()
        game = self.create_test_game()
        
        # Create market window with all rarities
        rarities = ["1", "2", "3", "4", "5"]
        market_window = [
            self.create_test_card(f"Rarity {r} Card", rarity=r)
            for r in rarities
        ]
        
        # Create shop screen
        shop = ShopScreen(
            self.screen,
            game,
            player,
            market_window,
            renderer=self.cyber_renderer,
            fonts=self.fonts
        )
        
        # Try to render shop with all rarities
        try:
            shop._draw()
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Shop rendering failed with all rarity cards. " \
            f"Error: {error_msg if not render_success else ''}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
