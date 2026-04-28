# Deprecated Wrapper Cleanup - Summary

## Problem

`TurnManager` and `CombatEngine` were calling their own deprecated wrapper methods internally, generating hundreds of `DeprecationWarning`s per game:

- **TurnManager.start_turn()** called `self._clear_transient_board_state()` every turn
- **CombatEngine.run_combat()** called `self._clear_transient_board_state()` twice per combat match

With 8 players, 50 turns, 4 matches/turn = **400 DeprecationWarnings per game**.

Python's warning filter was suppressing these, but the code path was still executing. Adding `filterwarnings("error")` to CI would have caused all simulation tests to fail.

## Solution

### 1. Replaced Internal Calls with Direct Imports

**TurnManager (engine_core/turn_manager.py):**
```python
# BEFORE
self._clear_transient_board_state(alive, current_turn=_turn, clear_combat_meta=True)

# AFTER
clear_transient_board_state(alive, current_turn=_turn, clear_combat_meta=True)
```

**CombatEngine (engine_core/combat_engine.py):**
```python
# BEFORE (2 locations)
self._clear_transient_board_state([p_a, p_b], current_turn=_turn, clear_combat_meta=True)

# AFTER
clear_transient_board_state([p_a, p_b], current_turn=_turn, clear_combat_meta=True)
```

### 2. Removed Deprecated Wrapper Methods

Deleted the following deprecated methods from all three classes:
- `_clear_transient_board_state()` from `TurnManager`, `CombatEngine`, and `Game`
- `_iter_board_cards()` from `TurnManager`, `CombatEngine`, and `Game`

### 3. Updated Documentation

- Removed references to deleted methods from module docstrings
- Updated test file to remove obsolete test case

## Files Modified

1. **engine_core/turn_manager.py**
   - Replaced 1 internal call to deprecated wrapper
   - Removed 2 deprecated wrapper methods
   - Updated module docstring

2. **engine_core/combat_engine.py**
   - Replaced 2 internal calls to deprecated wrappers
   - Removed 2 deprecated wrapper methods
   - Updated module docstring

3. **engine_core/game.py**
   - Removed 2 deprecated wrapper methods (no internal calls)

4. **tests/test_turn_manager_contract.py**
   - Removed test for deleted `_clear_transient_board_state` method

## Verification

✅ All 35 TurnManager contract tests pass
✅ No DeprecationWarnings raised with `-W error::DeprecationWarning`
✅ Game simulation runs successfully without warnings

## Impact

- **Zero DeprecationWarnings** during normal gameplay
- CI can now safely use `filterwarnings("error")` without breaking tests
- Cleaner codebase with direct function calls instead of unnecessary wrappers
- No behavioral changes - all functionality preserved

## Migration Path

External code calling these deprecated methods will still see the deprecation warning from `board_utils.py` (if any exists). Internal code now bypasses the wrapper layer entirely.
