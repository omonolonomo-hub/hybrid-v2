# Implementation Plan

## Bug 1: UIAdapter.build_public_state() Performance Leak

- [x] 1. Write bug condition exploration test for cache invalidation performance leak
  - **Property 1: Bug Condition** - Unnecessary BFS on Non-Board Signals
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate unnecessary BFS runs
  - **Scoped PBT Approach**: Test concrete failing cases: economy_changed, inventory_changed, turn_started signals trigger BFS despite board unchanged
  - Test implementation details from Bug Condition in design:
    - Trigger economy_changed signal → Measure if SynergyCalculator.compute() BFS runs → Verify board unchanged
    - Trigger inventory_changed signal → Measure if SynergyCalculator.compute() BFS runs → Verify board unchanged
    - Trigger turn_started signal → Measure if SynergyCalculator.compute() BFS runs → Verify board unchanged
    - Trigger 15-20 signals in sequence (simulating start_turn with AI purchases) → Count BFS runs → Verify multiple unnecessary BFS calls
  - The test assertions should match the Expected Behavior Properties from design (BFS only runs for board_mutated)
  - Run test on UNFIXED code in `v2/adapters/ui_adapter.py`
  - **EXPECTED OUTCOME**: Test FAILS with BFS running for non-board signals (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation unit tests for UIAdapter.build_public_state() (BEFORE implementing fix)
  - **Property 2: Preservation** - Full State Computation
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for full state computation (no cache exists)
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: build_public_state() with no cache produces complete state with BFS + DB + triple-iteration
    - Test 2: Synergy calculations return correct data
    - Test 3: Shop/hand/board card info returns correct data
  - Multiple explicit unit tests provide stronger guarantees than property-based tests for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [-] 3. Fix UIAdapter.build_public_state() performance leak

  - [x] 3.1 Replace monolithic cache with granular cache tracking in v2/adapters/ui_adapter.py
    - Replace single `_cache_valid` flag with granular cache storage
    - Add `_cached_public_state: Optional[PublicState]` to store full cached state
    - Add invalidation flags: `_synergy_stale: bool`, `_board_stale: bool`, `_shop_stale: bool`, `_hand_stale: bool`, `_hud_stale: bool`
    - Initialize all stale flags to True (force initial computation)
    - _Bug_Condition: isBugCondition(input) where input.signal IN [economy_changed, inventory_changed, turn_started] AND input.invalidates_entire_cache == True AND SynergyCalculator.compute() called unnecessarily_
    - _Expected_Behavior: Granular invalidation - only affected cache components recomputed_
    - _Preservation: Full state computation when no cache exists_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

  - [x] 3.2 Implement signal-to-cache mapping in signal handlers
    - Modify `_on_board_mutated()` to set only `_synergy_stale = True` + `_board_stale = True`
    - Modify `_on_economy_changed()` to set only `_hud_stale = True`
    - Modify `_on_inventory_changed()` to set only `_hand_stale = True`
    - Modify `_on_turn_started()` to set only `_shop_stale = True`
    - Note: turn_started affects turn number in HUD, but economy_changed fires for income anyway, so HUD gets invalidated naturally
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Implement selective recomputation in build_public_state()
    - Check each stale flag before recomputing
    - Only run SynergyCalculator.compute() BFS if `_synergy_stale == True`
    - Only fetch board card info if `_board_stale == True`
    - Only fetch shop data if `_shop_stale == True`
    - Only fetch hand card info if `_hand_stale == True`
    - Only fetch HUD data if `_hud_stale == True`
    - Reuse cached components for non-stale data from `_cached_public_state`:
      - If `_synergy_stale == False` → Reuse `_cached_public_state.active_player.synergy`
      - If `_board_stale == False` → Reuse `_cached_public_state.active_player.board_cards`, `board_rotations`, `board_card_info`
      - If `_shop_stale == False` → Reuse `_cached_public_state.active_player.shop`, `shop_card_info`
      - If `_hand_stale == False` → Reuse `_cached_public_state.active_player.hand`, `hand_card_info`
      - If `_hud_stale == False` → Reuse `_cached_public_state.active_player.hud`
    - Construct new PublicState with mix of cached and fresh components
    - Store new PublicState in `_cached_public_state`
    - Reset stale flags to False after recomputation
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Granular Cache Invalidation
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms BFS only runs for board_mutated)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Full State Computation
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation unit tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

