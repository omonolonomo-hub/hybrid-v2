# ACIL/IMMEDIATE Fixes Bugfix Design

## Overview

This design document addresses three critical bugs identified in Phase 1 (ACIL/IMMEDIATE) of OMNISCIENT AUDIT V7. These are zero-risk, single-location fixes with no architectural impact:

1. **Signal.emit() Fatal Crash** - RuntimeError when observers disconnect during notification loop
2. **K_v Shortcut Bypass** - Debug shortcut bypasses critical game logic in production
3. **StateStore.phase Validation Missing** - Silent acceptance of invalid phase strings

All fixes are minimal 1-line or few-line changes designed for immediate deployment. No refactoring is performed in this phase to maintain 100% backward compatibility and zero architectural impact.

## Glossary

- **Bug_Condition (C)**: The condition that triggers each bug
- **Property (P)**: The desired behavior when the bug condition is met
- **Preservation**: Existing behavior that must remain unchanged by the fix
- **Signal.emit()**: The method in `engine_core/signals.py` that notifies all connected observers
- **Observer**: A callback function connected to a Signal
- **K_v Shortcut**: Debug keyboard shortcut (K_v key) in ShopScene that transitions to STATE_VERSUS
- **commit_human_turn()**: Critical method that executes AI turn, market cleanup, and state transitions
- **StateStore.phase**: Property in `v2/core/state_store.py` that stores the current game phase
- **Valid Phases**: The four allowed phase strings: "STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"

## Bug Details

### Bug 1: Signal.emit() Fatal Crash

#### Bug Condition

The bug manifests when Signal.emit() is called and an observer disconnects itself or another observer during the notification loop. The `_observers` list is being modified while iterating over it, causing Python's RuntimeError.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SignalEmitContext
  OUTPUT: boolean
  
  RETURN input.is_emitting == True
         AND input.observer_list_modified_during_iteration == True
         AND (input.observer_disconnects_self OR input.observer_disconnects_other)
END FUNCTION
```

#### Examples

- **Example 1**: Observer A is notified, calls `signal.disconnect(A)` in its callback → RuntimeError: "dictionary changed size during iteration"
- **Example 2**: Observer A is notified, calls `signal.disconnect(B)` in its callback → RuntimeError: "dictionary changed size during iteration"
- **Example 3**: Three observers connected, second observer disconnects itself during notification → RuntimeError
- **Edge Case**: Observer disconnects during emit() but is the last observer → May or may not crash depending on iteration state

### Bug 2: K_v Shortcut Bypass

#### Bug Condition

The bug manifests when a user presses K_v in ShopScene. The shortcut directly calls `phase_machine.transition_to("STATE_VERSUS")`, completely bypassing `commit_human_turn()`. This causes:
- AI opponent does not play its turn
- Market does not clean up properly
- pool_copies state becomes corrupted
- Game state becomes inconsistent

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type KeyboardEvent
  OUTPUT: boolean
  
  RETURN input.key == pygame.K_v
         AND input.type == pygame.KEYDOWN
         AND current_scene == ShopScene
         AND current_phase == "STATE_PREPARATION"
         AND Config.DEBUG_MODE == False  # Bug: no check exists
END FUNCTION
```

#### Examples

- **Example 1**: User presses K_v in ShopScene → Transitions to STATE_VERSUS without AI turn → AI board remains empty
- **Example 2**: User presses K_v after buying cards → Market doesn't clean up → Stale cards remain in shop
- **Example 3**: User presses K_v repeatedly → pool_copies becomes corrupted → Card distribution breaks
- **Edge Case**: K_v pressed during drag operation → State corruption with dragged card

### Bug 3: StateStore.phase Validation Missing

#### Bug Condition

