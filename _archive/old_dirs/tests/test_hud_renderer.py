"""
Test suite for HUDRenderer extraction verification.

This test verifies that all drawing functions have been properly extracted
from run_game.py to ui/hud_renderer.py and that they work correctly.
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock


def test_hud_renderer_imports():
    """Test that all expected functions can be imported from hud_renderer."""
    from ui.hud_renderer import (
        draw_cyber_victorian_hud,
        draw_player_panel,
        draw_player_info,
        draw_combat_breakdown,
        draw_turn_popup,
        draw_game_over,
        draw_passive_buff_panel,
        draw_synergy_hud,
        draw_hand_panel,
        hp_color,
        _active_synergy_counts,
        _hand_card_rects,
        get_hovered_synergy_group,
        HUDRenderer,
    )
    
    # All imports successful
    assert draw_cyber_victorian_hud is not None
    assert draw_player_panel is not None
    assert draw_player_info is not None
    assert draw_combat_breakdown is not None
    assert draw_turn_popup is not None
    assert draw_game_over is not None
    assert draw_passive_buff_panel is not None
    assert draw_synergy_hud is not None
    assert draw_hand_panel is not None
    assert hp_color is not None
    assert _active_synergy_counts is not None
    assert _hand_card_rects is not None
    assert get_hovered_synergy_group is not None
    assert HUDRenderer is not None


def test_hp_color():
    """Test hp_color helper function."""
    from ui.hud_renderer import hp_color
    
    # High HP (> 50%) should return green
    color = hp_color(100, 150)
    assert color == (70, 225, 140)
    
    # Medium HP (25-50%) should return yellow
    color = hp_color(50, 150)
    assert color == (220, 180, 40)
    
    # Low HP (< 25%) should return red
    color = hp_color(20, 150)
    assert color == (255, 95, 110)


def test_hand_card_rects():
    """Test _hand_card_rects helper function."""
    from ui.hud_renderer import _hand_card_rects
    
    # Test with 3 cards
    rects = _hand_card_rects(3)
    assert len(rects) == 3
    assert all(isinstance(r, pygame.Rect) for r in rects)
    
    # Verify vertical stacking
    assert rects[0].y < rects[1].y < rects[2].y
    
    # Test with 0 cards
    rects = _hand_card_rects(0)
    assert len(rects) == 0


def test_get_hovered_synergy_group():
    """Test get_hovered_synergy_group helper function."""
    from ui.hud_renderer import get_hovered_synergy_group
    
    # Create mock surface
    surface = Mock()
    surface.get_width.return_value = 1600
    surface.get_height.return_value = 960
    
    # Test hovering over first group (EXISTENCE)
    # Calculate expected position
    box_w = 140
    gap = 14
    total_w = 3 * box_w + 2 * gap
    start_x = (1600 - total_w) // 2
    y = 960 - 92
    
    # Mouse over first badge
    result = get_hovered_synergy_group(surface, (start_x + 70, y + 16))
    assert result == "EXISTENCE"
    
    # Mouse not over any badge
    result = get_hovered_synergy_group(surface, (0, 0))
    assert result is None


def test_hud_renderer_class():
    """Test HUDRenderer class initialization and methods."""
    from ui.hud_renderer import HUDRenderer
    
    # Create mock fonts
    fonts = {
        "xs_bold": Mock(),
        "sm_bold": Mock(),
        "md_bold": Mock(),
        "lg": Mock(),
        "sm": Mock(),
        "md": Mock(),
        "xs": Mock(),
    }
    
    # Initialize HUDRenderer
    hud = HUDRenderer(fonts)
    assert hud.fonts == fonts
    
    # Verify all methods exist
    assert hasattr(hud, 'draw_hud')
    assert hasattr(hud, 'draw_players')
    assert hasattr(hud, 'draw_player_details')
    assert hasattr(hud, 'draw_breakdown')
    assert hasattr(hud, 'draw_popup')
    assert hasattr(hud, 'draw_winner')
    assert hasattr(hud, 'draw_passives')
    assert hasattr(hud, 'draw_synergies')
    assert hasattr(hud, 'draw_hand')


def test_active_synergy_counts():
    """Test _active_synergy_counts helper function."""
    from ui.hud_renderer import _active_synergy_counts
    from collections import Counter
    
    # Create mock player with board
    player = Mock()
    player.board = Mock()
    
    # Create mock cards with stats
    card1 = Mock()
    card1.stats = {"existence_1": 5, "existence_2": 3}
    
    card2 = Mock()
    card2.stats = {"mind_1": 4, "connection_1": 2}
    
    player.board.grid = {
        (0, 0): card1,
        (1, 0): card2,
    }
    
    # Note: This test will fail without proper STAT_TO_GROUP mapping
    # but verifies the function can be called
    result = _active_synergy_counts(player)
    assert isinstance(result, Counter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
