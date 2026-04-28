# Implementation Plan

## Overview

This task list implements the fix for the tier-milestone-ui-separation bug, which violates separation of concerns by placing milestone checking logic in the UI layer. The fix moves milestone detection to the ShopController's command flow and uses the SignalBus event system to notify the UI layer.

**Key Changes:**
1. Add `milestone_reached` signal to SignalBus
2. Move milestone detection logic from ShopScene to ShopController
3. Emit signals when milestones are reached during controller actions
4. Convert ShopScene's `_check_tier_milestones()` into a signal handler

---

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Milestone Detection in UI Layer
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate milestone checking occurs in UI layer during frame updates
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: milestone checking called from `ShopScene.update()` rather than from controller action methods
  - Test that `_check_tier_milestones()` is called from `ShopScene.update()` every frame (Bug Condition from design)
  - Test that milestone detection does NOT occur in `ShopController.handle_shop_action()` or `place_card_from_hand()`
  - Test that `milestone_reached` signal is NOT emitted when milestones are reached
  - Test that milestone detection is delayed until the next frame update after an action
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found:
    - Milestone checking occurs in UI layer (`ShopScene._check_tier_milestones()`)
    - Milestone checking is called every frame in `update()` method
    - No `milestone_reached` signal is emitted
    - Milestone detection is delayed until the next frame update
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Milestone Display Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for milestone display scenarios
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - Tier milestone floating text format: `"{TIER_SHORT} +{bonus}pts UP"` (e.g., "MIND +3pts UP")
    - Copy milestone floating text: "2-COPY POWER UP" or "3-COPY POWER UP"
    - Floating text positioning at board center with camera offset adjustments
    - Tier milestone colors: MIND (Colors.MIND), CONNECTION (Colors.CONNECTION), EXISTENCE (Colors.EXISTENCE)
    - Copy milestone color: Colors.PLATINUM
    - Font sizes: tier milestones (13), copy milestones (15)
    - Milestone deduplication (no duplicate floating text for the same milestone)
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for tier-milestone-ui-separation

  - [x] 3.1 Add milestone_reached signal to SignalBus
    - Open `engine_core/signals.py`
    - Add `self.milestone_reached = Signal()` to `SignalBus.__init__()` method
    - Follow the pattern of existing signals (`board_mutated`, `economy_changed`, etc.)
    - Signal will carry milestone data: type (tier/copy), group/card name, bonus points, etc.
    - _Bug_Condition: isBugCondition(execution_context) where execution_context.method == "_check_tier_milestones" AND execution_context.layer == "UI" AND execution_context.caller == "ShopScene.update()" AND execution_context.frequency == "every_frame"_
    - _Expected_Behavior: Milestone detection occurs in ShopController layer and emits milestone_reached signal through SignalBus_
    - _Preservation: All existing SignalBus signals continue to function_
    - _Requirements: 2.2, 3.6_

  - [x] 3.2 Add milestone detection logic to ShopController
    - Open `v2/core/shop_controller.py`
    - Add milestone tracking state to `__init__()` method:
      - `self._prev_group_counts: Dict[str, int] = {}` - tracks previous synergy counts
      - `self._seen_copy_milestones: Set[Tuple[str, str]] = set()` - tracks seen copy milestones
    - Create private method `_check_and_emit_milestones()` that:
      - Compares current synergy state to previous state (from `self._prev_group_counts`)
      - Detects tier milestones (2, 3, 4, 5, 6 cards of same group)
      - Detects copy milestones (2-copy or 3-copy power-ups)
      - Emits `milestone_reached` signal with appropriate data (type, group/card, bonus, etc.)
      - Updates `self._prev_group_counts` and `self._seen_copy_milestones` after checking
    - Access SignalBus through `self._game_state._adapter._engine.signals` (following GameState pattern)
    - _Bug_Condition: isBugCondition(execution_context) from design_
    - _Expected_Behavior: Milestone detection occurs in controller layer after state-mutating actions_
    - _Preservation: Milestone detection logic produces same results as original implementation_
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Integrate milestone checking with controller action methods
    - In `handle_shop_action()` method:
      - Call `self._check_and_emit_milestones()` after "buy" action completes successfully
      - Only call if `result == ActionResult.OK` or similar success condition
    - In `place_card_from_hand()` method:
      - Call `self._check_and_emit_milestones()` after card placement succeeds
      - Only call if `result == ActionResult.OK`
    - Consider other methods that might trigger milestones (reroll, etc.) and add checks if needed
    - _Bug_Condition: isBugCondition(execution_context) from design_
    - _Expected_Behavior: Milestone checking occurs immediately after controller actions complete_
    - _Preservation: Milestone timing is improved (immediate vs delayed to next frame)_
    - _Requirements: 2.1, 2.2_

  - [x] 3.4 Convert ShopScene milestone method to signal handler
    - Open `v2/scenes/shop.py`
    - Rename `_check_tier_milestones()` to `_on_milestone_reached(self, **kwargs)`
    - Convert to signal handler:
      - Accept `**kwargs` parameter containing milestone data from signal
      - Remove state comparison logic (now handled in controller)
      - Keep floating text spawning logic
      - Use signal data to determine text content, position, color
      - Extract milestone type, group/card name, bonus points from kwargs
    - Preserve all floating text formatting:
      - Tier milestone format: `"{TIER_SHORT} +{bonus}pts UP"`
      - Copy milestone format: "2-COPY POWER UP" or "3-COPY POWER UP"
      - Positioning at board center with camera offset
      - Colors: MIND, CONNECTION, EXISTENCE for tiers; PLATINUM for copies
      - Font sizes: 13 for tiers, 15 for copies
    - _Bug_Condition: isBugCondition(execution_context) from design_
    - _Expected_Behavior: UI layer responds to milestone_reached signal instead of polling_
    - _Preservation: Floating text display behavior remains identical_
    - _Requirements: 2.3, 3.1, 3.2, 3.3_

  - [x] 3.5 Update signal connections in ShopScene lifecycle methods
    - In `on_enter()` method:
      - Add signal connection: `self.controller._game_state._adapter._engine.signals.milestone_reached.connect(self._on_milestone_reached)`
      - Follow the pattern used for `board_mutated` signal connection
    - In `on_exit()` method:
      - Add signal disconnection: `self.controller._game_state._adapter._engine.signals.milestone_reached.disconnect(self._on_milestone_reached)`
      - Follow the pattern used for `board_mutated` signal disconnection
    - Remove `self._check_tier_milestones()` call from `update()` method
    - Remove `_prev_group_counts` and `_seen_copy_milestones` initialization from ShopScene (now in controller)
    - _Bug_Condition: isBugCondition(execution_context) from design_
    - _Expected_Behavior: UI layer subscribes to milestone_reached signal instead of polling every frame_
    - _Preservation: Signal connection/disconnection follows existing patterns_
    - _Requirements: 2.3, 2.4, 3.5, 3.6_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Milestone Detection in Controller Layer
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied:
      - Milestone detection occurs in ShopController layer (not UI layer)
      - `milestone_reached` signal is emitted when milestones are reached
      - Milestone detection happens immediately after controller actions (not delayed to next frame)
      - `_check_tier_milestones()` is no longer called from `ShopScene.update()`
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Milestone Display Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix:
      - Tier milestone floating text format unchanged
      - Copy milestone floating text format unchanged
      - Floating text positioning unchanged
      - Colors unchanged (MIND, CONNECTION, EXISTENCE, PLATINUM)
      - Font sizes unchanged (13 for tiers, 15 for copies)
      - Milestone deduplication still works
      - Other SignalBus signals still function
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run all tests (bug condition exploration test + preservation tests)
  - Verify bug condition test now passes (milestone detection in controller layer)
  - Verify preservation tests still pass (floating text display unchanged)
  - Verify no regressions in other game systems (board rendering, shop actions, etc.)
  - If any tests fail, investigate and fix before proceeding
  - Ask the user if questions arise or if manual testing is needed