The bug manifests when StateStore.phase is set to an invalid string value. The setter accepts any string without validation, allowing invalid phase values like "STATE_GARBAGE", "INVALID", or typos like "STATE_PREPARTION". This causes phase guards to fail silently downstream.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type str
  OUTPUT: boolean
  
  VALID_PHASES = {"STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"}
  
  RETURN input NOT IN VALID_PHASES
         AND setter_called_with(input)
         AND no_validation_performed
END FUNCTION
```

#### Examples

- **Example 1**: `state_store.phase = "STATE_GARBAGE"` → Silently accepted → Phase guards fail → Unpredictable behavior
- **Example 2**: `state_store.phase = "STATE_PREPARTION"` (typo) → Silently accepted → UI shows wrong state
- **Example 3**: `state_store.phase = ""` (empty string) → Silently accepted → All phase checks fail
- **Edge Case**: `state_store.phase = None` → TypeError downstream but not at setter

## Expected Behavior

### Bug 1: Signal.emit() Fatal Crash

**Correct Behavior:**
When Signal.emit() is called and an observer disconnects itself or another observer during the notification loop, the system SHALL complete the notification loop without crashing by iterating over a snapshot of the observer list.

**Implementation:**
- Create a shallow copy of `_observers` list before iteration
- Iterate over the snapshot, not the live list
- Disconnections during emit() will affect the live list but not the iteration
- Next emit() will use the updated list

### Bug 2: K_v Shortcut Bypass

**Correct Behavior:**
When the user presses K_v in ShopScene:
- IF `Config.DEBUG_MODE == False` THEN ignore the shortcut (no action taken)
- IF `Config.DEBUG_MODE == True` THEN execute the shortcut (for development testing only)

This ensures the shortcut is only available in development environments where `DEBUG_MODE=true` is explicitly set.

### Bug 3: StateStore.phase Validation Missing

**Correct Behavior:**
When StateStore.phase is set:
- IF value is in VALID_PHASES THEN accept and store the value
- IF value is NOT in VALID_PHASES THEN raise ValueError with message: "Invalid phase: '{value}'. Valid phases: STATE_PREPARATION, STATE_VERSUS, STATE_COMBAT, STATE_ENDGAME"

This provides immediate feedback at the point of error rather than silent failure downstream.

## Hypothesized Root Cause

### Bug 1: Signal.emit() Fatal Crash

Based on the code analysis, the root cause is:

1. **Direct List Iteration**: The emit() method iterates directly over `self._observers`:
   ```python
   for observer in self._observers:
       observer(**kwargs)
   ```

2. **Live List Modification**: The disconnect() method modifies the same list during iteration:
   ```python
   def disconnect(self, observer: Callable):
       if observer in self._observers:
           self._observers.remove(observer)  # Modifies list during iteration
   ```

3. **Python Iterator Invalidation**: Python's list iterator is invalidated when the list is modified, causing RuntimeError

### Bug 2: K_v Shortcut Bypass

Based on the code analysis, the root cause is:

1. **No Debug Gate**: The K_v handler in `v2/scenes/shop.py` line 197-199 has no `Config.DEBUG_MODE` check:
   ```python
   if event.key == pygame.K_v:
       self.phase_machine.transition_to("STATE_VERSUS")
       return
   ```

2. **Direct Phase Transition**: The shortcut calls `transition_to()` directly instead of going through the normal "Ready" button flow

3. **Bypassed Logic**: The normal flow calls `commit_human_turn()` which:
   - Executes AI opponent's turn via `adapter.commit_turn()`
   - Updates pairings for combat
   - Cleans up market state
   - Maintains pool_copies consistency

### Bug 3: StateStore.phase Validation Missing

Based on the code analysis, the root cause is:

1. **No Validation in Setter**: The phase setter in `v2/core/state_store.py` line 16-17 accepts any string:
   ```python
   @phase.setter
   def phase(self, value: str): self._phase = value
   ```

2. **No Defined Valid Set**: There is no VALID_PHASES constant or validation logic

3. **Silent Failure**: Invalid phases are stored and only cause problems downstream when phase guards check the value

## Correctness Properties

Property 1: Bug Condition - Signal.emit() Completes Without Crash

_For any_ Signal.emit() call where an observer disconnects itself or another observer during the notification loop, the fixed emit() method SHALL complete the notification loop without raising RuntimeError by iterating over a snapshot of the observer list.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Signal Notification Order and Arguments

_For any_ Signal.emit() call where no observers disconnect during notification, the fixed emit() method SHALL produce exactly the same behavior as the original method, preserving notification order and argument passing.

**Validates: Requirements 3.1, 3.2, 3.3**

Property 3: Bug Condition - K_v Shortcut Gated by DEBUG_MODE

_For any_ keyboard input where K_v is pressed in ShopScene during STATE_PREPARATION phase, the fixed handler SHALL ignore the shortcut when Config.DEBUG_MODE is False, and SHALL execute the shortcut only when Config.DEBUG_MODE is True.

**Validates: Requirements 2.3, 2.4, 2.5**

Property 4: Preservation - Normal ShopScene Interactions

_For any_ user interaction in ShopScene that is NOT the K_v shortcut (buy, sell, reroll, lock, commit, drag, camera controls), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing functionality.

**Validates: Requirements 3.4, 3.5, 3.6**

Property 5: Bug Condition - StateStore.phase Validation

_For any_ attempt to set StateStore.phase to an invalid string (not in VALID_PHASES), the fixed setter SHALL raise ValueError with a clear error message listing valid phases, preventing silent acceptance of invalid values.

**Validates: Requirements 2.6**

Property 6: Preservation - Valid Phase Assignment

_For any_ attempt to set StateStore.phase to a valid phase string (in VALID_PHASES), the fixed setter SHALL accept and store the value exactly as the original setter did, preserving all existing phase transition logic.

**Validates: Requirements 3.7, 3.8, 3.9**

## Fix Implementation

### Bug 1: Signal.emit() Fatal Crash

**File**: `engine_core/signals.py`

**Function**: `Signal.emit()`

**Current Code (lines 24-26)**:
```python
def emit(self, **kwargs):
    for observer in self._observers:
        observer(**kwargs)
