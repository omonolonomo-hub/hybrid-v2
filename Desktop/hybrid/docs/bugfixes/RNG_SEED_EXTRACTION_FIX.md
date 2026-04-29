# RNG Seed Extraction Fix

## Problem

The `Game(rng=...)` parameter path had a critical bug that **completely broke** multiplayer synchronization from the start:

```python
# BROKEN CODE (before fix)
elif rng is not None:
    self.rng = rng
    state = rng.getstate()
    self._rng_seed = state[1][0]  # ❌ ALWAYS RETURNS 2147483648!
```

### Why This Was Broken

`random.Random.getstate()` returns:
```python
(3, (625-element Mersenne Twister internal state tuple...), None)
```

`state[1][0]` extracts the **first internal state element**, which is:
- **Always `2147483648` (2^31)** initially - a Mersenne Twister initialization constant
- **NOT the original seed** - not even close!
- **Changes as state evolves** - but never becomes the seed

**Result:** Two computers receiving this "seed" would:
1. Both get `2147483648` regardless of the actual seed used
2. Produce **identical sequences to each other** (both using wrong seed)
3. Produce **completely different sequences from the server** (server using correct seed)

This means **multiplayer was broken from turn 1**, not just after state evolution!

## Root Cause

The Mersenne Twister algorithm (Python's default RNG) maintains 625 integers of internal state. The first element (`state[1][0]`) is always initialized to `2147483648` (2^31) regardless of the seed. This is an internal constant, not the seed.

After initialization with a seed, this state evolves with each random number generated. The internal state cannot be reverse-engineered back to the original seed, and `state[1][0]` was never the seed to begin with.

## Solution

### 1. Deprecated `rng=` Parameter

The `rng=` parameter is now deprecated for multiplayer games:

```python
# ⚠️ DEPRECATED - emits DeprecationWarning
game = Game(players, rng=some_rng)

# ✅ CORRECT - always use seed= for multiplayer
game = Game(players, seed=1337)
```

### 2. Fixed `game_factory.py`

**Before:**
```python
rng = random.Random(seed)
game = Game(players, rng=rng)
game._rng_seed = seed  # Manual workaround
```

**After:**
```python
# Pass seed directly - no workaround needed
game = Game(players, seed=seed)
```

### 3. Fixed Simulation Scripts

**Before:**
```python
# Reused RNG across games (bad for independence)
rng = random.Random(seed)
for game_num in range(500):
    game = Game(players, rng=rng)
```

**After:**
```python
# Each game gets independent seed
master_rng = random.Random(seed)  # Only for strategy shuffling
for game_num in range(500):
    game_seed = seed + game_num
    game = Game(players, seed=game_seed)
```

## Migration Guide

### For Local/Test Code

If you're using `rng=` for local testing, you'll see a deprecation warning but code will still work:

```python
# Still works, but emits warning
rng = random.Random(42)
game = Game(players, rng=rng)

# Better: use seed= directly
game = Game(players, seed=42)
```

### For Multiplayer Code

**CRITICAL:** Always use `seed=` parameter:

```python
# Server side
game = Game(players, seed=server_seed)
# game._rng_seed is automatically set to server_seed

# NetworkServer sends game._rng_seed to clients
# Clients create: random.Random(received_seed)
# ✅ Both produce identical sequences
```

## Files Changed

- `engine_core/game.py` - Added deprecation warning and clarified comments
- `engine_core/game_factory.py` - Changed from `rng=` to `seed=`
- `scripts/simulation/run_simulation.py` - Fixed to use independent seeds per game
- `tools/run_comprehensive_8player_simulation.py` - Fixed to use `seed=`
- `tests/test_game_seed_tracking.py` - Updated to expect deprecation warning
- `tests/test_network_seed_sync.py` - Updated to expect deprecation warning

## Verification

All tests pass:
```bash
pytest tests/test_game_seed_tracking.py -v      # ✅ 8 passed
pytest tests/test_network_seed_sync.py -v       # ✅ 8 passed
```

## Technical Details

### Why `seed=` Works

```python
# Server
game = Game(players, seed=1337)
# Internally: self.rng = random.Random(1337)
# Server sends: 1337

# Client receives: 1337
client_rng = random.Random(1337)
# ✅ Identical sequence to server
```

### Why `rng=` Fails

```python
# Server
server_rng = random.Random(1337)
game = Game(players, rng=server_rng)
# Extracts: state[1][0] = 2147483648 (ALWAYS this value, NOT 1337!)

# Server sends: 2147483648 to clients

# Client receives: 2147483648
client_rng = random.Random(2147483648)
# ❌ Client uses seed 2147483648, server uses seed 1337
# ❌ COMPLETELY DIFFERENT SEQUENCES FROM TURN 1!

# Even worse: ALL games send the same "seed" (2147483648)
# So clients can't distinguish between different games!
```

## Lessons Learned

1. **Never extract seeds from RNG state** - it's not reversible
2. **Always pass seeds explicitly** for deterministic systems
3. **Each game should have independent seed** - don't reuse RNG across games
4. **Test determinism explicitly** - verify same seed produces same results

## Related Issues

- Original bug report: Network desync in multiplayer games
- Related: `NETWORK_SEED_SYNC_FIX.md` (initial fix that added `_rng_seed` attribute)
- This fix: Deprecates the broken `rng=` path entirely
