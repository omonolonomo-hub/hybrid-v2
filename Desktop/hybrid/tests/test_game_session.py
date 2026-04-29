"""Tests for GameSession ready state management.

Verifies that:
1. GameSession correctly tracks player readiness
2. mark_ready() returns True only when all alive players are ready
3. Ready set is cleared after all players are ready
4. Dead players are excluded from ready checks
"""

import pytest
from engine_core.game import Game
from engine_core.player import Player
from engine_core.game_session import GameSession
from v2.core.engine_adapter import EngineAdapter
from v2.core.local_dispatcher import LocalCommandDispatcher


def test_game_session_initialization():
    """Verify GameSession initializes with correct state."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    assert session.game is game
    assert len(session.players) == 2
    assert 0 in session.players
    assert 1 in session.players
    assert len(session.get_ready_players()) == 0


def test_game_session_with_dispatcher():
    """Verify GameSession can be initialized with a dispatcher."""
    game = Game(players=[Player(pid=0)])
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    
    session = GameSession(game, dispatcher)
    
    assert session.dispatcher is dispatcher


def test_mark_ready_single_player_returns_true():
    """Single-player game should return True immediately."""
    game = Game(players=[Player(pid=0)])
    session = GameSession(game)
    
    # Single player marks ready - should return True
    result = session.mark_ready(0)
    
    assert result is True
    assert len(session.get_ready_players()) == 0  # Cleared after all ready


def test_mark_ready_two_players_waits_for_both():
    """Two-player game should wait for both players."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # First player marks ready
    result1 = session.mark_ready(0)
    assert result1 is False
    assert session.is_player_ready(0) is True
    assert session.is_player_ready(1) is False
    
    # Second player marks ready
    result2 = session.mark_ready(1)
    assert result2 is True
    assert len(session.get_ready_players()) == 0  # Cleared


def test_mark_ready_three_players_progression():
    """Three-player game should wait for all three."""
    game = Game(players=[
        Player(pid=0),
        Player(pid=1),
        Player(pid=2)
    ])
    session = GameSession(game)
    
    # First player
    assert session.mark_ready(0) is False
    assert len(session.get_ready_players()) == 1
    
    # Second player
    assert session.mark_ready(1) is False
    assert len(session.get_ready_players()) == 2
    
    # Third player - all ready
    assert session.mark_ready(2) is True
    assert len(session.get_ready_players()) == 0


def test_mark_ready_excludes_dead_players():
    """Dead players should not block turn progression."""
    p0 = Player(pid=0)
    p1 = Player(pid=1)
    p2 = Player(pid=2)
    
    # Kill player 2
    p2.alive = False
    
    game = Game(players=[p0, p1, p2])
    session = GameSession(game)
    
    # Only need players 0 and 1 to be ready
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True  # All alive players ready
    
    # Ready set cleared
    assert len(session.get_ready_players()) == 0


def test_mark_ready_invalid_pid_raises_error():
    """Marking ready with invalid pid should raise KeyError."""
    game = Game(players=[Player(pid=0)])
    session = GameSession(game)
    
    with pytest.raises(KeyError, match="Player 99 not found"):
        session.mark_ready(99)


def test_mark_ready_same_player_twice_is_idempotent():
    """Marking ready twice should not cause issues."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Player 0 marks ready twice
    assert session.mark_ready(0) is False
    assert session.mark_ready(0) is False  # Still waiting for player 1
    
    # Player 1 marks ready
    assert session.mark_ready(1) is True


def test_reset_ready_state_clears_all_markers():
    """reset_ready_state() should clear all ready markers."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    session.mark_ready(0)
    assert len(session.get_ready_players()) == 1
    
    session.reset_ready_state()
    assert len(session.get_ready_players()) == 0
    assert session.is_player_ready(0) is False


def test_get_waiting_players_returns_not_ready():
    """get_waiting_players() should return alive players not yet ready."""
    game = Game(players=[
        Player(pid=0),
        Player(pid=1),
        Player(pid=2)
    ])
    session = GameSession(game)
    
    # Initially all waiting
    waiting = session.get_waiting_players()
    assert waiting == {0, 1, 2}
    
    # Player 0 marks ready
    session.mark_ready(0)
    waiting = session.get_waiting_players()
    assert waiting == {1, 2}
    
    # Player 1 marks ready
    session.mark_ready(1)
    waiting = session.get_waiting_players()
    assert waiting == {2}
    
    # Player 2 marks ready - all ready, set cleared
    session.mark_ready(2)
    waiting = session.get_waiting_players()
    assert waiting == {0, 1, 2}  # Reset for next turn


def test_get_alive_count_excludes_dead_players():
    """get_alive_count() should only count alive players."""
    p0 = Player(pid=0)
    p1 = Player(pid=1)
    p2 = Player(pid=2)
    
    game = Game(players=[p0, p1, p2])
    session = GameSession(game)
    
    assert session.get_alive_count() == 3
    
    # Kill one player
    p1.alive = False
    assert session.get_alive_count() == 2
    
    # Kill another
    p2.alive = False
    assert session.get_alive_count() == 1


def test_multiple_turn_cycles():
    """Verify ready state works correctly across multiple turns."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Turn 1
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True
    
    # Turn 2 - ready set was cleared
    assert session.mark_ready(0) is False
    assert session.mark_ready(1) is True
    
    # Turn 3
    assert session.mark_ready(1) is False
    assert session.mark_ready(0) is True  # Order doesn't matter


def test_player_elimination_during_turn():
    """If a player dies after marking ready, turn should still progress."""
    p0 = Player(pid=0)
    p1 = Player(pid=1)
    p2 = Player(pid=2)
    
    game = Game(players=[p0, p1, p2])
    session = GameSession(game)
    
    # All players mark ready
    session.mark_ready(0)
    session.mark_ready(1)
    
    # Player 2 dies before marking ready
    p2.alive = False
    
    # Check if turn can progress (only alive players needed)
    # Since p2 is dead, we already have all alive players ready
    alive_pids = {p.pid for p in game.players if p.alive}
    ready_pids = session.get_ready_players()
    
    # We have p0 and p1 ready, p2 is dead
    assert ready_pids == {0, 1}
    assert alive_pids == {0, 1}
    assert ready_pids >= alive_pids  # All alive players are ready


def test_session_player_mapping_matches_game():
    """Verify player mapping is correctly built from game."""
    p0 = Player(pid=0)
    p1 = Player(pid=1)
    p2 = Player(pid=2)
    
    game = Game(players=[p0, p1, p2])
    session = GameSession(game)
    
    assert session.players[0] is p0
    assert session.players[1] is p1
    assert session.players[2] is p2
