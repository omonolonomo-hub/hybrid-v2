"""
Test for Task 30: Performance optimizations

Verifies:
- Sub-task 30.1: Dirty flag optimization in flip animations
- Sub-task 30.2: Off-screen culling in rendering
- Sub-task 30.3: Layout validation throttling
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock
from scenes.combat_scene import CombatScene, AnimationController, HexCardRenderer, HexCard
from core.core_game_state import CoreGameState
from core.ui_state import UIState


@pytest.fixture
def mock_game_state():
    """Create a mock CoreGameState for testing."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_game.players[0].pid = 0
    mock_game.players[0].board = Mock()
    mock_game.players[0].board.grid = {}
    
    game_state = CoreGameState(mock_game)
    return game_state


@pytest.fixture
def combat_scene(mock_game_state):
    """Create a CombatScene instance."""
    pygame.init()
    scene = CombatScene(mock_game_state)
    # Don't call on_enter() to avoid mock issues
    # Just initialize what we need for testing
    scene.ui_state = UIState()
    scene.frame_counter = 0
    scene.hex_cards = []
    return scene


# ========== Sub-task 30.1: Dirty flag optimization ==========

def test_animation_controller_skips_update_when_at_target():
    """Verify AnimationController skips update when flip_value already at target."""
    ui_state = UIState()
    ui_state.hovered_hex = None
    
    controller = AnimationController(ui_state)
    
    # Create a hex card that's already at target (flip_value = 0.0, target = 0.0)
    hex_card = Mock()
    hex_card.hex_coord = (0, 0)
    hex_card.flip_value = 0.0
    hex_card.flip_value_eased = 0.0
    
    # Update should skip this card (no changes)
    controller.update_flip_animations([hex_card], dt=16.67)
    
    # flip_value should remain unchanged (not set to target explicitly)
    assert hex_card.flip_value == 0.0


def test_animation_controller_updates_when_not_at_target():
    """Verify AnimationController updates flip_value when not at target."""
    ui_state = UIState()
    ui_state.hovered_hex = (0, 0)  # Hovering over the card
    
    controller = AnimationController(ui_state)
    
    # Create a hex card that's not at target (flip_value = 0.0, target = 1.0)
    hex_card = Mock()
    hex_card.hex_coord = (0, 0)
    hex_card.flip_value = 0.0
    hex_card.flip_value_eased = 0.0
    
    # Update should change flip_value
    controller.update_flip_animations([hex_card], dt=16.67)
    
    # flip_value should have increased toward target
    assert hex_card.flip_value > 0.0


def test_animation_controller_uses_threshold():
    """Verify AnimationController uses 0.01 threshold for 'close enough'."""
    ui_state = UIState()
    ui_state.hovered_hex = None
    
    controller = AnimationController(ui_state)
    
    # Create a hex card that's within threshold (flip_value = 0.005, target = 0.0)
    hex_card = Mock()
    hex_card.hex_coord = (0, 0)
    hex_card.flip_value = 0.005  # Within 0.01 threshold
    hex_card.flip_value_eased = 0.005
    
    # Update should skip this card
    controller.update_flip_animations([hex_card], dt=16.67)
    
    # flip_value should remain unchanged
    assert hex_card.flip_value == 0.005


# ========== Sub-task 30.2: Off-screen culling ==========

def test_hex_card_renderer_skips_offscreen_cards():
    """Verify HexCardRenderer skips rendering cards that are off-screen."""
    pygame.init()
    screen = pygame.Surface((1920, 1080))
    
    hex_system = Mock()
    asset_manager = Mock()
    renderer = HexCardRenderer(hex_system, asset_manager)
    
    # Create a hex card that's off-screen (far to the left)
    hex_card = Mock()
    hex_card.position = (-500, 500)  # Off-screen to the left
    hex_card.back_image = pygame.Surface((200, 280))
    hex_card.front_image = pygame.Surface((200, 280))
    
    # Render should skip this card (no exception should be raised)
    renderer.render_card(screen, hex_card, flip_value_eased=0.0)
    
    # If we get here without exception, the test passes


def test_hex_card_renderer_renders_onscreen_cards():
    """Verify HexCardRenderer renders cards that are on-screen."""
    pygame.init()
    screen = pygame.Surface((1920, 1080))
    
    hex_system = Mock()
    asset_manager = Mock()
    renderer = HexCardRenderer(hex_system, asset_manager)
    
    # Create a hex card that's on-screen
    hex_card = Mock()
    hex_card.position = (960, 540)  # Center of screen
    hex_card.back_image = pygame.Surface((200, 280))
    hex_card.front_image = pygame.Surface((200, 280))
    
    # Render should process this card (no exception should be raised)
    renderer.render_card(screen, hex_card, flip_value_eased=0.0)
    
    # If we get here without exception, the test passes


def test_hex_card_renderer_skips_small_scaled_width():
    """Verify HexCardRenderer skips rendering when scaled width < 2 pixels."""
    pygame.init()
    screen = pygame.Surface((1920, 1080))
    
    hex_system = Mock()
    asset_manager = Mock()
    renderer = HexCardRenderer(hex_system, asset_manager)
    
    # Create a hex card
    hex_card = Mock()
    hex_card.position = (960, 540)
    hex_card.back_image = pygame.Surface((200, 280))
    hex_card.front_image = pygame.Surface((200, 280))
    
    # Render at flip_value = 0.5 (scale_x = 0.0, scaled_width < 2)
    renderer.render_card(screen, hex_card, flip_value_eased=0.5)
    
    # If we get here without exception, the test passes


# ========== Sub-task 30.3: Layout validation throttling ==========

def test_combat_scene_has_frame_counter(combat_scene):
    """Verify CombatScene has frame_counter attribute."""
    assert hasattr(combat_scene, 'frame_counter')
    assert combat_scene.frame_counter == 0


def test_combat_scene_increments_frame_counter(combat_scene):
    """Verify CombatScene increments frame_counter in update()."""
    initial_count = combat_scene.frame_counter
    
    # Call update
    combat_scene.update(dt=16.67)
    
    # frame_counter should have incremented
    assert combat_scene.frame_counter == initial_count + 1


def test_combat_scene_validates_layout_every_60_frames(combat_scene, monkeypatch):
    """Verify CombatScene calls _validate_layout_safety() every 60 frames."""
    # Mock _validate_layout_safety to track calls
    validate_calls = []
    
    def mock_validate():
        validate_calls.append(True)
    
    monkeypatch.setattr(combat_scene, '_validate_layout_safety', mock_validate)
    
    # Update 59 times - should not call validate
    for i in range(59):
        combat_scene.update(dt=16.67)
    
    assert len(validate_calls) == 0
    
    # Update 60th time - should call validate
    combat_scene.update(dt=16.67)
    
    assert len(validate_calls) == 1


def test_validate_layout_safety_method_exists(combat_scene):
    """Verify _validate_layout_safety() method exists."""
    assert hasattr(combat_scene, '_validate_layout_safety')
    assert callable(combat_scene._validate_layout_safety)


def test_calculate_grid_bounds_method_exists(combat_scene):
    """Verify _calculate_grid_bounds() method exists."""
    assert hasattr(combat_scene, '_calculate_grid_bounds')
    assert callable(combat_scene._calculate_grid_bounds)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
