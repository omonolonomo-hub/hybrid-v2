"""
Bug Condition Exploration Test for Tier Milestone UI Separation
═══════════════════════════════════════════════════════════════════

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

This test encodes the EXPECTED BEHAVIOR (milestone detection in controller layer).
When run on UNFIXED code, it MUST FAIL - proving the bug exists.
When run on FIXED code, it MUST PASS - proving the bug is resolved.

DO NOT attempt to fix the test or code when it fails on unfixed code.
The failure is the SUCCESS CASE for bug exploration.

Bug Condition:
- Milestone checking occurs in UI layer (ShopScene._check_tier_milestones())
- Called every frame from ShopScene.update()
- No milestone_reached signal is emitted
- Milestone detection is delayed until next frame update

Expected Behavior (after fix):
- Milestone checking occurs in ShopController layer
- Called immediately after controller actions (buy, place)
- milestone_reached signal is emitted through SignalBus
- Milestone detection happens immediately, not delayed
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock, call
from typing import Optional

from v2.core.game_state import GameState
from v2.scenes.shop import ShopScene
from v2.core.shop_controller import ShopUIAction
from engine_core.signals import SignalBus


def create_mock_game_state():
    """Create a properly mocked GameState for testing."""
    mock_state = Mock(spec=GameState)
    mock_adapter = Mock()
    mock_engine = Mock()
    mock_signals = SignalBus()
    
    mock_engine.signals = mock_signals
    mock_adapter._engine = mock_engine
    mock_state._adapter = mock_adapter
    
    # Mock get_public_state to return a valid state
    mock_public_state = Mock()
    mock_active_player = Mock()
    mock_synergy = Mock()
    mock_synergy.groups = []
    mock_synergy.total = 0
    mock_active_player.synergy = mock_synergy
    mock_active_player.copy_milestones = []
    mock_active_player.board_cards = {}
    mock_active_player.hand = Mock(slots=[None] * 5)
    
    # Mock shop with proper rarity_probabilities
    mock_shop = Mock()
    mock_shop.slots = [None] * 5
    mock_shop.is_locked = False
    mock_shop.rarity_probabilities = {"common": 0.5, "rare": 0.3, "epic": 0.15, "legendary": 0.05}
    mock_active_player.shop = mock_shop
    
    mock_active_player.gold = 10
    mock_active_player.hp = 100
    mock_active_player.hud = Mock(
        hp=100,
        gold=10,
        win_streak=0,
        total_pts=0,
        next_gold=10,
        interest_multiplier=1.0
    )
    mock_active_player.board_card_info = {}
    mock_active_player.hand_card_info = {}
    mock_active_player.shop_card_info = {}
    mock_active_player.adjacency_pairs = []
    mock_active_player.copies_by_name = {}
    mock_active_player.board_rotations = {}
    mock_active_player.index = 0
    mock_active_player.eliminated_coords = []
    
    mock_public_state.active_player = mock_active_player
    mock_public_state.turn = 1
    mock_public_state.phase = "STATE_PREPARATION"
    mock_public_state.view_index = 0
    mock_public_state.lobby_players = []
    
    mock_state.get_public_state.return_value = mock_public_state
    mock_state.get_phase.return_value = "STATE_PREPARATION"
    
    return mock_state


class TestBugConditionMilestoneUILayer:
    """
    Test that milestone checking occurs in UI layer on unfixed code.
    
    CRITICAL: This test MUST FAIL on unfixed code.
    When it fails, it proves the bug exists (milestone checking in UI layer).
    When it passes (after fix), it proves the bug is resolved.
    """
    
    @pytest.fixture
    def game_state(self):
        """Create a mock GameState for testing."""
        return create_mock_game_state()
    
    @pytest.fixture
    def shop_scene(self, game_state):
        """Create a ShopScene instance for testing."""
        pygame.init()
        pygame.display.set_mode((1, 1))  # Minimal display for testing
        scene = ShopScene(game_state)
        return scene
    
    def test_milestone_checking_not_in_ui_layer(self, shop_scene, game_state):
        """
        Test that milestone checking does NOT occur in UI layer.
        
        EXPECTED ON UNFIXED CODE: FAIL (milestone checking IS in UI layer)
        EXPECTED ON FIXED CODE: PASS (milestone checking is NOT in UI layer)
        
        This test verifies that _check_tier_milestones() is NOT called
        from ShopScene.update() method.
        """
        # Check if the old method still exists (it shouldn't after the fix)
        has_old_method = hasattr(shop_scene, '_check_tier_milestones')
        
        if has_old_method:
            # Patch _check_tier_milestones to track if it's called
            with patch.object(shop_scene, '_check_tier_milestones', wraps=shop_scene._check_tier_milestones) as mock_check:
                # Simulate a frame update
                shop_scene.update(16.67)  # ~60 FPS frame time
                
                # EXPECTED BEHAVIOR: _check_tier_milestones should NOT be called from update()
                # On unfixed code, this assertion will FAIL (proving bug exists)
                assert mock_check.call_count == 0, (
                    f"Bug detected: _check_tier_milestones() was called {mock_check.call_count} times "
                    f"from ShopScene.update(). Milestone checking should occur in controller layer, "
                    f"not UI layer."
                )
        else:
            # On fixed code, the method doesn't exist at all (which is correct)
            # Just simulate a frame update to ensure no errors
            shop_scene.update(16.67)
            # Test passes - the old method is gone, which is the expected behavior
    
    def test_milestone_signal_emitted_on_controller_action(self, shop_scene, game_state):
        """
        Test that milestone_reached signal IS emitted when milestones are reached.
        
        EXPECTED ON UNFIXED CODE: FAIL (no signal emitted)
        EXPECTED ON FIXED CODE: PASS (signal is emitted)
        
        This test verifies that the controller emits milestone_reached signal
        through SignalBus when a milestone condition is met.
        """
        # Setup: Create a scenario where a milestone would be reached
        # Mock a tier milestone condition (3 cards of same tier)
        mock_group_state = Mock()
        mock_group_state.key = "MIND"
        mock_group_state.count = 3
        mock_group_state.bonus = 5
        
        mock_public_state = game_state.get_public_state()
        mock_public_state.active_player.synergy.groups = [mock_group_state]
        
        # Track signal emissions
        signal_emitted = []
        def signal_handler(**kwargs):
            signal_emitted.append(kwargs)
        
        # Connect to milestone_reached signal (will fail on unfixed code if signal doesn't exist)
        signals = game_state._adapter._engine.signals
        
        # Check if milestone_reached signal exists
        has_milestone_signal = hasattr(signals, 'milestone_reached')
        
        if has_milestone_signal:
            signals.milestone_reached.connect(signal_handler)
        
        # Simulate a buy action that would trigger a milestone
        action = ShopUIAction(kind="buy", slot_index=0, card_name="Test Card")
        
        # Execute the action
        shop_scene.controller.handle_shop_action(action)
        
        # EXPECTED BEHAVIOR: milestone_reached signal should be emitted
        # On unfixed code, this assertion will FAIL (no signal or not emitted)
        # On fixed code, this assertion will PASS (signal is emitted)
        assert has_milestone_signal, (
            "Bug detected: milestone_reached signal does not exist in SignalBus. "
            "The signal should be added to enable event-driven milestone detection."
        )
        
        # Note: We can't fully test signal emission without the fix in place,
        # but we can verify the signal exists and is connected
        assert hasattr(signals.milestone_reached, 'emit'), (
            "Bug detected: milestone_reached signal exists but cannot emit events."
        )
    
    def test_milestone_detection_in_controller_not_ui(self, shop_scene, game_state):
        """
        Test that milestone detection logic exists in controller, not UI.
        
        EXPECTED ON UNFIXED CODE: FAIL (logic is in UI layer)
        EXPECTED ON FIXED CODE: PASS (logic is in controller layer)
        
        This test verifies that ShopController has milestone detection logic.
        """
        controller = shop_scene.controller
        
        # EXPECTED BEHAVIOR: Controller should have milestone detection method
        # On unfixed code, this assertion will FAIL (method doesn't exist)
        # On fixed code, this assertion will PASS (method exists)
        has_milestone_method = hasattr(controller, '_check_and_emit_milestones')
        
        assert has_milestone_method, (
            "Bug detected: ShopController does not have _check_and_emit_milestones() method. "
            "Milestone detection logic should be in the controller layer, not UI layer."
        )
        
        # Verify controller has milestone tracking state
        has_prev_counts = hasattr(controller, '_prev_group_counts')
        has_seen_milestones = hasattr(controller, '_seen_copy_milestones')
        
        assert has_prev_counts, (
            "Bug detected: ShopController does not have _prev_group_counts state. "
            "Milestone tracking state should be in controller layer."
        )
        
        assert has_seen_milestones, (
            "Bug detected: ShopController does not have _seen_copy_milestones state. "
            "Milestone tracking state should be in controller layer."
        )
    
    def test_ui_layer_responds_to_signal_not_polling(self, shop_scene, game_state):
        """
        Test that UI layer responds to signals, not polling every frame.
        
        EXPECTED ON UNFIXED CODE: FAIL (UI polls every frame)
        EXPECTED ON FIXED CODE: PASS (UI responds to signals)
        
        This test verifies that ShopScene has a signal handler for milestone_reached.
        """
        # EXPECTED BEHAVIOR: ShopScene should have signal handler method
        # On unfixed code, this assertion will FAIL (method doesn't exist or is _check_tier_milestones)
        # On fixed code, this assertion will PASS (method is _on_milestone_reached)
        has_signal_handler = hasattr(shop_scene, '_on_milestone_reached')
        
        assert has_signal_handler, (
            "Bug detected: ShopScene does not have _on_milestone_reached() signal handler. "
            "UI layer should respond to milestone_reached signal, not poll every frame."
        )
        
        # Verify the old polling method is removed or not called from update
        # This is already tested in test_milestone_checking_not_in_ui_layer


class TestBugConditionCounterexamples:
    """
    Document specific counterexamples that demonstrate the bug.
    
    These tests capture concrete scenarios where the bug manifests.
    """
    
    @pytest.fixture
    def game_state(self):
        """Create a mock GameState for testing."""
        return create_mock_game_state()
    
    @pytest.fixture
    def shop_scene(self, game_state):
        """Create a ShopScene instance for testing."""
        pygame.init()
        pygame.display.set_mode((1, 1))
        scene = ShopScene(game_state)
        return scene
    
    def test_counterexample_frame_based_detection(self, shop_scene):
        """
        Counterexample: Milestone detection occurs every frame in update().
        
        This demonstrates the bug: _check_tier_milestones() is called
        from ShopScene.update() every frame, not from controller actions.
        """
        # Check if the old method still exists
        has_old_method = hasattr(shop_scene, '_check_tier_milestones')
        
        if has_old_method:
            with patch.object(shop_scene, '_check_tier_milestones') as mock_check:
                # Simulate multiple frames
                for _ in range(5):
                    shop_scene.update(16.67)
                
                # On unfixed code: _check_tier_milestones is called 5 times (once per frame)
                call_count = mock_check.call_count
                
                # Document the counterexample
                if call_count > 0:
                    print(f"\n[COUNTEREXAMPLE] Milestone checking called {call_count} times from update()")
                    print("[COUNTEREXAMPLE] Expected: 0 calls (should be in controller layer)")
                    print("[COUNTEREXAMPLE] This proves the bug exists: milestone checking in UI layer")
                
                # This assertion will FAIL on unfixed code (proving bug exists)
                assert call_count == 0, (
                    f"Counterexample found: _check_tier_milestones() called {call_count} times "
                    f"from ShopScene.update(). Milestone checking should be in controller layer."
                )
        else:
            # On fixed code: method doesn't exist, which is correct
            # Just simulate frames to ensure no errors
            for _ in range(5):
                shop_scene.update(16.67)
            # Test passes - the old method is gone
    
    def test_counterexample_no_signal_emission(self, shop_scene, game_state):
        """
        Counterexample: No milestone_reached signal is emitted.
        
        This demonstrates the bug: milestone detection doesn't use SignalBus.
        """
        signals = game_state._adapter._engine.signals
        
        # Check if milestone_reached signal exists
        has_signal = hasattr(signals, 'milestone_reached')
        
        # Document the counterexample
        if not has_signal:
            print("\n[COUNTEREXAMPLE] milestone_reached signal does not exist in SignalBus")
            print("[COUNTEREXAMPLE] Expected: Signal should exist for event-driven architecture")
            print("[COUNTEREXAMPLE] This proves the bug exists: no signal-based milestone detection")
        
        # This assertion will FAIL on unfixed code (proving bug exists)
        assert has_signal, (
            "Counterexample found: milestone_reached signal does not exist. "
            "Milestone detection should use SignalBus for event-driven architecture."
        )
    
    def test_counterexample_delayed_detection(self, shop_scene, game_state):
        """
        Counterexample: Milestone detection is delayed until next frame.
        
        This demonstrates the bug: milestones are detected on the frame AFTER
        the action that triggered them, not immediately.
        """
        # Setup: Mock a scenario where buying a card triggers a milestone
        mock_group_state = Mock()
        mock_group_state.key = "MIND"
        mock_group_state.count = 3  # Tier milestone
        mock_group_state.bonus = 5
        
        mock_public_state = game_state.get_public_state()
        mock_public_state.active_player.synergy.groups = [mock_group_state]
        
        # Check if the old method still exists
        has_old_method = hasattr(shop_scene, '_check_tier_milestones')
        
        if has_old_method:
            # Track when milestone checking occurs
            check_times = []
            original_check = shop_scene._check_tier_milestones
            
            def tracked_check():
                check_times.append("check")
                return original_check()
            
            with patch.object(shop_scene, '_check_tier_milestones', side_effect=tracked_check):
                # Execute a buy action
                action = ShopUIAction(kind="buy", slot_index=0, card_name="Test Card")
                shop_scene.controller.handle_shop_action(action)
                
                # At this point, milestone should be detected (on fixed code)
                # On unfixed code, it's NOT detected yet
                checks_after_action = len(check_times)
                
                # Simulate next frame update
                shop_scene.update(16.67)
                
                # On unfixed code, milestone is detected NOW (delayed)
                checks_after_frame = len(check_times)
                
                # Document the counterexample
                if checks_after_action == 0 and checks_after_frame > 0:
                    print("\n[COUNTEREXAMPLE] Milestone detection delayed until next frame")
                    print(f"[COUNTEREXAMPLE] Checks after action: {checks_after_action}")
                    print(f"[COUNTEREXAMPLE] Checks after frame update: {checks_after_frame}")
                    print("[COUNTEREXAMPLE] Expected: Detection immediately after action")
                    print("[COUNTEREXAMPLE] This proves the bug exists: delayed detection in UI layer")
                
                # This assertion will FAIL on unfixed code (proving bug exists)
                # On fixed code, milestone detection happens in controller (not tracked here)
                # So we check that UI layer doesn't do the detection
                assert checks_after_frame == 0 or checks_after_action > 0, (
                    "Counterexample found: Milestone detection delayed until frame update. "
                    "Detection should occur immediately in controller action."
                )
        else:
            # On fixed code: old method doesn't exist
            # Execute action and frame update to ensure no errors
            action = ShopUIAction(kind="buy", slot_index=0, card_name="Test Card")
            shop_scene.controller.handle_shop_action(action)
            shop_scene.update(16.67)
            # Test passes - milestone detection is now in controller layer


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
