"""
Test scene transition validation in SceneManager.

Tests:
- Valid transitions are allowed
- Invalid transitions are rejected
- Override flag bypasses validation
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock

from core.scene_manager import SceneManager
from core.scene import Scene
from core.core_game_state import CoreGameState


class MockLobbyScene(Scene):
    """Mock lobby scene for testing."""
    
    def __init__(self, core_game_state):
        super().__init__(core_game_state)
    
    def handle_input(self, input_state):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass


class MockGameLoopScene(Scene):
    """Mock game loop scene for testing."""
    
    def __init__(self, core_game_state):
        super().__init__(core_game_state)
    
    def handle_input(self, input_state):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass


class MockShopScene(Scene):
    """Mock shop scene for testing."""
    
    def __init__(self, core_game_state):
        super().__init__(core_game_state)
    
    def handle_input(self, input_state):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass


class MockCombatScene(Scene):
    """Mock combat scene for testing."""
    
    def __init__(self, core_game_state):
        super().__init__(core_game_state)
    
    def handle_input(self, input_state):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass


class MockGameOverScene(Scene):
    """Mock game over scene for testing."""
    
    def __init__(self, core_game_state):
        super().__init__(core_game_state)
    
    def handle_input(self, input_state):
        pass
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        pass


def create_mock_game_state():
    """Create a mock CoreGameState for testing."""
    mock_game = Mock()
    mock_game.turn = 1
    mock_game.players = []
    
    return CoreGameState(game=mock_game)


def test_valid_transitions_allowed():
    """Test that valid transitions are allowed."""
    # Initialize pygame (required for Scene)
    pygame.init()
    
    core_game_state = create_mock_game_state()
    
    # Create scene manager with lobby scene
    lobby_scene = MockLobbyScene(core_game_state)
    scene_manager = SceneManager(lobby_scene)
    
    # Register all scene factories
    scene_manager.register_scene_factory("lobby", lambda cgs, **kw: MockLobbyScene(cgs))
    scene_manager.register_scene_factory("game_loop", lambda cgs, **kw: MockGameLoopScene(cgs))
    scene_manager.register_scene_factory("shop", lambda cgs, **kw: MockShopScene(cgs))
    scene_manager.register_scene_factory("combat", lambda cgs, **kw: MockCombatScene(cgs))
    scene_manager.register_scene_factory("game_over", lambda cgs, **kw: MockGameOverScene(cgs))
    
    # Test valid transition: lobby -> game_loop
    scene_manager.request_transition("game_loop")
    assert scene_manager._transition_requested is not None
    assert scene_manager._transition_requested[0] == "game_loop"
    
    # Execute transition
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "game_loop"
    
    # Test valid transition: game_loop -> shop
    scene_manager.request_transition("shop")
    assert scene_manager._transition_requested is not None
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "shop"
    
    # Test valid transition: shop -> combat
    scene_manager.request_transition("combat")
    assert scene_manager._transition_requested is not None
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "combat"
    
    # Test valid transition: combat -> game_loop
    scene_manager.request_transition("game_loop")
    assert scene_manager._transition_requested is not None
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "game_loop"
    
    # Test valid transition: game_loop -> game_over
    scene_manager.request_transition("game_over")
    assert scene_manager._transition_requested is not None
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "game_over"
    
    # Test valid transition: game_over -> lobby
    scene_manager.request_transition("lobby")
    assert scene_manager._transition_requested is not None
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "lobby"
    
    pygame.quit()


def test_invalid_transitions_rejected(capsys):
    """Test that invalid transitions are rejected."""
    pygame.init()
    
    core_game_state = create_mock_game_state()
    lobby_scene = MockLobbyScene(core_game_state)
    
    scene_manager = SceneManager(lobby_scene)
    scene_manager.register_scene_factory("shop", lambda cgs, **kw: MockShopScene(cgs))
    scene_manager.register_scene_factory("combat", lambda cgs, **kw: MockCombatScene(cgs))
    
    # Test invalid transition: lobby -> shop (should be lobby -> game_loop)
    scene_manager.request_transition("shop")
    assert scene_manager._transition_requested is None  # Transition rejected
    
    # Verify error message was printed
    captured = capsys.readouterr()
    assert "ERROR: Invalid scene transition: lobby -> shop" in captured.out
    
    # Test invalid transition: lobby -> combat
    scene_manager.request_transition("combat")
    assert scene_manager._transition_requested is None  # Transition rejected
    
    captured = capsys.readouterr()
    assert "ERROR: Invalid scene transition: lobby -> combat" in captured.out
    
    # Verify scene didn't change
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "lobby"
    
    pygame.quit()


def test_override_flag_bypasses_validation():
    """Test that override_validation flag bypasses transition validation."""
    pygame.init()
    
    core_game_state = create_mock_game_state()
    lobby_scene = MockLobbyScene(core_game_state)
    
    scene_manager = SceneManager(lobby_scene)
    scene_manager.register_scene_factory("combat", lambda cgs, **kw: MockCombatScene(cgs))
    
    # Test invalid transition with override flag
    scene_manager.request_transition("combat", override_validation=True)
    assert scene_manager._transition_requested is not None  # Transition allowed
    assert scene_manager._transition_requested[0] == "combat"
    
    # Execute transition
    scene_manager._execute_transition()
    assert scene_manager._get_scene_name(scene_manager.active_scene) == "combat"
    
    pygame.quit()


def test_get_valid_targets():
    """Test _get_valid_targets helper method."""
    pygame.init()
    
    core_game_state = create_mock_game_state()
    lobby_scene = MockLobbyScene(core_game_state)
    scene_manager = SceneManager(lobby_scene)
    
    # Test valid targets from lobby
    targets = scene_manager._get_valid_targets("lobby")
    assert targets == ["game_loop"]
    
    # Test valid targets from game_loop
    targets = scene_manager._get_valid_targets("game_loop")
    assert set(targets) == {"shop", "game_over"}
    
    # Test valid targets from shop
    targets = scene_manager._get_valid_targets("shop")
    assert targets == ["combat"]
    
    # Test valid targets from combat
    targets = scene_manager._get_valid_targets("combat")
    assert targets == ["game_loop"]
    
    # Test valid targets from game_over
    targets = scene_manager._get_valid_targets("game_over")
    assert targets == ["lobby"]
    
    pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
