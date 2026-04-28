"""
Checkpoint verification for LobbyScene implementation.
Task 6: Verify LobbyScene is complete and working correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_lobby_scene_structure():
    """Verify LobbyScene has all required methods and fields."""
    print("=" * 60)
    print("CHECKPOINT 6: LobbyScene Implementation Verification")
    print("=" * 60)
    
    from v2.scenes.lobby import LobbyScene
    from v2.core.scene_manager import Scene
    
    # Check inheritance
    assert issubclass(LobbyScene, Scene), "LobbyScene must inherit from Scene"
    print("✓ LobbyScene inherits from Scene")
    
    # Create instance
    lobby = LobbyScene()
    print("✓ LobbyScene instance created successfully")
    
    # Check required fields
    assert hasattr(lobby, '_strategies'), "Missing _strategies field"
    assert hasattr(lobby, '_human_name'), "Missing _human_name field"
    assert hasattr(lobby, '_font_title'), "Missing _font_title field"
    assert hasattr(lobby, '_font_row'), "Missing _font_row field"
    assert hasattr(lobby, '_font_button'), "Missing _font_button field"
    assert hasattr(lobby, '_btn_rect'), "Missing _btn_rect field"
    assert hasattr(lobby, '_audio_loader'), "Missing _audio_loader field"
    print("✓ All required fields present")
    
    # Check lazy initialization (fonts should be None before init)
    assert lobby._font_title is None, "Font should be None before initialization"
    assert lobby._font_row is None, "Font should be None before initialization"
    assert lobby._font_button is None, "Font should be None before initialization"
    assert lobby._btn_rect is None, "Button rect should be None before initialization"
    print("✓ Lazy initialization verified (fonts are None)")
    
    # Check strategies list
    assert len(lobby._strategies) == 7, "Should have exactly 7 AI strategies"
    expected_strategies = ["random", "warrior", "builder", "evolver", "economist", "balancer", "rare_hunter"]
    assert lobby._strategies == expected_strategies, f"Strategies mismatch: {lobby._strategies}"
    print(f"✓ 7 AI strategies configured: {lobby._strategies}")
    
    # Check human name
    assert lobby._human_name == "HUMAN", f"Human name should be 'HUMAN', got '{lobby._human_name}'"
    print(f"✓ Human player name: {lobby._human_name}")
    
    # Check required methods
    assert hasattr(lobby, '_init_fonts'), "Missing _init_fonts method"
    assert hasattr(lobby, 'draw'), "Missing draw method"
    assert hasattr(lobby, 'handle_event'), "Missing handle_event method"
    assert hasattr(lobby, 'on_exit'), "Missing on_exit method"
    print("✓ All required methods present")
    
    # Check method signatures
    import inspect
    
    # _init_fonts should take no parameters (except self)
    sig = inspect.signature(lobby._init_fonts)
    assert len(sig.parameters) == 0, "_init_fonts should take no parameters"
    
    # draw should take surface parameter
    sig = inspect.signature(lobby.draw)
    assert len(sig.parameters) == 1, "draw should take 1 parameter (surface)"
    
    # handle_event should take event parameter
    sig = inspect.signature(lobby.handle_event)
    assert len(sig.parameters) == 1, "handle_event should take 1 parameter (event)"
    
    # on_exit should take no parameters
    sig = inspect.signature(lobby.on_exit)
    assert len(sig.parameters) == 0, "on_exit should take no parameters"
    
    print("✓ Method signatures correct")
    
    # Test on_exit cleanup
    lobby._audio_loader = "test_value"
    lobby.on_exit()
    assert lobby._audio_loader is None, "on_exit should set _audio_loader to None"
    print("✓ on_exit cleanup works correctly")
    
    print("\n" + "=" * 60)
    print("✅ CHECKPOINT 6 PASSED: LobbyScene implementation complete!")
    print("=" * 60)
    print("\nSummary:")
    print("  • Constructor initializes all fields correctly")
    print("  • Lazy initialization pattern implemented")
    print("  • 7 AI strategies configured")
    print("  • Human player configured")
    print("  • All required methods present with correct signatures")
    print("  • Resource cleanup (on_exit) works correctly")
    print("\nNext steps:")
    print("  • Task 7: Update main.py to use MenuScene")
    print("  • Optional: Write property-based tests")
    print("  • Optional: Write integration tests")
    
    return True


if __name__ == "__main__":
    try:
        test_lobby_scene_structure()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ CHECKPOINT 6 FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
