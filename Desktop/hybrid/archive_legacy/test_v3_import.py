"""
Quick test to verify V3 renderers can be imported and instantiated.
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("Testing V3 renderer imports...")

try:
    from ui.renderer_v3 import CyberRendererV3
    print("✓ CyberRendererV3 imported successfully")
    
    from ui.board_renderer_v3 import BoardRendererV3, hex_to_pixel, pixel_to_hex
    print("✓ BoardRendererV3 imported successfully")
    
    # Test instantiation
    cyber = CyberRendererV3()
    print("✓ CyberRendererV3 instantiated")
    
    board_renderer = BoardRendererV3((800, 480), "tempo", cyber)
    print("✓ BoardRendererV3 instantiated")
    
    # Test coordinate conversion
    px, py = hex_to_pixel(0, 0, 800, 480)
    print(f"✓ hex_to_pixel(0, 0) = ({px}, {py})")
    
    q, r = pixel_to_hex(px, py, 800, 480)
    print(f"✓ pixel_to_hex({px}, {py}) = ({q}, {r})")
    
    print("\n✅ All V3 renderer tests passed!")
    print("The game should now use the clean V3 renderers.")
    print("\nTo test in game:")
    print("1. Run: python run_game.py")
    print("2. Check that board cards have tarot-style hex frames")
    print("3. Check that shop cards show only non-zero stats")
    print("4. Check that hover compare mode works in shop")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
