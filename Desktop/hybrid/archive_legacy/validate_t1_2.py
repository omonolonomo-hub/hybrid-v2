"""
T1.2 Validation Script
Validates that all HUD functions are properly extracted and importable.
"""

import sys

def validate_imports():
    """Validate all HUD functions can be imported."""
    print("=" * 60)
    print("T1.2 VALIDATION: HUD Renderer Extraction")
    print("=" * 60)
    
    try:
        # Test importing all extracted functions
        from ui.hud_renderer import (
            hp_color,
            _active_synergy_counts,
            _draw_text,
            draw_player_info,
            draw_player_panel,
            draw_synergy_hud,
            draw_combat_breakdown,
            draw_turn_popup,
            draw_game_over,
            draw_passive_buff_panel,
            draw_hand_panel,
            draw_cyber_victorian_hud,
            _hand_card_rects,
        )
        print("✓ All HUD functions imported successfully from ui.hud_renderer")
        
        # Test importing run_game with new imports
        import run_game
        print("✓ run_game.py imports successfully with HUD functions")
        
        # Verify functions are callable
        assert callable(hp_color), "hp_color is not callable"
        assert callable(_active_synergy_counts), "_active_synergy_counts is not callable"
        assert callable(_draw_text), "_draw_text is not callable"
        assert callable(draw_player_info), "draw_player_info is not callable"
        assert callable(draw_player_panel), "draw_player_panel is not callable"
        assert callable(draw_synergy_hud), "draw_synergy_hud is not callable"
        assert callable(draw_combat_breakdown), "draw_combat_breakdown is not callable"
        assert callable(draw_turn_popup), "draw_turn_popup is not callable"
        assert callable(draw_game_over), "draw_game_over is not callable"
        assert callable(draw_passive_buff_panel), "draw_passive_buff_panel is not callable"
        assert callable(draw_hand_panel), "draw_hand_panel is not callable"
        assert callable(draw_cyber_victorian_hud), "draw_cyber_victorian_hud is not callable"
        assert callable(_hand_card_rects), "_hand_card_rects is not callable"
        print("✓ All functions are callable")
        
        # Test helper functions
        color = hp_color(100)
        assert isinstance(color, tuple), "hp_color should return a tuple"
        assert len(color) == 3, "hp_color should return RGB tuple"
        print("✓ hp_color() works correctly")
        
        rects = _hand_card_rects(5)
        assert len(rects) == 5, "_hand_card_rects should return correct number of rects"
        print("✓ _hand_card_rects() works correctly")
        
        print("\n" + "=" * 60)
        print("IMPORT VALIDATION: PASSED ✓")
        print("=" * 60)
        print("\nNOTE: Visual validation requires running the game manually.")
        print("Please run: python run_game.py")
        print("\nManual validation checklist:")
        print("1. Player panel renders correctly (right side)")
        print("2. Player info renders correctly (left side)")
        print("3. Synergy HUD appears at bottom")
        print("4. Hand panel renders on left side")
        print("5. Passive buff panel renders below hand")
        print("6. Cyber-Victorian HUD renders (top-left corner + bottom bar)")
        print("7. Combat breakdown appears after combat")
        print("8. Turn popup renders and fades")
        print("9. Game over screen renders when game ends")
        print("\nIf all visual elements match the original, T1.2 is complete.")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"✗ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_imports()
    sys.exit(0 if success else 1)
