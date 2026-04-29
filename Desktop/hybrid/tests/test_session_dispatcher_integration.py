"""Integration tests for GameSession + CommandDispatcher workflow.

Verifies that:
1. GameSession can manage game with LocalCommandDispatcher
2. Commands can be executed through dispatcher while tracking ready state
3. Full turn workflow: commands → ready → turn progression
"""

import pytest
from engine_core.game_factory import build_game
from engine_core.game_session import GameSession
from v2.core.engine_adapter import EngineAdapter
from v2.core.local_dispatcher import LocalCommandDispatcher
from v2.core.action_result import ActionResult


def test_session_with_dispatcher_buy_and_ready():
    """Test buying cards through dispatcher and marking ready."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    # Start turn
    game.start_turn()
    
    # Player 0 buys a card through dispatcher
    result = dispatcher.perform_buy_card(0, 0)
    assert result == ActionResult.OK
    
    # Player 0 marks ready
    assert session.mark_ready(0) is False  # Waiting for player 1
    
    # Player 1 marks ready
    assert session.mark_ready(1) is True  # All ready!


def test_full_turn_workflow_with_session():
    """Full turn workflow: buy → place → ready → combat."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    # Start turn
    game.start_turn()
    
    # Player 0 actions
    dispatcher.perform_buy_card(0, 0)
    dispatcher.perform_placement(0, 0, (0, 0), 0)
    session.mark_ready(0)
    
    # Player 1 actions (AI would do this)
    session.mark_ready(1)
    
    # Check ready state was cleared
    assert len(session.get_ready_players()) == 0


def test_session_tracks_multiple_turns():
    """Verify session correctly tracks ready state across multiple turns."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # Turn 1
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True
    
    # Turn 2 - ready state was cleared
    assert len(session.get_ready_players()) == 0
    assert session.mark_ready(1) is False
    assert session.mark_ready(0) is True
    
    # Turn 3
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True


def test_session_dispatcher_with_three_players():
    """Test session with three players and dispatcher."""
    game = build_game(strategies=["random", "random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # All players buy cards
    for pid in range(3):
        result = dispatcher.perform_buy_card(pid, 0)
        # Player 0 should succeed, others might fail (not owner)
        if pid == 0:
            assert result == ActionResult.OK
    
    # All players mark ready
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is False
    assert session.mark_ready(2) is True  # All ready!


def test_session_handles_player_elimination():
    """Test that session correctly handles player elimination."""
    game = build_game(strategies=["random", "random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # Kill player 2
    game.players[2].alive = False
    
    # Only need players 0 and 1 to be ready
    assert session.get_alive_count() == 2
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True  # All alive players ready


def test_session_reroll_and_ready():
    """Test reroll through dispatcher and ready tracking."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # Give player gold
    game.players[0].gold = 10
    
    # Reroll through dispatcher
    result = dispatcher.perform_reroll(0)
    assert result is True
    
    # Mark ready
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True


def test_session_waiting_players_during_workflow():
    """Test get_waiting_players() during a turn workflow."""
    game = build_game(strategies=["random", "random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # Initially all waiting
    waiting = session.get_waiting_players()
    assert waiting == {0, 1, 2}
    
    # Player 0 does actions and marks ready
    dispatcher.perform_buy_card(0, 0)
    session.mark_ready(0)
    
    waiting = session.get_waiting_players()
    assert waiting == {1, 2}
    
    # Player 1 marks ready
    session.mark_ready(1)
    
    waiting = session.get_waiting_players()
    assert waiting == {2}
    
    # Player 2 marks ready - all ready
    session.mark_ready(2)
    
    # Ready state cleared, back to all waiting
    waiting = session.get_waiting_players()
    assert waiting == {0, 1, 2}


def test_session_reset_during_workflow():
    """Test manual reset of ready state during workflow."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    game.start_turn()
    
    # Player 0 marks ready
    session.mark_ready(0)
    assert session.is_player_ready(0) is True
    
    # Manual reset (e.g., player disconnected)
    session.reset_ready_state()
    assert session.is_player_ready(0) is False
    
    # Start over
    session.mark_ready(0)
    session.mark_ready(1)
    assert len(session.get_ready_players()) == 0  # Cleared after all ready


def test_session_properties_accessible():
    """Test that session properties are accessible."""
    game = build_game(strategies=["random", "random"])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    
    # Access properties
    assert session.game is game
    assert session.dispatcher is dispatcher
    assert len(session.players) == 2
    assert 0 in session.players
    assert 1 in session.players
