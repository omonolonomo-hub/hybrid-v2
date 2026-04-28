"""
Preservation test for "Ready" button flow (Bug 2: K_v Shortcut Bypass).

This test validates the baseline behavior that must be preserved when fixing
the K_v shortcut bug. It verifies that the normal "Ready" button flow:
1. Calls commit_human_turn() correctly
2. Triggers AI opponent turn execution (via finish_turn)
3. Updates pairings for combat

IMPORTANT: This test runs on UNFIXED code and should PASS, confirming the
baseline behavior to preserve.

Requirements: 3.4, 3.5, 3.6
"""
import pytest
import pygame
from unittest.mock import Mock, patch, call

from v2.core.game_state import GameState
from v2.core.shop_controller import ShopController, ShopUIAction
from v2.mock.engine_mock import MockGame


def test_ready_button_calls_commit_human_turn():
    """
    Preservation Test: Verify Ready button flow calls commit_human_turn().
    
    This test validates that when the user clicks the "Ready" button:
    - commit_human_turn() is called on GameState
    - The engine's finish_turn() is executed (AI plays turn)
    - Pairings are updated for combat
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (baseline behavior).
    """
    # Setup
    gs = GameState()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    
    # Add finish_turn method to MockGame to match real engine interface
    finish_turn_called = []
    def mock_finish_turn():
        finish_turn_called.append(True)
    mock_game.finish_turn = mock_finish_turn
    
    gs.hook_engine(mock_game)
    controller = ShopController(gs)
    
    # Get initial state
    initial_state = gs.get_public_state()
    initial_turn = initial_state.turn
    
    # Simulate "Ready" button click
    ready_action = ShopUIAction(kind="ready")
    outcome = controller.handle_shop_action(ready_action)
    
    # Verify commit_human_turn() was executed by checking finish_turn() was called
    assert len(finish_turn_called) == 1, "finish_turn() should be called once (AI turn execution)"
    
    # Verify state was updated
    assert outcome.state is not None, "Ready action should return updated state"
    assert outcome.action == ready_action, "Outcome should reference the ready action"
    
    # Verify pairings were updated (swiss_pairs() is called in commit_turn)
    pairings = gs.get_current_pairings()
    assert len(pairings) > 0, "Pairings should be updated after commit_human_turn()"


def test_ready_button_triggers_ai_opponent_turn():
    """
    Preservation Test: Verify AI opponent plays turn after Ready button.
    
    This test validates that the AI opponent's turn is executed when the
    human player clicks Ready, ensuring the game progresses correctly.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (baseline behavior).
    """
    # Setup
    gs = GameState()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    
    # Track AI turn execution by monitoring finish_turn calls
    finish_turn_count = []
    def mock_finish_turn():
        finish_turn_count.append(1)
    mock_game.finish_turn = mock_finish_turn
    
    gs.hook_engine(mock_game)
    controller = ShopController(gs)
    
    # Execute Ready action
    ready_action = ShopUIAction(kind="ready")
    controller.handle_shop_action(ready_action)
    
    # Verify finish_turn was called (this executes AI turns)
    assert sum(finish_turn_count) == 1, "AI turn should execute via finish_turn()"


def test_ready_button_updates_pairings_for_combat():
    """
    Preservation Test: Verify pairings are updated for combat phase.
    
    This test validates that commit_human_turn() updates the combat pairings
    correctly, ensuring players are matched for the combat phase.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (baseline behavior).
    """
    # Setup
    gs = GameState()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    
    # Add finish_turn method to MockGame
    def mock_finish_turn():
        pass
    mock_game.finish_turn = mock_finish_turn
    
    gs.hook_engine(mock_game)
    controller = ShopController(gs)
    
    # Get initial pairings (should be empty or default)
    initial_pairings = gs.get_current_pairings()
    
    # Execute Ready action
    ready_action = ShopUIAction(kind="ready")
    controller.handle_shop_action(ready_action)
    
    # Verify pairings were updated
    updated_pairings = gs.get_current_pairings()
    assert updated_pairings is not None, "Pairings should be set after Ready"
    
    # MockGame.swiss_pairs() returns player pairs
    assert len(updated_pairings) > 0, "Pairings should contain at least one match"
    assert isinstance(updated_pairings[0], tuple), "Each pairing should be a tuple"
    assert len(updated_pairings[0]) == 2, "Each pairing should have 2 players"


def test_ready_button_preserves_shop_scene_state():
    """
    Preservation Test: Verify Ready button doesn't corrupt ShopScene state.
    
    This test validates that the Ready button flow maintains consistent
    game state, including market state, player state, and board state.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (baseline behavior).
    """
    # Setup
    gs = GameState()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    gs.hook_engine(mock_game)
    
    controller = ShopController(gs)
    
    # Capture initial state
    initial_state = gs.get_public_state()
    initial_gold = initial_state.active_player.gold
    initial_hp = initial_state.active_player.hp
    
    # Execute Ready action
    ready_action = ShopUIAction(kind="ready")
    outcome = controller.handle_shop_action(ready_action)
    
    # Verify state consistency
    final_state = outcome.state
    assert final_state is not None, "State should be returned"
    assert final_state.active_player.hp == initial_hp, "HP should not change from Ready button"
    
    # Gold might change due to interest/income, but should be valid
    assert final_state.active_player.gold >= 0, "Gold should remain non-negative"
    
    # Verify no crash or exception occurred
    assert outcome.result is None or outcome.result.name == "OK", "Ready action should succeed"


def test_ready_button_integration_with_shop_controller():
    """
    Integration Test: Verify full Ready button flow through ShopController.
    
    This test validates the complete integration between ShopController and
    GameState when processing the Ready action, ensuring all components
    work together correctly.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (baseline behavior).
    """
    # Setup
    gs = GameState()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    gs.hook_engine(mock_game)
    
    controller = ShopController(gs)
    
    # Track method calls
    commit_called = []
    original_commit = gs.commit_human_turn
    
    def spy_commit():
        commit_called.append(True)
        return original_commit()
    
    gs.commit_human_turn = spy_commit
    
    # Execute Ready action through controller
    ready_action = ShopUIAction(kind="ready")
    outcome = controller.handle_shop_action(ready_action)
    
    # Verify commit_human_turn was called
    assert len(commit_called) == 1, "commit_human_turn() should be called exactly once"
    
    # Verify outcome structure
    assert outcome.state is not None, "Outcome should contain updated state"
    assert outcome.action == ready_action, "Outcome should reference the action"
    assert outcome.result is None, "Ready action doesn't return a result code"
    
    # Verify state is valid
    state = outcome.state
    assert state.active_player is not None, "Active player should exist"
    assert state.turn >= 0, "Turn number should be valid"
