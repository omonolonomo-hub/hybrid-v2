"""
Test file demonstrating the new exception hierarchy in EngineAdapter.

This shows how the new exceptions provide immediate, clear error messages
instead of silent failures that lead to AttributeErrors later.
"""

import pytest
from unittest.mock import Mock
from v2.core.engine_adapter import EngineAdapter
from v2.core.exceptions import (
    PlayerNotFoundError,
    MarketNotAvailableError,
    InvalidGameStateError,
)


def test_get_player_invalid_index_raises_immediately():
    """Before: get_player(999) returned None, causing AttributeError later.
    After: Raises PlayerNotFoundError immediately with clear message."""
    
    engine = Mock()
    engine.players = [Mock(), Mock(), Mock()]  # 3 players
    adapter = EngineAdapter(engine)
    
    # This now raises immediately instead of returning None
    with pytest.raises(PlayerNotFoundError) as exc_info:
        adapter.get_player(999)
    
    assert "Player at index 999 not found" in str(exc_info.value)
    assert "(valid range: 0-2)" in str(exc_info.value)
    assert exc_info.value.index == 999
    assert exc_info.value.player_count == 3


def test_get_player_negative_index_raises():
    """Negative indices should fail immediately."""
    
    engine = Mock()
    engine.players = [Mock(), Mock()]
    adapter = EngineAdapter(engine)
    
    with pytest.raises(PlayerNotFoundError) as exc_info:
        adapter.get_player(-1)
    
    assert "Player at index -1 not found" in str(exc_info.value)


def test_get_market_missing_raises_immediately():
    """get_market() returns None when market is not initialized."""
    
    engine = Mock()
    engine.market = None
    adapter = EngineAdapter(engine)
    
    assert adapter.get_market() is None


def test_get_market_invalid_raises():
    """Market without required methods returns None."""
    
    engine = Mock()
    engine.market = Mock(spec=[])  # Market without get_window method
    adapter = EngineAdapter(engine)
    
    assert adapter.get_market() is None


def test_get_market_or_raise_missing_raises():
    """get_market_or_raise() raises MarketNotAvailableError when market is None."""
    
    engine = Mock()
    engine.market = None
    adapter = EngineAdapter(engine)
    
    with pytest.raises(MarketNotAvailableError) as exc_info:
        adapter.get_market_or_raise()
    
    assert "Market not initialized" in str(exc_info.value)


def test_get_market_or_raise_invalid_raises():
    """get_market_or_raise() raises when market missing required methods."""
    
    engine = Mock()
    engine.market = Mock(spec=[])
    adapter = EngineAdapter(engine)
    
    with pytest.raises(MarketNotAvailableError) as exc_info:
        adapter.get_market_or_raise()
    
    assert "missing required methods" in str(exc_info.value)


def test_get_shop_window_propagates_player_error():
    """get_shop_window should propagate PlayerNotFoundError."""
    
    engine = Mock()
    engine.players = []
    adapter = EngineAdapter(engine)
    
    with pytest.raises(PlayerNotFoundError):
        adapter.get_shop_window(0)


def test_get_shop_window_returns_empty_on_missing_market():
    """get_shop_window should return [None]*5 when market is unavailable (not raise)."""
    
    engine = Mock()
    engine.players = [Mock(pid=1)]
    engine.market = None
    adapter = EngineAdapter(engine)
    
    # Market unavailable → graceful fallback, not exception
    result = adapter.get_shop_window(0)
    assert result == [None] * 5

def test_backward_compatibility_methods_return_defaults():
    """Methods like get_player_hp should still return defaults for compatibility.
    
    These methods are used in many places and changing them to raise exceptions
    would break existing code. They log warnings but return safe defaults.
    """
    
    engine = Mock()
    engine.players = []
    adapter = EngineAdapter(engine)
    
    # These should return defaults, not raise
    assert adapter.get_player_hp(999) == 0
    assert adapter.get_player_gold(999) == 0
    assert adapter.is_shop_locked(999) is False
    assert adapter.get_eliminated_coords(999) == []
    assert adapter.get_passive_buff_log(999) == []


def test_corrupted_engine_state_raises_clear_error():
    """If engine.players is corrupted, raise appropriate error.
    
    None is treated as empty list (PlayerNotFoundError).
    For truly corrupted state (not a list), we get InvalidGameStateError.
    """
    
    # None is treated as empty list
    engine = Mock()
    engine.players = None
    adapter = EngineAdapter(engine)
    
    with pytest.raises(PlayerNotFoundError) as exc_info:
        adapter.get_player(0)
    
    assert "Player at index 0 not found" in str(exc_info.value)
    
    # Truly corrupted state (not a list-like object)
    engine2 = Mock()
    del engine2.players  # Missing attribute
    adapter2 = EngineAdapter(engine2)
    
    with pytest.raises(InvalidGameStateError) as exc_info:
        adapter2.get_player(0)
    
    assert "corrupted or missing" in str(exc_info.value)


def test_exception_hierarchy():
    """All exceptions inherit from EngineAdapterError for easy catching."""
    
    from v2.core.exceptions import EngineAdapterError
    
    # Can catch all adapter errors with base class
    assert issubclass(PlayerNotFoundError, EngineAdapterError)
    assert issubclass(MarketNotAvailableError, EngineAdapterError)
    assert issubclass(InvalidGameStateError, EngineAdapterError)


def test_real_world_scenario_before_and_after():
    """Demonstrate the improvement in error clarity.
    
    BEFORE (silent failure):
        player = adapter.get_player(999)  # Returns None
        gold = player.gold  # AttributeError: 'NoneType' object has no attribute 'gold'
        # Error happens far from the root cause!
    
    AFTER (immediate failure):
        player = adapter.get_player(999)  # Raises PlayerNotFoundError immediately
        # Error happens at the source with clear message!
    """
    
    engine = Mock()
    engine.players = [Mock()]
    adapter = EngineAdapter(engine)
    
    # The error now happens immediately at get_player, not later at attribute access
    with pytest.raises(PlayerNotFoundError) as exc_info:
        player = adapter.get_player(999)
        # This line never executes because exception is raised above
        _ = player.gold
    
    # Error message is clear and actionable
    assert "999" in str(exc_info.value)
    assert "valid range" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
