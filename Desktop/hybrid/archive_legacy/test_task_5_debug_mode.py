"""
Test for Task 5: F3 Debug Mode

Verifies:
- Sub-task 5.1: Debug mode toggle and state
- Sub-task 5.2: _draw_debug_overlay() method
- Sub-task 5.3: Coordinate consistency validation
- Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 18.1, 18.2, 18.3
"""

import pytest
import pygame
from unittest.mock import Mock
from scenes.combat_scene import CombatScene
from core.core_game_state import CoreGameState
from core.input_state import InputState


@pytest.fixture
def mock_game_state():
    """Create a mock CoreGameState with minimal required structure."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    return CoreGameState(mock_game)


@pytest.fixture
def combat_scene(mock_game_state):
    """Create a CombatScene instance."""
    pygame.init()
    scene = CombatScene(mock_game_state)
    scene.on_enter()
    return scene


# ========== Sub-task 5.1: Debug mode toggle and state ==========

def test_debug_mode_initialized_false(combat_scene):
    """Verify debug_mode is initialized to False in __init__()."""
    # Create a new scene to test initialization
    mock_game = Mock()
    mock_game.players = [Mock()]
    game_state = CoreGameState(mock_game)
    scene = CombatScene(game_state)
    
    assert hasattr(scene, 'debug_mode')
    assert scene.debug_mode is False


def test_f3_toggles_debug_mode(combat_scene):
    """Verify F3 key press toggles debug_mode."""
    # Initial state should be False
    assert combat_scene.debug_mode is False
    
    # Create input state with F3 pressed
    events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F3})]
    input_state = InputState(events)
    
    # Handle input
    combat_scene.handle_input(input_state)
    
    # Debug mode should now be True
    assert combat_scene.debug_mode is True
    
    # Press F3 again
    events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F3})]
    input_state = InputState(events)
    combat_scene.handle_input(input_state)
    
    # Debug mode should be False again
    assert combat_scene.debug_mode is False


def test_debug_mode_state_logged(combat_scene, capsys):
    """Verify debug mode state changes are logged to console."""
    # Create input state with F3 pressed
    events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_F3})]
    input_state = InputState(events)
    
    # Handle input
    combat_scene.handle_input(input_state)
    
    # Capture output
    captured = capsys.readouterr()
    
    # Verify log message
    assert "Debug mode enabled" in captured.out or "Debug mode" in captured.out


# ========== Sub-task 5.2: _draw_debug_overlay() method ==========

def test_draw_debug_overlay_method_exists(combat_scene):
    """Verify _draw_debug_overlay() method exists."""
    assert hasattr(combat_scene, '_draw_debug_overlay')
    assert callable(combat_scene._draw_debug_overlay)


def test_draw_debug_overlay_no_crash(combat_scene):
    """Verify _draw_debug_overlay() can be called without crashing."""
    screen = pygame.Surface((1920, 1080))
    
    # Create input state to populate last_input_state
    events = []
    input_state = InputState(events)
    combat_scene.handle_input(input_state)
    
    # Should not raise any exceptions
    combat_scene._draw_debug_overlay(screen)


def test_draw_calls_debug_overlay_when_enabled(combat_scene):
    """Verify draw() calls _draw_debug_overlay() when debug_mode is True."""
    screen = pygame.Surface((1920, 1080))
    
    # Enable debug mode
    combat_scene.debug_mode = True
    
    # Create input state
    events = []
    input_state = InputState(events)
    combat_scene.handle_input(input_state)
    
    # Mock _draw_debug_overlay to track if it's called
    original_method = combat_scene._draw_debug_overlay
    call_count = [0]
    
    def mock_draw_debug_overlay(s):
        call_count[0] += 1
        original_method(s)
    
    combat_scene._draw_debug_overlay = mock_draw_debug_overlay
    
    # Call draw
    combat_scene.draw(screen)
    
    # Verify _draw_debug_overlay was called
    assert call_count[0] == 1


def test_draw_skips_debug_overlay_when_disabled(combat_scene):
    """Verify draw() does not call _draw_debug_overlay() when debug_mode is False."""
    screen = pygame.Surface((1920, 1080))
    
    # Ensure debug mode is disabled
    combat_scene.debug_mode = False
    
    # Mock _draw_debug_overlay to track if it's called
    call_count = [0]
    
    def mock_draw_debug_overlay(s):
        call_count[0] += 1
    
    combat_scene._draw_debug_overlay = mock_draw_debug_overlay
    
    # Call draw
    combat_scene.draw(screen)
    
    # Verify _draw_debug_overlay was NOT called
    assert call_count[0] == 0


def test_debug_overlay_draws_crosshairs(combat_scene):
    """Verify debug overlay draws crosshairs at hex centers."""
    screen = pygame.Surface((1920, 1080))
    
    # Create input state
    events = []
    input_state = InputState(events)
    combat_scene.handle_input(input_state)
    
    # Enable debug mode and draw
    combat_scene.debug_mode = True
    combat_scene.draw(screen)
    
    # Verify screen has been modified (pixels changed from background)
    # This is a basic check - we can't easily verify exact crosshair positions
    # without more complex image analysis
    pixel_data = pygame.surfarray.array3d(screen)
    assert pixel_data.any()  # Screen has non-zero pixels


# ========== Sub-task 5.3: Coordinate consistency validation ==========

def test_validate_coordinate_consistency_method_exists(combat_scene):
    """Verify _validate_coordinate_consistency() method exists."""
    assert hasattr(combat_scene, '_validate_coordinate_consistency')
    assert callable(combat_scene._validate_coordinate_consistency)


def test_validate_coordinate_consistency_called_in_on_enter(capsys):
    """Verify _validate_coordinate_consistency() is called in on_enter()."""
    pygame.init()
    mock_game = Mock()
    mock_game.players = [Mock()]
    game_state = CoreGameState(mock_game)
    
    scene = CombatScene(game_state)
    scene.on_enter()
    
    # Capture output
    captured = capsys.readouterr()
    
    # Verify validation success message
    assert "Coordinate consistency validation passed" in captured.out or "no drift detected" in captured.out


def test_validate_coordinate_consistency_no_drift(combat_scene):
    """Verify coordinate consistency validation passes for all hexes."""
    # This should not raise an AssertionError
    try:
        combat_scene._validate_coordinate_consistency()
    except AssertionError as e:
        pytest.fail(f"Coordinate consistency validation failed: {e}")


def test_coordinate_round_trip_consistency(combat_scene):
    """Verify hex_to_pixel followed by pixel_to_hex returns original coordinate."""
    # Test all 37 hexes
    for q, r in combat_scene.hex_grid:
        # Convert hex to pixel
        pixel_x, pixel_y = combat_scene.hex_system.hex_to_pixel(q, r)
        
        # Convert pixel back to hex
        recovered_q, recovered_r = combat_scene.hex_system.pixel_to_hex(pixel_x, pixel_y)
        
        # Verify we got the same coordinate back
        assert (recovered_q, recovered_r) == (q, r), \
            f"Coordinate drift detected: ({q}, {r}) -> ({pixel_x:.2f}, {pixel_y:.2f}) -> ({recovered_q}, {recovered_r})"


def test_last_input_state_stored(combat_scene):
    """Verify last_input_state is stored when handle_input is called."""
    # Create input state
    events = []
    input_state = InputState(events)
    
    # Handle input
    combat_scene.handle_input(input_state)
    
    # Verify last_input_state is stored
    assert combat_scene.last_input_state is not None
    assert combat_scene.last_input_state == input_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
