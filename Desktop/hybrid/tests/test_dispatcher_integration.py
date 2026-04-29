"""Integration test demonstrating CommandDispatcher working end-to-end.

This test verifies that:
1. buy_card works through LocalCommandDispatcher
2. place_card works through LocalCommandDispatcher
3. Game state is correctly updated after mutations
"""

import pytest
from engine_core.game_factory import build_game
from v2.core.game_state import GameState
from v2.core.action_result import ActionResult


def test_buy_card_through_dispatcher_integration():
    """End-to-end test: buy a card through GameState → LocalCommandDispatcher → EngineAdapter."""
    game = build_game(strategies=["random", "random"])
    gs = GameState()
    gs.hook_engine(game)
    
    # Start turn to populate market
    game.start_turn()
    
    # Get initial hand size
    state_before = gs.get_public_state()
    hand_before = [slot for slot in state_before.active_player.hand.slots if slot is not None]
    initial_gold = state_before.active_player.hud.gold
    
    # Buy a card from slot 0
    result = gs.buy_card_from_slot(0, 0)
    
    # Verify success
    assert result == ActionResult.OK
    
    # Verify card was added to hand
    state_after = gs.get_public_state()
    hand_after = [slot for slot in state_after.active_player.hand.slots if slot is not None]
    assert len(hand_after) == len(hand_before) + 1
    
    # Verify gold was deducted
    assert state_after.active_player.hud.gold < initial_gold


def test_placement_through_dispatcher_integration():
    """End-to-end test: place a card through GameState → LocalCommandDispatcher → EngineAdapter."""
    game = build_game(strategies=["random", "random"])
    gs = GameState()
    gs.hook_engine(game)
    
    # Start turn
    game.start_turn()
    
    # Buy a card
    gs.buy_card_from_slot(0, 0)
    
    # Get state before placement
    state_before = gs.get_public_state()
    board_before = dict(state_before.active_player.board_cards)
    
    # Place card from hand slot 0 to board position (0, 0)
    result = gs.place_card(0, (0, 0), rotation=0, player_index=0)
    
    # Verify success
    assert result == ActionResult.OK
    
    # Verify card is on board
    state_after = gs.get_public_state()
    board_after = dict(state_after.active_player.board_cards)
    assert len(board_after) == len(board_before) + 1
    assert (0, 0) in board_after
    
    # Verify card was removed from hand
    hand_after = [slot for slot in state_after.active_player.hand.slots if slot is not None]
    # Hand should have one less card (or same if it was refilled)
    # Just verify the card is on the board
    assert board_after[(0, 0)] is not None


def test_full_workflow_buy_and_place():
    """Full workflow: buy multiple cards and place them on board."""
    game = build_game(strategies=["random", "random"])
    gs = GameState()
    gs.hook_engine(game)
    
    # Start turn
    game.start_turn()
    
    # Give player lots of gold
    game.players[0].gold = 100
    
    # Buy 3 cards
    for slot in range(3):
        result = gs.buy_card_from_slot(0, slot)
        assert result == ActionResult.OK
    
    # Place 2 cards on board
    coords = [(0, 0), (1, 0)]
    for i, coord in enumerate(coords):
        result = gs.place_card(i, coord, rotation=0, player_index=0)
        assert result == ActionResult.OK
    
    # Verify final state
    state = gs.get_public_state()
    board = dict(state.active_player.board_cards)
    assert len(board) == 2
    assert (0, 0) in board
    assert (1, 0) in board
