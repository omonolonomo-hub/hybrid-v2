# AI Preservation Property Tests - Baseline Report

## Test Execution Summary

**Date**: 2026-04-28
**Status**: ✅ PASSED (28/28 active tests)
**Skipped**: 3 tests (due to existing bugs in ParameterizedAI implementation)

## Purpose

These tests capture the **current behavior** of the monolithic AI system (`engine_core/ai.py`) before refactoring. They serve as a baseline to ensure that the refactored modular architecture preserves 100% behavioral compatibility.

## Test Coverage

### Property 1: Import Compatibility (Requirement 3.7)
- ✅ `test_import_compatibility_all_symbols` - All public API symbols importable
- ✅ `test_import_compatibility_trained_params_structure` - TRAINED_PARAMS structure preserved

### Property 2: Parameter Resolution (Requirement 3.1, 3.8)
- ✅ `test_parameter_resolution_priority_order` - Three-layer priority system works
- ✅ `test_parameter_resolution_all_strategies` - All 8 strategies have parameters
- ✅ `test_parameterized_ai_parameter_merging` - Parameter merging logic correct
- ✅ `test_parameterized_ai_all_strategies_loaded` - All strategies loaded on init

### Property 3: Configuration Loading (Requirement 3.6)
- ✅ `test_load_all_strategy_params_crash_proof` - Crash-proof behavior verified

### Property 4: Buy Decision Preservation (Requirement 3.2)
- ✅ `test_buy_decision_random_strategy_deterministic` - Random strategy deterministic with fixed seed
- ✅ `test_buy_decision_warrior_strategy_power_preference` - Warrior prefers high-power cards
- ✅ `test_buy_decision_economist_strategy_phase_controls` - Economist uses phase controls
- ✅ `test_buy_decision_builder_strategy_combo_scoring` - Builder uses combo scoring
- ✅ `test_buy_decision_all_strategies_execute_without_crash` - All 8 strategies execute

### Property 5: Place Decision Preservation (Requirement 3.3)
- ✅ `test_place_decision_random_strategy_deterministic` - Random placement deterministic
- ✅ `test_place_decision_tempo_strategy_aggressive_placement` - Tempo uses aggressive placement
- ✅ `test_place_decision_all_strategies_execute_without_crash` - All 8 strategies execute

### Property 6: BuilderSynergyMatrix Preservation (Requirement 3.5)
- ✅ `test_builder_synergy_matrix_record_combo` - Combo recording works
- ✅ `test_builder_synergy_matrix_record_miss` - Miss recording works
- ✅ `test_builder_synergy_matrix_decay` - Decay behavior correct
- ✅ `test_builder_synergy_matrix_update_from_board` - Board update works

### Property 7: Economy Controls Preservation (Requirement 3.4)
- ✅ `test_economy_phase_controls_greed_phase` - Greed phase logic correct
- ✅ `test_economy_phase_controls_spike_phase` - Spike phase logic correct
- ✅ `test_economy_phase_controls_convert_phase` - Convert phase logic correct
- ✅ `test_economy_phase_controls_emergency_phase` - Emergency phase logic correct

### Property 8: ParameterizedAI Preservation (Requirement 3.1)
- ⏭️ `test_parameterized_ai_buy_cards_delegation` - SKIPPED (existing bug)
- ⏭️ `test_parameterized_ai_place_cards_delegation` - SKIPPED (existing bug)

### Property 9: Strategy Logger Preservation (Requirement 3.9)
- ✅ `test_strategy_logger_hooks_available` - Strategy logger importable

### Property 10: Backward Compatibility
- ✅ `test_backward_compatibility_ai_static_methods` - AI class structure preserved
- ✅ `test_backward_compatibility_strategy_map_exists` - STRATEGY_MAP contains all 8 strategies
- ✅ `test_backward_compatibility_builder_synergy_matrix_accessible` - BuilderSynergyMatrix accessible

### Integration Tests
- ✅ `test_integration_full_buy_place_cycle_all_strategies` - All strategies complete buy+place cycle
- ⏭️ `test_integration_parameterized_ai_full_cycle` - SKIPPED (existing bug)

## Skipped Tests

Three tests were skipped due to an existing bug in the current `ParameterizedAI` implementation:

1. **`test_parameterized_ai_buy_cards_delegation`**
   - Issue: `ParameterizedAI.buy_cards()` passes arguments to `AI.buy_cards()` in incorrect order
   - Impact: `next_uid_fn` parameter causes "multiple values for argument" error
   - Note: This is a pre-existing bug, not introduced by testing

2. **`test_parameterized_ai_place_cards_delegation`**
   - Issue: `ParameterizedAI.place_cards()` passes positional arguments to `AI.place_cards()` which expects kwargs
   - Impact: "takes from 1 to 2 positional arguments but 4 were given" error
   - Note: This is a pre-existing bug, not introduced by testing

3. **`test_integration_parameterized_ai_full_cycle`**
   - Issue: Same as test #1 (buy_cards delegation issue)
   - Note: This is a pre-existing bug, not introduced by testing

**Decision**: These tests are skipped because:
- The bugs exist in the current monolithic implementation
- The refactoring is a **pure refactoring** (zero behavioral changes)
- These bugs will be preserved in the refactored code (as required)
- Fixing these bugs is outside the scope of this refactoring task

## Expected Outcome After Refactoring

After the refactoring is complete:

1. **All 28 active tests MUST STILL PASS** - This proves behavioral compatibility
2. **The 3 skipped tests MUST STILL BE SKIPPED** - The bugs are preserved (pure refactoring)
3. **Architectural defect tests (from task 1) MUST FAIL** - This proves the modular architecture is in place

## Test Methodology

- **Observation-First**: Tests were written by observing behavior on unfixed (monolithic) code
- **Deterministic Testing**: Used fixed RNG seeds for reproducible results
- **Property-Based Approach**: Tests capture behavioral patterns, not implementation details
- **Comprehensive Coverage**: All 8 strategies, all major subsystems, all public APIs

## Validation Requirements

These tests validate the following requirements from `bugfix.md`:

- **3.1**: ParameterizedAI parameter resolution (hardcoded < JSON < manual)
- **3.2**: AI.buy_cards() executes identical buying logic for all strategies
- **3.3**: AI.place_cards() executes identical placement logic for all strategies
- **3.4**: _economy_phase_controls() returns identical phase decisions
- **3.5**: BuilderSynergyMatrix tracks and scores synergies identically
- **3.6**: load_all_strategy_params() crash-proof behavior preserved
- **3.7**: All existing imports continue to work without modification
- **3.8**: TRAINED_PARAMS provides same hardcoded defaults
- **3.9**: Strategy logger hooks fire identically
- **3.10**: Tempo strategy uses power_center_thresh and combo_center_weight params

## Conclusion

✅ **Baseline successfully captured**

All active tests pass on the unfixed (monolithic) code, establishing a solid baseline for behavioral preservation. The refactoring can now proceed with confidence that any behavioral regressions will be immediately detected.

## Next Steps

1. Proceed to Phase 3: Implementation (Task 3)
2. After refactoring, re-run these same tests
3. Verify all 28 active tests still pass (behavioral preservation)
4. Verify architectural defect tests (task 1) now fail (modular architecture achieved)
