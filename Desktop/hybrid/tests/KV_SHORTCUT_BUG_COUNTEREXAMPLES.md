# K_v Shortcut Bypass Bug - Counterexamples Documentation

## Test Execution Date
2026-04-28

## Bug Confirmation Status
✅ **BUG CONFIRMED** - All tests demonstrate the expected buggy behavior on unfixed code

## Counterexamples Found

### Test Case 1: K_v Bypasses commit_human_turn() in Production Mode
**Status**: ❌ FAILED (as expected - confirms bug exists)

**Bug Condition**:
- Input: K_v keydown event
- Config.DEBUG_MODE: False (production mode)

**Expected Behavior (after fix)**:
- `phase_machine.transition_to()` should NOT be called
- `controller.handle_shop_action()` should NOT be called
- The shortcut should be completely ignored in production mode

**Actual Behavior (unfixed code)**:
- ❌ `phase_machine.transition_to('STATE_VERSUS')` WAS called (1 time)
- ✅ `controller.handle_shop_action()` was NOT called
- **Root Cause Confirmed**: K_v directly transitions to STATE_VERSUS without any DEBUG_MODE check

**Impact**:
- AI opponent does not play its turn
- Market does not clean up properly
- pool_copies state becomes corrupted
- Game state becomes inconsistent

---

### Test Case 2: K_v Should Call Proper Flow in Debug Mode
**Status**: ❌ FAILED (as expected - confirms bug exists)

**Bug Condition**:
- Input: K_v keydown event
- Config.DEBUG_MODE: True (debug mode)

**Expected Behavior (after fix)**:
- `controller.handle_shop_action()` SHOULD be called with ShopUIAction(kind="ready")
- This ensures `commit_human_turn()` executes properly
- AI plays turn, market cleans up, pool_copies stays consistent

**Actual Behavior (unfixed code)**:
- ❌ `controller.handle_shop_action()` was NOT called (0 times)
- ❌ `phase_machine.transition_to('STATE_VERSUS')` WAS called directly
- **Root Cause Confirmed**: Even in debug mode, K_v bypasses the proper flow

**Impact**:
- Even when debugging, the shortcut causes state corruption
- Developers cannot use K_v safely even with DEBUG_MODE=True

---

### Test Case 3: Direct Phase Transition Demonstrates Bypass
**Status**: ✅ PASSED (documentation test)

**Counterexample Documentation**:
```
Config.DEBUG_MODE: False
phase_machine.transition_to called: True
phase_machine.transition_to call count: 1
phase_machine.transition_to args: call('STATE_VERSUS')
controller.handle_shop_action called: False
```

**Analysis**:
- The K_v handler directly calls `phase_machine.transition_to("STATE_VERSUS")`
- No DEBUG_MODE check exists in the handler
- No call to `controller.handle_shop_action()` occurs
- This confirms the root cause: missing DEBUG_MODE gate

---

### Test Case 4: Other Keyboard Events Not Affected
**Status**: ✅ PASSED

**Verification**:
- K_r (reset camera) works correctly regardless of DEBUG_MODE
- Other keyboard shortcuts are not affected by this bug
- The bug is isolated to the K_v handler only

---

## Root Cause Analysis

Based on the counterexamples, the root cause is confirmed:

**File**: `v2/scenes/shop.py`
**Lines**: 197-199

**Current Code**:
```python
if event.key == pygame.K_v:
    self.phase_machine.transition_to("STATE_VERSUS")
    return
```

**Issues**:
1. ❌ No `Config.DEBUG_MODE` check exists
2. ❌ Direct call to `phase_machine.transition_to()` bypasses proper flow
3. ❌ Does not call `controller.handle_shop_action("ready")`
4. ❌ Bypasses `commit_human_turn()` which causes:
   - AI turn not executed
   - Market not cleaned up
   - pool_copies corruption

---

## Fix Validation Strategy

When the fix is implemented, these same tests should:

1. **Test Case 1**: ✅ PASS - K_v ignored in production mode
2. **Test Case 2**: ✅ PASS - K_v calls proper flow in debug mode
3. **Test Case 3**: ✅ PASS - Documentation shows correct behavior
4. **Test Case 4**: ✅ PASS - Other shortcuts still work

---

## Next Steps

1. ✅ Bug condition exploration complete
2. ⏭️ Write preservation tests (Task 5)
3. ⏭️ Implement fix (Task 6)
4. ⏭️ Verify fix with these same tests

---

## Test Command

To reproduce these counterexamples:
```bash
python -m pytest tests/test_kv_shortcut_bypass_bug.py -v -s
```

Expected output on UNFIXED code:
- 2 tests FAIL (test_kv_bypasses_commit_in_production_mode, test_kv_calls_proper_flow_in_debug_mode)
- 2 tests PASS (test_kv_direct_phase_transition_demonstrates_bypass, test_other_keydown_events_not_affected)

Expected output on FIXED code:
- 4 tests PASS
