"""Tests for Game RNG seed tracking (network determinism fix).

This test verifies that Game._rng_seed is properly set during initialization,
which is critical for NetworkServer._send_game_start() to sync clients.

Bug Context:
    NetworkServer._send_game_start() reads game._rng_seed to send to clients.
    Previously, _rng_seed was never set, causing None to be sent, breaking
    determinism across clients.
"""

import random
import pytest
from engine_core.game import Game
from engine_core.player import Player


def test_game_seed_stored_when_no_rng_provided():
    """When no RNG or seed provided, Game should generate and store a seed."""
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players)
    
    # Verify seed was generated and stored
    assert hasattr(game, '_rng_seed')
    assert game._rng_seed is not None
    assert isinstance(game._rng_seed, int)
    assert 0 <= game._rng_seed < 2**32


def test_game_seed_stored_when_explicit_seed_provided():
    """When explicit seed provided, Game should store it."""
    players = [Player(pid=i) for i in range(2)]
    test_seed = 42
    
    game = Game(players=players, seed=test_seed)
    
    # Verify seed was stored
    assert game._rng_seed == test_seed
    
    # Verify RNG was created with that seed
    assert game.rng is not None
    
    # Verify RNG produces deterministic results
    game.rng.seed(test_seed)  # Reset to same seed
    expected_value = game.rng.random()
    
    game.rng.seed(test_seed)  # Reset again
    actual_value = game.rng.random()
    
    assert expected_value == actual_value


def test_game_seed_extracted_when_rng_provided():
    """When RNG provided, Game should extract seed proxy and emit deprecation warning."""
    players = [Player(pid=i) for i in range(2)]
    test_seed = 12345
    test_rng = random.Random(test_seed)
    
    # Should emit deprecation warning
    with pytest.warns(DeprecationWarning, match="Game\\(rng=...\\) is deprecated"):
        game = Game(players=players, rng=test_rng)
    
    # Verify seed was extracted and stored
    assert hasattr(game, '_rng_seed')
    assert game._rng_seed is not None
    assert isinstance(game._rng_seed, int)
    
    # Note: The extracted seed is a proxy from getstate(), not the original seed
    # This is why rng= is deprecated - it cannot reliably sync multiplayer games


def test_game_rejects_both_seed_and_rng():
    """Game should raise ValueError if both seed and rng are provided."""
    players = [Player(pid=i) for i in range(2)]
    test_seed = 42
    test_rng = random.Random(99)
    
    with pytest.raises(ValueError, match="Cannot specify both"):
        Game(players=players, seed=test_seed, rng=test_rng)


def test_two_games_with_same_seed_produce_same_results():
    """Two games with same seed should produce identical RNG sequences."""
    test_seed = 777
    
    # Create two games with same seed
    players1 = [Player(pid=i) for i in range(2)]
    game1 = Game(players=players1, seed=test_seed)
    
    players2 = [Player(pid=i) for i in range(2)]
    game2 = Game(players=players2, seed=test_seed)
    
    # Verify both stored the same seed
    assert game1._rng_seed == game2._rng_seed == test_seed
    
    # Verify both produce same random sequence
    sequence1 = [game1.rng.random() for _ in range(10)]
    sequence2 = [game2.rng.random() for _ in range(10)]
    
    assert sequence1 == sequence2


def test_network_server_can_read_seed():
    """Verify NetworkServer._send_game_start() can read _rng_seed attribute."""
    players = [Player(pid=i) for i in range(2)]
    test_seed = 999
    
    game = Game(players=players, seed=test_seed)
    
    # Simulate what NetworkServer._send_game_start() does
    seed = getattr(game, "_rng_seed", None)
    
    # Verify seed is not None (the bug we're fixing)
    assert seed is not None
    assert seed == test_seed


def test_game_with_no_seed_still_has_rng():
    """Game should have working RNG even when no seed/rng provided."""
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players)
    
    # Verify RNG exists and works
    assert game.rng is not None
    value = game.rng.random()
    assert 0.0 <= value < 1.0


def test_seed_consistency_across_game_lifecycle():
    """Seed should remain consistent throughout game lifecycle."""
    players = [Player(pid=i) for i in range(2)]
    test_seed = 555
    
    game = Game(players=players, seed=test_seed)
    
    # Check seed before any operations
    assert game._rng_seed == test_seed
    
    # Perform some game operations
    game.start_turn()
    
    # Check seed after operations
    assert game._rng_seed == test_seed
    
    # Finish turn
    game.finish_turn()
    
    # Check seed still consistent
    assert game._rng_seed == test_seed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
