# Implementation Plan

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Fallback Path Resolution
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Test with cards.json placed only in engine_core/ directory (same as card.py), not at ../assets/data/cards.json
  - Test that build_card_pool() successfully loads cards.json from the local directory when it's not at the original path
  - The test assertions should verify: result is List[Card], len(result) > 0, no FileNotFoundError raised
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS with FileNotFoundError (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause (e.g., "build_card_pool() raises FileNotFoundError when cards.json is only in engine_core/ directory")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Original Path Compatibility
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code: build_card_pool() successfully loads from ../assets/data/cards.json
  - Observe: Card objects have correct attributes (name, category, rarity, stats, passive_type)
  - Observe: Function returns List[Card] with all cards from JSON file
  - Write property-based tests capturing observed behavior patterns: for all environments where cards.json exists at original path, result equals the cards loaded from that path
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 3. Fix for cards.json path resolution

  - [ ] 3.1 Implement the fallback mechanism
    - Calculate base_dir as os.path.dirname(os.path.abspath(__file__))
    - Construct local_path as os.path.join(base_dir, "cards.json")
    - Check if local_path exists using os.path.exists()
    - If local_path exists, use it as json_path
    - Otherwise, fall back to original path: os.path.join(base_dir, "..", "assets", "data", "cards.json")
    - Keep all JSON loading and card creation logic unchanged
    - _Bug_Condition: isBugCondition(environment) where NOT file_exists(base_dir + "/../assets/data/cards.json") AND file_exists(base_dir + "/cards.json")_
    - _Expected_Behavior: build_card_pool() returns List[Card] without FileNotFoundError when cards.json is in local directory_
    - _Preservation: When cards.json exists at original path, function loads from original path with identical Card objects_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3_

  - [ ] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Fallback Path Resolution
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [ ] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Original Path Compatibility
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
