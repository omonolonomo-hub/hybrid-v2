"""Security tests for slot range validation.

This test verifies that ServerOrchestrator properly validates slot indices
to prevent IndexError, undefined behavior, and potential security exploits.

Bug Context:
    Previously, _handle_buy() only checked if slot was an integer, but didn't
    validate the range. This allowed negative indices (Python list wraparound)
    and out-of-bounds indices that could cause crashes or undefined behavior.
    
    Attack vectors:
    - slot=-1: Accesses last element (Python negative indexing)
    - slot=9999: IndexError or undefined behavior
    - slot="0": Type confusion (now caught)
    
    Fix: Added range validation (0 <= slot < MARKET_WINDOW_SIZE)
"""

import pytest
from unittest.mock import Mock
from engine_core.server_orchestrator import ServerOrchestrator, MARKET_WINDOW_SIZE
from engine_core.game_session import GameSession
from engine_core.game import Game
from engine_core.player import Player
from v2.core.action_result import ActionResult


@pytest.fixture
def orchestrator():
    """Create a ServerOrchestrator for testing."""
    mock_cards = []
    for i in range(10):
        card = Mock()
        card.name = f"TestCard{i}"
        card.tier = 1
        card.rarity = "1"  # Use valid rarity (1-5, not "common")
        mock_cards.append(card)
    
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players, card_pool=mock_cards, seed=42)
    
    from v2.core.engine_adapter import EngineAdapter
    from v2.core.local_dispatcher import LocalCommandDispatcher
    
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    orchestrator = ServerOrchestrator(session, state_builder=None)
    
    # Start turn so market is available
    game.start_turn()
    
    return orchestrator


def test_valid_slot_indices_accepted(orchestrator):
    """Test that valid slot indices (0-4) are accepted."""
    for slot in range(MARKET_WINDOW_SIZE):
        result = orchestrator.submit_action(0, {"type": "buy", "slot": slot})
        # Result may be OK or ERR_INSUFFICIENT_GOLD, but not ERR_ENGINE_EXCEPTION
        assert result != ActionResult.ERR_ENGINE_EXCEPTION, \
            f"Valid slot {slot} should not return ERR_ENGINE_EXCEPTION"


def test_negative_slot_rejected(orchestrator):
    """Test that negative slot indices are rejected (security fix)."""
    # Attack vector: slot=-1 would access last element in Python
    result = orchestrator.submit_action(0, {"type": "buy", "slot": -1})
    
    assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
        "Negative slot should be rejected with ERR_ENGINE_EXCEPTION"


def test_out_of_bounds_slot_rejected(orchestrator):
    """Test that out-of-bounds slot indices are rejected."""
    # Test various out-of-bounds values
    invalid_slots = [5, 6, 10, 100, 9999]
    
    for slot in invalid_slots:
        result = orchestrator.submit_action(0, {"type": "buy", "slot": slot})
        
        assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
            f"Out-of-bounds slot {slot} should be rejected with ERR_ENGINE_EXCEPTION"


def test_non_integer_slot_rejected(orchestrator):
    """Test that non-integer slot values are rejected."""
    invalid_types = [
        "0",           # String
        0.0,           # Float
        None,          # None
        [0],           # List
        {"slot": 0},   # Dict
        True,          # Boolean (technically int subclass, but semantically wrong)
    ]
    
    for invalid_slot in invalid_types:
        result = orchestrator.submit_action(0, {"type": "buy", "slot": invalid_slot})
        
        assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
            f"Non-integer slot {invalid_slot} (type {type(invalid_slot).__name__}) should be rejected"


def test_missing_slot_rejected(orchestrator):
    """Test that missing slot parameter is rejected."""
    result = orchestrator.submit_action(0, {"type": "buy"})
    
    assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
        "Missing slot parameter should be rejected"


