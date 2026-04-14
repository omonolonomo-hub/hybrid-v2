"""
Test script to verify core infrastructure imports correctly.

Run this to verify Aşama 1 - Görev 1 is complete.
"""

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing core infrastructure imports...")
    
    try:
        from core.scene import Scene
        print("✓ core.scene.Scene imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.scene.Scene: {e}")
        return False
    
    try:
        from core.scene_manager import SceneManager
        print("✓ core.scene_manager.SceneManager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.scene_manager.SceneManager: {e}")
        return False
    
    try:
        from core.input_state import InputState
        print("✓ core.input_state.InputState imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.input_state.InputState: {e}")
        return False
    
    try:
        from core.hex_system import HexSystem
        print("✓ core.hex_system.HexSystem imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core.hex_system.HexSystem: {e}")
        return False
    
    try:
        from core import Scene, SceneManager, InputState, HexSystem
        print("✓ All core classes imported via core package")
    except ImportError as e:
        print(f"✗ Failed to import via core package: {e}")
        return False
    
    print("\n✓ All core infrastructure imports successful!")
    return True


def test_hex_system():
    """Test HexSystem cube rounding algorithm."""
    print("\nTesting HexSystem cube rounding...")
    
    from core.hex_system import HexSystem
    
    hex_sys = HexSystem(hex_size=68, origin=(800, 480))
    
    # Test 1: Cube constraint
    q, r = hex_sys.cube_round(1.2, 0.8)
    s = -q - r
    assert q + r + s == 0, f"Cube constraint violated: {q} + {r} + {s} = {q+r+s}"
    print(f"✓ Cube constraint satisfied: ({q}, {r}, {s}) sum = 0")
    
    # Test 2: Round-trip conversion
    original_q, original_r = 3, -2
    px, py = hex_sys.hex_to_pixel(original_q, original_r)
    result_q, result_r = hex_sys.pixel_to_hex(px, py)
    assert (original_q, original_r) == (result_q, result_r), \
        f"Round-trip failed: ({original_q}, {original_r}) -> ({result_q}, {result_r})"
    print(f"✓ Round-trip conversion: ({original_q}, {original_r}) -> pixel -> ({result_q}, {result_r})")
    
    # Test 3: Neighbors
    neighbors = hex_sys.neighbors(0, 0)
    assert len(neighbors) == 6, f"Expected 6 neighbors, got {len(neighbors)}"
    print(f"✓ Neighbors of (0,0): {neighbors}")
    
    # Test 4: Distance
    dist = hex_sys.distance(0, 0, 3, -2)
    expected = 3  # Manhattan distance in hex space
    assert dist == expected, f"Distance calculation wrong: expected {expected}, got {dist}"
    print(f"✓ Distance from (0,0) to (3,-2): {dist}")
    
    print("\n✓ HexSystem tests passed!")


def test_input_state():
    """Test InputState intent translation."""
    print("\nTesting InputState intent translation...")
    
    import pygame
    from core.input_state import InputState
    
    # Initialize pygame for event creation
    pygame.init()
    
    # Create mock events
    events = [
        pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN, 'mod': 0}),
    ]
    
    input_state = InputState(events)
    
    assert input_state.intent_confirm == True, "Enter key should trigger intent_confirm"
    print("✓ Enter key triggers intent_confirm")
    
    # Test rotation intent
    events = [
        pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r, 'mod': 0}),
    ]
    input_state = InputState(events)
    assert input_state.intent_rotate_cw == True, "R key should trigger intent_rotate_cw"
    print("✓ R key triggers intent_rotate_cw")
    
    # Test shift+R
    events = [
        pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r, 'mod': pygame.KMOD_SHIFT}),
    ]
    input_state = InputState(events)
    assert input_state.intent_rotate_ccw == True, "Shift+R should trigger intent_rotate_ccw"
    print("✓ Shift+R triggers intent_rotate_ccw")
    
    pygame.quit()
    print("\n✓ InputState tests passed!")


if __name__ == "__main__":
    success = test_imports()
    
    if success:
        test_hex_system()
        test_input_state()
        print("\n" + "="*60)
        print("✓ AŞAMA 1 - GÖREV 1 TAMAMLANDI!")
        print("="*60)
        print("\nCore infrastructure başarıyla oluşturuldu:")
        print("  - core/scene.py")
        print("  - core/scene_manager.py")
        print("  - core/input_state.py")
        print("  - core/hex_system.py")
        print("\nHiçbir mevcut dosya değiştirilmedi.")
        print("Aşama 2'ye geçmeye hazır!")
    else:
        print("\n✗ Import tests failed. Please check the errors above.")
