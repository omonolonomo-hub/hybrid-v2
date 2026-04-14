"""
Test for Task 4: Basic hex grid rendering

Verifies:
- Sub-task 4.1: _draw_hex_grid() method exists and works
- Sub-task 4.2: _get_hex_corners() helper method exists and works
- Requirements 1.5, 3.1: Hex grid rendering with coordinate conversion
"""

import pytest
import pygame
import math
from unittest.mock import Mock
from scenes.combat_scene import CombatScene
from core.core_game_state import CoreGameState


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


def test_get_hex_corners_method_exists(combat_scene):
    """Verify _get_hex_corners() method exists."""
    assert hasattr(combat_scene, '_get_hex_corners')
    assert callable(combat_scene._get_hex_corners)


def test_get_hex_corners_returns_six_corners(combat_scene):
    """Verify _get_hex_corners() returns exactly 6 corners."""
    corners = combat_scene._get_hex_corners(100, 100, 50)
    assert len(corners) == 6
    assert all(isinstance(corner, tuple) for corner in corners)
    assert all(len(corner) == 2 for corner in corners)


def test_get_hex_corners_correct_angles(combat_scene):
    """Verify _get_hex_corners() calculates corners at correct angles."""
    center_x, center_y = 100, 100
    size = 50
    corners = combat_scene._get_hex_corners(center_x, center_y, size)
    
    # Expected angles: 0°, 60°, 120°, 180°, 240°, 300°
    expected_angles = [0, 60, 120, 180, 240, 300]
    
    for i, angle in enumerate(expected_angles):
        rad = math.radians(angle)
        expected_x = center_x + size * math.cos(rad)
        expected_y = center_y + size * math.sin(rad)
        
        # Allow small floating point error
        assert abs(corners[i][0] - expected_x) < 0.01
        assert abs(corners[i][1] - expected_y) < 0.01


def test_draw_hex_grid_method_exists(combat_scene):
    """Verify _draw_hex_grid() method exists."""
    assert hasattr(combat_scene, '_draw_hex_grid')
    assert callable(combat_scene._draw_hex_grid)


def test_draw_hex_grid_no_crash(combat_scene):
    """Verify _draw_hex_grid() can be called without crashing."""
    screen = pygame.Surface((1920, 1080))
    # Should not raise any exceptions
    combat_scene._draw_hex_grid(screen)


def test_draw_method_calls_draw_hex_grid(combat_scene):
    """Verify draw() method calls _draw_hex_grid()."""
    screen = pygame.Surface((1920, 1080))
    
    # Mock _draw_hex_grid to track if it's called
    original_method = combat_scene._draw_hex_grid
    call_count = [0]
    
    def mock_draw_hex_grid(s):
        call_count[0] += 1
        original_method(s)
    
    combat_scene._draw_hex_grid = mock_draw_hex_grid
    
    # Call draw
    combat_scene.draw(screen)
    
    # Verify _draw_hex_grid was called
    assert call_count[0] == 1


def test_hex_grid_has_37_hexes(combat_scene):
    """Verify hex_grid contains exactly 37 hexes."""
    assert len(combat_scene.hex_grid) == 37


def test_hex_system_initialized(combat_scene):
    """Verify HexSystem is initialized in on_enter."""
    assert combat_scene.hex_system is not None
    assert combat_scene.hex_system.hex_size == combat_scene.hex_size
    assert combat_scene.hex_system.origin == (int(combat_scene.origin_x), int(combat_scene.origin_y))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
