"""
Visual verification test for HUDRenderer extraction.

This test creates a minimal pygame environment and calls each drawing function
to verify they execute without errors. This is not a pixel-perfect comparison,
but ensures the functions are callable and don't crash.
"""

import pygame
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock


def test_visual_verification():
    """Test that all drawing functions can be called without errors."""
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1600, 960))
    
    # Create fonts
    def _font(name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            return pygame.font.SysFont("consolas", size, bold=bold)
    
    fonts = {
        "title": _font("bahnschrift", 28, bold=True),
        "lg": _font("consolas", 24, bold=True),
        "md": _font("consolas", 16),
        "md_bold": _font("consolas", 16, bold=True),
        "sm": _font("consolas", 13),
        "sm_bold": _font("consolas", 13, bold=True),
        "xs": _font("consolas", 12),
        "xs_bold": _font("consolas", 12, bold=True),
    }
    
    # Import all functions
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
        HUDRenderer,
    )
    
    # Create mock player
    player = Mock()
    player.pid = 0
    player.strategy = "test_strategy"
    player.hp = 100
    player.max_hp = 150
    player.gold = 50
    player.xp = 5
    player.xp_max = 10
    player.hand = []
    player.board = Mock()
    player.board.grid = {}
    player.board.alive_count = Mock(return_value=0)
    player.board.alive_cards = Mock(return_value=[])
    player.alive = True
    player.total_pts = 100
    player.win_streak = 3
    player.stats = {
        "wins": 5,
        "losses": 2,
        "win_streak_max": 5,
        "market_rolls": 10,
        "damage_taken": 50,
        "gold_earned": 200,
        "gold_spent": 150,
    }
    player.evolved_card_names = []
    player.passive_buff_log = []
    
    # Create mock players list
    players = [player]
    
    # Test each function
    try:
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Test draw_cyber_victorian_hud
        draw_cyber_victorian_hud(screen, player, 1, fonts, fast_mode=False, status_msg="Test")
        
        # Test draw_player_panel
        draw_player_panel(screen, players, 0, fonts["md_bold"], fonts["sm_bold"], 1300, 20)
        
        # Test draw_player_info
        draw_player_info(screen, player, 1, fonts["md_bold"], fonts["sm_bold"], 20, 145)
        
        # Test draw_synergy_hud
        draw_synergy_hud(screen, player, fonts, hovered_group=None)
        
        # Test draw_hand_panel
        draw_hand_panel(screen, player, fonts, None, (0, 0), 0)
        
        # Test draw_passive_buff_panel
        draw_passive_buff_panel(screen, player, fonts["sm_bold"], 20, 600, 200)
        
        # Test draw_combat_breakdown
        results = {
            "pid_a": 0,
            "pid_b": 1,
            "pts_a": 10,
            "pts_b": 8,
            "kill_a": 3,
            "kill_b": 2,
            "combo_a": 2,
            "combo_b": 1,
            "synergy_a": 1,
            "synergy_b": 0,
            "winner_pid": 0,
            "dmg": 5,
        }
        draw_combat_breakdown(screen, results, 0, players, fonts["md_bold"], fonts["sm_bold"])
        
        # Test draw_turn_popup
        popup_data = [results]
        draw_turn_popup(screen, popup_data, 0, players, fonts["lg"], fonts["md_bold"], fonts["sm_bold"], 255)
        
        # Test draw_game_over
        draw_game_over(screen, player, fonts["lg"], fonts["md_bold"])
        
        # Test HUDRenderer class
        hud = HUDRenderer(fonts)
        hud.draw_hud(screen, player, 1)
        hud.draw_players(screen, players, 0, 1300, 20)
        hud.draw_player_details(screen, player, 1, 20, 145)
        hud.draw_synergies(screen, player)
        hud.draw_hand(screen, player, None, (0, 0), 0)
        
        print("✓ All drawing functions executed successfully")
        print("✓ Visual verification complete")
        
        pygame.quit()
        return True
        
    except Exception as e:
        print(f"✗ Error during visual verification: {e}")
        pygame.quit()
        return False


if __name__ == "__main__":
    success = test_visual_verification()
    sys.exit(0 if success else 1)