- [x] 4. Write bug condition exploration test for redundant get_card_info() call
  - **Property 1: Bug Condition** - Redundant DB Lookup Despite Cache
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate redundant DB lookups
  - **Scoped Test Approach**: Test isolated mouse event handler logic with mock/spy on EngineAdapter.get_card_info()
  - Test implementation details from Bug Condition in design:
    - Populate _public_state.active_player.hand_card_info[idx] with card data
    - Simulate hand card click event
    - Verify EngineAdapter.get_card_info(card_name) is called despite cached data existing
    - Test multiple clicks on same card → Verify get_card_info() called multiple times
    - Test rapid clicks on different cards → Verify multiple redundant get_card_info() calls
  - The test assertions should match the Expected Behavior Properties from design (use cached data, no DB call)
  - Run test on UNFIXED code in `v2/scenes/shop.py` (or wherever hand card click is handled)
  - **EXPECTED OUTCOME**: Test FAILS with redundant get_card_info() calls (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.5, 1.6_

- [x] 5. Write preservation unit tests for card click actions (BEFORE implementing fix)
  - **Property 2: Preservation** - Card Click Actions
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for card click actions (drag, play, sell)
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: Card click triggers correct drag action
    - Test 2: Card click triggers correct play action
    - Test 3: Card click triggers correct sell action
    - Test 4: Other mouse events (board clicks, shop clicks) work correctly
  - Multiple explicit unit tests provide stronger guarantees for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.4, 3.5, 3.6_

- [x] 6. Fix MOUSEBUTTONDOWN redundant get_card_info() call

  - [x] 6.1 Add cache accessor method to retrieve cached card data
    - Create helper method `_get_cached_card_info(location: str, index: int) -> Optional[CardDataSnapshot]`
    - For location == "hand", retrieve from `self._current_public_state().active_player.hand_card_info`
    - Return cached CardDataSnapshot if index valid, else None
    - _Requirements: 2.5, 2.6_

  - [x] 6.2 Modify hand card click handler to use cached data
    - Replace direct `EngineAdapter.get_card_info(card_name)` call
    - Use `_get_cached_card_info("hand", idx)` instead
    - Add fallback: if cache miss (shouldn't happen), call `EngineAdapter.get_card_info()` for robustness
    - _Bug_Condition: isBugCondition(input) where input.type == MOUSEBUTTONDOWN AND input.target == hand_card AND cached_data_exists_in_cache_
    - _Expected_Behavior: Use cached data, no DB call_
    - _Preservation: Card click actions (drag, play, sell) work correctly_
    - _Requirements: 2.5, 2.6, 3.4, 3.5, 3.6_

  - [x] 6.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Use Cached Card Data
    - **IMPORTANT**: Re-run the SAME test from task 4 - do NOT write a new test
    - The test from task 4 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 4
    - **EXPECTED OUTCOME**: Test PASSES (confirms cached data used, no DB call)
    - _Requirements: 2.5, 2.6_

  - [x] 6.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Card Click Actions
    - **IMPORTANT**: Re-run the SAME tests from task 5 - do NOT write new tests
    - Run preservation unit tests from step 5
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 3: SceneManager Singleton Memory Leak

- [x] 7. Write bug condition exploration test for SceneManager memory leak
  - **Property 1: Bug Condition** - Singleton Prevents GC
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate memory leak
  - **Scoped Test Approach**: Test concrete failing cases using weakref pattern (reliable, deterministic)
  - Test implementation details from Bug Condition in design:
    - Use weakref pattern for reliable GC testing (not RAM measurement which is flaky):
      ```python
      import weakref, gc
      old_scene = ShopScene(gs)
      ref = weakref.ref(old_scene)
      sm.set_scene(new_scene)
      del old_scene
      gc.collect()
      assert ref() is None, "Old scene should be GC'd"
      ```
    - Test 1: Single scene transition → Verify old scene not GC'd (weakref still alive)
    - Test 2: Multiple scene transitions (3-4) → Verify multiple old scenes not GC'd
    - Test 3: Check if old GameState references survive → Verify GC blocked
    - Test 4: First set_scene() call with no old scene → Verify no null scene operations (edge case)
  - The test assertions should match the Expected Behavior Properties from design (old scene GC'd)
  - Run test on UNFIXED code in `v2/core/scene_manager.py`
  - **EXPECTED OUTCOME**: Test FAILS with weakref still alive (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.7, 1.8, 1.9, 1.10_

- [x] 8. Write preservation unit tests for SceneManager lifecycle (BEFORE implementing fix)
  - **Property 2: Preservation** - Scene Lifecycle
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for normal scene transitions
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: set_scene() calls on_exit() on old scene
    - Test 2: Scenes render and update correctly after transition
    - Test 3: Scene lifecycle methods (on_enter, on_exit, update, render) work correctly
    - Test 4: First set_scene() call with no old scene works correctly (no cleanup needed)
  - Multiple explicit unit tests provide stronger guarantees for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.7, 3.8, 3.9_

- [x] 9. Fix SceneManager singleton memory leak

  - [x] 9.1 Add explicit cleanup in set_scene() method in v2/core/scene_manager.py
    - Add check: if `self._current is not None` (only cleanup if current scene exists)
    - Call `self._current.on_exit()` as before
    - Null out reference: `self._current = None`
    - Delete fade surface if exists: `if hasattr(self, '_fade_surface') and self._fade_surface is not None: del self._fade_surface; self._fade_surface = None`
    - Then set new scene: `self._current = new_scene; self._current.on_enter()`
    - _Bug_Condition: isBugCondition(input) where input.old_scene EXISTS AND input.old_scene.references_not_cleared == True AND GC cannot reclaim memory_
    - _Expected_Behavior: Cleanup old scene (call on_exit(), null references, delete fade surface) before replacing_
    - _Preservation: Scene lifecycle (on_exit, on_enter, update, render) preserved_
    - _Requirements: 2.7, 2.8, 2.9, 2.10, 3.7, 3.8, 3.9_

  - [x] 9.2 Add dispose() class method for testing isolation
    - Create `@classmethod dispose(cls)` method
    - Check if `cls._instance is not None`
    - If instance exists and has current scene, call `cls._instance._current.on_exit()`
    - Set `cls._instance = None` to reset singleton
    - This replaces monkey-patching for test isolation
    - _Requirements: 2.9_

  - [x] 9.3 Update scene on_exit() methods to null heavy references
    - Ensure each scene's on_exit() nulls out:
      - GameState references
      - Pygame Surfaces
      - UI component references
    - This breaks reference cycles and allows GC to reclaim memory
    - _Requirements: 2.7, 2.8_

  - [x] 9.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Scene Cleanup on Transition
    - **IMPORTANT**: Re-run the SAME test from task 7 - do NOT write a new test
    - The test from task 7 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 7
    - **EXPECTED OUTCOME**: Test PASSES (confirms old scene GC'd, RAM stable)
    - _Requirements: 2.7, 2.8, 2.9, 2.10_

  - [x] 9.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Scene Lifecycle
    - **IMPORTANT**: Re-run the SAME tests from task 8 - do NOT write new tests
    - Run preservation unit tests from step 8
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 4: ShopController.handle_phase_change() Not Atomic

- [x] 10. Write bug condition exploration test for non-atomic phase transition
  - **Property 1: Bug Condition** - Phase Inconsistent on Exception
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate inconsistent phase state
  - **Scoped Test Approach**: Test concrete failing cases: inject exceptions at different points in sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn)
  - Test implementation details from Bug Condition in design:
    - Test 1: mirror_phase() succeeds → cleanup_dead_cards() throws exception → Verify phase already mirrored but turn not started (inconsistent state)
    - Test 2: mirror_phase() + cleanup_dead_cards() succeed → start_turn() throws exception → Verify phase inconsistent
    - Test 3: All steps succeed except reset_turn() → Verify phase inconsistent
    - Verify StateStore._phase is modified before sequence completes
    - Verify no rollback mechanism exists
  - The test assertions should match the Expected Behavior Properties from design (phase restored on exception)
  - Run test on UNFIXED code in `v2/core/shop_controller.py`
  - **EXPECTED OUTCOME**: Test FAILS with inconsistent phase state (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.11, 1.12, 1.13_

- [x] 11. Write preservation unit tests for successful phase transitions (BEFORE implementing fix)
  - **Property 2: Preservation** - Successful Phase Transitions
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for successful phase transitions (no exceptions)
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: Successful STATE_PREPARATION transition executes sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn) correctly
    - Test 2: Phase state updated correctly after transition
    - Test 3: Other ShopController methods work correctly
  - Multiple explicit unit tests provide stronger guarantees for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.10, 3.11, 3.12_

- [x] 12. Fix ShopController.handle_phase_change() atomicity

  - [x] 12.1 Wrap phase transition in try/except with rollback in v2/core/shop_controller.py
    - First, add get_phase() method to GameState class (v2/core/game_state.py):
      ```python
      def get_phase(self) -> str:
          return self._store.phase
      ```
    - This avoids expensive get_public_state() call which triggers full UIAdapter computation
    - Store previous phase: `previous_phase = self._game_state.get_phase()`
    - Note: Do NOT use `self._game_state.get_public_state().phase` - it's expensive (triggers BFS + DB + triple-iteration)
    - Wrap phase transition sequence in try/except block
    - In except block: restore phase with `self._game_state.mirror_phase(previous_phase)`
    - Re-raise exception for logging/debugging
    - Only StateStore._phase is rolled back (engine mutations like board/market are NOT undone - they are idempotent or logged)
    - _Bug_Condition: isBugCondition(input) where input.phase == "STATE_PREPARATION" AND exception_thrown_during_sequence == True AND StateStore._phase already modified_
    - _Expected_Behavior: Restore StateStore._phase to previous value on exception_
    - _Preservation: Successful phase transitions execute sequence correctly_
    - _Requirements: 2.11, 2.12, 2.13, 3.10, 3.11, 3.12_

  - [x] 12.2 Document rollback scope in comments
    - Add comment explaining only StateStore._phase is rolled back
    - Add comment explaining engine-level mutations (board, market) are NOT undone
    - Add comment explaining this is intentional: they are idempotent or logged
    - _Requirements: 2.11, 2.12, 2.13_

  - [x] 12.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Phase Rollback on Exception
    - **IMPORTANT**: Re-run the SAME test from task 10 - do NOT write a new test
    - The test from task 10 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 10
    - **EXPECTED OUTCOME**: Test PASSES (confirms phase restored on exception)
    - _Requirements: 2.11, 2.12, 2.13_

  - [x] 12.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Successful Phase Transitions
    - **IMPORTANT**: Re-run the SAME tests from task 11 - do NOT write new tests
    - Run preservation unit tests from step 11
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Bug 5: frozen=True Dataclass with Mutable Dicts

- [x] 13. Write bug condition exploration test for frozen dataclass with mutable dicts
  - **Property 1: Bug Condition** - Immutability Bypass
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate immutability bypass
  - **Scoped Test Approach**: Test concrete failing cases: attempt to mutate dict contents in frozen dataclass
  - Test implementation details from Bug Condition in design:
    - Test 1: Attempt `state.active_player.stats["bonus"] = 99` → Verify mutation allowed (should fail - mutation succeeds)
    - Test 2: Attempt `state.active_player.board_cards[coord]["hp"] = 999` → Verify nested dict mutation allowed (should fail - mutation succeeds)
    - Test 3: Mutate dict → Verify cache not invalidated → Verify stale data persists
    - Test 4: Serialize state with mutated dict → Verify temporary data persists in serialization
  - The test assertions should match the Expected Behavior Properties from design (TypeError raised on mutation attempt)
  - Run test on UNFIXED code in `v2/adapters/ui_adapter.py` (or wherever ActivePlayerViewState is defined)
  - **EXPECTED OUTCOME**: Test FAILS with mutation succeeding (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.14, 1.15, 1.16_

- [x] 14. Write preservation unit tests for dataclass read access (BEFORE implementing fix)
  - **Property 2: Preservation** - Dataclass Read Access
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for dataclass read access and operations
  - Write unit tests capturing observed behavior patterns from Preservation Requirements:
    - Test 1: Read access to stats, board_cards, copies_by_name returns correct values
    - Test 2: Dataclass equality checks work correctly
    - Test 3: Dataclass hashing works correctly
    - Test 4: Dataclass serialization works correctly
  - Multiple explicit unit tests provide stronger guarantees for this case
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.13, 3.14, 3.15_

- [x] 15. Fix frozen dataclass with mutable dicts

  - [x] 15.1 Import MappingProxyType in `v2/core/public_state.py` (ActivePlayerViewState lives here)
    - Add import: `from types import MappingProxyType`
    - _Requirements: 2.14, 2.15, 2.16_

  - [x] 15.2 Add __post_init__() to wrap dicts with MappingProxyType
    - Create `__post_init__(self)` method in ActivePlayerViewState dataclass
    - Wrap simple dicts with single MappingProxyType:
      - `object.__setattr__(self, 'stats', MappingProxyType(self.stats))`
      - `object.__setattr__(self, 'copies_by_name', MappingProxyType(self.copies_by_name))`
      - `object.__setattr__(self, 'shop_card_info', MappingProxyType(self.shop_card_info))`
      - `object.__setattr__(self, 'hand_card_info', MappingProxyType(self.hand_card_info))`
      - `object.__setattr__(self, 'board_card_info', MappingProxyType(self.board_card_info))`
    - Wrap nested dicts (both outer and inner) with MappingProxyType:
      - `object.__setattr__(self, 'board_cards', MappingProxyType({k: MappingProxyType(v) for k, v in self.board_cards.items()}))`
    - Note: object.__setattr__() bypasses frozen=True restriction during initialization
    - _Bug_Condition: isBugCondition(input) where input.frozen == True AND input.contains_mutable_dict == True AND dict_content_mutation_allowed == True_
    - _Expected_Behavior: TypeError raised on mutation attempt (e.g., state.active_player.stats["bonus"] = 99)_
    - _Preservation: Read access, equality checks, hashing, serialization work correctly_
    - _Requirements: 2.14, 2.15, 2.16, 3.13, 3.14, 3.15_

  - [x] 15.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Immutable Dict Enforcement
    - **IMPORTANT**: Re-run the SAME test from task 13 - do NOT write a new test
    - The test from task 13 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 13
    - **EXPECTED OUTCOME**: Test PASSES (confirms TypeError raised on mutation attempt)
    - _Requirements: 2.14, 2.15, 2.16_

  - [x] 15.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Dataclass Read Access
    - **IMPORTANT**: Re-run the SAME tests from task 14 - do NOT write new tests
    - Run preservation unit tests from step 14
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

## Final Checkpoint

- [x] 16. Checkpoint - Ensure all tests pass
  - Run all exploration tests (tasks 1, 4, 7, 10, 13) - should now PASS
  - Run all preservation tests (tasks 2, 5, 8, 11, 14) - should still PASS
  - Verify no regressions in existing functionality
  - Ensure all five bugs are fixed and validated
  - Ask the user if questions arise
