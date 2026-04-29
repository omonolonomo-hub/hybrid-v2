#!/usr/bin/env python3
"""
Quick demo of serialization round-trip.
Run: python v2/core/test_serialization_demo.py
"""

import json
from engine_core.game import Game
from engine_core.player import Player
from engine_core.action_log import ActionEntry
from v2.core.serialization import to_dict, from_dict, action_to_dict, action_from_dict
from v2.core.engine_adapter import EngineAdapter
from v2.core.ui_adapter import UIAdapter
from v2.core.state_store import StateStore
from v2.core.ui_formatter import UIFormatter


def demo_public_state_serialization():
    """Demonstrate PublicState round-trip."""
    print("=" * 70)
    print("PublicState Serialization Demo")
    print("=" * 70)
    
    # Create game
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players)
    game.start_turn()
    
    # Build PublicState
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    print(f"\n✓ Created PublicState:")
    print(f"  - Phase: {original_state.phase}")
    print(f"  - Turn: {original_state.turn}")
    print(f"  - Player HP: {original_state.active_player.hp}")
    print(f"  - Player Gold: {original_state.active_player.gold}")
    print(f"  - Shop slots: {len(original_state.active_player.shop.slots)}")
    print(f"  - Hand slots: {len(original_state.active_player.hand.slots)}")
    
    # Serialize
    state_dict = to_dict(original_state)
    json_str = json.dumps(state_dict, indent=2)
    
    print(f"\n✓ Serialized to JSON ({len(json_str)} bytes)")
    
    # Deserialize
    restored_dict = json.loads(json_str)
    restored_state = from_dict(restored_dict)
    
    print(f"\n✓ Deserialized from JSON")
    
    # Verify
    if restored_state == original_state:
        print("\n✅ Round-trip successful! States are identical.")
    else:
        print("\n❌ Round-trip failed! States differ.")
        return False
    
    # Verify specific fields
    assert restored_state.phase == original_state.phase
    assert restored_state.turn == original_state.turn
    assert restored_state.active_player.hp == original_state.active_player.hp
    assert restored_state.active_player.gold == original_state.active_player.gold
    
    print("✅ All field checks passed!")
    return True


def demo_action_entry_serialization():
    """Demonstrate ActionEntry round-trip."""
    print("\n" + "=" * 70)
    print("ActionEntry Serialization Demo")
    print("=" * 70)
    
    # Create action entries
    actions = [
        ActionEntry("buy_card", {"pid": 0, "slot": 0, "card": "Warrior"}, turn=1, sub_turn=0),
        ActionEntry("place_card", {"pid": 0, "hand_idx": 0, "coord": (0, 0), "rotation": 2}, turn=1, sub_turn=1),
        ActionEntry("reroll", {"pid": 0, "cost": 2}, turn=1, sub_turn=2),
    ]
    
    print(f"\n✓ Created {len(actions)} ActionEntry records:")
    for action in actions:
        print(f"  - {action.action_type}: {action.params}")
    
    # Serialize
    serialized = [action_to_dict(action) for action in actions]
    json_str = json.dumps(serialized, indent=2)
    
    print(f"\n✓ Serialized to JSON ({len(json_str)} bytes)")
    
    # Deserialize
    restored_dicts = json.loads(json_str)
    restored_actions = [action_from_dict(d) for d in restored_dicts]
    
    print(f"\n✓ Deserialized {len(restored_actions)} actions")
    
    # Verify
    all_match = True
    for original, restored in zip(actions, restored_actions):
        if (restored.action_type != original.action_type or
            restored.params != original.params or
            restored.turn != original.turn or
            restored.sub_turn != original.sub_turn):
            all_match = False
            break
    
    if all_match:
        print("\n✅ Round-trip successful! All actions match.")
    else:
        print("\n❌ Round-trip failed! Actions differ.")
        return False
    
    # Verify coord tuple preservation
    place_action = restored_actions[1]
    if isinstance(place_action.params["coord"], tuple):
        print("✅ Coord tuple preserved correctly!")
    else:
        print("❌ Coord tuple not preserved!")
        return False
    
    return True


if __name__ == "__main__":
    print("\n🚀 Serialization Layer Demo\n")
    
    success = True
    success &= demo_public_state_serialization()
    success &= demo_action_entry_serialization()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ All demos passed! Serialization layer working correctly.")
    else:
        print("❌ Some demos failed. Check implementation.")
    print("=" * 70 + "\n")
