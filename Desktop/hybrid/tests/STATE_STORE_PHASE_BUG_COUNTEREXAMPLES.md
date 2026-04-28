# StateStore.phase Validation Bug - Counterexamples

## Bug Summary

**Bug**: StateStore.phase setter accepts invalid phase strings silently without validation
**Location**: `v2/core/state_store.py`, lines 16-17
**Impact**: Invalid phases cause phase guards to fail silently downstream, leading to unpredictable behavior

## Root Cause Analysis

The phase setter has no validation logic:

```python
@phase.setter
def phase(self, value: str): self._phase = value
```

There is no `VALID_PHASES` constant or validation check. Any string value is accepted and stored.

## Counterexamples Found

All tests FAILED as expected on unfixed code, confirming the bug exists:

### Test 1: Completely Invalid Phase String
- **Input**: `store.phase = "STATE_GARBAGE"`
- **Expected**: ValueError raised
- **Actual**: No error raised, value accepted silently
- **Result**: ❌ FAILED (DID NOT RAISE ValueError)

### Test 2: Typo in Valid Phase Name
- **Input**: `store.phase = "STATE_PREPARTION"` (missing 'A')
- **Expected**: ValueError raised
- **Actual**: No error raised, value accepted silently
- **Result**: ❌ FAILED (DID NOT RAISE ValueError)

### Test 3: Empty String Phase
- **Input**: `store.phase = ""`
- **Expected**: ValueError raised
- **Actual**: No error raised, value accepted silently
- **Result**: ❌ FAILED (DID NOT RAISE ValueError)

### Test 4: Multiple Invalid Phase Strings
All of the following were accepted silently:
- `"INVALID"`
- `"STATE_INVALID"`
- `"state_preparation"` (lowercase)
- `"STATE_PREP"` (abbreviated)
- `"STATE_COMBAT_PHASE"` (extra suffix)
- `"None"`
- `"null"`

**Expected**: ValueError raised for each
**Actual**: No errors raised, all values accepted silently
**Result**: ❌ FAILED (DID NOT RAISE ValueError for any)

## Bug Confirmation

✅ **Bug Confirmed**: The StateStore.phase setter accepts ANY string value without validation.

The valid phases should be:
- `"STATE_PREPARATION"`
- `"STATE_VERSUS"`
- `"STATE_COMBAT"`
- `"STATE_ENDGAME"`

But the current implementation has no enforcement mechanism.

## Downstream Impact

When invalid phases are stored:
1. Phase guards like `if phase == "STATE_PREPARATION"` fail silently
2. UI shows incorrect state
3. Game logic may execute in wrong phase
4. Debugging becomes difficult (error manifests far from root cause)

## Fix Required

Add validation in the phase setter:
1. Define `_VALID_PHASES` constant at module level
2. Check `value not in _VALID_PHASES` in setter
3. Raise ValueError with descriptive message listing valid phases
4. Only set `self._phase` if validation passes

## Test Status

- ✅ Bug condition exploration test written
- ✅ Test run on unfixed code
- ✅ Test FAILED as expected (confirms bug exists)
- ✅ Counterexamples documented
- ⏳ Preservation tests (Task 8)
- ⏳ Fix implementation (Task 9)
- ⏳ Verification on fixed code (Task 9.3)

## Next Steps

1. Write preservation unit tests (Task 8) to capture valid phase assignment behavior
2. Implement the fix (Task 9)
3. Re-run this test to verify it PASSES on fixed code
4. Verify preservation tests still PASS on fixed code
