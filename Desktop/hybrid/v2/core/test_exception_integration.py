"""
Integration test to verify exception refactor works with real Game instances.
"""

import pytest
from engine_core.game import Game
from engine_core.player import Player
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive
from engine_core.card import get_card_pool
from v2.core.engine_adapter import EngineAdapter
from v2.core.exceptions import PlayerNotFoundError, MarketNotAvailableError


def test_real_game_invalid_player_raises():
    """Test that real Game instance raises PlayerNotFoundError for invalid index."""
    players = [Player(pid=i, strategy="random") for i in range(4)]
    game = Game(
        players,
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    adapter = EngineAdapter(game)
    
    # Valid indices work
    assert adapter.get_player(0) is not None
    assert adapter.get_player(3) is not None
    
    # Invalid indices raise
    with pytest.raises(PlayerNotFoundError) as exc_info:
        adapter.get_player(4)
    assert exc_info.value.index == 4
    assert exc_info.value.player_count == 4
    
    with pytest.raises(PlayerNotFoundError):
        adapter.get_player(-1)


def test_real_game_market_available():
    """Test that real Game instance has valid market."""
    players = [Player(pid=i, strategy="random") for i in range(2)]
    game = Game(
        players,
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    adapter = EngineAdapter(game)
    
    # get_market() returns the market object
    market = adapter.get_market()
    assert market is not None
    assert hasattr(market, "get_window")
    
    # get_market_or_raise() also works
    market2 = adapter.get_market_or_raise()
    assert market2 is market


def test_real_game_get_hand_works():
    """Test that get_hand works with real Game instance."""
    players = [Player(pid=i, strategy="random") for i in range(2)]
    game = Game(
        players,
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    adapter = EngineAdapter(game)
    
    # Start turn to populate hand
    game.start_turn()
    
    # get_hand should work for valid player
    hand = adapter.get_hand(0)
    assert isinstance(hand, list)
    assert len(hand) == 6
    
    # get_hand should raise for invalid player
    with pytest.raises(PlayerNotFoundError):
        adapter.get_hand(999)


def test_real_game_backward_compatible_methods():
    """Test that backward-compatible methods return safe defaults."""
    players = [Player(pid=i, strategy="random") for i in range(2)]
    game = Game(
        players,
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    adapter = EngineAdapter(game)
    
    # These should return safe defaults for invalid indices
    assert adapter.get_player_hp(999) == 0
    assert adapter.get_player_gold(999) == 0
    assert adapter.is_shop_locked(999) is False
    assert adapter.get_eliminated_coords(999) == []


def test_exception_attributes_are_useful():
    """Test that exception attributes provide useful debugging info."""
    players = [Player(pid=i, strategy="random") for i in range(3)]
    game = Game(
        players,
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    adapter = EngineAdapter(game)
    
    try:
        adapter.get_player(10)
        assert False, "Should have raised PlayerNotFoundError"
    except PlayerNotFoundError as e:
        # Exception attributes are accessible
        assert e.index == 10
        assert e.player_count == 3
        
        # Error message is informative
        msg = str(e)
        assert "10" in msg
        assert "0-2" in msg or "valid range" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
