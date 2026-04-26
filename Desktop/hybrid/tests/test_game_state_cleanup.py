"""
Test GameState cleanup to verify memory leak fix.

This test verifies that GameState.cleanup() properly disconnects
signal observers and breaks circular references.
"""
import pytest
from v2.core.game_state import GameState
from engine_core.game_factory import build_game


def test_cleanup_disconnects_signal_observers():
    """Verify cleanup() disconnects all signal observers."""
    # Arrange
    gs = GameState()
    game = build_game(strategies=["human", "random"])
    gs.hook_engine(game)
    
    # Verify signals are connected
    assert hasattr(game, "signals")
    assert len(game.signals.board_mutated._observers) > 0
    
    # Act
    gs.cleanup()
    
    # Assert - all observers should be disconnected
    assert len(game.signals.board_mutated._observers) == 0
    assert len(game.signals.economy_changed._observers) == 0
    assert len(game.signals.inventory_changed._observers) == 0
    assert len(game.signals.turn_started._observers) == 0
    assert len(game.signals.combat_finished._observers) == 0


def test_cleanup_is_idempotent():
    """Verify cleanup() can be called multiple times safely."""
    # Arrange
    gs = GameState()
    game = build_game(strategies=["human", "random"])
    gs.hook_engine(game)
    
    # Act - call cleanup multiple times
    gs.cleanup()
    gs.cleanup()
    gs.cleanup()
    
    # Assert - should not raise any exceptions
    assert gs._adapter is None
    assert gs._cached_public_state is None


def test_cleanup_clears_adapter_reference():
    """Verify cleanup() clears the adapter reference."""
    # Arrange
    gs = GameState()
    game = build_game(strategies=["human", "random"])
    gs.hook_engine(game)
    
    assert gs._adapter is not None
    
    # Act
    gs.cleanup()
    
    # Assert
    assert gs._adapter is None


def test_cleanup_clears_cached_state():
    """Verify cleanup() clears the cached public state."""
    # Arrange
    gs = GameState()
    game = build_game(strategies=["human", "random"])
    gs.hook_engine(game)
    
    # Force cache creation
    _ = gs.get_public_state()
    assert gs._cached_public_state is not None
    
    # Act
    gs.cleanup()
    
    # Assert
    assert gs._cached_public_state is None


def test_no_del_method_exists():
    """Verify __del__ method has been removed (memory leak fix)."""
    # This test ensures we don't accidentally reintroduce __del__
    assert not hasattr(GameState, '__del__'), \
        "__del__ should not exist - use explicit cleanup() instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
