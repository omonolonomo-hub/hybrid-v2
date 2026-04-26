"""
Test Task 25: Rotation Mechanics

Tests for rotation mechanics implementation:
- Task 25.1: Right-click detection in _handle_input_placing()
- Task 25.2: Rotation lock on placement
- Task 25.3: can_rotate_card() helper
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock
from scenes.combat_scene import CombatScene, PlacementController, HexCard
from core.input_state import InputState
from core.core_game_state import CoreGameState


def test_input_state_has_right_clicked():
    """Test that InputState has right_clicked property."""
    pygame.init()
    
    # Create right-click event
    events = [
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (100, 100)})
    ]
    
    input_state = InputState(events)
    
    assert hasattr(input_state, 'right_clicked'), "InputState should have right_clicked property"
    assert input_state.right_clicked is True, "right_clicked should be True for right-click event"
    
    pygame.quit()


def test_placement_controller_handle_right_click():
    """Test that PlacementController.handle_right_click() rotates by 60 degrees."""
    pygame.init()
    
    # Create mock dependencies
    core_game_state = Mock(spec=CoreGameState)
    ui_state = Mock()
    hex_system = Mock()
    
    controller = PlacementController(core_game_state, ui_state, hex_system)
    
    # Initial rotation should be 0
    assert controller.preview_rotation == 0
    
    # First right-click: 0 -> 60
    controller.handle_right_click()
    assert controller.preview_rotation == 60
    
    # Second right-click: 60 -> 120
    controller.handle_right_click()
    assert controller.preview_rotation == 120
    
    # Third right-click: 120 -> 180
    controller.handle_right_click()
    assert controller.preview_rotation == 180
    
    # Fourth right-click: 180 -> 240
    controller.handle_right_click()
    assert controller.preview_rotation == 240
    
    # Fifth right-click: 240 -> 300
    controller.handle_right_click()
    assert controller.preview_rotation == 300
    
    # Sixth right-click: 300 -> 0 (wrap around)
    controller.handle_right_click()
    assert controller.preview_rotation == 0
    
    pygame.quit()


def test_placement_controller_can_rotate_card():
    """Test that can_rotate_card() checks is_rotation_locked."""
    pygame.init()
    
    # Create mock dependencies
    core_game_state = Mock(spec=CoreGameState)
    ui_state = Mock()
    hex_system = Mock()
    
    controller = PlacementController(core_game_state, ui_state, hex_system)
    
    # Create HexCard with rotation not locked
    hex_card_unlocked = HexCard(
        hex_coord=(0, 0),
        card_data=Mock(),
        front_image=pygame.Surface((100, 100)),
        back_image=pygame.Surface((100, 100)),
        position=(0, 0),
        hex_size=50,
        rotation=0,
        placement_state="preview",
        is_rotation_locked=False
    )
    
    # Create HexCard with rotation locked
    hex_card_locked = HexCard(
        hex_coord=(1, 0),
        card_data=Mock(),
        front_image=pygame.Surface((100, 100)),
        back_image=pygame.Surface((100, 100)),
        position=(100, 0),
        hex_size=50,
        rotation=60,
        placement_state="placed",
        is_rotation_locked=True
    )
    
    # Test can_rotate_card
    assert controller.can_rotate_card(hex_card_unlocked) is True, "Should be able to rotate unlocked card"
    assert controller.can_rotate_card(hex_card_locked) is False, "Should NOT be able to rotate locked card"
    
    pygame.quit()


def test_hex_card_rotation_lock_on_placement():
    """Test that HexCard has rotation and is_rotation_locked fields."""
    pygame.init()
    
    # Create HexCard
    hex_card = HexCard(
        hex_coord=(0, 0),
        card_data=Mock(),
        front_image=pygame.Surface((100, 100)),
        back_image=pygame.Surface((100, 100)),
        position=(0, 0),
        hex_size=50,
        rotation=120,
        placement_state="placed",
        is_rotation_locked=True
    )
    
    # Verify fields exist
    assert hasattr(hex_card, 'rotation'), "HexCard should have rotation field"
    assert hasattr(hex_card, 'is_rotation_locked'), "HexCard should have is_rotation_locked field"
    
    # Verify values
    assert hex_card.rotation == 120, "Rotation should be stored"
    assert hex_card.is_rotation_locked is True, "Rotation should be locked"
    
    pygame.quit()


def test_handle_input_placing_calls_handle_right_click():
    """Test that _handle_input_placing() calls handle_right_click() on right-click."""
    pygame.init()
    
    # Create mock CombatScene
    core_game_state = Mock(spec=CoreGameState)
    scene = CombatScene(core_game_state)
    
    # Mock placement_controller
    scene.placement_controller = Mock(spec=PlacementController)
    scene.placement_controller.preview_rotation = 0
    
    # Create right-click input
    events = [
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (100, 100)})
    ]
    input_state = InputState(events)
    
    # Call _handle_input_placing
    scene._handle_input_placing(input_state)
    
    # Verify handle_right_click was called
    scene.placement_controller.handle_right_click.assert_called_once()
    
    pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
