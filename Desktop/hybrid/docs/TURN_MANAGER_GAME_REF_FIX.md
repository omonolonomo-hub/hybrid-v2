# TurnManager Game Reference Fix

## Problem Identification

**Pattern Mismatch:** Asymmetric context creation between preparation and combat phases.

### Root Cause

In `TurnManager.start_turn()`:
```python
_ctx = {
    "turn": _turn,
    "game": None,  # ← Always None, causing AttributeError
    "market": _market,
    ...
}
```

In `CombatEngine.run_combat()`:
```python
game_ref = getattr(p_a, "game", None)  # ← Correctly retrieves from player
```

### Impact

Passive triggers (e.g., `income`, `market_refresh`) that access `ctx["game"]` during the preparation phase would fail with `AttributeError` when trying to use game-level functionality.

## Solution

### Changes Made

1. **TurnManager.__init__** - Added `game_ref` parameter:
   ```python
   def __init__(
       self,
       ...,
       game_ref=None,  # New parameter
   ) -> None:
       ...
       self._game_ref = game_ref
   ```

2. **TurnManager.start_turn()** - Use game reference in context:
   ```python
   _ctx = {
       "turn": _turn,
       "game": self._game_ref,  # ← Now properly set
       "market": _market,
       ...
   }
   ```

3. **Game.__init__** - Pass self reference to TurnManager:
   ```python
   self._turn_manager = TurnManager(
       ...,
       game_ref=self,  # ← Inject game reference
   )
   ```

4. **Test Updates** - Updated test files to pass `game_ref=None` for isolated testing:
   - `tests/test_turn_manager_contract.py`
   - `tests/test_aaa_verification.py`

## Benefits

- **Symmetry:** Both preparation and combat phases now have consistent access to game reference
- **Robustness:** Passive triggers can safely access game-level functionality during preparation
- **Backward Compatible:** Tests can still run TurnManager in isolation with `game_ref=None`
- **Clean Architecture:** Uses dependency injection pattern (no circular imports)

## Verification

All tests pass:
- ✅ 36/36 TurnManager contract tests
- ✅ 7/7 AAA verification tests

## Notes

- Consider using `weakref` for `game_ref` to avoid circular reference issues if memory management becomes a concern
- The fix maintains the existing separation of concerns: TurnManager doesn't import Game, only receives a reference via dependency injection