def test_boundary_values(orchestrator):
    """Test boundary values (0 and MARKET_WINDOW_SIZE-1)."""
    # Lower boundary (valid)
    result = orchestrator.submit_action(0, {"type": "buy", "slot": 0})
    assert result != ActionResult.ERR_ENGINE_EXCEPTION, \
        "Slot 0 (lower boundary) should be valid"
    
    # Upper boundary (valid)
    result = orchestrator.submit_action(0, {"type": "buy", "slot": MARKET_WINDOW_SIZE - 1})
    assert result != ActionResult.ERR_ENGINE_EXCEPTION, \
        f"Slot {MARKET_WINDOW_SIZE - 1} (upper boundary) should be valid"
    
    # Just below lower boundary (invalid)
    result = orchestrator.submit_action(0, {"type": "buy", "slot": -1})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
        "Slot -1 (below lower boundary) should be invalid"
    
    # Just above upper boundary (invalid)
    result = orchestrator.submit_action(0, {"type": "buy", "slot": MARKET_WINDOW_SIZE})
    assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
        f"Slot {MARKET_WINDOW_SIZE} (above upper boundary) should be invalid"


def test_large_negative_slot_rejected(orchestrator):
    """Test that large negative indices are rejected."""
    # Python allows negative indexing: list[-1000] wraps around
    result = orchestrator.submit_action(0, {"type": "buy", "slot": -1000})
    
    assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
        "Large negative slot should be rejected"


def test_integer_overflow_attempt(orchestrator):
    """Test that extremely large integers are rejected."""
    # Test with values that could cause integer overflow in some languages
    large_values = [2**31, 2**32, 2**63, 2**64 - 1]
    
    for large_slot in large_values:
        result = orchestrator.submit_action(0, {"type": "buy", "slot": large_slot})
        
        assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
            f"Extremely large slot {large_slot} should be rejected"


def test_slot_validation_prevents_crash(orchestrator):
    """Test that invalid slots don't cause crashes."""
    # These should all be handled gracefully without exceptions
    dangerous_slots = [-1, -100, 5, 10, 100, 9999, "0", None, [], {}]
    
    for slot in dangerous_slots:
        try:
            result = orchestrator.submit_action(0, {"type": "buy", "slot": slot})
            # Should return error, not crash
            assert result == ActionResult.ERR_ENGINE_EXCEPTION, \
                f"Dangerous slot {slot} should return ERR_ENGINE_EXCEPTION"
        except Exception as e:
            pytest.fail(f"Slot validation should not raise exception for {slot}, got: {e}")


def test_market_window_size_constant():
    """Test that MARKET_WINDOW_SIZE constant is defined correctly."""
    assert MARKET_WINDOW_SIZE == 5, "Market window size should be 5"
    assert isinstance(MARKET_WINDOW_SIZE, int), "MARKET_WINDOW_SIZE should be an integer"


def test_valid_purchase_flow(orchestrator):
    """Test that valid purchases still work after validation."""
    # Give player enough gold
    game = orchestrator.session.game
    game.players[0].economy.gold = 10
    
    # Valid purchase should work
    result = orchestrator.submit_action(0, {"type": "buy", "slot": 0})
    
    # Should succeed or fail due to game logic, not validation
    assert result in [ActionResult.OK, ActionResult.ERR_INSUFFICIENT_GOLD], \
        "Valid purchase should not fail validation"


def test_multiple_invalid_attempts_dont_crash(orchestrator):
    """Test that multiple invalid attempts are handled gracefully."""
    # Simulate attacker trying multiple invalid slots
    for _ in range(10):
        result = orchestrator.submit_action(0, {"type": "buy", "slot": -1})
        assert result == ActionResult.ERR_ENGINE_EXCEPTION
        
        result = orchestrator.submit_action(0, {"type": "buy", "slot": 9999})
        assert result == ActionResult.ERR_ENGINE_EXCEPTION
    
    # Server should still be functional
    result = orchestrator.submit_action(0, {"type": "buy", "slot": 0})
    assert result != ActionResult.ERR_ENGINE_EXCEPTION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
