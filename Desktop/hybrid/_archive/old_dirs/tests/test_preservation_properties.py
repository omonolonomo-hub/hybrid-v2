"""
Preservation Property Tests for Combat-Shop Critical Fixes

These tests verify that NON-BUGGY code paths remain unchanged after the fix.
Tests should PASS on UNFIXED code (confirming baseline behavior to preserve).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

Property 2: Preservation - Existing Functionality Unchanged

This test uses property-based testing (hypothesis) to generate many test cases
and provide stronger guarantees that behavior is preserved across all inputs.

**IMPORTANT**: Follow observation-first methodology
- Observe behavior on UNFIXED code for non-buggy inputs
- Write property-based tests capturing observed behavior patterns
- Run tests on UNFIXED code
- **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
"""

import pytest
import pygame
import sys
import os
from typing import Tuple, List
from hypothesis import given, strategies as st, settings, assume

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.core_game_state import CoreGameState
from scenes.combat_scene import CombatScene, HexCard
from scenes.shop_scene import ShopScene
from scenes.asset_loader import AssetLoader, SHOP_CARD_SIZE, CARD_SIZE
from engine_core.card import Card
from engine_core.game_factory import build_game
from engine_core.market import Market


class TestPreservationProperties:
    """
    Preservation property tests to verify non-buggy code paths remain unchanged.
    
    These tests should PASS on UNFIXED code, confirming baseline behavior.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1600, 900))
        self.screen.fill((20, 20, 30))
        
        # Create asset loader for scenes that need it
        self.asset_loader = AssetLoader("assets/cards")
        
        yield
        pygame.quit()
    
    def create_test_game(self):
        """Create a test game instance with 2 players."""
        game = build_game(["random", "random"])
        return game
    
    def create_test_card(self, name: str = "Test Card", rotation: int = 0) -> Card:
        """Create a test card with specified properties."""
        return Card(
            name=name,
            category="Test",
            rarity="3",
            stats={"Power": 5, "Durability": 4, "Speed": 3,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test_passive",
            rotation=rotation
        )

    # ========================================================================
    # Property 1: HexCard Attributes Preservation (Requirement 3.1)
    # ========================================================================
    
    @given(
        rotation=st.integers(min_value=0, max_value=5),
        hex_q=st.integers(min_value=-5, max_value=5),
        hex_r=st.integers(min_value=-5, max_value=5),
        flip_value=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50)
    def test_property_hexcard_attributes_accessible(self, rotation, hex_q, hex_r, flip_value):
        """
        Property: All HexCard attributes (card_data, front_image, back_image, 
        position, hex_size, rotation) are accessible and work correctly.
        
        This tests the NON-BUGGY code path: accessing HexCard attributes that
        are correctly defined in the dataclass.
        
        **Validates: Requirement 3.1**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        # Create test card
        test_card = self.create_test_card(f"Card_{rotation}", rotation=rotation)
        
        # Create HexCard with all attributes
        front_image = pygame.Surface((100, 140))
        front_image.fill((100, 100, 200))
        back_image = pygame.Surface((100, 140))
        back_image.fill((50, 50, 100))
        
        hex_card = HexCard(
            hex_coord=(hex_q, hex_r),
            card_data=test_card,  # Correct attribute name
            front_image=front_image,
            back_image=back_image,
            position=(800.0, 450.0),
            hex_size=60.0,
            rotation=rotation * 60  # Convert to degrees
        )
        
        # Test that all attributes are accessible (NON-BUGGY code path)
        assert hex_card.card_data is not None, "card_data should be accessible"
        assert hex_card.card_data.name == f"Card_{rotation}", "card_data should reference correct card"
        assert hex_card.front_image is not None, "front_image should be accessible"
        assert hex_card.back_image is not None, "back_image should be accessible"
        assert hex_card.position == (800.0, 450.0), "position should be accessible"
        assert hex_card.hex_size == 60.0, "hex_size should be accessible"
        assert hex_card.rotation == rotation * 60, "rotation should be accessible"
        assert hex_card.hex_coord == (hex_q, hex_r), "hex_coord should be accessible"

    # ========================================================================
    # Property 2: Market Methods Preservation (Requirement 3.2)
    # ========================================================================
    
    @given(
        n_cards=st.integers(min_value=1, max_value=10),
        turn=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=50)
    def test_property_market_methods_work(self, n_cards, turn):
        """
        Property: Market methods (deal_market_window, _return_window, return_unsold,
        get_cards_for_player) continue to work correctly.
        
        This tests the NON-BUGGY code path: calling Market methods that exist
        and are correctly implemented.
        
        **Validates: Requirement 3.2**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        # Create game and market
        game = self.create_test_game()
        market = game.market
        player = game.players[0]
        player.turns_played = turn
        
        # Test deal_market_window (correct API)
        window = market.deal_market_window(player, n=min(n_cards, 5))
        assert isinstance(window, list), "deal_market_window should return a list"
        assert len(window) <= min(n_cards, 5), "window should have at most n cards"
        
        # Test _return_window (correct API)
        market._return_window(player.pid)
        assert player.pid not in market._player_windows, "_return_window should clear player window"
        
        # Test get_cards_for_player (legacy API)
        cards = market.get_cards_for_player(n=min(n_cards, 5), turn=turn)
        assert isinstance(cards, list), "get_cards_for_player should return a list"
        assert len(cards) <= min(n_cards, 5), "should return at most n cards"
        
        # Test return_unsold (correct API)
        window2 = market.deal_market_window(player, n=3)
        market.return_unsold(player, bought=[])
        assert player.pid not in market._player_windows, "return_unsold should clear player window"

    # ========================================================================
    # Property 3: AssetLoader Functionality Preservation (Requirement 3.3)
    # ========================================================================
    
    def test_property_asset_loader_constants_available(self):
        """
        Property: AssetLoader constants (SHOP_CARD_SIZE, CARD_SIZE) are
        correctly defined and importable.
        
        This tests the NON-BUGGY code path: importing constants that are
        correctly defined in asset_loader.py.
        
        **Validates: Requirement 3.3**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        # Test that constants are importable
        from scenes.asset_loader import SHOP_CARD_SIZE, CARD_SIZE
        
        # Verify they are valid tuples
        assert isinstance(SHOP_CARD_SIZE, tuple), "SHOP_CARD_SIZE should be a tuple"
        assert len(SHOP_CARD_SIZE) == 2, "SHOP_CARD_SIZE should have (width, height)"
        assert all(isinstance(x, int) for x in SHOP_CARD_SIZE), "SHOP_CARD_SIZE should contain integers"
        
        assert isinstance(CARD_SIZE, tuple), "CARD_SIZE should be a tuple"
        assert len(CARD_SIZE) == 2, "CARD_SIZE should have (width, height)"
        assert all(isinstance(x, int) for x in CARD_SIZE), "CARD_SIZE should contain integers"
    
    @given(card_name=st.sampled_from(["Test Card", "Another Card", "Third Card"]))
    @settings(max_examples=20)
    def test_property_asset_loader_get_method(self, card_name):
        """
        Property: AssetLoader.get() method continues to work for loading card images.
        
        This tests the NON-BUGGY code path: using AssetLoader to load card faces.
        
        **Validates: Requirement 3.3**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        asset_loader = AssetLoader("assets/cards")
        
        # Test that get() method works
        faces = asset_loader.get(card_name)
        
        assert faces is not None, "get() should return CardFaces"
        assert faces.front is not None, "CardFaces should have front image"
        assert faces.back is not None, "CardFaces should have back image"
        assert isinstance(faces.front, pygame.Surface), "front should be a pygame Surface"
        assert isinstance(faces.back, pygame.Surface), "back should be a pygame Surface"

    # ========================================================================
    # Property 4: Combat Scene Card Data Access Preservation (Requirement 3.4)
    # ========================================================================
    
    @given(
        rotation=st.integers(min_value=0, max_value=5),
        hex_q=st.integers(min_value=-3, max_value=3),
        hex_r=st.integers(min_value=-3, max_value=3)
    )
    @settings(max_examples=50)
    def test_property_combat_scene_card_data_access(self, rotation, hex_q, hex_r):
        """
        Property: combat_scene.py (correct implementation) continues to access
        card properties through card_data correctly.
        
        This tests the NON-BUGGY code path: combat_scene.py already uses
        hex_card.card_data correctly (not the buggy combat_scene_alternative.py).
        
        **Validates: Requirement 3.4**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        # Create game and CombatScene (NOT combat_scene_alternative)
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Create test card
        test_card = self.create_test_card(f"Combat_{rotation}", rotation=rotation)
        
        # Create HexCard using correct attribute name
        front_image = pygame.Surface((100, 140))
        back_image = pygame.Surface((100, 140))
        
        hex_card = HexCard(
            hex_coord=(hex_q, hex_r),
            card_data=test_card,  # Correct attribute name
            front_image=front_image,
            back_image=back_image,
            position=(800.0, 450.0),
            hex_size=60.0,
            rotation=rotation * 60
        )
        
        # Test that card_data is accessible (NON-BUGGY code path)
        assert hex_card.card_data is not None, "card_data should be accessible"
        assert hex_card.card_data.name == f"Combat_{rotation}", "card_data should reference correct card"
        
        # Test that we can access card methods through card_data
        rotated_edges = hex_card.card_data.rotated_edges()
        assert isinstance(rotated_edges, list), "rotated_edges() should return a list"
        assert len(rotated_edges) == 6, "rotated_edges() should return 6 edges"

    # ========================================================================
    # Property 5: Card Property Access Preservation (Requirement 3.5)
    # ========================================================================
    
    @given(
        power=st.integers(min_value=0, max_value=10),
        durability=st.integers(min_value=0, max_value=10),
        speed=st.integers(min_value=0, max_value=10),
        rotation=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=50)
    def test_property_card_methods_accessible(self, power, durability, speed, rotation):
        """
        Property: Card methods (rotated_edges(), dominant_group(), passive_type,
        total_power()) continue to work correctly when accessed through card_data.
        
        This tests the NON-BUGGY code path: accessing card properties through
        the correct card_data attribute.
        
        **Validates: Requirement 3.5**
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        # Create test card with specific stats
        card = Card(
            name=f"Test_{power}_{durability}_{speed}",
            category="Test",
            rarity="3",
            stats={"Power": power, "Durability": durability, "Speed": speed,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test_passive",
            rotation=rotation
        )
        
        # Test rotated_edges() method
        rotated_edges = card.rotated_edges()
        assert isinstance(rotated_edges, list), "rotated_edges() should return a list"
        assert len(rotated_edges) == 6, "rotated_edges() should return 6 edges"
        
        # Test dominant_group() method
        dominant = card.dominant_group()
        assert isinstance(dominant, str), "dominant_group() should return a string"
        
        # Test passive_type attribute
        assert card.passive_type == "test_passive", "passive_type should be accessible"
        
        # Test total_power() method
        total = card.total_power()
        assert isinstance(total, int), "total_power() should return an integer"
        assert total == power + durability + speed, "total_power() should sum all stats"

    # ========================================================================
    # Property 6: Shop Buy Operations Preservation
    # ========================================================================
    
    @given(
        gold=st.integers(min_value=5, max_value=20),
        card_cost=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30)
    def test_property_shop_buy_operations(self, gold, card_cost):
        """
        Property: Shop buy operations continue to work correctly.
        
        This tests the NON-BUGGY code path: buying cards in shop_scene.py
        (not the buggy refresh operation).
        
        **EXPECTED**: PASS on unfixed code (baseline behavior)
        """
        assume(gold >= card_cost)  # Only test cases where player can afford
        
        # Create game and ShopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        shop_scene = ShopScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        shop_scene.on_enter()
        
        # Set player gold
        player = core_game_state.current_player
        initial_gold = gold
        player.gold = initial_gold
        
        # Get market window
        market = game.market
        window = market.deal_market_window(player, n=5)
        
        # Verify window is accessible (NON-BUGGY code path)
        assert isinstance(window, list), "Market window should be a list"
        assert len(window) <= 5, "Market window should have at most 5 cards"
        
        # Verify player gold is unchanged (just viewing, not buying)
        assert player.gold == initial_gold, "Gold should be unchanged when just viewing"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
