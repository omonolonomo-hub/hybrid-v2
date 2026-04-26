"""Test ESC key handling for all input modes in CombatScene.

This test verifies Task 22 implementation:
- 22.1: ESC in NORMAL mode pushes PAUSED mode
- 22.2: ESC in PLACING mode calls _cancel_placement() and pops mode
- 22.3: ESC in CARD_DETAIL mode pops input mode
- 22.4: ESC in PAUSED mode pops input mode
"""

import pygame
from unittest.mock import Mock, MagicMock, patch
from scenes.combat_scene import CombatScene
from core.input_state import InputState, InputMode
from core.core_game_state import CoreGameState, Player


def create_mock_game_state():
    """Create a minimal mock CoreGameState for testing."""
    game_state = Mock(spec=CoreGameState)
    player = Mock(spec=Player)
    player.board = Mock()
    player.board.grid = {}  # Empty board
    game_state.players = [player]
    game_state.current_player_index = 0
    return game_state


def create_mock_input_state(key_pressed=None):
    """Create a mock InputState with specified key pressed."""
    input_state = Mock(spec=InputState)
    input_state.mouse_pos = (400, 300)
    
    # Mock the was_key_pressed_this_frame method
    def was_key_pressed(key):
        return key == key_pressed
    
    input_state.was_key_pressed_this_frame = was_key_pressed
    return input_state


def test_esc_in_normal_mode():
    """Test 22.1: ESC in NORMAL mode pushes PAUSED mode."""
    print("\n=== Test 22.1: ESC in NORMAL mode ===")
    
    # Create scene with mock dependencies
    game_state = create_mock_game_state()
    scene = CombatScene(game_state)
    
    # Initialize scene (this sets up input_mode to NORMAL)
    scene.input_mode = InputMode.NORMAL
    scene.input_stack = []
    
    # Create input state with ESC pressed
    input_state = create_mock_input_state(key_pressed=pygame.K_ESCAPE)
    
    # Handle input
    scene._handle_input_normal(input_state)
    
    # Verify: mode should be PAUSED, stack should contain NORMAL
    assert scene.input_mode == InputMode.PAUSED, f"Expected PAUSED mode, got {scene.input_mode}"
    assert len(scene.input_stack) == 1, f"Expected stack depth 1, got {len(scene.input_stack)}"
    assert scene.input_stack[0] == InputMode.NORMAL, f"Expected NORMAL in stack, got {scene.input_stack[0]}"
    
    print("✓ Test passed: ESC in NORMAL mode correctly pushes PAUSED mode")


def test_esc_in_placing_mode():
    """Test 22.2: ESC in PLACING mode calls _cancel_placement() and pops mode."""
    print("\n=== Test 22.2: ESC in PLACING mode ===")
    
    # Create scene with mock dependencies
    game_state = create_mock_game_state()
    scene = CombatScene(game_state)
    
    # Set up PLACING mode with NORMAL in stack
    scene.input_mode = InputMode.PLACING
    scene.input_stack = [InputMode.NORMAL]
    
    # Mock _cancel_placement to track if it was called
    cancel_called = [False]
    original_cancel = scene._cancel_placement
    
    def mock_cancel():
        cancel_called[0] = True
        original_cancel()
    
    scene._cancel_placement = mock_cancel
    
    # Create input state with ESC pressed
    input_state = create_mock_input_state(key_pressed=pygame.K_ESCAPE)
    
    # Handle input
    scene._handle_input_placing(input_state)
    
    # Verify: _cancel_placement was called, mode popped back to NORMAL
    assert cancel_called[0], "_cancel_placement() was not called"
    assert scene.input_mode == InputMode.NORMAL, f"Expected NORMAL mode, got {scene.input_mode}"
    assert len(scene.input_stack) == 0, f"Expected empty stack, got {len(scene.input_stack)}"
    
    print("✓ Test passed: ESC in PLACING mode correctly cancels placement and returns to NORMAL")