```

**Fixed Code**:
```python
def emit(self, **kwargs):
    for observer in list(self._observers):
        observer(**kwargs)
```

**Specific Changes**:
1. **Snapshot Creation**: Wrap `self._observers` with `list()` to create a shallow copy
2. **Iteration Safety**: Iterate over the snapshot, allowing safe modification of the live list
3. **Zero Overhead**: `list()` creates a shallow copy in O(n) time with minimal memory overhead

**Why This Works**:
- The snapshot is created before iteration begins
- Disconnections modify `self._observers` but not the snapshot
- Next emit() will use the updated `self._observers` list
- No change to observer order or argument passing

### Bug 2: K_v Shortcut Bypass

**File**: `v2/scenes/shop.py`

**Function**: `ShopScene.handle_event()`

**Current Code (lines 197-200)**:
```python
if event.type == pygame.KEYDOWN:
    if event.key == pygame.K_v:
        self.phase_machine.transition_to("STATE_VERSUS")
        return
```

**Required Import Addition (at top of file)**:
```python
# Current import:
from v2.core.shop_controller import ShopController

# Change to:
from v2.core.shop_controller import ShopController, ShopUIAction
```

**Fixed Code**:
```python
if event.type == pygame.KEYDOWN:
    if event.key == pygame.K_v:
        from v2.constants import Config
        if Config.DEBUG_MODE:
            # Debug modda bile doğru yoldan git - commit_human_turn() çağrılmalı
            outcome = self.controller.handle_shop_action(ShopUIAction(kind="ready"))
            self._public_state = outcome.state
            self.phase_machine.transition_to("STATE_VERSUS")
        return
