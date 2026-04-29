"""Integration tests for replay attack protection in ServerOrchestrator.

Verifies that:
1. ServerOrchestrator correctly passes sequence numbers to GameSession
2. Replay attacks are rejected at the orchestrator level
3. Error handling returns appropriate ActionResult codes
"""

import pytest
from unittest.mock import Mock
from engine_core.game import Game
from engine_core.player import Player
from engine_core.game_session import GameSession
from engine_core.server_orchestrator import ServerOrchestrator
from v2.core.action_result import ActionResult


def test_end_turn_with_seq_accepted():
    """Valid end_turn with sequence number should be accepted."""
    # Setup
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Player 0 ends turn with seq=1
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    assert session.get_last_seq(0) == 1
    
    # Player 1 ends turn with seq=1
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    assert session.get_last_seq(1) == 1


def test_end_turn_replay_attack_rejected():
    """Duplicate end_turn with same sequence number should be rejected."""
    # Setup
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Player 0 ends turn with seq=1 - should succeed
    result1 = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result1 == ActionResult.OK
    
    # Player 0 tries to end turn again with seq=1 - should fail (replay attack)
    result2 = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result2 == ActionResult.ERR_ENGINE_EXCEPTION


def test_end_turn_without_seq_backward_compatible():
    """end_turn without sequence number should still work (backward compatibility)."""
    # Setup
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Player 0 ends turn without seq
    result = orchestrator.submit_action(0, {"type": "end_turn"})
    assert result == ActionResult.OK
    
    # Can call multiple times (idempotent without seq)
    result = orchestrator.submit_action(0, {"type": "end_turn"})
    assert result == ActionResult.OK


def test_seq_validation_rejects_non_integer():
    """Sequence number must be an integer."""
    # Setup
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Try with string seq
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": "1"})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION
    
    # Try with bool seq (bool is int subclass in Python)
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": True})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION
    
    # Try with float seq
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1.5})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION


def test_turn_advancement_with_seq_protection():
    """Turn advancement should work correctly with sequence number protection."""
    # Setup
    game = Mock()
    game.players = [Player(pid=0), Player(pid=1)]
    game.turn = 1
    game.finish_turn = Mock()
    game.combat_phase = Mock()
    game.start_turn = Mock()
    
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Player 0 ends turn with seq=1
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    
    # Turn should not advance yet
    game.finish_turn.assert_not_called()
    
    # Player 1 ends turn with seq=1 - triggers turn advancement
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    
    # Turn advancement should have been triggered
    game.finish_turn.assert_called_once()
    game.combat_phase.assert_called_once()
    game.start_turn.assert_called_once()


def test_replay_attack_does_not_trigger_turn_advancement():
    """Replay attack should not count toward turn advancement."""
    # Setup
    game = Mock()
    game.players = [Player(pid=0), Player(pid=1)]
    game.turn = 1
    game.finish_turn = Mock()
    game.combat_phase = Mock()
    game.start_turn = Mock()
    
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Player 0 ends turn with seq=1
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    
    # Player 0 tries replay attack with seq=1 - should be rejected
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION
    
    # Player 1 ends turn with seq=1 - should trigger turn advancement
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 1})
    assert result == ActionResult.OK
    
    # Turn advancement should have been triggered (replay didn't count)
    game.finish_turn.assert_called_once()


def test_multiple_turns_with_increasing_seq():
    """Multiple turns should work with increasing sequence numbers."""
    # Setup
    game = Mock()
    game.players = [Player(pid=0), Player(pid=1)]
    game.turn = 1
    game.finish_turn = Mock()
    game.combat_phase = Mock()
    game.start_turn = Mock()
    
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    # Turn 1
    orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    orchestrator.submit_action(1, {"type": "end_turn", "seq": 1})
    
    # Turn 2
    orchestrator.submit_action(0, {"type": "end_turn", "seq": 2})
    orchestrator.submit_action(1, {"type": "end_turn", "seq": 2})
    
    # Turn 3
    orchestrator.submit_action(0, {"type": "end_turn", "seq": 3})
    orchestrator.submit_action(1, {"type": "end_turn", "seq": 3})
    
    # Should have advanced 3 times
    assert game.finish_turn.call_count == 3
    assert game.combat_phase.call_count == 3
    assert game.start_turn.call_count == 3
    
    # Verify last seq numbers
    assert session.get_last_seq(0) == 3
    assert session.get_last_seq(1) == 3