def test_esc_in_card_detail_mode():
    """Test 22.3: ESC in CARD_DETAIL mode pops input mode."""
    print("\n=== Test 22.3: ESC in CARD_DETAIL mode ===")
    
    # Create scene with mock dependencies
    game_state = create_mock_game_state()
    scene = CombatScene(game_state)
    
    # Set up CARD_DETAIL mode with NORMAL in stack
    scene.input_mode = InputMode.CARD_DETAIL
    scene.input_stack = [InputMode.NORMAL]
    
    # Create input state with ESC pressed
    input_state = create_mock_input_state(key_pressed=pygame.K_ESCAPE)
    
    # Handle input
    scene._handle_input_card_detail(input_state)
    
    # Verify: mode popped back to NORMAL
    assert scene.input_mode == InputMode.NORMAL, f"Expected NORMAL mode, got {scene.input_mode}"
    assert len(scene.input_stack) == 0, f"Expected empty stack, got {len(scene.input_stack)}"
    
    print("✓ Test passed: ESC in CARD_DETAIL mode correctly pops to previous mode")


def test_esc_in_paused_mode():
    """Test 22.4: ESC in PAUSED mode pops input mode."""
    print("\n=== Test 22.4: ESC in PAUSED mode ===")
    
    # Create scene with mock dependencies
    game_state = create_mock_game_state()
    scene = CombatScene(game_state)
    
    # Set up PAUSED mode with NORMAL in stack
    scene.input_mode = InputMode.PAUSED
    scene.input_stack = [InputMode.NORMAL]
    
    # Create input state with ESC pressed
    input_state = create_mock_input_state(key_pressed=pygame.K_ESCAPE)
    
    # Handle input
    scene._handle_input_paused(input_state)
    
    # Verify: mode popped back to NORMAL
    assert scene.input_mode == InputMode.NORMAL, f"Expected NORMAL mode, got {scene.input_mode}"
    assert len(scene.input_stack) == 0, f"Expected empty stack, got {len(scene.input_stack)}"
    
    print("✓ Test passed: ESC in PAUSED mode correctly pops to previous mode")


def test_nested_mode_transitions():
    """Test nested mode transitions: NORMAL -> PLACING -> PAUSED -> PLACING -> NORMAL."""
    print("\n=== Test: Nested mode transitions ===")
    
    # Create scene with mock dependencies
    game_state = create_mock_game_state()
    scene = CombatScene(game_state)
    
    # Start in NORMAL mode
    scene.input_mode = InputMode.NORMAL
    scene.input_stack = []
    
    # Transition to PLACING
    scene.push_input_mode(InputMode.PLACING)
    assert scene.input_mode == InputMode.PLACING
    assert scene.input_stack == [InputMode.NORMAL]
    
    # Transition to PAUSED (nested)
    scene.push_input_mode(InputMode.PAUSED)
    assert scene.input_mode == InputMode.PAUSED
    assert scene.input_stack == [InputMode.NORMAL, InputMode.PLACING]
    
    # Pop back to PLACING
    scene.pop_input_mode()
    assert scene.input_mode == InputMode.PLACING
    assert scene.input_stack == [InputMode.NORMAL]
    
    # Pop back to NORMAL
    scene.pop_input_mode()
    assert scene.input_mode == InputMode.NORMAL
    assert scene.input_stack == []
    
    print("✓ Test passed: Nested mode transitions work correctly")


if __name__ == "__main__":
    print("Testing ESC key handling for Task 22...")
    
    try:
        test_esc_in_normal_mode()
        test_esc_in_placing_mode()
        test_esc_in_card_detail_mode()
        test_esc_in_paused_mode()
        test_nested_mode_transitions()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nTask 22 verification complete:")
        print("  ✓ 22.1: ESC in NORMAL mode pushes PAUSED mode")
        print("  ✓ 22.2: ESC in PLACING mode cancels placement and pops mode")
        print("  ✓ 22.3: ESC in CARD_DETAIL mode pops input mode")
        print("  ✓ 22.4: ESC in PAUSED mode pops input mode")
        print("  ✓ Nested mode transitions work correctly")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