```

**Specific Changes**:
1. **Import ShopUIAction**: Add `ShopUIAction` to the existing import from `v2.core.shop_controller` (ShopScene currently doesn't import it because it receives ShopUIAction instances from `shop_panel.get_action_for_event()`, but now needs to instantiate it directly for the K_v shortcut)
2. **Import Config**: Add `from v2.constants import Config` inside the if block (local import to avoid circular dependencies)
3. **Debug Gate**: Wrap the shortcut logic with `if Config.DEBUG_MODE:`
4. **Proper Flow**: Even in debug mode, call `controller.handle_shop_action("ready")` to trigger `commit_human_turn()` - this ensures AI plays, market cleans up, and pool_copies stays consistent
5. **Keep Return**: Keep the `return` statement to consume the event even when DEBUG_MODE is False

**Why This Works**:
- `Config.DEBUG_MODE` is False by default (from `v2/constants.py` line 19)
- In production, K_v is ignored, forcing users through the normal "Ready" button flow
- In development with DEBUG_MODE=True, the shortcut still goes through the proper flow via `handle_shop_action("ready")`, ensuring `commit_human_turn()` executes correctly
- This maintains state consistency even when using the debug shortcut

### Bug 3: StateStore.phase Validation Missing

**File**: `v2/core/state_store.py`

**Class**: `StateStore`

**Current Code (lines 16-17)**:
```python
@phase.setter
def phase(self, value: str): self._phase = value
```

**Fixed Code**:
```python
# Modül seviyesinde sabit tanımla (class dışında, dosyanın üstünde)
_VALID_PHASES = frozenset({"STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"})

# StateStore class içinde:
@phase.setter
def phase(self, value: str):
    if value not in _VALID_PHASES:
        raise ValueError(
            f"Invalid phase: '{value}'. Valid phases: STATE_PREPARATION, STATE_VERSUS, STATE_COMBAT, STATE_ENDGAME"
        )
    self._phase = value
```

**Specific Changes**:
1. **Module-Level Constant**: Define `_VALID_PHASES` as a `frozenset` at module level (outside the class, at the top of the file) - this prevents recreating the set on every assignment
2. **Validation Check**: Check if `value not in _VALID_PHASES`
3. **Raise ValueError**: Raise descriptive error with the invalid value and list of valid phases
4. **Accept Valid**: Only set `self._phase` if validation passes

**Why This Works**:
- Validation happens at the point of assignment, not downstream
- `frozenset` at module level is created once, not on every setter call (performance optimization)
- Clear error message helps developers identify typos or invalid phase strings immediately
- Valid phases continue to work exactly as before
- No performance impact (frozenset lookup is O(1), and set is reused)

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fixes. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

#### Bug 1: Signal.emit() Fatal Crash

**Test Plan**: Write tests that create a Signal, connect observers that disconnect during notification, and call emit(). Run these tests on the UNFIXED code to observe RuntimeError.

**Test Cases**:
1. **Self-Disconnect Test**: Observer disconnects itself during callback (will fail on unfixed code with RuntimeError)
2. **Other-Disconnect Test**: Observer A disconnects Observer B during callback (will fail on unfixed code with RuntimeError)
3. **Multiple Disconnect Test**: Multiple observers disconnect during single emit() (will fail on unfixed code with RuntimeError)
4. **Last Observer Disconnect**: Last observer in list disconnects itself (may fail on unfixed code depending on iteration state)

**Expected Counterexamples**:
- RuntimeError: "dictionary changed size during iteration" (or similar list modification error)
- Possible causes: direct iteration over live list, no snapshot mechanism

#### Bug 2: K_v Shortcut Bypass

**Test Plan**: Write tests that simulate K_v keypress in ShopScene with DEBUG_MODE=False, verify that commit_human_turn() is NOT called and AI turn does not execute. Run these tests on the UNFIXED code to observe the bypass.

**Test Cases**:
1. **Production K_v Test**: Press K_v with DEBUG_MODE=False → Verify phase transitions without commit_human_turn() (will fail on unfixed code)
2. **AI Turn Bypass Test**: Press K_v → Verify AI opponent does not play turn (will fail on unfixed code)
3. **Market Cleanup Bypass Test**: Press K_v after buying cards → Verify market does not clean up (will fail on unfixed code)
4. **Pool Corruption Test**: Press K_v multiple times → Verify pool_copies becomes inconsistent (will fail on unfixed code)

**Expected Counterexamples**:
- Phase transitions to STATE_VERSUS without calling commit_human_turn()
- AI opponent's board remains empty after transition
- Market state remains stale
- Possible causes: no DEBUG_MODE check, direct phase transition

#### Bug 3: StateStore.phase Validation Missing

**Test Plan**: Write tests that attempt to set StateStore.phase to invalid strings, verify that invalid values are silently accepted. Run these tests on the UNFIXED code to observe silent failure.

**Test Cases**:
1. **Invalid String Test**: Set phase to "STATE_GARBAGE" → Verify it's accepted silently (will fail on unfixed code by NOT raising error)
2. **Typo Test**: Set phase to "STATE_PREPARTION" → Verify it's accepted silently (will fail on unfixed code by NOT raising error)
3. **Empty String Test**: Set phase to "" → Verify it's accepted silently (will fail on unfixed code by NOT raising error)
4. **Downstream Failure Test**: Set invalid phase → Verify phase guards fail silently (will fail on unfixed code with unpredictable behavior)

**Expected Counterexamples**:
- Invalid phase strings are stored without error
- Phase guards fail silently downstream
- Possible causes: no validation in setter, no VALID_PHASES constant

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed functions produce the expected behavior.

#### Bug 1: Signal.emit() Fatal Crash

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition_Signal(input) DO
  result := Signal.emit_fixed(**kwargs)
  ASSERT result completes without RuntimeError
  ASSERT all observers (except disconnected) were notified
END FOR
```

