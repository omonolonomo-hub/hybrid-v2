"""Test Task 3: Initialize HexSystem with calculated parameters."""

import pytest
import pygame
from unittest.mock import Mock
from scenes.combat_scene import CombatScene
from core.core_game_state import CoreGameState


def test_hex_system_initialized_in_on_enter():
    """Test that HexSystem is initialized in on_enter()."""
    # Setup
    pygame.init()
    mock_game = Mock()
    mock_game.players = [Mock()]
    core_game_state = CoreGameState(mock_game)
    
    combat_scene = CombatScene(core_game_state)
    
    # Before on_enter, hex_system should be None
    assert combat_scene.hex_system is None
    
    # Call on_enter
    combat_scene.on_enter()
    
    # After on_enter, hex_system should be initialized
    assert combat_scene.hex_system is not None
    assert combat_scene.hex_system.hex_size == combat_scene.hex_size
    assert combat_scene.hex_system.origin == (int(combat_scene.origin_x), int(combat_scene.origin_y))


def test_radial_grid_generates_37_hexes():
    """Test that radial_grid generates exactly 37 hexes."""
    # Setup
    pygame.init()
    mock_game = Mock()
    mock_game.players = [Mock()]
    core_game_state = CoreGameState(mock_game)
    
    combat_scene = CombatScene(core_game_state)
    combat_scene.on_enter()
    
    # Verify grid has exactly 37 hexes
    assert len(combat_scene.hex_grid) == 37
    
    # Verify center hex exists
    assert (0, 0) in combat_scene.hex_grid
    
    # Verify grid is stored for coordinate conversions
    assert combat_scene.hex_grid is not None
    assert isinstance(combat_scene.hex_grid, list)


def test_hex_system_parameters_from_layout():
    """Test that HexSystem uses calculated hex_size and origin."""
    # Setup
    pygame.init()
    mock_game = Mock()
    mock_game.players = [Mock()]
    core_game_state = CoreGameState(mock_game)
    
    combat_scene = CombatScene(core_game_state)
    combat_scene.on_enter()
    
    # Verify hex_size is calculated (should be > 0)
    assert combat_scene.hex_size > 0
    
    # Verify origin is calculated (should be centered)
    assert combat_scene.origin_x > 0
    assert combat_scene.origin_y > 0
    
    # Verify HexSystem uses these values
    assert combat_scene.hex_system.hex_size == combat_scene.hex_size
    assert combat_scene.hex_system.origin[0] == int(combat_scene.origin_x)
    assert combat_scene.hex_system.origin[1] == int(combat_scene.origin_y)


def test_hex_grid_ring_distribution():
    """Test that hex grid has correct ring distribution (1, 6, 12, 18)."""
    # Setup
    pygame.init()
    mock_game = Mock()
    mock_game.players = [Mock()]
    core_game_state = CoreGameState(mock_game)
    
    combat_scene = CombatScene(core_game_state)
    combat_scene.on_enter()
    
    # Count hexes by distance from center
    from collections import Counter
    distances = Counter()
    for q, r in combat_scene.hex_grid:
        # Cube distance from origin
        s = -q - r
        dist = (abs(q) + abs(r) + abs(s)) // 2
        distances[dist] += 1
    
    # Verify ring distribution
    assert distances[0] == 1, "Ring 0 should have 1 hex"
    assert distances[1] == 6, "Ring 1 should have 6 hexes"
    assert distances[2] == 12, "Ring 2 should have 12 hexes"
    assert distances[3] == 18, "Ring 3 should have 18 hexes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
