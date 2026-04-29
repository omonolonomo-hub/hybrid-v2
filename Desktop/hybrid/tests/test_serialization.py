"""
tests/test_serialization.py
═══════════════════════════════════════════════════════════════════
Test suite for v2/core/serialization.py

Verifies lossless round-trip serialization:
- PublicState → dict → PublicState
- ActionEntry → dict → ActionEntry

Uses real Game instance to ensure realistic data structures.
═══════════════════════════════════════════════════════════════════
"""

import json
import pytest

from engine_core.game import Game
from engine_core.player import Player
from engine_core.action_log import ActionEntry
from v2.core.serialization import (
    to_dict,
    from_dict,
    action_to_dict,
    action_from_dict,
)
from v2.core.engine_adapter import EngineAdapter
from v2.core.ui_adapter import UIAdapter
from v2.core.state_store import StateStore
from v2.core.ui_formatter import UIFormatter


@pytest.fixture
def game_with_actions():
    """Create a real game and play one turn to generate realistic state."""
    players = [Player(pid=i) for i in range(4)]
    game = Game(players=players)
    game.start_turn()
    
    # Player 0: buy a card, place it
    player = game.players[0]
    market = game.market
    
    # Buy first available card
    window = market.get_window(player.pid)
    if window and window[0] is not None:
        card = window[0]
        player.buy_card(
            card,
            market=market,
            uid=game.next_card_uid(),
            trigger_passive_fn=game.trigger_passive_fn,
            game_ref=game,
        )
        market.clear_slot(player.pid, 0)
        
        # Place card on board
        if player.hand and player.hand[0] is not None:
            coord = (0, 0)
            placed_card = player.hand[0]
            placed_card.rotation = 2
            player.inventory.clear_slot(0)
            player.board.place(coord, placed_card)
    
    # Reroll market
    if player.economy.spend_gold(2):
        market.deal_market_window(player, 5)
    
    return game


def test_public_state_round_trip(game_with_actions):
    """Test PublicState serialization round-trip with real game data."""
    game = game_with_actions
    
    # Build PublicState using real adapters
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize to dict
    state_dict = to_dict(original_state)
    
    # Verify it's JSON-serializable
    json_str = json.dumps(state_dict)
    assert len(json_str) > 0
    
    # Deserialize back
    restored_dict = json.loads(json_str)
    restored_state = from_dict(restored_dict)
    
    # Verify equality
    assert restored_state == original_state
    
    # Verify specific fields
    assert restored_state.phase == original_state.phase
    assert restored_state.turn == original_state.turn
    assert restored_state.view_index == original_state.view_index
    assert restored_state.active_player.hp == original_state.active_player.hp
    assert restored_state.active_player.gold == original_state.active_player.gold
    
    # Verify tuple coords are preserved
    assert isinstance(restored_state.active_player.eliminated_coords, tuple)
    if restored_state.active_player.eliminated_coords:
        assert isinstance(restored_state.active_player.eliminated_coords[0], tuple)
    
    # Verify board_cards coord keys are tuples
    for coord in restored_state.active_player.board_cards.keys():
        assert isinstance(coord, tuple)
        assert len(coord) == 2
        assert isinstance(coord[0], int)
        assert isinstance(coord[1], int)


def test_action_entry_round_trip():
    """Test ActionEntry serialization round-trip."""
    # Create a sample action entry
    original_entry = ActionEntry(
        action_type="buy_card",
        params={"pid": 0, "slot": 2, "card": "Warrior"},
        turn=5,
        sub_turn=3,
    )
    
    # Serialize to dict
    entry_dict = action_to_dict(original_entry)
    
    # Verify it's JSON-serializable
    json_str = json.dumps(entry_dict)
    assert len(json_str) > 0
    
    # Deserialize back
    restored_dict = json.loads(json_str)
    restored_entry = action_from_dict(restored_dict)
    
    # Verify equality
    assert restored_entry.action_type == original_entry.action_type
    assert restored_entry.params == original_entry.params
    assert restored_entry.turn == original_entry.turn
    assert restored_entry.sub_turn == original_entry.sub_turn


def test_coord_serialization(game_with_actions):
    """Test that tuple coords are correctly serialized and deserialized."""
    game = game_with_actions
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize
    state_dict = to_dict(original_state)
    
    # Check that board_cards keys are strings in dict
    board_cards = state_dict["active_player"]["board_cards"]
    for key in board_cards.keys():
        assert isinstance(key, str)
        assert "," in key
    
    # Deserialize
    restored_state = from_dict(state_dict)
    
    # Check that board_cards keys are tuples in restored state
    for coord in restored_state.active_player.board_cards.keys():
        assert isinstance(coord, tuple)
        assert len(coord) == 2