#### Bug 2: K_v Shortcut Bypass

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition_Kv(input) DO
  result := ShopScene.handle_event_fixed(input)
  IF Config.DEBUG_MODE == False THEN
    ASSERT phase did NOT transition
    ASSERT commit_human_turn() was NOT called
  ELSE
    ASSERT phase transitioned to STATE_VERSUS
  END IF
END FOR
```

#### Bug 3: StateStore.phase Validation Missing

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition_Phase(input) DO
  TRY
    StateStore.phase_fixed = input
    FAIL "Should have raised ValueError"
  CATCH ValueError as e
    ASSERT e.message contains "Invalid phase"
    ASSERT e.message contains input
    ASSERT e.message lists valid phases
  END TRY
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed functions produce the same result as the original functions.

#### Bug 1: Signal.emit() Fatal Crash

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition_Signal(input) DO
  # No observers disconnect during emit
  ASSERT Signal.emit_original(**kwargs) == Signal.emit_fixed(**kwargs)
  ASSERT all observers notified in same order
  ASSERT all observers received same arguments
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for normal emit() calls (no disconnections), then write unit tests capturing that behavior.

**Test Cases**:
1. **Normal Notification Preservation**: Verify observers are notified in same order when no disconnections occur
2. **Argument Passing Preservation**: Verify observers receive same arguments as before
3. **Connection/Disconnection Preservation**: Verify connect() and disconnect() outside of emit() work correctly

#### Bug 2: K_v Shortcut Bypass

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition_Kv(input) DO
  # Normal ShopScene interactions (not K_v)
  ASSERT ShopScene.handle_event_original(input) == ShopScene.handle_event_fixed(input)
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for normal ShopScene interactions (buy, sell, reroll, lock, commit, drag, camera), then write unit tests capturing that behavior.

**Test Cases**:
1. **Normal UI Preservation**: Verify buy, sell, reroll, lock, commit buttons work correctly after fix
2. **Ready Button Preservation**: Verify "Ready" button calls commit_human_turn() correctly
3. **Drag and Drop Preservation**: Verify card drag and drop works correctly
4. **Camera Controls Preservation**: Verify WASD, zoom, pan controls work correctly
5. **Other Shortcuts Preservation**: Verify K_r (reset camera) and other shortcuts work correctly

#### Bug 3: StateStore.phase Validation Missing

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition_Phase(input) DO
  # Valid phase strings
  StateStore.phase_fixed = input
  ASSERT StateStore.phase_fixed == input
  ASSERT no error raised
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for valid phase assignments, then write unit tests capturing that behavior.

**Test Cases**:
1. **Valid Phase Preservation**: Verify all four valid phases are accepted and stored correctly
2. **Phase Transition Preservation**: Verify phase transitions work correctly after fix
3. **Phase Guard Preservation**: Verify phase guards (e.g., `if phase == "STATE_PREPARATION"`) work correctly

### Unit Tests

#### Bug 1: Signal.emit() Fatal Crash
- Test observer self-disconnect during emit()
- Test observer disconnecting another observer during emit()
- Test multiple observers disconnecting during single emit()
- Test edge case: last observer disconnects itself

#### Bug 2: K_v Shortcut Bypass
- Test K_v with DEBUG_MODE=False (should be ignored)
- Test K_v with DEBUG_MODE=True (should transition)
- Test that normal "Ready" button flow calls commit_human_turn()
- Test that AI turn executes after "Ready" button

#### Bug 3: StateStore.phase Validation Missing
- Test invalid phase strings raise ValueError
- Test valid phase strings are accepted
- Test error message contains invalid value and valid phases list
- Test edge cases: empty string, None, numeric values

### Property-Based Tests

**NOTE**: Property-based testing with `hypothesis` is NOT currently set up in this project. The following test cases should be implemented as standard unit tests with multiple explicit test cases covering the input domain. If property-based testing is desired in the future, add `pytest-hypothesis` to `requirements.txt` and configure `pytest.ini`.

#### Bug 1: Signal.emit() Fatal Crash
- **Unit Test Approach**: Create multiple explicit test cases with different observer connection/disconnection patterns
- Test case 1: Single observer disconnects itself
- Test case 2: First observer disconnects second observer
- Test case 3: Middle observer disconnects itself
- Test case 4: Last observer disconnects itself
- Test case 5: Multiple observers disconnect during single emit

#### Bug 2: K_v Shortcut Bypass
- **Unit Test Approach**: Create multiple explicit test cases with different ShopScene states and DEBUG_MODE values
- Test case 1: K_v with DEBUG_MODE=False (should be ignored)
- Test case 2: K_v with DEBUG_MODE=True (should call commit_human_turn)
- Test case 3: Other keyboard inputs work correctly
- Test case 4: Verify commit_human_turn() is called in normal "Ready" button flow

#### Bug 3: StateStore.phase Validation Missing
- **Unit Test Approach**: Create multiple explicit test cases with different phase strings
- Test case 1: Invalid string "STATE_GARBAGE" raises ValueError
- Test case 2: Typo "STATE_PREPARTION" raises ValueError
- Test case 3: Empty string "" raises ValueError
- Test case 4: All four valid phases are accepted
- Test case 5: Error message contains invalid value and valid phases list

### Integration Tests

#### Bug 1: Signal.emit() Fatal Crash
- Test full game flow with observers disconnecting during various game events
- Test signal bus with multiple signals firing simultaneously
- Test that game continues normally after observer disconnections

#### Bug 2: K_v Shortcut Bypass
- Test full game flow from ShopScene through combat with DEBUG_MODE=False
- Test that AI opponent plays correctly when using "Ready" button
- Test that market cleanup happens correctly in normal flow
- Test that pool_copies remains consistent across multiple turns

#### Bug 3: StateStore.phase Validation Missing
- Test full game flow with phase transitions
- Test that invalid phase assignments are caught early in development
- Test that phase guards work correctly across all game phases
