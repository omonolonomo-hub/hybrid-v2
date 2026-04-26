# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - AttributeError on Incorrect Attribute/Method Names
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bugs exist
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: hover card in combat_scene_alternative.py and click refresh in shop_scene.py
  - Test that hovering over a placed card in combat_scene_alternative.py crashes with `AttributeError: 'HexCard' object has no attribute 'card'` (from Bug Condition in design)
  - Test that clicking refresh button in shop_scene.py crashes with `AttributeError: 'Market' object has no attribute 'refresh_window'` (from Bug Condition in design)
  - Test that importing SHOP_CARD_SIZE and CARD_SIZE from asset_loader.py succeeds (verification - should pass)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS for bugs 1 and 2 (this is correct - it proves the bugs exist), PASSES for bug 3 (verification)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Functionality Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (other HexCard attributes, other Market methods, other combat/shop operations)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Test that accessing other HexCard attributes (front_image, back_image, position, hex_size, rotation) continues to work
  - Test that calling other Market methods (return_unsold, get_cards_for_player) continues to work
  - Test that combat_scene.py (not alternative) continues to work with card_data
  - Test that shop buy operations continue to work
  - Test that card property access through card_data (rotated_edges(), dominant_group(), passive_type, total_power()) continues to work
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for AttributeError crashes in combat and shop scenes

  - [x] 3.1 Implement the fixes
    - Fix combat_scene_alternative.py line 1904: Change `hex_card.card` to `hex_card.card_data`
    - Fix shop_scene.py line 546: Replace `market.refresh_window()` with `market._return_window(player.pid)` followed by `market.deal_market_window(player, n=5)`
    - Verify asset_loader.py constants are correctly imported (no change needed)
    - _Bug_Condition: isBugCondition(input) where input.action == "hover_card" OR input.action == "click_refresh"_
    - _Expected_Behavior: No AttributeError, correct attribute/method access (card_data, _return_window, deal_market_window)_
    - _Preservation: All other HexCard attributes, Market methods, combat/shop operations unchanged_
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - No AttributeError on Correct Attribute/Method Names
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Functionality Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
