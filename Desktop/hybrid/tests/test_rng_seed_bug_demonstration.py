"""Demonstration of the RNG seed extraction bug that was fixed.

This test shows why Game(rng=...) is broken for multiplayer synchronization.
"""

import random
import pytest
from engine_core.game import Game
from engine_core.player import Player


def test_demonstrate_seed_extraction_bug():
    """Demonstrates that state[1][0] is NOT the original seed.
    
    This test shows the exact bug that broke multiplayer sync:
    - Server creates RNG with seed=1337
    - Server extracts state[1][0] and sends it to client
    - Client creates RNG with that extracted value
    - Result: DIFFERENT sequences!
    """
    original_seed = 1337
    
    # Server side: Create RNG with known seed
    server_rng = random.Random(original_seed)
    
    # Extract what the old broken code would send to client
    state = server_rng.getstate()
    extracted_value = state[1][0]  # This is what the bug did
    
    # The extracted value is NOT the original seed!
    # It's actually a constant: 2^31 (Mersenne Twister initialization constant)
    assert extracted_value == 2147483648  # Always this value!
    assert extracted_value != original_seed  # ❌ NOT the seed!
    
    # If client uses this extracted value...
    client_rng = random.Random(extracted_value)
    
    # Generate sequences
    server_sequence = [server_rng.random() for _ in range(5)]
    client_sequence = [client_rng.random() for _ in range(5)]
    
    # The sequences will be COMPLETELY DIFFERENT!
    assert server_sequence != client_sequence  # ❌ DESYNC from the start!


def test_correct_approach_with_seed_parameter():
    """Shows the correct approach: always use seed= parameter.
    
    This is how multiplayer sync should work:
    - Server creates Game with seed=1337
    - Server sends 1337 to client
    - Client creates random.Random(1337)
    - Result: IDENTICAL sequences!
    """
    original_seed = 1337
    
    # Server side: Create game with explicit seed
    server_players = [Player(pid=i) for i in range(2)]
    
    # Suppress deprecation warning for this test
    with pytest.warns(DeprecationWarning):
        # Old broken way (for comparison)
        server_rng_old = random.Random(original_seed)
        game_old = Game(players=server_players, rng=server_rng_old)
    
    # New correct way
    server_players2 = [Player(pid=i) for i in range(2)]
    game_new = Game(players=server_players2, seed=original_seed)
    
    # The new way stores the actual seed
    assert game_new._rng_seed == original_seed
    
    # Client side: Create RNG with received seed
    client_rng = random.Random(game_new._rng_seed)
    
    # Generate sequences
    server_sequence = [game_new.rng.random() for _ in range(10)]
    client_sequence = [client_rng.random() for _ in range(10)]
    
    # ✅ PERFECT SYNC!
    assert server_sequence == client_sequence


def test_why_state_extraction_fails():
    """Technical explanation of why state[1][0] doesn't work.
    
    Python's Mersenne Twister maintains 625 integers of internal state.
    After initialization, this state evolves with each random() call.
    The internal state cannot be reverse-engineered to the original seed.
    """
    seed = 42
    rng = random.Random(seed)
    
    # Get initial state
    state = rng.getstate()
    # state = (version, (625 MT state integers...), None)
    
    # The state tuple has 625 elements (not 624!)
    assert len(state[1]) == 625
    
    # state[1][0] is just the first internal state integer
    first_state_int = state[1][0]
    
    # It's always 2^31 initially (MT initialization constant)
    assert first_state_int == 2147483648
    
    # This is NOT the seed!
    assert first_state_int != seed
    
    # Generate some randoms to evolve state
    for _ in range(100):
        rng.random()
    
    # Get evolved state
    state2 = rng.getstate()
    first_state_int2 = state2[1][0]
    
    # The first state integer has changed
    assert first_state_int != first_state_int2
    
    # If we try to create a new RNG with the evolved state integer...
    rng2 = random.Random(first_state_int2)
    
    # It will produce a COMPLETELY DIFFERENT sequence than the original
    # This is the root cause of multiplayer desync!


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
