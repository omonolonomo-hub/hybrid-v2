"""
Bug Condition Exploration Test for Combat-Shop Critical Fixes

This test surfaces counterexamples that demonstrate the bugs exist on UNFIXED code.
The test is EXPECTED TO FAIL on unfixed code - failure confirms the bugs exist.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

Bug 1: AttributeError when hovering over card in combat_scene_alternative.py
Bug 2: AttributeError when clicking refresh in shop_scene.py  
Bug 3: Verification that asset_loader constants import correctly (should pass)

**CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
**DO NOT attempt to fix the test or the code when it fails.**
**NOTE**: This test encodes the expected behavior - it will validate the fix when it passes.
"""

import pytest
import pygame
import sys
import os
from typing import Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.core_game_state import CoreGameState
from core.input_state import InputState
from scenes.combat_scene_alternative import CombatScene, HexCard
from scenes.shop_scene import ShopScene
from engine_core.card import Card
from engine_core.game_factory import build_game


class TestBugConditionExploration:
    """
    Bug condition exploration tests to surface counterexamples on UNFIXED code.
    
    These tests are EXPECTED TO FAIL on unfixed code:
    - Bug 1: AttributeError: 'HexCard' object has no attribute 'card'
    - Bug 2: AttributeError: 'Market' object has no attribute 'refresh_window'
    - Bug 3: Should PASS (verification only)
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1600, 900))
        self.screen.fill((20, 20, 30))
        
        # Create asset loader for scenes that need it
        from scenes.asset_loader import AssetLoader
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

    def test_bug1_hover_card_in_combat_scene_alternative(self):
        """
        Bug 1: Test hovering over a placed card in combat_scene_alternative.py
        
        **EXPECTED OUTCOME ON UNFIXED CODE**: 
        AttributeError: 'HexCard' object has no attribute 'card'
        
        This test triggers the bug at line 1904 in combat_scene_alternative.py:
        `hovered_card = hex_card.card`  # Should be hex_card.card_data
        
        **Validates: Requirement 1.2**
        """
        print("\n=== Bug 1: Hover Card in combat_scene_alternative.py ===")
        
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Create test card and hex coordinate
        test_card = self.create_test_card("Hover Test Card")
        target_hex = (0, 0)
        
        # Create a HexCard manually to simulate what combat_scene creates
        front_image = pygame.Surface((100, 140))
        front_image.fill((100, 100, 200))
        back_image = pygame.Surface((100, 140))
        back_image.fill((50, 50, 100))
        
        hex_card = HexCard(
            hex_coord=target_hex,
            card_data=test_card,  # Correct attribute name
            front_image=front_image,
            back_image=back_image,
            position=(800, 450),
            hex_size=60.0,
            rotation=0
        )
        
        # Add hex_card to ui_state
        combat_scene.ui_state.hex_cards.append(hex_card)
        
        # Set hovered_hex to trigger the hover logic
        combat_scene.ui_state.hovered_hex = target_hex
        
        # Create input state with mouse position
        combat_scene.last_input_state = InputState([])
        combat_scene.last_input_state.mouse_pos = (800, 450)
        
        # Try to draw the priority popup - this will trigger the bug
        try:
            combat_scene._draw_priority_popup(self.screen)
            
            # If we reach here, the bug is FIXED (or doesn't exist)
            print("✓ No AttributeError - bug appears to be FIXED")
            print("  Expected: AttributeError: 'HexCard' object has no attribute 'card'")
            print("  Actual: Code executed successfully")
            
        except AttributeError as e:
            error_msg = str(e)
            print(f"✗ AttributeError caught: {error_msg}")
            
            # Verify this is the expected bug
            if "'HexCard' object has no attribute 'card'" in error_msg:
                print("✓ EXPECTED BUG CONFIRMED: HexCard.card does not exist")
                print("  Root cause: Line 1904 uses hex_card.card instead of hex_card.card_data")
                
                # Re-raise to fail the test (expected on unfixed code)
                raise
            else:
                # Unexpected AttributeError
                print(f"✗ UNEXPECTED AttributeError: {error_msg}")
                raise

    def test_bug2_click_refresh_in_shop_scene(self):
        """
        Bug 2: Test clicking refresh button in shop_scene.py
        
        **EXPECTED OUTCOME ON UNFIXED CODE**: 
        AttributeError: 'Market' object has no attribute 'refresh_window'
        
        This test triggers the bug at line 546 in shop_scene.py:
        `self.core_game_state.game.market.refresh_window()`  # Method doesn't exist
        
        **Validates: Requirement 1.3**
        """
        print("\n=== Bug 2: Click Refresh in shop_scene.py ===")
        
        # Create game and ShopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        shop_scene = ShopScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        shop_scene.on_enter()
        
        # Give player enough gold to refresh
        current_player = core_game_state.current_player
        current_player.gold = 10  # Ensure player has enough gold
        
        # Try to call _request_refresh - this will trigger the bug
        try:
            shop_scene._request_refresh()
            
            # If we reach here, the bug is FIXED (or doesn't exist)
            print("✓ No AttributeError - bug appears to be FIXED")
            print("  Expected: AttributeError: 'Market' object has no attribute 'refresh_window'")
            print("  Actual: Code executed successfully")
            
        except AttributeError as e:
            error_msg = str(e)
            print(f"✗ AttributeError caught: {error_msg}")
            
            # Verify this is the expected bug
            if "'Market' object has no attribute 'refresh_window'" in error_msg:
                print("✓ EXPECTED BUG CONFIRMED: Market.refresh_window() does not exist")
                print("  Root cause: Line 546 calls non-existent refresh_window() method")
                print("  Correct API: market._return_window(pid) + market.deal_market_window(player, n=5)")
                
                # Re-raise to fail the test (expected on unfixed code)
                raise
            else:
                # Unexpected AttributeError
                print(f"✗ UNEXPECTED AttributeError: {error_msg}")
                raise

    def test_bug3_asset_loader_constants_import(self):
        """
        Bug 3: Verify that SHOP_CARD_SIZE and CARD_SIZE import correctly
        
        **EXPECTED OUTCOME**: This test should PASS (verification only, no bug)
        
        This verifies that asset_loader.py constants are correctly defined and importable.
        
        **Validates: Requirement 1.4**
        """
        print("\n=== Bug 3: AssetLoader Constants Import (Verification) ===")
        
        try:
            from scenes.asset_loader import SHOP_CARD_SIZE, CARD_SIZE
            
            print(f"✓ SHOP_CARD_SIZE imported successfully: {SHOP_CARD_SIZE}")
            print(f"✓ CARD_SIZE imported successfully: {CARD_SIZE}")
            
            # Verify they are tuples with 2 elements (width, height)
            assert isinstance(SHOP_CARD_SIZE, tuple), \
                f"SHOP_CARD_SIZE should be a tuple, got {type(SHOP_CARD_SIZE)}"
            assert len(SHOP_CARD_SIZE) == 2, \
                f"SHOP_CARD_SIZE should have 2 elements, got {len(SHOP_CARD_SIZE)}"
            
            assert isinstance(CARD_SIZE, tuple), \
                f"CARD_SIZE should be a tuple, got {type(CARD_SIZE)}"
            assert len(CARD_SIZE) == 2, \
                f"CARD_SIZE should have 2 elements, got {len(CARD_SIZE)}"
            
            print("✓ Constants are valid tuples with (width, height)")
            print("✓ VERIFICATION PASSED: No bug exists for asset_loader imports")
            
        except ImportError as e:
            print(f"✗ ImportError: {e}")
            print("✗ UNEXPECTED: Constants should be importable")
            raise


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
