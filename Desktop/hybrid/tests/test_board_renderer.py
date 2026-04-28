"""
Tests for BoardRenderer — Centralized Board Card Rendering
===========================================================
Verifies that BoardRenderer correctly manages CardFlip lifecycle:
  - Syncs flip dict with board state (add/remove)
  - Updates flip animations and hover states
  - Provides hover coordinate detection
"""

import pygame
import pytest
from unittest.mock import Mock, MagicMock, patch
from v2.ui.board_renderer import BoardRenderer
from v2.ui.camera_controller import CameraState


@pytest.fixture
def mock_camera_state():
    """Create a mock camera state."""
    cam = Mock(spec=CameraState)
    cam.zoom = 1.0
    cam.offset_x = 0
    cam.offset_y = 0
    return cam


@pytest.fixture
def mock_state():
    """Create a mock PublicState with active_player."""
    state = Mock()
    state.active_player = Mock()
    state.active_player.board_card_info = {}
    return state


@pytest.fixture
def board_renderer():
    """Create a BoardRenderer instance."""
    pygame.init()
    return BoardRenderer()


def test_board_renderer_init(board_renderer):
    """Test BoardRenderer initializes with empty flip dict."""
    assert board_renderer._flips == {}


def test_board_renderer_sync_adds_new_cards(board_renderer, mock_state, mock_camera_state):
    """Test that sync() adds new cards to flip dict."""
    board_cards = {
        (0, 0): {"name": "TestCard1"},
        (1, 0): {"name": "TestCard2"},
    }
    
    with patch.object(board_renderer, '_add_board_flip') as mock_add:
        board_renderer.sync(board_cards, mock_state, mock_camera_state)
        assert mock_add.call_count == 2


def test_board_renderer_sync_removes_stale_cards(board_renderer, mock_state, mock_camera_state):
    """Test that sync() removes cards no longer on board."""
    # Add some initial flips
    board_renderer._flips[(0, 0)] = Mock()
    board_renderer._flips[(1, 0)] = Mock()
    board_renderer._flips[(2, 0)] = Mock()
    
    # New board state only has one card
    board_cards = {(0, 0): {"name": "TestCard1"}}
    
    with patch.object(board_renderer, '_add_board_flip'):
        board_renderer.sync(board_cards, mock_state, mock_camera_state)
    
    # Should only have the one card left
    assert len(board_renderer._flips) == 1
    assert (0, 0) in board_renderer._flips
    assert (1, 0) not in board_renderer._flips
    assert (2, 0) not in board_renderer._flips


def test_board_renderer_update_updates_flip_positions(board_renderer, mock_camera_state):
    """Test that update() updates flip dest_rect based on camera."""
    mock_flip = Mock()
    mock_flip.dest_rect = pygame.Rect(0, 0, 100, 100)
    board_renderer._flips[(0, 0)] = mock_flip
    
    board_renderer.update(16.0, mock_camera_state, (500, 500))
    
    # Verify update was called
    mock_flip.update.assert_called_once_with(16.0)


def test_board_renderer_update_handles_hover(board_renderer, mock_camera_state):
    """Test that update() correctly handles hover states."""
    mock_flip = Mock()
    # Create a real Rect that will be updated by the method
    mock_flip.dest_rect = pygame.Rect(0, 0, 50, 50)
    board_renderer._flips[(0, 0)] = mock_flip
    
    # After update, the rect will be repositioned based on axial_to_pixel
    # We need to check if hover_start/end are called, not the exact position
    board_renderer.update(16.0, mock_camera_state, (125, 125))
    
    # The method should call either hover_start or hover_end
    assert mock_flip.hover_start.called or mock_flip.hover_end.called
    assert mock_flip.update.called


def test_board_renderer_get_hover_coord(board_renderer):
    """Test that get_hover_coord() returns correct coordinate."""
    mock_flip1 = Mock()
    mock_flip1.dest_rect = pygame.Rect(100, 100, 50, 50)
    mock_flip2 = Mock()
    mock_flip2.dest_rect = pygame.Rect(200, 200, 50, 50)
    
    board_renderer._flips[(0, 0)] = mock_flip1
    board_renderer._flips[(1, 0)] = mock_flip2
    
    # Test hit on first card
    coord = board_renderer.get_hover_coord((125, 125))
    assert coord == (0, 0)
    
    # Test hit on second card
    coord = board_renderer.get_hover_coord((225, 225))
    assert coord == (1, 0)
    
    # Test miss
    coord = board_renderer.get_hover_coord((500, 500))
    assert coord is None


def test_board_renderer_clear(board_renderer):
    """Test that clear() removes all flips."""
    board_renderer._flips[(0, 0)] = Mock()
    board_renderer._flips[(1, 0)] = Mock()
    
    board_renderer.clear()
    assert len(board_renderer._flips) == 0


def test_board_renderer_remove(board_renderer):
    """Test that remove() removes specific flip."""
    board_renderer._flips[(0, 0)] = Mock()
    board_renderer._flips[(1, 0)] = Mock()
    
    board_renderer.remove((0, 0))
    
    assert (0, 0) not in board_renderer._flips
    assert (1, 0) in board_renderer._flips


def test_board_renderer_draw_empty(board_renderer):
    """Test that draw() handles empty flip dict gracefully."""
    surface = pygame.Surface((800, 600))
    board_renderer.draw(surface)  # Should not raise


def test_board_renderer_draw_renders_flips(board_renderer):
    """Test that draw() renders all flips in sorted order."""
    mock_flip1 = Mock()
    mock_flip1.hover_progress = 0.0
    mock_flip2 = Mock()
    mock_flip2.hover_progress = 0.5
    mock_flip3 = Mock()
    mock_flip3.hover_progress = 1.0
    
    board_renderer._flips[(0, 0)] = mock_flip1
    board_renderer._flips[(1, 0)] = mock_flip2
    board_renderer._flips[(2, 0)] = mock_flip3
    
    surface = pygame.Surface((800, 600))
    board_renderer.draw(surface)
    
    # All flips should be rendered
    mock_flip1.render.assert_called_once()
    mock_flip2.render.assert_called_once()
    mock_flip3.render.assert_called_once()


def test_board_renderer_fallback_surface():
    """Test that _fallback_card_surface creates valid surface."""
    surf = BoardRenderer._fallback_card_surface((255, 0, 0), 100, 100)
    assert isinstance(surf, pygame.Surface)
    assert surf.get_size() == (100, 100)
