import random

from engine_core.board import combat_phase
from engine_core.card import get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.action_result import ActionResult
from v2.core.engine_adapter import EngineAdapter


def _build_adapter(seed: int = 77, n: int = 4) -> tuple[Game, EngineAdapter]:
    strategies = ["random", "warrior", "economist", "builder"][:n]
    rng = random.Random(seed)
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    game = Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )
    return game, EngineAdapter(game)


def test_invalid_player_reads_do_not_crash():
    """Invalid player reads should raise exceptions for critical methods,
    but return safe defaults for backward-compatible methods."""
    game, adapter = _build_adapter()

    # Critical methods now raise exceptions
    from v2.core.exceptions import PlayerNotFoundError
    import pytest
    
    with pytest.raises(PlayerNotFoundError):
        adapter.get_player(999)
    
    # Backward-compatible methods return safe defaults
    assert adapter.get_player_hp(999) == 0
    assert adapter.get_player_gold(999) == 0
    
    # get_hand now raises exception for invalid player
    with pytest.raises(PlayerNotFoundError):
        adapter.get_hand(999)
    
    # get_shop_window now raises exception for invalid player
    with pytest.raises(PlayerNotFoundError):
        adapter.get_shop_window(999)


def test_mutation_calls_fail_with_explicit_error_results_not_crashes():
    """Mutation calls with invalid player should return error results."""
    game, adapter = _build_adapter()

    # These methods return ActionResult for backward compatibility
    assert adapter.perform_buy_card(999, 0) == ActionResult.ERR_ENGINE_EXCEPTION
    assert adapter.perform_placement(999, 0, (0, 0), 0) == ActionResult.ERR_ENGINE_EXCEPTION


def test_missing_market_is_handled_gracefully():
    """Missing market: get_market() returns None, get_market_or_raise() raises."""
    game, adapter = _build_adapter()
    game.market = None

    # get_market() returns None (backward compatible)
    assert adapter.get_market() is None
    
    # get_market_or_raise() raises explicitly
    from v2.core.exceptions import MarketNotAvailableError
    import pytest
    with pytest.raises(MarketNotAvailableError):
        adapter.get_market_or_raise()
    
    # Other methods return safe defaults
    assert adapter.get_pool_copies() == {}
    assert adapter.get_rarity_weight("1", 1) == 0.0
    assert adapter.get_shop_window(0) == [None] * 5
    assert adapter.perform_buy_card(0, 0) == ActionResult.ERR_ENGINE_EXCEPTION


def test_missing_board_is_handled_gracefully():
    """Missing board should be detected and return error result."""
    game, adapter = _build_adapter()
    player = game.players[0]
    player.board = None
    if not player.hand:
        game.start_turn()

    result = adapter.perform_placement(0, 0, (0, 0), 2)

    # Missing board is now correctly detected as an error
    assert result == ActionResult.ERR_ENGINE_EXCEPTION


def test_invalid_hand_index_returns_error_result():
    game, adapter = _build_adapter()
    game.start_turn()

    assert adapter.perform_placement(0, 999, (0, 0), 0) == ActionResult.ERR_INVALID_HAND_IDX
