# Implementation Plan

## Bug 1: Signal.emit() Fatal Crash

- [x] 1. Write bug condition exploration test for Signal.emit() crash
  - **Property 1: Bug Condition** - Observer Disconnect During Emit
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the RuntimeError exists
  - **Scoped PBT Approach**: Test concrete failing cases: observer disconnects self, observer disconnects other
  - Test implementation details from Bug Condition in design:
    - Create Signal instance
    - Connect observer that disconnects itself during callback
    - Call emit() and verify RuntimeError: "dictionary changed size during iteration"
    - Connect observer A that disconnects observer B during callback
    - Call emit() and verify RuntimeError occurs
  - The test assertions should match the Expected Behavior Properties from design (emit completes without crash)
  - Run test on UNFIXED code in `engine_core/signals.py`
  - **EXPECTED OUTCOME**: Test FAILS with RuntimeError (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation unit tests for Signal.emit() (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Signal Notification Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for normal emit() calls (no disconnections during notification)
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: Observers notified in same order when no disconnections occur
    - Test 2: Observers receive same arguments as before
    - Test 3: connect() and disconnect() outside of emit() work correctly
  - Multiple explicit unit tests provide stronger guarantees than property-based tests for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3. Fix Signal.emit() fatal crash

  - [x] 3.1 Implement the fix in engine_core/signals.py
    - Change line 25: `for observer in self._observers:` → `for observer in list(self._observers):`
    - This creates a shallow copy (snapshot) before iteration
    - Disconnections modify the live list but not the iteration snapshot
    - Zero overhead: O(n) time, minimal memory
    - _Bug_Condition: isBugCondition(input) where input.is_emitting == True AND input.observer_list_modified_during_iteration == True_
    - _Expected_Behavior: emit() completes without RuntimeError by iterating over snapshot_
    - _Preservation: Normal notification order and argument passing preserved_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Observer Disconnect During Emit
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal Signal Notification Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation unit tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 2: K_v Shortcut Bypass

- [x] 4. Write bug condition exploration test for K_v shortcut bypass
  - **Property 1: Bug Condition** - K_v Bypasses commit_human_turn()
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bypass exists
  - **Scoped Test Approach**: Test isolated K_v handler logic, NOT full ShopScene
  - Test implementation details from Bug Condition in design:
    - Test the K_v handler logic in isolation (no full ShopScene mock needed)
    - Set Config.DEBUG_MODE = False (production mode)
    - Verify that with DEBUG_MODE=False, the handler does NOT call controller.handle_shop_action()
    - Verify that with DEBUG_MODE=True, the handler DOES call controller.handle_shop_action("ready")
  - The test assertions should match the Expected Behavior Properties from design (K_v ignored when DEBUG_MODE=False)
  - Run test on UNFIXED code in `v2/scenes/shop.py`
  - **EXPECTED OUTCOME**: Test FAILS (K_v bypasses logic - this is correct, it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.3, 1.4, 1.5, 1.6_

- [x] 5. Write preservation integration test for "Ready" button flow (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Ready Button Flow
  - **IMPORTANT**: Follow observation-first methodology
  - **SCOPE REDUCTION**: Full ShopScene mock is too costly for Phase 1 "zero-risk" fixes
  - Focus on single critical preservation test: "Ready" button integration test
  - Test implementation:
    - Use existing test infrastructure (no new mock setup needed)
    - Test that "Ready" button flow calls commit_human_turn() correctly
    - Verify AI opponent plays turn after Ready button
    - Verify market cleanup happens correctly
  - This single integration test validates the most critical preservation requirement
  - Other ShopScene interactions (drag/drop, camera controls) are orthogonal to K_v fix and don't need explicit tests
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test PASSES (this confirms baseline behavior to preserve)
  - Mark task complete when test is written, run, and passing on unfixed code
  - _Requirements: 3.4, 3.5, 3.6_

- [x] 6. Fix K_v shortcut bypass

  - [x] 6.1 Add required import to v2/scenes/shop.py
    - Change import at top of file from: `from v2.core.shop_controller import ShopController`
    - To: `from v2.core.shop_controller import ShopController, ShopUIAction`
    - ShopUIAction is needed to instantiate action for K_v shortcut
    - _Requirements: 2.3, 2.4, 2.5_

  - [x] 6.2 Implement the fix in v2/scenes/shop.py (lines 197-200)
    - Replace current K_v handler with DEBUG_MODE gate
    - Add local import: `from v2.constants import Config`
    - Wrap logic with: `if Config.DEBUG_MODE:`
    - Even in debug mode, call: `self.controller.handle_shop_action(ShopUIAction(kind="ready"))`
    - This ensures commit_human_turn() executes, AI plays, market cleans up
    - Keep `return` statement to consume event even when DEBUG_MODE=False
    - _Bug_Condition: isBugCondition(input) where input.key == K_v AND Config.DEBUG_MODE == False_
    - _Expected_Behavior: K_v ignored when DEBUG_MODE=False, executes proper flow when DEBUG_MODE=True_
    - _Preservation: Normal ShopScene interactions (buy, sell, reroll, lock, commit, drag, camera) preserved_
    - _Requirements: 2.3, 2.4, 2.5, 3.4, 3.5, 3.6_

  - [x] 6.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - K_v Gated by DEBUG_MODE
    - **IMPORTANT**: Re-run the SAME test from task 4 - do NOT write a new test
    - The test from task 4 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 4
    - **EXPECTED OUTCOME**: Test PASSES (confirms K_v is now gated by DEBUG_MODE)
    - _Requirements: 2.3, 2.4, 2.5_

  - [x] 6.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal ShopScene Interactions
    - **IMPORTANT**: Re-run the SAME tests from task 5 - do NOT write new tests
    - Run preservation unit tests from step 5
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 3: StateStore.phase Validation Missing

- [x] 7. Write bug condition exploration test for StateStore.phase validation
  - **Property 1: Bug Condition** - Invalid Phase Silently Accepted
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate silent acceptance of invalid phases
  - **Scoped PBT Approach**: Test concrete failing cases: "STATE_GARBAGE", "STATE_PREPARTION" (typo), "" (empty)
  - Test implementation details from Bug Condition in design:
    - Create StateStore instance
    - Attempt to set phase to "STATE_GARBAGE"
    - Verify it's accepted silently (NO ValueError raised)
    - Attempt to set phase to "STATE_PREPARTION" (typo)
    - Verify it's accepted silently (NO ValueError raised)
    - Attempt to set phase to "" (empty string)
    - Verify it's accepted silently (NO ValueError raised)
  - The test assertions should match the Expected Behavior Properties from design (ValueError raised for invalid phases)
  - Run test on UNFIXED code in `v2/core/state_store.py`
  - **EXPECTED OUTCOME**: Test FAILS (invalid phases accepted - this is correct, it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.7, 1.8_

- [x] 8. Write preservation unit tests for StateStore.phase (BEFORE implementing fix)
  - **Property 2: Preservation** - Valid Phase Assignment
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for valid phase assignments
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: All four valid phases are accepted and stored correctly
    - Test 2: Phase transitions work correctly
    - Test 3: Phase guards (e.g., `if phase == "STATE_PREPARATION"`) work correctly
  - Multiple explicit unit tests provide stronger guarantees for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.7, 3.8, 3.9_

- [x] 9. Fix StateStore.phase validation

  - [x] 9.1 Add module-level constant to v2/core/state_store.py
    - Add at top of file (outside class, after imports):
    - `_VALID_PHASES = frozenset({"STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"})`
    - frozenset at module level is created once, not on every setter call (performance optimization)
    - _Requirements: 2.6, 2.7_

  - [x] 9.2 Implement validation in phase setter (lines 16-17)
    - Add validation check: `if value not in _VALID_PHASES:`
    - Raise ValueError with descriptive message: `f"Invalid phase: '{value}'. Valid phases: STATE_PREPARATION, STATE_VERSUS, STATE_COMBAT, STATE_ENDGAME"`
    - Only set `self._phase = value` if validation passes
    - _Bug_Condition: isBugCondition(input) where input NOT IN VALID_PHASES_
    - _Expected_Behavior: ValueError raised for invalid phases with clear error message_
    - _Preservation: Valid phase assignments work exactly as before_
    - _Requirements: 2.6, 2.7, 3.7, 3.8, 3.9_

  - [x] 9.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Invalid Phase Raises ValueError
    - **IMPORTANT**: Re-run the SAME test from task 7 - do NOT write a new test
    - The test from task 7 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 7
    - **EXPECTED OUTCOME**: Test PASSES (confirms ValueError is now raised for invalid phases)
    - _Requirements: 2.6, 2.7_

  - [x] 9.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Valid Phase Assignment
    - **IMPORTANT**: Re-run the SAME tests from task 8 - do NOT write new tests
    - Run preservation unit tests from step 8
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Final Checkpoint

- [x] 10. Checkpoint - Ensure all tests pass
  - Run all exploration tests (tasks 1, 4, 7) - should now PASS
  - Run all preservation tests (tasks 2, 5, 8) - should still PASS
  - Verify no regressions in existing functionality
  - Ensure all three bugs are fixed and validated
  - Ask the user if questions arise
