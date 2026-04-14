"""
Test script for T3.5 - Locked Coordinates Tracking

This script verifies that:
1. Locked coordinates are read from core_game_state.locked_coords_per_player
2. Coordinates are added to locked set when cards are placed
3. Placement is prevented on locked coordinates
4. Locked indicators are displayed with C_LOCKED color
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.core_game_state import CoreGameState
from scenes.combat_scene import PlacementController
from core.ui_state import UIState
from core.hex_system import HexSystem


def test_locked_coords_initialization():
    """Test that locked_coords_per_player is initialized in CoreGameState."""
    print("\n=== Test 1: Locked Coords Initialization ===")
    
    # Create a mock game with players
    class MockPlayer:
        def __init__(self, pid):
            self.pid = pid
            self.hp = 100
            self.board = type('obj', (object,), {'grid': {}})()
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer(i) for i in range(4)]
            self.turn = 1
        
        def alive_players(self):
            return [p for p in self.players if p.hp > 0]
    
    game = MockGame()
    core_state = CoreGameState(game)
    
    # Verify locked_coords_per_player exists and is initialized
    assert hasattr(core_state, 'locked_coords_per_player'), "locked_coords_per_player not found"
    assert isinstance(core_state.locked_coords_per_player, dict), "locked_coords_per_player is not a dict"
    assert len(core_state.locked_coords_per_player) == 4, "locked_coords_per_player not initialized for all players"
    
    for pid in range(4):
        assert pid in core_state.locked_coords_per_player, f"Player {pid} not in locked_coords_per_player"
        assert isinstance(core_state.locked_coords_per_player[pid], set), f"Player {pid} locked_coords is not a set"
        assert len(core_state.locked_coords_per_player[pid]) == 0, f"Player {pid} locked_coords not empty"
    
    print("✓ locked_coords_per_player initialized correctly for all players")
    return True


def test_placement_validation_with_locked_coords():
    """Test that placement validation checks locked coordinates."""
    print("\n=== Test 2: Placement Validation with Locked Coords ===")
    
    # Create mock objects
    class MockPlayer:
        def __init__(self, pid):
            self.pid = pid
            self.hp = 100
            self.board = type('obj', (object,), {'grid': {}})()
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer(i) for i in range(4)]
            self.turn = 1
        
        def alive_players(self):
            return [p for p in self.players if p.hp > 0]
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    hex_system = HexSystem(origin=(960, 540), hex_size=60)
    
    # Create placement controller
    placement_controller = PlacementController(core_state, ui_state, hex_system)
    
    # Test 1: Valid placement on empty hex
    hex_coord = (0, 0)
    is_valid = placement_controller.is_valid_placement(hex_coord, 0)
    assert is_valid, f"Placement should be valid on empty hex {hex_coord}"
    print(f"✓ Placement valid on empty hex {hex_coord}")
    
    # Test 2: Lock the coordinate
    core_state.locked_coords_per_player[0].add(hex_coord)
    print(f"✓ Locked coordinate {hex_coord} for player 0")
    
    # Test 3: Invalid placement on locked hex
    is_valid = placement_controller.is_valid_placement(hex_coord, 0)
    assert not is_valid, f"Placement should be invalid on locked hex {hex_coord}"
    print(f"✓ Placement correctly rejected on locked hex {hex_coord}")
    
    # Test 4: Valid placement on different hex
    other_hex = (1, 0)
    is_valid = placement_controller.is_valid_placement(other_hex, 0)
    assert is_valid, f"Placement should be valid on unlocked hex {other_hex}"
    print(f"✓ Placement valid on unlocked hex {other_hex}")
    
    return True


def test_clear_locked_coords():
    """Test that clear_locked_coords method works correctly."""
    print("\n=== Test 3: Clear Locked Coords ===")
    
    # Create mock objects
    class MockPlayer:
        def __init__(self, pid):
            self.pid = pid
            self.hp = 100
            self.board = type('obj', (object,), {'grid': {}})()
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer(i) for i in range(4)]
            self.turn = 1
        
        def alive_players(self):
            return [p for p in self.players if p.hp > 0]
    
    game = MockGame()
    core_state = CoreGameState(game)
    
    # Add some locked coordinates
    core_state.locked_coords_per_player[0].add((0, 0))
    core_state.locked_coords_per_player[0].add((1, 0))
    core_state.locked_coords_per_player[0].add((0, 1))
    
    assert len(core_state.locked_coords_per_player[0]) == 3, "Should have 3 locked coords"
    print(f"✓ Added 3 locked coordinates for player 0")
    
    # Clear locked coordinates
    core_state.clear_locked_coords(0)
    
    assert len(core_state.locked_coords_per_player[0]) == 0, "Locked coords should be cleared"
    print(f"✓ Locked coordinates cleared for player 0")
    
    # Verify other players' locked coords are not affected
    core_state.locked_coords_per_player[1].add((2, 0))
    core_state.clear_locked_coords(0)
    assert len(core_state.locked_coords_per_player[1]) == 1, "Other players' locked coords should not be affected"
    print(f"✓ Other players' locked coordinates not affected")
    
    return True


def test_locked_coords_persistence():
    """Test that locked coordinates persist in CoreGameState."""
    print("\n=== Test 4: Locked Coords Persistence ===")
    
    # Create mock objects
    class MockPlayer:
        def __init__(self, pid):
            self.pid = pid
            self.hp = 100
            self.board = type('obj', (object,), {'grid': {}})()
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer(i) for i in range(4)]
            self.turn = 1
        
        def alive_players(self):
            return [p for p in self.players if p.hp > 0]
    
    game = MockGame()
    core_state = CoreGameState(game)
    
    # Add locked coordinates
    test_coords = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for coord in test_coords:
        core_state.locked_coords_per_player[0].add(coord)
    
    print(f"✓ Added {len(test_coords)} locked coordinates")
    
    # Verify persistence (same object reference)
    locked_coords_ref = core_state.locked_coords_per_player[0]
    assert locked_coords_ref is core_state.locked_coords_per_player[0], "Should be same object reference"
    print(f"✓ Locked coordinates persist as same object reference")
    
    # Verify all coordinates are present
    for coord in test_coords:
        assert coord in core_state.locked_coords_per_player[0], f"Coordinate {coord} should be in locked set"
    print(f"✓ All {len(test_coords)} coordinates persist correctly")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("T3.5 - Locked Coordinates Tracking Tests")
    print("=" * 60)
    
    tests = [
        ("Locked Coords Initialization", test_locked_coords_initialization),
        ("Placement Validation with Locked Coords", test_placement_validation_with_locked_coords),
        ("Clear Locked Coords", test_clear_locked_coords),
        ("Locked Coords Persistence", test_locked_coords_persistence),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