def test_nested_tuples_preserved(game_with_actions):
    """Test that nested tuples (adjacency_pairs, pairings) are preserved."""
    game = game_with_actions
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize and deserialize
    state_dict = to_dict(original_state)
    restored_state = from_dict(state_dict)
    
    # Verify pairings are tuples of tuples
    assert isinstance(restored_state.pairings, tuple)
    for pair in restored_state.pairings:
        assert isinstance(pair, tuple)
        assert len(pair) == 2
    
    # Verify adjacency_pairs structure
    assert isinstance(restored_state.active_player.adjacency_pairs, tuple)


def test_shop_slots_preserved(game_with_actions):
    """Test that shop slots (with None values) are preserved."""
    game = game_with_actions
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize and deserialize
    state_dict = to_dict(original_state)
    restored_state = from_dict(state_dict)
    
    # Verify shop slots are tuples
    assert isinstance(restored_state.active_player.shop.slots, tuple)
    assert len(restored_state.active_player.shop.slots) == 5
    
    # Verify hand slots are tuples
    assert isinstance(restored_state.active_player.hand.slots, tuple)
    assert len(restored_state.active_player.hand.slots) == 6


def test_synergy_groups_preserved(game_with_actions):
    """Test that synergy groups with color tuples are preserved."""
    game = game_with_actions
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize and deserialize
    state_dict = to_dict(original_state)
    restored_state = from_dict(state_dict)
    
    # Verify synergy groups
    assert isinstance(restored_state.active_player.synergy.groups, tuple)
    for group in restored_state.active_player.synergy.groups:
        assert isinstance(group.color, tuple)
        assert len(group.color) == 3


def test_empty_board_serialization():
    """Test serialization with empty board (no cards placed)."""
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players)
    game.start_turn()
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize and deserialize
    state_dict = to_dict(original_state)
    json_str = json.dumps(state_dict)
    restored_dict = json.loads(json_str)
    restored_state = from_dict(restored_dict)
    
    # Verify equality
    assert restored_state == original_state
    assert len(restored_state.active_player.board_cards) == 0


def test_multiple_actions_serialization(game_with_actions):
    """Test serialization of multiple action entries."""
    game = game_with_actions
    
    # Create multiple action entries
    actions = [
        ActionEntry("buy_card", {"pid": 0, "slot": 0, "card": "Warrior"}, turn=1, sub_turn=0),
        ActionEntry("place_card", {"pid": 0, "hand_idx": 0, "coord": (0, 0), "rotation": 2}, turn=1, sub_turn=1),
        ActionEntry("reroll", {"pid": 0, "cost": 2}, turn=1, sub_turn=2),
    ]
    
    # Serialize all
    serialized = [action_to_dict(action) for action in actions]
    
    # JSON round-trip
    json_str = json.dumps(serialized)
    restored_dicts = json.loads(json_str)
    
    # Deserialize all
    restored_actions = [action_from_dict(d) for d in restored_dicts]
    
    # Verify
    assert len(restored_actions) == len(actions)
    for original, restored in zip(actions, restored_actions):
        assert restored.action_type == original.action_type
        assert restored.params == original.params
        assert restored.turn == original.turn
        assert restored.sub_turn == original.sub_turn


def test_card_info_serialization(game_with_actions):
    """Test that card_info dicts are properly serialized."""
    game = game_with_actions
    
    adapter = EngineAdapter(game)
    store = StateStore()
    formatter = UIFormatter()
    ui_adapter = UIAdapter()
    
    original_state = ui_adapter.build_public_state(adapter, store, formatter)
    
    # Serialize and deserialize
    state_dict = to_dict(original_state)
    json_str = json.dumps(state_dict)
    restored_dict = json.loads(json_str)
    restored_state = from_dict(restored_dict)
    
    # Verify card_info fields exist and are dict-like (MappingProxyType is acceptable)
    from types import MappingProxyType
    assert isinstance(restored_state.active_player.shop_card_info, (dict, MappingProxyType))
    assert isinstance(restored_state.active_player.hand_card_info, (dict, MappingProxyType))
    assert isinstance(restored_state.active_player.board_card_info, (dict, MappingProxyType))
    
    # Verify board_card_info keys are tuples
    for coord in restored_state.active_player.board_card_info.keys():
        assert isinstance(coord, tuple)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
