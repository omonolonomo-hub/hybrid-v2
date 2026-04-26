"""
Tests for GameOverScene

Verifies game over scene functionality:
- Scene initialization
- Restart flow (transitions to lobby)
- Quit flow (exits cleanly)
- Winner display
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock

from scenes.game_over_scene import GameOverScene
from core.core_game_state import CoreGameState
from core.input_state import InputState


@pytest.fixture
def mock_game():
    """Create a mock game instance."""
    game = Mock()
    game.turn = 10
    
    # Create mock players
    players = []
    for i in range(4):
        player = Mock()
        player.pid = i
        player.hp = 100 - i * 20  # P0: 100, P1: 80, P2: 60, P3: 40
        player.strategy = "warrior"
        player.alive = player.hp > 0
        player.total_pts = 50 + i * 10
        player.win_streak = i
        player.stats = {
            'wins': i * 2,
            'losses': i,
            'win_streak_max': i + 1,
            'gold_earned': 100 + i * 50,
            'damage_dealt': 200 + i * 100,
        }
        players.append(player)
    
    game.players = players
    return game


@pytest.fixture
def core_game_state(mock_game):
    """Create a CoreGameState with mock game."""
    return CoreGameState(mock_game)


@pytest.fixture
def game_over_scene(core_game_state):
    """Create a GameOverScene instance."""
    # Initialize pygame (required for font rendering)
    pygame.init()
    
    # Create scene with winner (P0)
    winner = core_game_state.game.players[0]
    scene = GameOverScene(core_game_state, winner=winner)
    
    # Mock scene_manager
    scene.scene_manager = Mock()
    
    return scene


def test_scene_initialization(game_over_scene):
    """Test that GameOverScene initializes correctly."""
    assert game_over_scene is not None
    assert game_over_scene.winner is not None
    assert game_over_scene.winner.pid == 0
    assert game_over_scene.winner.hp == 100


def test_on_enter_creates_ui_state(game_over_scene):
    """Test that on_enter creates UIState."""
    game_over_scene.on_enter()
    assert game_over_scene.ui_state is not None


def test_on_exit_discards_ui_state(game_over_scene):
    """Test that on_exit discards UIState."""
    game_over_scene.on_enter()
    assert game_over_scene.ui_state is not None
    
    game_over_scene.on_exit()
    assert game_over_scene.ui_state is None


def test_restart_key_transitions_to_lobby(game_over_scene):
    """Test that R key transitions to lobby."""
    game_over_scene.on_enter()
    
    # Create a real pygame event for R key
    pygame.event.clear()
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, mod=0)
    events = [event]
    input_state = InputState(events)
    
    # Handle input
    game_over_scene.handle_input(input_state)
    
    # Verify transition to lobby
    game_over_scene.scene_manager.request_transition.assert_called_once_with("lobby")


def test_restart_button_click_transitions_to_lobby(game_over_scene):
    """Test that clicking restart button transitions to lobby."""
    game_over_scene.on_enter()
    
    # Create a mock screen to calculate button positions
    screen = pygame.Surface((1920, 1080))
    game_over_scene.draw(screen)
    
    # Get restart button rect
    restart_rect = game_over_scene.restart_rect
    assert restart_rect is not None
    
    # Mock pygame.mouse.get_pos to return restart button center
    import unittest.mock
    with unittest.mock.patch('pygame.mouse.get_pos', return_value=restart_rect.center):
        # Create a real pygame event for mouse click
        pygame.event.clear()
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=restart_rect.center)
        events = [event]
        input_state = InputState(events)
        
        # Handle input
        game_over_scene.handle_input(input_state)
    
    # Verify transition to lobby
    game_over_scene.scene_manager.request_transition.assert_called_once_with("lobby")


def test_winner_determined_from_alive_players(core_game_state):
    """Test that winner is determined from alive players if not provided."""
    pygame.init()
    
    # Mock alive_players property to return list of players
    alive_players = [p for p in core_game_state.game.players if p.alive]
    type(core_game_state).alive_players = property(lambda self: alive_players)
    
    # Create scene without winner
    scene = GameOverScene(core_game_state)
    scene.scene_manager = Mock()
    
    # Call on_enter (should determine winner)
    scene.on_enter()
    
    # Verify winner is player with max HP (P0 with 100 HP)
    assert scene.winner is not None
    assert scene.winner.pid == 0
    assert scene.winner.hp == 100


def test_draw_renders_without_error(game_over_scene):
    """Test that draw method renders without error."""
    game_over_scene.on_enter()
    
    # Create a mock screen
    screen = pygame.Surface((1920, 1080))
    
    # Draw should not raise any exceptions
    game_over_scene.draw(screen)
    
    # Verify button rects are created
    assert game_over_scene.restart_rect is not None
    assert game_over_scene.quit_rect is not None


def test_hover_state_updates(game_over_scene):
    """Test that hover state updates based on mouse position."""
    game_over_scene.on_enter()
    
    # Draw to create button rects
    screen = pygame.Surface((1920, 1080))
    game_over_scene.draw(screen)
    
    # Create input state with mouse over restart button
    restart_center = game_over_scene.restart_rect.center
    events = []
    input_state = InputState(events)
    input_state.mouse_pos = restart_center
    
    # Handle input (updates hover state)
    game_over_scene.handle_input(input_state)
    
    # Verify hover state
    assert game_over_scene.hover_restart is True
    assert game_over_scene.hover_quit is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
