"""
Bug Condition Exploration Test: K_v Shortcut Bypass
═══════════════════════════════════════════════════════════════════

Property 1: Bug Condition - K_v Bypasses commit_human_turn()

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
DO NOT attempt to fix the test or the code when it fails
NOTE: This test encodes the expected behavior - it will validate the fix when it passes

GOAL: Surface counterexamples that demonstrate the bypass exists

Test implementation details from Bug Condition in design:
- Test the K_v handler logic in isolation (no full ShopScene mock needed)
- Set Config.DEBUG_MODE = False (production mode)
- Verify that with DEBUG_MODE=False, the handler does NOT call controller.handle_shop_action()
- Verify that with DEBUG_MODE=True, the handler DOES call controller.handle_shop_action("ready")

EXPECTED OUTCOME: Test FAILS (K_v bypasses logic - this is correct, it proves the bug exists)

Requirements: 1.3, 1.4, 1.5, 1.6
═══════════════════════════════════════════════════════════════════
"""

import pytest
import pygame
from unittest.mock import Mock, patch
from v2.core.game_state import GameState
from v2.mock.engine_mock import MockGame
from v2.scenes.shop import ShopScene
from v2.constants import Config


class TestKvShortcutBypassBugCondition:
    """
    Bug Condition Exploration: K_v shortcut bypasses commit_human_turn()
    
    These tests demonstrate the bug on UNFIXED code by showing that
    K_v directly transitions to STATE_VERSUS without calling commit_human_turn(),
    which causes AI turn bypass, market cleanup bypass, and pool_copies corruption.
    """
    
    @pytest.fixture
    def shop_scene(self):
        """Create a ShopScene instance with real GameState and MockGame"""
        # Initialize pygame if not already initialized
        if not pygame.get_init():
            pygame.init()
            pygame.display.set_mode((1, 1))  # Minimal display for testing
        
        # Create real GameState with MockGame
        gs = GameState()
        mock_game = MockGame()
        mock_game.initialize_deterministic_fixture()
        gs.hook_engine(mock_game)
        
        # Create ShopScene
        scene = ShopScene(gs)
        
        # Mock the controller to track calls
        original_handle_shop_action = scene.controller.handle_shop_action
        scene.controller.handle_shop_action = Mock(side_effect=original_handle_shop_action)
        
        # Mock phase_machine to track transitions
        original_transition_to = scene.phase_machine.transition_to
        scene.phase_machine.transition_to = Mock(side_effect=original_transition_to)
        
        return scene
    
    def test_kv_bypasses_commit_in_production_mode(self, shop_scene):
        """
        Test Case 1: K_v bypasses commit_human_turn() when DEBUG_MODE=False
        
        Bug Condition: isBugCondition(input) where
            input.key == pygame.K_v AND
            Config.DEBUG_MODE == False
        
        Expected Behavior (after fix): K_v is ignored when DEBUG_MODE=False
        Current Behavior (unfixed): K_v directly calls phase_machine.transition_to("STATE_VERSUS")
                                    without calling controller.handle_shop_action()
        
        This causes:
        - AI opponent does not play its turn
        - Market does not clean up properly
        - pool_copies state becomes corrupted
        """
        # Set production mode (DEBUG_MODE=False)
        with patch.object(Config, 'DEBUG_MODE', False):
            # Create K_v keydown event
            event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_v})
            
            # Handle the event
            shop_scene.handle_event(event)
            
            # EXPECTED BEHAVIOR (after fix):
            # - controller.handle_shop_action() should NOT be called
            # - phase_machine.transition_to() should NOT be called
            # - The shortcut should be ignored in production mode
            
            # CURRENT BEHAVIOR (unfixed):
            # - phase_machine.transition_to("STATE_VERSUS") IS called
            # - controller.handle_shop_action() is NOT called
            # - This bypasses commit_human_turn()
            
            # Assert expected behavior (this will FAIL on unfixed code)
            shop_scene.phase_machine.transition_to.assert_not_called()
            shop_scene.controller.handle_shop_action.assert_not_called()
    
    def test_kv_calls_proper_flow_in_debug_mode(self, shop_scene):
        """
        Test Case 2: K_v should call proper flow when DEBUG_MODE=True
        
        Bug Condition: isBugCondition(input) where
            input.key == pygame.K_v AND
            Config.DEBUG_MODE == True
        
        Expected Behavior (after fix): K_v calls controller.handle_shop_action("ready")
                                       which triggers commit_human_turn()
        Current Behavior (unfixed): K_v directly calls phase_machine.transition_to("STATE_VERSUS")
                                    without calling controller.handle_shop_action()
        """
        # Set debug mode (DEBUG_MODE=True)
        with patch.object(Config, 'DEBUG_MODE', True):
            # Create K_v keydown event
            event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_v})
            
            # Handle the event
            shop_scene.handle_event(event)
            
            # EXPECTED BEHAVIOR (after fix):
            # - controller.handle_shop_action() SHOULD be called with "ready" action
            # - This ensures commit_human_turn() executes
            # - AI plays turn, market cleans up, pool_copies stays consistent
            
            # CURRENT BEHAVIOR (unfixed):
            # - phase_machine.transition_to("STATE_VERSUS") IS called directly
            # - controller.handle_shop_action() is NOT called
            # - commit_human_turn() is bypassed even in debug mode
            
            # Assert expected behavior (this will FAIL on unfixed code)
            # The fix should call handle_shop_action with a "ready" action
            from v2.core.shop_controller import ShopUIAction
            expected_action = ShopUIAction(kind="ready")
            
            # Check if handle_shop_action was called with the correct action
            shop_scene.controller.handle_shop_action.assert_called_once()
            actual_call = shop_scene.controller.handle_shop_action.call_args
            
            # Verify the action kind is "ready"
            assert actual_call is not None, "handle_shop_action should have been called"
            called_action = actual_call[0][0]  # First positional argument
            assert called_action.kind == "ready", \
                f"Expected action kind 'ready', got '{called_action.kind}'"
    
    def test_kv_direct_phase_transition_demonstrates_bypass(self, shop_scene):
        """
        Test Case 3: Demonstrate that K_v directly transitions phase without proper flow
        
        This test documents the current buggy behavior to understand the root cause.
        
        Bug Condition: K_v handler directly calls phase_machine.transition_to()
                       instead of going through controller.handle_shop_action()
        
        Root Cause: No DEBUG_MODE check exists in the K_v handler
        """
        # Set production mode
        with patch.object(Config, 'DEBUG_MODE', False):
            # Create K_v keydown event
            event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_v})
            
            # Handle the event
            shop_scene.handle_event(event)
            
            # DOCUMENT CURRENT BEHAVIOR:
            # On UNFIXED code, this will show:
            # 1. phase_machine.transition_to("STATE_VERSUS") WAS called
            # 2. controller.handle_shop_action() was NOT called
            # 3. This proves the bypass exists
            
            print("\n=== COUNTEREXAMPLE DOCUMENTATION ===")
            print(f"Config.DEBUG_MODE: {Config.DEBUG_MODE}")
            print(f"phase_machine.transition_to called: {shop_scene.phase_machine.transition_to.called}")
            print(f"phase_machine.transition_to call count: {shop_scene.phase_machine.transition_to.call_count}")
            if shop_scene.phase_machine.transition_to.called:
                print(f"phase_machine.transition_to args: {shop_scene.phase_machine.transition_to.call_args}")
            print(f"controller.handle_shop_action called: {shop_scene.controller.handle_shop_action.called}")
            print("===================================\n")
            
            # The bug is confirmed if:
            # - phase_machine.transition_to WAS called (bypassing proper flow)
            # - controller.handle_shop_action was NOT called (missing commit_human_turn)
            
            # This demonstrates the root cause: no DEBUG_MODE gate exists
    
    def test_other_keydown_events_not_affected(self, shop_scene):
        """
        Test Case 4: Verify other keyboard shortcuts work correctly
        
        This ensures the fix doesn't break other keyboard handling.
        """
        # Test K_r (reset camera) - should work regardless of DEBUG_MODE
        with patch.object(Config, 'DEBUG_MODE', False):
            event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})
            
            # Store initial camera state
            initial_offset_x = shop_scene.camera.offset_x
            initial_offset_y = shop_scene.camera.offset_y
            initial_zoom = shop_scene.camera.zoom
            
            # Modify camera state
            shop_scene.camera.offset_x = 100
            shop_scene.camera.offset_y = 100
            shop_scene.camera.zoom = 1.5
            
            # Handle K_r event
            shop_scene.handle_event(event)
            
            # Verify camera was reset
            assert shop_scene.camera.offset_x == 0, "Camera offset_x should be reset"
            assert shop_scene.camera.offset_y == 0, "Camera offset_y should be reset"
            assert shop_scene.camera.zoom == 1.0, "Camera zoom should be reset"
            
            # Verify phase_machine.transition_to was NOT called for K_r
            shop_scene.phase_machine.transition_to.assert_not_called()


if __name__ == "__main__":
    # Run tests to demonstrate the bug
    pytest.main([__file__, "-v", "-s"])
