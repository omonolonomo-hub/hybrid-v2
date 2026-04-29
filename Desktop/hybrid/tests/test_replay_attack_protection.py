"""Test suite for replay attack protection via sequence numbers.

Verifies that:
1. Duplicate sequence numbers are rejected
2. Out-of-order sequence numbers are rejected
3. Valid increasing sequence numbers are accepted
4. Sequence numbers are tracked per player independently
"""

import pytest
from engine_core.game import Game
from engine_core.player import Player
from engine_core.game_session import GameSession


def test_replay_attack_same_seq_rejected():
    """Sending the same sequence number twice should be rejected."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # First call with seq=1 should succeed
    result1 = session.mark_ready(0, seq_no=1)
    assert result1 is False  # Waiting for player 1
    assert session.get_last_seq(0) == 1
    
    # Second call with same seq=1 should raise ValueError
    with pytest.raises(ValueError, match="Replay attack detected"):
        session.mark_ready(0, seq_no=1)
    
    # Last seq should still be 1 (rejected call didn't update it)
    assert session.get_last_seq(0) == 1


def test_replay_attack_lower_seq_rejected():
    """Sending a lower sequence number should be rejected."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Send seq=5
    session.mark_ready(0, seq_no=5)
    assert session.get_last_seq(0) == 5
    
    # Try to send seq=3 (lower) - should be rejected
    with pytest.raises(ValueError, match="Replay attack detected"):
        session.mark_ready(0, seq_no=3)
    
    assert session.get_last_seq(0) == 5


def test_valid_increasing_seq_accepted():
    """Valid increasing sequence numbers should be accepted."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Send increasing sequence numbers
    session.mark_ready(0, seq_no=1)
    assert session.get_last_seq(0) == 1
    
    # Clear ready state to test again
    session.reset_ready_state()
    
    session.mark_ready(0, seq_no=2)
    assert session.get_last_seq(0) == 2
    
    session.reset_ready_state()
    
    session.mark_ready(0, seq_no=100)
    assert session.get_last_seq(0) == 100


def test_seq_tracked_per_player_independently():
    """Each player's sequence numbers are tracked independently."""
    game = Game(players=[Player(pid=0), Player(pid=1), Player(pid=2)])
    session = GameSession(game)
    
    # Player 0 sends seq=10
    session.mark_ready(0, seq_no=10)
    assert session.get_last_seq(0) == 10
    
    # Player 1 can still send seq=1 (independent tracking)
    session.mark_ready(1, seq_no=1)
    assert session.get_last_seq(1) == 1
    
    # Player 2 can send seq=5
    session.mark_ready(2, seq_no=5)
    assert session.get_last_seq(2) == 5
    
    # Verify each player's last seq is independent
    assert session.get_last_seq(0) == 10
    assert session.get_last_seq(1) == 1
    assert session.get_last_seq(2) == 5


def test_seq_optional_backward_compatibility():
    """Sequence numbers are optional for backward compatibility."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Calling without seq_no should work (no replay protection)
    result1 = session.mark_ready(0)
    assert result1 is False
    
    # Can call multiple times without seq_no (idempotent)
    result2 = session.mark_ready(0)
    assert result2 is False
    
    # Last seq should still be -1 (initial value)
    assert session.get_last_seq(0) == -1


def test_seq_zero_is_valid():
    """Sequence number 0 is a valid starting point."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # seq=0 should be accepted (greater than initial -1)
    session.mark_ready(0, seq_no=0)
    assert session.get_last_seq(0) == 0
    
    # seq=0 again should be rejected
    with pytest.raises(ValueError, match="Replay attack detected"):
        session.mark_ready(0, seq_no=0)


def test_turn_progression_with_seq():
    """Turn progression should work correctly with sequence numbers."""
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    
    # Player 0 marks ready with seq=1
    result1 = session.mark_ready(0, seq_no=1)
    assert result1 is False  # Waiting for player 1
    
    # Player 1 marks ready with seq=1 - all ready
    result2 = session.mark_ready(1, seq_no=1)
    assert result2 is True  # All ready, turn progresses
    
    # Ready set should be cleared
    assert len(session.get_ready_players()) == 0
    
    # Next turn - players can use seq=2
    result3 = session.mark_ready(0, seq_no=2)
    assert result3 is False
    
    result4 = session.mark_ready(1, seq_no=2)
    assert result4 is True


def test_get_last_seq_invalid_pid():
    """Getting last seq for invalid pid should raise KeyError."""
    game = Game(players=[Player(pid=0)])
    session = GameSession(game)
    
    with pytest.raises(KeyError, match="Player 99 not found"):
        session.get_last_seq(99)


def test_initial_last_seq_is_negative_one():
    """Initial last_seq should be -1 for all players."""
    game = Game(players=[Player(pid=0), Player(pid=1), Player(pid=2)])
    session = GameSession(game)
    
    assert session.get_last_seq(0) == -1
    assert session.get_last_seq(1) == -1
    assert session.get_last_seq(2) == -1
