# Bug 4: Non-Atomic Phase Transition - Counterexamples

## Bug Summary

**Bug**: ShopController.handle_phase_change() Not Atomic
**Location**: `v2/core/shop_controller.py`
**Severity**: CRITICAL (Phase 2)

## Bug Description

Phase transitions in `handle_phase_change()` lack transaction pattern, leaving inconsistent state on exception. The sequence `mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn()` is not atomic. If any step throws an exception, the phase is already mirrored but the turn hasn't started, leaving the game in an inconsistent state.

## Root Cause Analysis

1. **No Exception Handling**: `handle_phase_change()` doesn't wrap the sequence in try/except
2. **Phase Modified Early**: `StateStore._phase` is modified by `mirror_phase()` before the sequence completes
3. **No Rollback Logic**: No mechanism exists to restore `_phase` to previous value on exception
4. **Partial Execution**: Some steps complete (mirror_phase, cleanup_dead_cards) but others don't (start_turn, reset_turn)

## Counterexamples Found

### Test Case 1: cleanup_dead_cards() Exception

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- Exception injected: `cleanup_dead_cards()` raises `RuntimeError`

**Expected Behavior** (after fix):
- Phase should be restored to `STATE_COMBAT` (rollback)

**Actual Behavior** (bug):
- Phase is `STATE_PREPARATION` (already mirrored by `mirror_phase()`)
- Turn not started (sequence incomplete)
- **Inconsistent state**: Phase says "PREPARATION" but turn hasn't started

**Test Output**:
```
AssertionError: BUG DETECTED: Phase transition not atomic. 
Exception during cleanup_dead_cards left phase in inconsistent state. 
Expected phase: STATE_COMBAT (rolled back). 
Got phase: STATE_PREPARATION (already mirrored but turn not started). 
This proves no rollback mechanism exists.
```

### Test Case 2: start_turn() Exception

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- Exception injected: `start_turn()` raises `RuntimeError`

**Expected Behavior** (after fix):
- Phase should be restored to `STATE_COMBAT` (rollback)

**Actual Behavior** (bug):
- Phase is `STATE_PREPARATION` (already mirrored)
- `cleanup_dead_cards()` completed successfully
- `start_turn()` failed (turn not started)
- **Inconsistent state**: Phase says "PREPARATION", dead cards cleaned, but turn not started

**Test Output**:
```
AssertionError: BUG DETECTED: Phase transition not atomic. 
Exception during start_turn left phase in inconsistent state. 
Expected phase: STATE_COMBAT (rolled back). 
Got phase: STATE_PREPARATION (already mirrored but turn not started). 
This proves no rollback mechanism exists.
```

### Test Case 3: reset_turn() Exception

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- Exception injected: `reset_turn()` raises `RuntimeError`

**Expected Behavior** (after fix):
- Phase should be restored to `STATE_COMBAT` (rollback)

**Actual Behavior** (bug):
- Phase is `STATE_PREPARATION` (already mirrored)
- `cleanup_dead_cards()` completed successfully
- `start_turn()` completed successfully
- `reset_turn()` failed (reset incomplete)
- **Inconsistent state**: Phase says "PREPARATION", turn started, but reset incomplete

**Test Output**:
```
AssertionError: BUG DETECTED: Phase transition not atomic. 
Exception during reset_turn left phase in inconsistent state. 
Expected phase: STATE_COMBAT (rolled back). 
Got phase: STATE_PREPARATION (already mirrored but reset incomplete). 
This proves no rollback mechanism exists.
```

### Test Case 4: Phase Modified Before Sequence Completes

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- Spy injected: Check phase inside `cleanup_dead_cards()`

**Expected Behavior**:
- Phase should be modified by `mirror_phase()` before `cleanup_dead_cards()` runs

**Actual Behavior** (confirms bug):
- Phase is `STATE_PREPARATION` inside `cleanup_dead_cards()`
- This confirms phase is modified early, before sequence completes
- **This is the root cause**: Phase changes immediately, no transaction pattern

**Test Output**:
```
PASSED - Phase should be modified by mirror_phase() before cleanup_dead_cards() runs. 
This confirms the bug: phase is modified early, before sequence completes.
```

### Test Case 5: No Rollback Mechanism Exists

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- Exception injected: `start_turn()` raises `RuntimeError`

**Expected Behavior**:
- Exception should propagate (not caught by rollback logic)
- Phase should NOT be restored (no rollback mechanism)

**Actual Behavior** (confirms bug):
- Exception propagates (no try/except in `handle_phase_change()`)
- Phase is `STATE_PREPARATION` (not restored)
- **This confirms**: No transaction pattern exists in `handle_phase_change()`

