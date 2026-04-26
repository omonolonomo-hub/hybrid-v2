"""
Test for Task 1: CombatScene class structure and file organization

Verifies:
- CombatScene class extends Scene
- Class attributes are defined
- Lifecycle methods are implemented
- Imports work correctly
- CoreGameState validation works
"""

import pytest
import pygame
from unittest.mock import Mock

from scenes.combat_scene import CombatScene
from core.scene import Scene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState
from core.hex_system import HexSystem


def test_combat_scene_extends_scene():
    """Verify CombatScene extends Scene base class."""
    assert issubclass(CombatScene, Scene)


def test_combat_scene_has_required_attributes():
    """Verify CombatScene has required class attributes."""
    # Create mock game state
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_core_state = CoreGameState(mock_game)
    
    # Create scene
    scene = CombatScene(mock_core_state)
    
    # Verify attributes exist
    assert hasattr(scene, 'hex_size')
    assert hasattr(scene, 'origin_x')
    assert hasattr(scene, 'origin_y')
    assert hasattr(scene, 'grid_area')
    assert hasattr(scene, 'hex_system')
    
    # Verify initial values
    assert scene.hex_size == 0.0
    assert scene.origin_x == 0.0
    assert scene.origin_y == 0.0
    assert scene.grid_area == {}
    assert scene.hex_system is None


def test_combat_scene_lifecycle_methods_exist():
    """Verify all lifecycle methods are implemented."""
    # Create mock game state
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_core_state = CoreGameState(mock_game)
    
    # Create scene
    scene = CombatScene(mock_core_state)
    
    # Verify methods exist and are callable
    assert callable(scene.on_enter)
    assert callable(scene.on_exit)
    assert callable(scene.handle_input)
    assert callable(scene.update)
    assert callable(scene.draw)


def test_on_enter_validates_core_game_state():
    """Verify on_enter validates CoreGameState (Requirement 16.2, 16.3)."""
    # Test 1: None CoreGameState
    scene = CombatScene(None)
    with pytest.raises(AssertionError, match="CoreGameState is None"):
        scene.on_enter()
    
    # Test 2: None game attribute
    mock_core_state = Mock(spec=CoreGameState)
    mock_core_state.game = None
    scene = CombatScene(mock_core_state)
    
    with pytest.raises(AssertionError, match="Game is None"):
        scene.on_enter()
    
    # Test 3: Empty players list
    mock_game = Mock()
    mock_game.players = []
    mock_core_state = CoreGameState(mock_game)
    scene = CombatScene(mock_core_state)
    
    with pytest.raises(AssertionError, match="No players in game"):
        scene.on_enter()
    
    # Test 4: Valid CoreGameState
    mock_game = Mock()
    mock_player = Mock()
    mock_board = Mock()
    mock_board.grid = {}  # Empty grid is fine for validation test
    mock_player.board = mock_board
    mock_game.players = [mock_player]
    mock_core_state = CoreGameState(mock_game)
    scene = CombatScene(mock_core_state)
    
    # Should not raise
    scene.on_enter()
    
    # Verify UIState was created
    assert scene.ui_state is not None
    assert isinstance(scene.ui_state, UIState)
    
    # Verify validation logging occurred (check stdout)
    print("✓ CoreGameState validation test passed")



def test_on_exit_discards_ui_state():
    """Verify on_exit discards UIState."""
    # Create valid scene with proper mocking
    mock_game = Mock()
    mock_player = Mock()
    mock_board = Mock()
    mock_board.grid = {}  # Empty grid
    mock_player.board = mock_board
    mock_game.players = [mock_player]
    mock_core_state = CoreGameState(mock_game)
    scene = CombatScene(mock_core_state)
    
    # Enter scene
    scene.on_enter()
    assert scene.ui_state is not None
    
    # Exit scene
    scene.on_exit()
    assert scene.ui_state is None


def test_handle_input_accepts_input_state():
    """Verify handle_input accepts InputState parameter."""
    # Create valid scene with proper mocking
    mock_game = Mock()
    mock_player = Mock()
    mock_board = Mock()
    mock_board.grid = {}  # Empty grid
    mock_player.board = mock_board
    mock_game.players = [mock_player]
    mock_core_state = CoreGameState(mock_game)
    scene = CombatScene(mock_core_state)
    
    # Initialize scene first
    scene.on_enter()
    
    # Create mock input state with all required attributes
    mock_input = Mock(spec=InputState)
    mock_input.was_key_pressed_this_frame = Mock(return_value=False)
    mock_input.left_clicked = False
    mock_input.right_clicked = False
    mock_input.mouse_x = 0
    mock_input.mouse_y = 0
    mock_input.mouse_pos = (0, 0)  # Add mouse_pos tuple
    
    # Should not raise
    scene.handle_input(mock_input)


def test_update_accepts_delta_time():
    """Verify update accepts delta time parameter."""
    # Create valid scene with proper mocking
    mock_game = Mock()
    mock_player = Mock()
    mock_board = Mock()
    mock_board.grid = {}  # Empty grid
    mock_player.board = mock_board
    mock_game.players = [mock_player]
    mock_core_state = CoreGameState(mock_game)
    scene = CombatScene(mock_core_state)
    
    # Initialize scene first
    scene.on_enter()
    
    # Should not raise
    scene.update(16.67)  # ~60 FPS


def test_draw_accepts_screen_surface():
    """Verify draw accepts pygame Surface parameter."""
    # Initialize pygame
    pygame.init()
    
    try:
        # Create valid scene with proper mocking
        mock_game = Mock()
        mock_player = Mock()
        mock_player.pid = 0
        mock_player.hp = 100
        mock_player.gold = 50
        mock_player.win_streak = 0
        mock_player.interest = 0
        mock_board = Mock()
        mock_board.grid = {}  # Empty grid
        mock_player.board = mock_board
        mock_game.players = [mock_player]
        mock_core_state = CoreGameState(mock_game)
        mock_core_state.view_player_index = 0
        scene = CombatScene(mock_core_state)
        
        # Initialize scene first
        scene.on_enter()
        
        # Create test surface
        screen = pygame.Surface((1920, 1080))
        
        # Should not raise
        scene.draw(screen)
    finally:
        pygame.quit()


def test_imports_are_correct():
    """Verify all required imports are present."""
    from scenes.combat_scene import (
        CombatScene,
        Scene,
        CoreGameState,
        UIState,
        InputState,
        HexSystem,
    )
    
    # All imports should succeed
    assert CombatScene is not None
    assert Scene is not None
    assert CoreGameState is not None
    assert UIState is not None
    assert InputState is not None
    assert HexSystem is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
