"""
Validation script for T1.1: CoreGameState locked_coords_per_player
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool
from engine_core.player import Player
from engine_core.game import Game
from engine_core.constants import STRATEGIES
from core.core_game_state import CoreGameState

def test_locked_coords_initialization():
    """Test that locked_coords_per_player is initialized correctly."""
    print("=" * 60)
    print("T1.1 VALIDATION: CoreGameState locked_coords_per_player")
    print("=" * 60)
    
    # Create a minimal game instance
    import random
    rng = random.Random()
    pool = get_card_pool()
    
    # Create 4 players for testing
    strategies = STRATEGIES[:4]
    players = [
        Player(pid=i, strategy=strategies[i])
        for i in range(4)
    ]
    
    # Create game instance
    game = Game(players=players, card_pool=pool, rng=rng)
    
    print(f"\n1. Created game with {len(game.players)} players")
    print(f"   Player IDs: {[p.pid for p in game.players]}")
    
    # Create CoreGameState
    core_state = CoreGameState(game)
    
    print(f"\n2. Created CoreGameState")
    print(f"   locked_coords_per_player type: {type(core_state.locked_coords_per_player)}")
    print(f"   locked_coords_per_player keys: {list(core_state.locked_coords_per_player.keys())}")
    
    # Verify initialization
    assert hasattr(core_state, 'locked_coords_per_player'), "locked_coords_per_player field missing!"
    assert isinstance(core_state.locked_coords_per_player, dict), "locked_coords_per_player should be a dict!"
    
    print(f"\n3. Verifying initialization for each player:")
    for player in game.players:
        pid = player.pid
        assert pid in core_state.locked_coords_per_player, f"Player {pid} not in locked_coords_per_player!"
        assert isinstance(core_state.locked_coords_per_player[pid], set), f"Player {pid} locked_coords should be a set!"
        assert len(core_state.locked_coords_per_player[pid]) == 0, f"Player {pid} locked_coords should be empty initially!"
        print(f"   ✓ Player {pid}: {core_state.locked_coords_per_player[pid]} (empty set)")
    
    # Test adding coordinates
    print(f"\n4. Testing coordinate locking:")
    test_coord = (0, 0)
    core_state.locked_coords_per_player[0].add(test_coord)
    print(f"   Added {test_coord} to player 0")
    print(f"   Player 0 locked_coords: {core_state.locked_coords_per_player[0]}")
    assert test_coord in core_state.locked_coords_per_player[0], "Coordinate not added!"
    
    # Test clear_locked_coords method
    print(f"\n5. Testing clear_locked_coords method:")
    core_state.clear_locked_coords(0)
    print(f"   Called clear_locked_coords(0)")
    print(f"   Player 0 locked_coords: {core_state.locked_coords_per_player[0]}")
    assert len(core_state.locked_coords_per_player[0]) == 0, "clear_locked_coords didn't clear!"
    print(f"   ✓ Cleared successfully")
    
    # Test clearing non-existent player (should not crash)
    print(f"\n6. Testing clear_locked_coords with invalid player ID:")
    core_state.clear_locked_coords(999)  # Non-existent player
    print(f"   Called clear_locked_coords(999) - should not crash")
    print(f"   ✓ Handled gracefully")
    
    # Test serialization
    print(f"\n7. Testing serialization (to_dict):")
    state_dict = core_state.to_dict()
    print(f"   Serialized keys: {list(state_dict.keys())}")
    assert 'locked_coords_per_player' in state_dict, "locked_coords_per_player not in serialization!"
    print(f"   locked_coords_per_player in dict: {state_dict['locked_coords_per_player']}")
    print(f"   ✓ Serialization works")
    
    # Test deserialization
    print(f"\n8. Testing deserialization (from_dict):")
    # Add some test data
    core_state.locked_coords_per_player[1].add((1, 1))
    core_state.locked_coords_per_player[2].add((2, 2))
    
    # Serialize
    state_dict = core_state.to_dict()
    
    # Deserialize
    restored_state = CoreGameState.from_dict(state_dict, game)
    print(f"   Restored locked_coords_per_player: {restored_state.locked_coords_per_player}")
    
    # Verify
    assert (1, 1) in restored_state.locked_coords_per_player[1], "Deserialization failed for player 1!"
    assert (2, 2) in restored_state.locked_coords_per_player[2], "Deserialization failed for player 2!"
    print(f"   ✓ Deserialization works")
    
    print(f"\n" + "=" * 60)
    print("✅ T1.1 VALIDATION PASSED - All checks successful!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        test_locked_coords_initialization()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
