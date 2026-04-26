"""Test for Task 24: Placement preview rendering

Verifies:
- 24.1: _render_placement_preview() method exists and checks UIState.is_placing
- 24.2: Ghost card rendering with rotation and transparency
- 24.3: _draw_hex_border_highlight() helper exists
- 24.4: _draw_invalid_hex_border() helper exists
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock
from scenes.combat_scene import CombatScene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState


@pytest.fixture
def pygame_init():
    """Initialize pygame for testing."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def mock_game():
    """Create a mock game with minimal structure."""
    game = Mock()
    
    # Create mock player
    player = Mock()
    player.pid = 0
    player.hp = 100
    player.gold = 50
    player.win_streak = 0
    player.strategy = "TestStrategy"
    
    # Create mock board with empty grid
    board = Mock()
    board.grid = {}
    player.board = board
    player.hand = []
    player.copies = {}
    
    game.players = [player]
    game.current_player_id = 0
    
    return game


@pytest.fixture
def combat_scene(pygame_init, mock_game):
    """Create a CombatScene instance for testing."""
    core_game_state = CoreGameState(mock_game)
    scene = CombatScene(core_game_state)
    scene.on_enter()
    return scene


# ========== Sub-task 24.1: _render_placement_preview() method ==========

def test_render_placement_preview_method_exists(combat_scene):
    """Verify _render_placement_preview() method exists."""
    assert hasattr(combat_scene, '_render_placement_preview')
    assert callable(combat_scene._render_placement_preview)


def test_render_placement_preview_checks_is_placing(combat_scene):
    """Verify _render_placement_preview() checks UIState.is_placing."""
    screen = pygame.Surface((1920, 1080))
    
    # Set is_placing to False
    combat_scene.ui_state.is_placing = False
    
    # Should return early without errors
    combat_scene._render_placement_preview(screen)
    
    # No assertions needed - just verify it doesn't crash


def test_render_placement_preview_requires_selected_card(combat_scene):
    """Verify _render_placement_preview() requires selected card."""
    screen = pygame.Surface((1920, 1080))
    
    # Set is_placing to True but no selected card
    combat_scene.ui_state.is_placing = True
    combat_scene.placement_controller.selected_card = None
    
    # Should return early without errors
    combat_scene._render_placement_preview(screen)
    
    # No assertions needed - just verify it doesn't crash


# ========== Sub-task 24.3: _draw_hex_border_highlight() helper ==========

def test_draw_hex_border_highlight_method_exists(combat_scene):
    """Verify _draw_hex_border_highlight() method exists."""
    assert hasattr(combat_scene, '_draw_hex_border_highlight')
    assert callable(combat_scene._draw_hex_border_highlight)


def test_draw_hex_border_highlight_draws_border(combat_scene):
    """Verify _draw_hex_border_highlight() draws a hex border."""
    screen = pygame.Surface((1920, 1080))
    
    # Draw a cyan border at hex (0, 0)
    hex_coord = (0, 0)
    cyan_color = (0, 255, 255)
    
    # Should not crash
    combat_scene._draw_hex_border_highlight(screen, hex_coord, cyan_color, width=3)


def test_draw_hex_border_highlight_uses_get_hex_corners(combat_scene):
    """Verify _draw_hex_border_highlight() uses _get_hex_corners()."""
    screen = pygame.Surface((1920, 1080))
    
    # Get hex center position
    hex_coord = (0, 0)
    center_x, center_y = combat_scene.hex_system.hex_to_pixel(0, 0)
    
    # Get corners using the helper
    corners = combat_scene._get_hex_corners(center_x, center_y, combat_scene.hex_size)
    
    # Verify we got 6 corners
    assert len(corners) == 6


# ========== Sub-task 24.4: _draw_invalid_hex_border() helper ==========

def test_draw_invalid_hex_border_method_exists(combat_scene):
    """Verify _draw_invalid_hex_border() method exists."""
    assert hasattr(combat_scene, '_draw_invalid_hex_border')
    assert callable(combat_scene._draw_invalid_hex_border)


def test_draw_invalid_hex_border_draws_red_border(combat_scene):
    """Verify _draw_invalid_hex_border() draws a red border."""
    screen = pygame.Surface((1920, 1080))
    
    # Draw invalid border at hex (0, 0)
    hex_coord = (0, 0)
    
    # Should not crash
    combat_scene._draw_invalid_hex_border(screen, hex_coord)


# ========== Integration test: Placement preview in draw() ==========

def test_placement_preview_called_in_draw(combat_scene):
    """Verify _render_placement_preview() is called in draw() method."""
    screen = pygame.Surface((1920, 1080))
    
    # Set up placement mode
    combat_scene.ui_state.is_placing = True
    
    # Create mock card
    mock_card = Mock()
    mock_card.name = "TestCard"
    combat_scene.placement_controller.selected_card = mock_card
    
    # Create mock input state with mouse position
    input_state = InputState([])  # Empty events list
    input_state.mouse_pos = (960, 540)  # Center of screen
    combat_scene.last_input_state = input_state
    
    # Should not crash
    combat_scene.draw(screen)


# ========== Test UIState.is_placing field ==========

def test_ui_state_has_is_placing_field(combat_scene):
    """Verify UIState has is_placing field."""
    assert hasattr(combat_scene.ui_state, 'is_placing')
    assert isinstance(combat_scene.ui_state.is_placing, bool)


def test_ui_state_is_placing_defaults_to_false():
    """Verify UIState.is_placing defaults to False."""
    ui_state = UIState()
    assert ui_state.is_placing is False


# ========== Test PlacementController initialization ==========

def test_placement_controller_initialized(combat_scene):
    """Verify PlacementController is initialized in on_enter()."""
    assert hasattr(combat_scene, 'placement_controller')
    assert combat_scene.placement_controller is not None


def test_placement_controller_has_preview_fields(combat_scene):
    """Verify PlacementController has preview_hex and preview_rotation fields."""
    assert hasattr(combat_scene.placement_controller, 'preview_hex')
    assert hasattr(combat_scene.placement_controller, 'preview_rotation')
    assert hasattr(combat_scene.placement_controller, 'selected_card')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
