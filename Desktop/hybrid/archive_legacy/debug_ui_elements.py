"""
Debug script to identify missing UI elements
"""

import pygame
import sys

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((1600, 960))

# Create fonts dictionary
def _font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.SysFont("consolas", size, bold=bold)

fonts = {
    "title":   _font("bahnschrift", 28, bold=True),
    "lg":      _font("consolas", 24, bold=True),
    "md":      _font("consolas", 16),
    "md_bold": _font("consolas", 16, bold=True),
    "sm":      _font("consolas", 13),
    "sm_bold": _font("consolas", 13, bold=True),
    "xs":      _font("consolas", 12),
    "xs_bold": _font("consolas", 12, bold=True),
    "icon":    _font("segoeuisymbol", 18, bold=True),
}

print("=" * 60)
print("UI ELEMENT DEBUG")
print("=" * 60)

# Check fonts
print("\n1. Fonts Dictionary:")
for key, font in fonts.items():
    print(f"   ✓ fonts['{key}'] = {font}")

# Test imports
print("\n2. Import Test:")
try:
    from ui.hud_renderer import (
        draw_cyber_victorian_hud,
        draw_hand_panel,
        draw_player_panel,
        draw_player_info,
    )
    print("   ✓ All HUD functions imported")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Create mock player
print("\n3. Mock Player Test:")
try:
    from engine_core.player import Player
    from engine_core.card import get_card_pool
    
    player = Player(pid=0, strategy="aggressive")
    player.gold = 100
    player.hp = 150
    player.hand = []
    
    print(f"   ✓ Player created: gold={player.gold}, hp={player.hp}, hand={len(player.hand)}")
except Exception as e:
    print(f"   ✗ Player creation failed: {e}")
    sys.exit(1)

# Test draw_cyber_victorian_hud
print("\n4. Test draw_cyber_victorian_hud:")
try:
    screen.fill((0, 0, 0))
    draw_cyber_victorian_hud(
        screen, 
        player, 
        game_turn=1, 
        fonts=fonts,
        fast_mode=False,
        status_msg="Test message"
    )
    print("   ✓ draw_cyber_victorian_hud executed without error")
    print(f"   ✓ Gold should be visible: {player.gold} CR")
except Exception as e:
    print(f"   ✗ draw_cyber_victorian_hud failed: {e}")
    import traceback
    traceback.print_exc()

# Test draw_hand_panel
print("\n5. Test draw_hand_panel:")
try:
    draw_hand_panel(
        screen,
        player,
        fonts,
        selected_idx=None,
        mouse_pos=(0, 0),
        current_rotation=0
    )
    print("   ✓ draw_hand_panel executed without error")
    print(f"   ✓ Hand panel should show: {len(player.hand)} cards")
except Exception as e:
    print(f"   ✗ draw_hand_panel failed: {e}")
    import traceback
    traceback.print_exc()

# Save screenshot
print("\n6. Saving screenshot:")
try:
    pygame.image.save(screen, "debug_ui_screenshot.png")
    print("   ✓ Screenshot saved to: debug_ui_screenshot.png")
    print("   → Check this file to see if UI elements are rendered")
except Exception as e:
    print(f"   ✗ Screenshot save failed: {e}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
print("\nIf screenshot shows UI elements, the functions work correctly.")
print("If screenshot is blank/black, there may be a rendering issue.")
print("\nNext steps:")
print("1. Open debug_ui_screenshot.png")
print("2. Check if gold text is visible in top-left")
print("3. Check if 'Hand empty' message is visible on left side")
print("4. If visible: functions work, issue is elsewhere")
print("5. If not visible: rendering issue in functions")

pygame.quit()
