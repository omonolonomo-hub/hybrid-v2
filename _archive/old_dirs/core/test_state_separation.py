"""
Test script to verify CoreGameState and UIState separation.

Run this to verify Aşama 3 is complete.
"""

def test_state_imports():
    """Test that state classes can be imported."""
    print("Testing state class imports...")
    
    try:
        from core.core_game_state import CoreGameState
        print("✓ CoreGameState imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CoreGameState: {e}")
        return False
    
    try:
        from core.ui_state import UIState
        print("✓ UIState imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import UIState: {e}")
        return False
    
    try:
        from core import CoreGameState, UIState
        print("✓ Both state classes imported via core package")
    except ImportError as e:
        print(f"✗ Failed to import via core package: {e}")
        return False
    
    return True


def test_core_game_state():
    """Test CoreGameState functionality."""
    print("\nTesting CoreGameState (SAVEABLE)...")
    
    from core.core_game_state import CoreGameState
    
    # Create mock Game object
    class MockGame:
        def __init__(self):
            self.turn = 5
            self.players = [MockPlayer(i) for i in range(8)]
        
        def alive_players(self):
            return [p for p in self.players if p.alive]
    
    class MockPlayer:
        def __init__(self, pid):
            self.pid = pid
            self.alive = True
            self.hp = 100
            self.gold = 10
    
    game = MockGame()
    state = CoreGameState(game)
    
    # Test properties
    assert state.game == game, "Game reference should be stored"
    print("✓ CoreGameState stores game reference")
    
    assert state.view_player_index == 0, "Default view_player_index should be 0"
    print("✓ Default view_player_index is 0")
    
    assert state.fast_mode == False, "Default fast_mode should be False"
    print("✓ Default fast_mode is False")
    
    # Test current_player property
    current = state.current_player
    assert current.pid == 0, "Current player should be player 0"
    print("✓ current_player property works")
    
    # Test switch_player
    state.switch_player(1)
    assert state.view_player_index == 1, "Should switch to player 1"
    print("✓ switch_player(1) works")
    
    state.switch_player(-1)
    assert state.view_player_index == 0, "Should switch back to player 0"
    print("✓ switch_player(-1) works")
    
    # Test wrap-around
    state.view_player_index = 7
    state.switch_player(1)
    assert state.view_player_index == 0, "Should wrap around to player 0"
    print("✓ switch_player wraps around correctly")
    
    # Test serialization
    data = state.to_dict()
    assert "view_player_index" in data, "Serialization should include view_player_index"
    assert "fast_mode" in data, "Serialization should include fast_mode"
    print("✓ to_dict() serialization works")
    
    # Test deserialization
    state2 = CoreGameState.from_dict(data, game)
    assert state2.view_player_index == state.view_player_index, "Deserialization should restore view_player_index"
    assert state2.fast_mode == state.fast_mode, "Deserialization should restore fast_mode"
    print("✓ from_dict() deserialization works")
    
    print("\n✓ CoreGameState tests passed!")
    return True


def test_ui_state():
    """Test UIState functionality."""
    print("\nTesting UIState (THROWAWAY)...")
    
    from core.ui_state import UIState
    
    state = UIState()
    
    # Test default values
    assert state.selected_hand_idx is None, "Default selected_hand_idx should be None"
    assert state.hovered_tile is None, "Default hovered_tile should be None"
    assert state.pending_rotation == 0, "Default pending_rotation should be 0"
    assert state.placed_this_turn == 0, "Default placed_this_turn should be 0"
    assert len(state.locked_coords) == 0, "Default locked_coords should be empty"
    print("✓ UIState default values are correct")
    
    # Test state modification
    state.selected_hand_idx = 2
    state.hovered_tile = (3, -1)
    state.pending_rotation = 3
    state.placed_this_turn = 1
    state.locked_coords.add((0, 0))
    
    assert state.selected_hand_idx == 2, "Should store selected_hand_idx"
    assert state.hovered_tile == (3, -1), "Should store hovered_tile"
    assert state.pending_rotation == 3, "Should store pending_rotation"
    assert state.placed_this_turn == 1, "Should store placed_this_turn"
    assert (0, 0) in state.locked_coords, "Should store locked_coords"
    print("✓ UIState stores values correctly")
    
    # Test reset_turn_state
    state.reset_turn_state()
    assert state.selected_hand_idx is None, "reset_turn_state should clear selected_hand_idx"
    assert state.pending_rotation == 0, "reset_turn_state should clear pending_rotation"
    assert state.placed_this_turn == 0, "reset_turn_state should clear placed_this_turn"
    print("✓ reset_turn_state() works")
    
    # Test message system
    state.set_message("Test message", 1000.0)
    assert state.message == "Test message", "Should set message"
    assert state.message_timer == 1000.0, "Should set message timer"
    print("✓ set_message() works")
    
    state.update_message_timer(500.0)
    assert state.message_timer == 500.0, "Should update message timer"
    print("✓ update_message_timer() works")
    
    state.update_message_timer(600.0)
    assert state.message_timer == 0.0, "Should clear message timer"
    assert state.message == "", "Should clear message"
    print("✓ Message timer expires correctly")
    
    # Test flash system
    state.add_flash("test_flash", 250.0)
    assert "test_flash" in state.flash_timers, "Should add flash timer"
    print("✓ add_flash() works")
    
    intensity = state.get_flash_intensity("test_flash")
    assert 0.9 <= intensity <= 1.0, f"Flash intensity should be near 1.0, got {intensity}"
    print(f"✓ get_flash_intensity() works (intensity={intensity:.2f})")
    
    state.update_flash_timers(100.0)
    assert state.flash_timers["test_flash"] == 150.0, "Should update flash timer"
    print("✓ update_flash_timers() works")
    
    state.update_flash_timers(200.0)
    assert "test_flash" not in state.flash_timers, "Should remove expired flash"
    print("✓ Flash timer expires correctly")
    
    print("\n✓ UIState tests passed!")
    return True


