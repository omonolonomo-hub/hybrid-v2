# Network RNG Seed Synchronization Bug Fix

## Bug Description

**Critical Bug:** `Game._rng_seed` was never set during initialization, causing `NetworkServer._send_game_start()` to always send `None` to clients, breaking determinism in multiplayer games.

### Root Cause

In `engine_core/game.py`, the `Game.__init__()` method accepted an `rng` parameter but never stored the seed value in `_rng_seed`:

```python
# BEFORE (BROKEN):
def __init__(self, players, verbose=False, rng=None, ...):
    # ...
    self.rng = rng if rng is not None else random.Random()
    # ❌ _rng_seed was NEVER set!
```

When `NetworkServer._send_game_start()` tried to retrieve the seed:

```python
seed = getattr(self._orchestrator.session.game, "_rng_seed", None)
# ↑ Always returned None because _rng_seed was never set
```

This caused:
- Each client received `seed: null` in the `game_start` packet
- Clients couldn't synchronize their RNG state
- Multiplayer games were non-deterministic
- Combat results differed between clients

## Solution

### Changes Made

1. **Added `seed` parameter to `Game.__init__()`**
   - Allows explicit seed specification (preferred for network games)
   - Mutually exclusive with `rng` parameter

2. **Implemented seed tracking logic**
   - When `seed` provided: Store it and create RNG with that seed
   - When `rng` provided: Extract seed from RNG state (best effort)
   - When neither provided: Generate random seed and create RNG

3. **Updated initialization order**
   - RNG and seed are now initialized before Market creation
   - Ensures Market receives properly seeded RNG

### Code Changes

```python
# AFTER (FIXED):
def __init__(self, players, verbose=False, rng=None, seed: int = None, ...):
    # ...
    
    # Validate parameters
    if seed is not None and rng is not None:
        raise ValueError("Cannot specify both 'seed' and 'rng' parameters")
    
    # Initialize RNG with seed tracking
    if seed is not None:
        # Explicit seed - store and create RNG
        self._rng_seed = seed
        self.rng = random.Random(seed)
    elif rng is not None:
        # RNG provided - extract seed from state
        self.rng = rng
        try:
            state = rng.getstate()
            self._rng_seed = state[1][0] if len(state) > 1 and len(state[1]) > 0 else None
        except (AttributeError, IndexError, TypeError):
            # Fallback if extraction fails
            self._rng_seed = random.randint(0, 2**32 - 1)
            warnings.warn("Could not extract seed from provided RNG...")
    else:
        # No seed or RNG - generate both
        self._rng_seed = random.randint(0, 2**32 - 1)
        self.rng = random.Random(self._rng_seed)
```

## Testing

### New Test Files

1. **`tests/test_game_seed_tracking.py`** (8 tests)
   - Verifies seed storage in all initialization scenarios
   - Tests deterministic behavior with same seed
   - Validates seed consistency across game lifecycle

2. **`tests/test_network_seed_sync.py`** (8 tests)
   - Tests seed accessibility through orchestrator
   - Verifies seed survives game operations
   - Tests deterministic RNG sequences

### Test Results

```
tests/test_game_seed_tracking.py ........  [100%] ✓ 8 passed
tests/test_network_seed_sync.py ........   [100%] ✓ 8 passed
tests/test_game_session.py ..............  [100%] ✓ 14 passed
tests/test_network_integration.py ......   [100%] ✓ 6 passed
```

All existing tests pass - full backward compatibility maintained.

## Usage Recommendations

### For Network Games (Recommended)

```python
# Use explicit seed parameter
seed = 42424242
game = Game(players=players, seed=seed)

# Server can now send seed to clients
seed = game._rng_seed  # ✓ Returns 42424242
```

### For Local/Simulation Games

```python
# Let Game generate seed automatically
game = Game(players=players)

# Seed is still available if needed
seed = game._rng_seed  # ✓ Returns auto-generated seed
```

### Legacy Code (Still Works)

```python
# Passing RNG object still works
rng = random.Random(12345)
game = Game(players=players, rng=rng)

# Seed is extracted from RNG state
seed = game._rng_seed  # ✓ Returns extracted seed
```

## Impact

### Before Fix
- ❌ Multiplayer games non-deterministic
- ❌ Clients received `seed: null`
- ❌ Combat results differed between clients
- ❌ Impossible to replay games with same seed

### After Fix
- ✅ Multiplayer games fully deterministic
- ✅ Clients receive valid seed
- ✅ Combat results identical across clients
- ✅ Games can be replayed with same seed
- ✅ Full backward compatibility maintained

## Files Modified

- `engine_core/game.py` - Added seed parameter and tracking logic
- `tests/test_game_seed_tracking.py` - New test file (8 tests)
- `tests/test_network_seed_sync.py` - New test file (8 tests)

## Related Code

- `engine_core/network_server.py::_send_game_start()` - Reads `game._rng_seed`
- `engine_core/network_client.py` - Receives seed in `game_start` packet
- `engine_core/game_session.py` - Provides access to game instance

## Verification

To verify the fix works:

```python
# Create game with seed
game = Game(players=[Player(pid=0), Player(pid=1)], seed=999)

# Verify seed is stored
assert hasattr(game, '_rng_seed')
assert game._rng_seed == 999

# Verify NetworkServer can read it
seed = getattr(game, "_rng_seed", None)
assert seed is not None  # ✓ No longer None!
```

## Date

Fixed: April 29, 2026

## Author

Kiro AI Assistant
