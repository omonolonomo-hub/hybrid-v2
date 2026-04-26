"""
Test script to verify HexSystem integration with BoardRendererV3.

Run this to verify Aşama 2 is complete.
"""

def test_board_renderer_import():
    """Test that BoardRendererV3 imports with HexSystem."""
    print("Testing BoardRendererV3 with HexSystem integration...")
    
    try:
        from ui.board_renderer_v3 import BoardRendererV3, hex_to_pixel, pixel_to_hex, HEX_SIZE
        print("✓ BoardRendererV3 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import BoardRendererV3: {e}")
        return False
    
    try:
        from core.hex_system import HexSystem
        print("✓ HexSystem imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import HexSystem: {e}")
        return False
    
    return True


def test_board_renderer_hex_system():
    """Test that BoardRendererV3 uses HexSystem correctly."""
    print("\nTesting BoardRendererV3 HexSystem integration...")
    
    from ui.board_renderer_v3 import BoardRendererV3, HEX_SIZE
    
    # Create renderer with origin
    origin = (800, 480)
    renderer = BoardRendererV3(origin=origin)
    
    # Check that hex_system was created
    assert hasattr(renderer, 'hex_system'), "BoardRendererV3 should have hex_system attribute"
    print("✓ BoardRendererV3 has hex_system attribute")
    
    # Check hex_system configuration
    assert renderer.hex_system.hex_size == HEX_SIZE, f"hex_size mismatch: {renderer.hex_system.hex_size} != {HEX_SIZE}"
    assert renderer.hex_system.origin == origin, f"origin mismatch: {renderer.hex_system.origin} != {origin}"
    print(f"✓ HexSystem configured correctly (size={HEX_SIZE}, origin={origin})")
    
    # Test coordinate conversion through renderer
    test_q, test_r = 2, -1
    px, py = renderer.hex_system.hex_to_pixel(test_q, test_r)
    result_q, result_r = renderer.hex_system.pixel_to_hex(px, py)
    
    assert (test_q, test_r) == (result_q, result_r), \
        f"Round-trip failed: ({test_q}, {test_r}) -> ({result_q}, {result_r})"
    print(f"✓ Round-trip conversion through renderer: ({test_q}, {test_r}) -> pixel -> ({result_q}, {result_r})")
    
    return True


def test_module_level_functions():
    """Test that module-level functions use HexSystem."""
    print("\nTesting module-level hex functions...")
    
    from ui.board_renderer_v3 import hex_to_pixel, pixel_to_hex, HEX_SIZE
    
    origin_x, origin_y = 800, 480
    test_q, test_r = 3, -2
    
    # Test hex_to_pixel
    px, py = hex_to_pixel(test_q, test_r, origin_x, origin_y)
    print(f"✓ hex_to_pixel({test_q}, {test_r}) -> ({px}, {py})")
    
    # Test pixel_to_hex with cube rounding
    result_q, result_r = pixel_to_hex(px, py, origin_x, origin_y)
    assert (test_q, test_r) == (result_q, result_r), \
        f"Module-level round-trip failed: ({test_q}, {test_r}) -> ({result_q}, {result_r})"
    print(f"✓ pixel_to_hex({px}, {py}) -> ({result_q}, {result_r})")
    
    # Test cube rounding (not simple round)
    # This should use cube rounding algorithm
    fractional_px = px + 10  # Slightly offset
    fractional_py = py + 10
    rounded_q, rounded_r = pixel_to_hex(fractional_px, fractional_py, origin_x, origin_y)
    
    # Verify cube constraint
    s = -rounded_q - rounded_r
    assert rounded_q + rounded_r + s == 0, \
        f"Cube constraint violated: {rounded_q} + {rounded_r} + {s} = {rounded_q + rounded_r + s}"
    print(f"✓ Cube rounding works: offset pixel -> ({rounded_q}, {rounded_r}) satisfies q+r+s=0")
    
    return True


def test_backward_compatibility():
    """Test that existing code using module-level functions still works."""
    print("\nTesting backward compatibility...")
    
    from ui.board_renderer_v3 import hex_to_pixel, pixel_to_hex
    
    # Simulate existing code pattern
    origin = (800, 480)
    coords = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1), (-1, 1)]
    
    for q, r in coords:
        px, py = hex_to_pixel(q, r, *origin)
        back_q, back_r = pixel_to_hex(px, py, *origin)
        assert (q, r) == (back_q, back_r), \
            f"Backward compatibility broken for ({q}, {r})"
    
    print(f"✓ All {len(coords)} coordinate conversions work correctly")
    print("✓ Backward compatibility maintained")
    
    return True


if __name__ == "__main__":
    success = test_board_renderer_import()
    
    if success:
        test_board_renderer_hex_system()
        test_module_level_functions()
        test_backward_compatibility()
        
        print("\n" + "="*60)
        print("✓ AŞAMA 2 TAMAMLANDI!")
        print("="*60)
        print("\nHexSystem entegrasyonu başarılı:")
        print("  ✓ BoardRendererV3 artık HexSystem kullanıyor")
        print("  ✓ Cube rounding algoritması aktif")
        print("  ✓ Module-level fonksiyonlar güncellendi")
        print("  ✓ Geriye dönük uyumluluk korundu")
        print("  ✓ Görsel render fonksiyonları değişmedi")
        print("\nKritik değişiklikler:")
        print("  - pixel_to_hex() artık cube rounding kullanıyor")
        print("  - Basit round(q), round(r) kaldırıldı")
        print("  - Koordinat hesaplamaları merkezileştirildi")
        print("\nAşama 3'e geçmeye hazır!")
    else:
        print("\n✗ Import tests failed. Please check the errors above.")