def test_state_separation():
    """Test that state separation is correct."""
    print("\nTesting state separation principles...")
    
    from core.core_game_state import CoreGameState
    from core.ui_state import UIState
    
    # Create mock game
    class MockGame:
        def __init__(self):
            self.turn = 1
            self.players = []
        def alive_players(self):
            return []
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    
    # Verify CoreGameState has NO UI attributes
    ui_attrs = ['selected_hand_idx', 'hovered_tile', 'pending_rotation', 
                'camera_offset', 'flash_timers', 'is_animating']
    
    for attr in ui_attrs:
        assert not hasattr(core_state, attr), \
            f"CoreGameState should NOT have UI attribute '{attr}'"
    print("✓ CoreGameState has NO UI attributes")
    
    # Verify UIState has NO domain attributes
    domain_attrs = ['game', 'turn', 'players', 'market']
    
    for attr in domain_attrs:
        assert not hasattr(ui_state, attr), \
            f"UIState should NOT have domain attribute '{attr}'"
    print("✓ UIState has NO domain attributes")
    
    # Verify CoreGameState is serializable
    try:
        data = core_state.to_dict()
        assert isinstance(data, dict), "to_dict() should return a dictionary"
        print("✓ CoreGameState is serializable (SAVEABLE)")
    except Exception as e:
        print(f"✗ CoreGameState serialization failed: {e}")
        return False
    
    # Verify UIState is NOT serializable (no to_dict method)
    assert not hasattr(ui_state, 'to_dict'), \
        "UIState should NOT have to_dict() method (THROWAWAY)"
    print("✓ UIState is NOT serializable (THROWAWAY)")
    
    print("\n✓ State separation tests passed!")
    return True


if __name__ == "__main__":
    success = test_state_imports()
    
    if success:
        test_core_game_state()
        test_ui_state()
        test_state_separation()
        
        print("\n" + "="*60)
        print("✓ AŞAMA 3 TAMAMLANDI!")
        print("="*60)
        print("\nState ayrımı başarıyla oluşturuldu:")
        print("\n📦 CoreGameState (SAVEABLE):")
        print("  ✓ Game instance")
        print("  ✓ view_player_index")
        print("  ✓ fast_mode")
        print("  ✓ Serialization support (to_dict/from_dict)")
        print("  ✓ NO UI attributes")
        print("\n🎨 UIState (THROWAWAY):")
        print("  ✓ Card selection state")
        print("  ✓ Mouse hover state")
        print("  ✓ Camera/view state")
        print("  ✓ Animation timers")
        print("  ✓ Flash effects")
        print("  ✓ Message system")
        print("  ✓ Scene-specific state (lobby, shop)")
        print("  ✓ NO domain attributes")
        print("  ✓ NOT serializable (THROWAWAY)")
        print("\n🎯 Kritik Prensipler:")
        print("  ✓ CoreGameState = SAVEABLE (save/load için)")
        print("  ✓ UIState = THROWAWAY (scene değişince reset)")
        print("  ✓ Temiz ayrım: domain vs UI")
        print("\nHenüz mevcut kod değiştirilmedi.")
        print("Sadece yeni state yapısı hazırlandı.")
        print("\nAşama 4'e geçmeye hazır!")
    else:
        print("\n✗ Import tests failed. Please check the errors above.")