**Test Output**:
```
PASSED - Exception should propagate (no try/except in handle_phase_change)
Phase should NOT be restored (no rollback mechanism exists). 
This confirms the bug: no transaction pattern in handle_phase_change().
```

### Test Case 6: Successful Phase Transition

**Input**:
- Initial phase: `STATE_COMBAT`
- Target phase: `STATE_PREPARATION`
- No exceptions injected

**Expected Behavior**:
- Full sequence should execute: `mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn()`

**Actual Behavior**:
- All steps execute successfully
- Phase is `STATE_PREPARATION`
- **This is NOT part of the bug**: Successful transitions work correctly

**Test Output**:
```
PASSED - Successful phase transition should execute full sequence.
```

## Impact Analysis

### Severity: CRITICAL

1. **Inconsistent Game State**: Phase says "PREPARATION" but turn not started
2. **Unpredictable Behavior**: Next action runs in inconsistent state
3. **Market Window Issue**: Phase is "PREPARATION" but market window not open
4. **Debugging Difficulty**: Hard to diagnose because phase looks correct but behavior is wrong

### Real-World Scenarios

1. **Network Error During start_turn()**: If network call fails, phase is mirrored but turn not started
2. **Database Error During cleanup_dead_cards()**: If DB call fails, phase is mirrored but cards not cleaned
3. **Memory Error During reset_turn()**: If memory allocation fails, phase is mirrored but reset incomplete

## Fix Requirements

### Expected Behavior (from design.md)

**Requirement 2.11**: When STATE_PREPARATION transition calls `mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn()` AND any step throws exception, the system SHALL restore `StateStore._phase` to its previous value.

**Requirement 2.12**: When phase transition logic is wrapped in try/except, the system SHALL restore phase to previous value on exception.

**Requirement 2.13**: When exception occurs during phase transition, the system SHALL restore `StateStore._phase` to prevent inconsistent state (engine-level mutations are not undone but phase guard remains correct).

### Fix Strategy

1. **Wrap Sequence in try/except**: Add exception handling to `handle_phase_change()`
2. **Store Previous Phase**: Save `previous_phase = game_state._store.phase` before transition
3. **Rollback on Exception**: In except block, restore phase with `game_state.mirror_phase(previous_phase)`
4. **Re-raise Exception**: Preserve error visibility for debugging
5. **Document Rollback Scope**: Only `StateStore._phase` is rolled back (engine mutations are idempotent/logged)

### Important Notes

- **Only restore StateStore._phase on exception**
- **Engine-level mutations (board, market) are NOT rolled back** because they are either idempotent (can be safely repeated) or logged (can be debugged)
- **No full transaction pattern needed** - only phase guard restoration required
- **PhaseTransactionContext pattern is optional** but not required for this fix

## Test Results Summary

| Test Case | Status | Description |
|-----------|--------|-------------|
| test_cleanup_dead_cards_exception_leaves_phase_inconsistent | **FAILED** ✓ | Confirms bug: phase not rolled back on cleanup exception |
| test_start_turn_exception_leaves_phase_inconsistent | **FAILED** ✓ | Confirms bug: phase not rolled back on start_turn exception |
| test_reset_turn_exception_leaves_phase_inconsistent | **FAILED** ✓ | Confirms bug: phase not rolled back on reset_turn exception |
| test_phase_modified_before_sequence_completes | **PASSED** ✓ | Confirms bug: phase modified early before sequence completes |
| test_no_rollback_mechanism_exists | **PASSED** ✓ | Confirms bug: no transaction pattern in handle_phase_change() |
| test_successful_phase_transition_completes_sequence | **PASSED** ✓ | Confirms: successful transitions work correctly (not part of bug) |

**Result**: 3 tests FAILED as expected (confirms bug exists), 3 tests PASSED (confirms bug characteristics)

## Next Steps

1. ✅ **Task 10 Complete**: Bug condition exploration test written and run
2. ⏭️ **Task 11**: Write preservation unit tests for successful phase transitions (BEFORE implementing fix)
3. ⏭️ **Task 12**: Implement fix with try/except and rollback logic
4. ⏭️ **Task 12.3**: Re-run bug condition exploration test (should PASS after fix)
5. ⏭️ **Task 12.4**: Re-run preservation tests (should still PASS after fix)

## References

- **Bug Report**: OMNISCIENT AUDIT V7 - Phase 2 (CRITICAL) - Bug 4
- **Design Document**: `.kiro/specs/kritik-phase2-fixes/design.md`
- **Requirements Document**: `.kiro/specs/kritik-phase2-fixes/bugfix.md`
- **Test File**: `tests/test_bug4_non_atomic_phase_transition.py`
