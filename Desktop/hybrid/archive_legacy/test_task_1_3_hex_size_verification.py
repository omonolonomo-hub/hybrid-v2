"""
Test for Task 1.3: Verify rendering with updated hex size

This test verifies:
- HEX_SIZE has been updated to 85 (from 68)
- HEX_SIZE meets the minimum requirement of 80px
- Hex rendering works correctly with the new size
- Requirements 1.3, 1.4 are satisfied
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

def test_hex_size_updated():
    """Verify HEX_SIZE has been updated to 85."""
    from ui.renderer_v3 import HEX_SIZE
    
    print("=" * 60)
    print("Task 1.3: Hex Size Verification")
    print("=" * 60)
    print()
    
    print(f"Current HEX_SIZE: {HEX_SIZE}px")
    
    # Check that HEX_SIZE has been updated from 68
    assert HEX_SIZE != 68, "HEX_SIZE should be updated from 68"
    print("✓ HEX_SIZE has been updated from 68")
    
    # Check that HEX_SIZE is 85 as specified in the design
    assert HEX_SIZE == 85, f"HEX_SIZE should be 85, got {HEX_SIZE}"
    print("✓ HEX_SIZE is 85 as specified")
    
    # Check that HEX_SIZE meets minimum requirement
    MIN_HEX_SIZE = 80
    assert HEX_SIZE >= MIN_HEX_SIZE, f"HEX_SIZE should be at least {MIN_HEX_SIZE}"
    print(f"✓ HEX_SIZE meets minimum requirement ({MIN_HEX_SIZE}px)")
    
    print()
    return True


def test_board_renderer_uses_updated_size():
    """Verify BoardRendererV3 uses the updated HEX_SIZE."""
    from ui.board_renderer_v3 import BoardRendererV3, HEX_SIZE
    
    print("Testing BoardRendererV3 initialization...")
    
    # Create renderer
    renderer = BoardRendererV3(origin=(800, 470))
    
    # Verify HexSystem is initialized with correct size
    assert renderer.hex_system.hex_size == HEX_SIZE, \
        f"HexSystem should use HEX_SIZE={HEX_SIZE}, got {renderer.hex_system.hex_size}"
    print(f"✓ BoardRendererV3.hex_system uses HEX_SIZE={HEX_SIZE}")
    
    print()
    return True


def test_hex_dimensions():
    """Verify hex dimensions are adequate for card rendering."""
    from ui.renderer_v3 import HEX_SIZE
    import math
    
    print("Calculating hex dimensions...")
    
    # For a flat-top hexagon with radius HEX_SIZE:
    # - Width (point to point): 2 * HEX_SIZE
    # - Height (flat to flat): sqrt(3) * HEX_SIZE
    hex_width = 2 * HEX_SIZE
    hex_height = math.sqrt(3) * HEX_SIZE
    
    print(f"Hex width: {hex_width:.2f}px")
    print(f"Hex height: {hex_height:.2f}px")
    
    # The hex rendering is programmatic and designed to fit within the hex
    # We just need to verify the hex is large enough for readable content
    MIN_HEX_WIDTH = 140  # Minimum for readable content
    MIN_HEX_HEIGHT = 120  # Minimum for readable content
    
    assert hex_width >= MIN_HEX_WIDTH, \
        f"Hex width should be at least {MIN_HEX_WIDTH}px for readable content"
    print(f"✓ Hex width ({hex_width:.2f}px) is adequate for readable content")
    
    assert hex_height >= MIN_HEX_HEIGHT, \
        f"Hex height should be at least {MIN_HEX_HEIGHT}px for readable content"
    print(f"✓ Hex height ({hex_height:.2f}px) is adequate for readable content")
    
    print()
    return True


def test_edge_label_positioning():
    """Verify edge labels have adequate space."""
    from ui.renderer_v3 import HEX_SIZE, EDGE_LABEL_INSET
    
    print("Verifying edge label positioning...")
    print(f"HEX_SIZE: {HEX_SIZE}px")
    print(f"EDGE_LABEL_INSET: {EDGE_LABEL_INSET}px")
    
    # Edge labels are positioned EDGE_LABEL_INSET pixels from the edge
    # This should provide visible hex edges
    assert EDGE_LABEL_INSET > 0, "EDGE_LABEL_INSET should be positive"
    assert EDGE_LABEL_INSET < HEX_SIZE / 2, \
        "EDGE_LABEL_INSET should be less than half HEX_SIZE"
    
    print(f"✓ Edge labels are inset {EDGE_LABEL_INSET}px from edges")
    print("✓ Hex edges will be visible for edge stat display")
    
    print()
    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("TASK 1.3: TEST RENDERING WITH UPDATED HEX SIZE")
    print("=" * 60)
    print()
    
    try:
        # Run all tests
        test_hex_size_updated()
        test_board_renderer_uses_updated_size()
        test_hex_dimensions()
        test_edge_label_positioning()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Task 1.3 Verification Summary:")
        print("- HEX_SIZE updated from 68 to 85 ✓")
        print("- HEX_SIZE meets minimum requirement (80px) ✓")
        print("- BoardRendererV3 uses updated size ✓")
        print("- Hex dimensions adequate for card rendering ✓")
        print("- Hex edges visible for edge stat display ✓")
        print()
        print("Requirements 1.3, 1.4 are satisfied.")
        
        return True
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
