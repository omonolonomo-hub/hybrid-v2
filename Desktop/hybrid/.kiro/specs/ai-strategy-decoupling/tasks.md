# Implementation Plan - AI Strategy Decoupling

## Overview

This is a pure refactoring task that decouples the monolithic `engine_core/ai.py` (55KB, 1400+ lines) into a modular architecture with 13 separate modules. The refactoring follows the Strategy pattern and maintains 100% behavioral compatibility — zero logic changes, zero new features, zero parameter tuning.

**Key Principle**: This is NOT a bugfix in the traditional sense. There is no "broken behavior" to fix. Instead, we are fixing architectural defects (violation of Open/Closed Principle, tight coupling, eager loading) while preserving all existing behavior.

---

## Phase 1: Exploration Tests (Verify Architectural Defects Exist)

- [x] 1. Write architectural defect exploration tests (BEFORE refactoring)
  - **Property 1: Bug Condition** - Monolithic Architecture Defects
  - **CRITICAL**: These tests MUST PASS on unfixed code - passing confirms the architectural defects exist
  - **DO NOT attempt to fix the tests or the code when they pass**
  - **NOTE**: These tests encode the expected modular architecture - they will validate the refactoring when they fail after implementation
  - **GOAL**: Confirm the architectural defects exist in the current codebase
  - Test that all 8 strategies exist in a single `engine_core/ai.py` file
  - Test that `engine_core/ai.py` file size is >= 55KB (confirms monolithic structure)
  - Test that importing `AI` loads `BuilderSynergyMatrix` even when not using builder strategy (confirms eager loading)
  - Test that adding a new strategy would require modifying `engine_core/ai.py` (confirms Open/Closed violation)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this is correct - it proves the architectural defects exist)
  - Document findings: "Confirmed monolithic structure with all strategies in single file, eager loading of all dependencies, and violation of Open/Closed Principle"
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

---

## Phase 2: Preservation Tests (Capture Baseline Behavior)

- [x] 2. Write preservation property tests (BEFORE refactoring)
  - **Property 2: Preservation** - Behavioral Compatibility
  - **IMPORTANT**: Follow observation-first methodology
  - **CRITICAL**: These tests capture the CURRENT behavior that must be preserved
  - Observe behavior on UNFIXED code for all 8 strategies
  - Write property-based tests capturing observed behavior patterns
  - Property-based testing generates many test cases for stronger guarantees
  - Test areas to cover:
    - **Buy Decision Preservation**: For each strategy (random, warrior, economist, builder, evolver, balancer, rare_hunter, tempo), verify `buy_cards()` makes identical purchasing decisions given the same player state and market
    - **Place Decision Preservation**: For each strategy, verify `place_cards()` makes identical placement decisions given the same player state and hand
    - **Parameter Resolution Preservation**: Verify `ParameterizedAI` resolves parameters identically (hardcoded defaults < JSON overrides < manual params)
    - **Strategy Logger Preservation**: Verify strategy logger hooks fire at the same points with identical data
    - **BuilderSynergyMatrix Preservation**: Verify builder's synergy matrix updates and scores identically
    - **Economy Controls Preservation**: Verify `_economy_phase_controls()` returns identical phase decisions for economist and builder
    - **Import Compatibility Preservation**: Verify `from engine_core.ai import AI, ParameterizedAI, TRAINED_PARAMS, load_all_strategy_params` works
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

---

## Phase 3: Implementation (Refactor to Modular Architecture)

- [x] 3. Refactor AI module to modular architecture

  - [ ] 3.1 Create `engine_core/ai/` directory structure
    - Create `engine_core/ai/` directory
    - Create `engine_core/ai/strategies/` subdirectory
    - _Bug_Condition: All strategies exist in single monolithic file_
    - _Expected_Behavior: Each strategy exists in its own module under `engine_core/ai/strategies/`_
    - _Preservation: All existing imports must continue to work_
    - _Requirements: 2.1, 2.2, 3.7_

  - [ ] 3.2 Create `engine_core/ai/config.py` (configuration module)
    - Move `TRAINED_PARAMS` dictionary from `ai.py`
    - Move `load_all_strategy_params()` function
    - Move `load_strategy_params()` function (deprecated but kept for backward compat)
    - Move `AIConfigError` exception class
    - Preserve crash-proof behavior (returns `{}` on any error)
    - Preserve all error handling and logging
    - _Bug_Condition: Configuration mixed with strategy implementations_
    - _Expected_Behavior: Configuration isolated in dedicated module_
    - _Preservation: Parameter loading behavior must be identical_
    - _Requirements: 2.1, 3.6, 3.8_

  - [ ] 3.3 Create `engine_core/ai/utils.py` (shared utilities)
    - Move `MAX_LOOKAHEAD_CARDS`, `MAX_COORD_CHECK`, `PLACEMENT_TIME_BUDGET_S` constants
    - Move `_economy_phase_controls()` function (used by economist and builder)
    - Move `_get_param_with_fallback()` function
    - Preserve all function signatures and return types
    - Add necessary imports (`Card`, `Player`, `CARD_COSTS`, etc.)
    - _Bug_Condition: Shared utilities buried in monolithic AI class_
    - _Expected_Behavior: Shared utilities accessible through common module_
    - _Preservation: Economy phase logic must be identical_
    - _Requirements: 2.5, 3.4_

  - [ ] 3.4 Create `engine_core/ai/base.py` (strategy interface and dispatcher)
    - Move `BaseStrategy` abstract class
    - Move `AI` class with `buy_cards()` and `place_cards()` static methods
    - Create `STRATEGY_MAP` dictionary (will be populated after strategy modules are created)
    - Import strategy classes from `strategies/` submodules (add after strategy modules exist)
    - Preserve dispatch logic: `STRATEGY_MAP.get(strat_name, STRATEGY_MAP["random"])`
    - _Bug_Condition: Strategy interface mixed with implementations_
    - _Expected_Behavior: Clean separation of interface and dispatcher_
    - _Preservation: Dispatch behavior must be identical_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [ ] 3.5 Create `engine_core/ai/strategies/random.py`
    - Create `RandomStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_random()` as module-level function
    - Move `_place_smart_default()` as module-level function
    - Update `RandomStrategy.buy_cards()` to call `_buy_random()`
    - Update `RandomStrategy.place_cards()` to call `_place_smart_default()`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `PLACE_PER_TURN`, `get_strategy_logger`
    - _Bug_Condition: Random strategy coupled in monolithic file_
    - _Expected_Behavior: Random strategy in dedicated module_
    - _Preservation: Random buying and placement logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3_

  - [ ] 3.6 Create `engine_core/ai/strategies/warrior.py`
    - Create `WarriorStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_warrior()` as module-level function
    - Update `WarriorStrategy.buy_cards()` to call `_buy_warrior()`
    - Update `WarriorStrategy.place_cards()` to import and call `_place_smart_default` from `random.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`
    - _Bug_Condition: Warrior strategy coupled in monolithic file_
    - _Expected_Behavior: Warrior strategy in dedicated module_
    - _Preservation: Warrior buying logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3_

  - [ ] 3.7 Create `engine_core/ai/strategies/economist.py`
    - Create `EconomistStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_economist()` as module-level function
    - Update `EconomistStrategy.buy_cards()` to call `_buy_economist()`
    - Update `EconomistStrategy.place_cards()` to import and call `_place_smart_default` from `random.py`
    - Import `_economy_phase_controls` from `utils.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`
    - _Bug_Condition: Economist strategy coupled in monolithic file_
    - _Expected_Behavior: Economist strategy in dedicated module_
    - _Preservation: Economist phase-aware buying logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.4_

  - [ ] 3.8 Create `engine_core/ai/strategies/builder.py`
    - Move `BuilderSynergyMatrix` class (entire class with all methods)
    - Create `BuilderStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_builder()` as module-level function
    - Move `_place_fast_synergy()` as module-level function
    - Move `_place_combo_optimized()` as module-level function
    - Update `BuilderStrategy.buy_cards()` to call `_buy_builder()`
    - Update `BuilderStrategy.place_cards()` to call `_place_fast_synergy()`
    - Import `_economy_phase_controls` from `utils.py`
    - Import `_get_param_with_fallback` from `utils.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `STAT_TO_GROUP`, `RARITY_TAVAN`, `get_strategy_logger`, `defaultdict`, `time`
    - _Bug_Condition: Builder strategy and synergy matrix coupled in monolithic file, loaded even when not used_
    - _Expected_Behavior: Builder strategy in dedicated module, synergy matrix loaded only when builder is used_
    - _Preservation: Builder combo scoring and synergy matrix behavior must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3, 3.5_

  - [ ] 3.9 Create `engine_core/ai/strategies/evolver.py`
    - Create `EvolverStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_evolver()` as module-level function
    - Update `EvolverStrategy.buy_cards()` to call `_buy_evolver()`
    - Update `EvolverStrategy.place_cards()` to import and call `_place_smart_default` from `random.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`
    - _Bug_Condition: Evolver strategy coupled in monolithic file_
    - _Expected_Behavior: Evolver strategy in dedicated module_
    - _Preservation: Evolver evolution-aware buying logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3_

  - [ ] 3.10 Create `engine_core/ai/strategies/balancer.py`
    - Create `BalancerStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_balancer()` as module-level function
    - Update `BalancerStrategy.buy_cards()` to call `_buy_balancer()`
    - Update `BalancerStrategy.place_cards()` to import and call `_place_smart_default` from `random.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`, `defaultdict`
    - _Bug_Condition: Balancer strategy coupled in monolithic file_
    - _Expected_Behavior: Balancer strategy in dedicated module_
    - _Preservation: Balancer group diversity logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3_

  - [ ] 3.11 Create `engine_core/ai/strategies/rare_hunter.py`
    - Create `RareHunterStrategy` class inheriting from `BaseStrategy`
    - Move `_buy_rare_hunter()` as module-level function
    - Update `RareHunterStrategy.buy_cards()` to call `_buy_rare_hunter()`
    - Update `RareHunterStrategy.place_cards()` to import and call `_place_smart_default` from `random.py`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`
    - _Bug_Condition: Rare hunter strategy coupled in monolithic file_
    - _Expected_Behavior: Rare hunter strategy in dedicated module_
    - _Preservation: Rare hunter high-rarity chasing logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3_

  - [ ] 3.12 Create `engine_core/ai/strategies/tempo.py`
    - Create `TempoStrategy` class inheriting from `BaseStrategy`
    - Move `_place_aggressive()` as module-level function
    - Update `TempoStrategy.buy_cards()` to import and call `_buy_warrior` from `warrior.py`
    - Update `TempoStrategy.place_cards()` to call `_place_aggressive()`
    - Add imports: `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `PLACE_PER_TURN`, `get_strategy_logger`
    - _Bug_Condition: Tempo strategy coupled in monolithic file_
    - _Expected_Behavior: Tempo strategy in dedicated module_
    - _Preservation: Tempo aggressive placement logic must be identical_
    - _Requirements: 2.1, 2.3, 2.4, 3.2, 3.3, 3.10_

  - [ ] 3.13 Create `engine_core/ai/strategies/__init__.py`
    - Create empty `__init__.py` file for strategies package
    - This makes `engine_core/ai/strategies/` a proper Python package
    - _Bug_Condition: N/A (new file)_
    - _Expected_Behavior: Strategies directory is a proper Python package_
    - _Preservation: N/A_
    - _Requirements: 2.1_

  - [ ] 3.14 Update `engine_core/ai/base.py` to import all strategies
    - Import all strategy classes from `strategies/` submodules
    - Populate `STRATEGY_MAP` dictionary with strategy instances
    - Verify dispatch logic works with new imports
    - _Bug_Condition: Strategy map references strategies in monolithic file_
    - _Expected_Behavior: Strategy map references modular strategy implementations_
    - _Preservation: Strategy dispatch must work identically_
    - _Requirements: 2.2, 3.1, 3.2, 3.3_

  - [ ] 3.15 Create `engine_core/ai/parameterized.py`
    - Move `ParameterizedAI` class (entire class with all methods)
    - Import `AI` from `base.py`
    - Import `load_all_strategy_params` from `config.py`
    - Import `TRAINED_PARAMS` from `config.py`
    - Preserve parameter merging logic (defaults < JSON < manual)
    - Preserve `get_param()` method behavior
    - _Bug_Condition: ParameterizedAI coupled in monolithic file_
    - _Expected_Behavior: ParameterizedAI in dedicated module_
    - _Preservation: Parameter resolution must be identical_
    - _Requirements: 2.1, 3.1, 3.6, 3.8_

  - [ ] 3.16 Create `engine_core/ai/__init__.py` (public API)
    - Import `AI` from `base.py`
    - Import `ParameterizedAI` from `parameterized.py`
    - Import `TRAINED_PARAMS`, `load_all_strategy_params`, `load_strategy_params`, `AIConfigError` from `config.py`
    - Define `__all__` list with all public exports
    - Verify `from engine_core.ai import AI, ParameterizedAI` works
    - _Bug_Condition: Public API exposed through monolithic file_
    - _Expected_Behavior: Public API maintained through `__init__.py` for backward compatibility_
    - _Preservation: All existing imports must work without modification_
    - _Requirements: 2.1, 3.7_

  - [ ] 3.17 Verify all external imports still work
    - Search codebase for `from engine_core.ai import` statements
    - Verify all imports resolve correctly with new structure
    - Test that `from engine_core.ai import AI, ParameterizedAI, TRAINED_PARAMS` works
    - Test that no code references `engine_core.ai.AI` directly (should use `engine_core.ai.AI` via `__init__.py`)
    - _Bug_Condition: External code may reference monolithic file directly_
    - _Expected_Behavior: All external imports work through new `__init__.py`_
    - _Preservation: Zero changes required to external code_
    - _Requirements: 3.7_

  - [ ] 3.18 Delete `engine_core/ai.py` (monolithic file)
    - **CRITICAL**: Only delete after all previous sub-tasks are complete
    - Verify all tests pass with new structure
    - Verify all external imports work
    - Delete `engine_core/ai.py`
    - _Bug_Condition: Monolithic file exists_
    - _Expected_Behavior: Monolithic file removed, modular structure in place_
    - _Preservation: All functionality preserved in new modules_
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.19 Verify exploration tests now fail (confirming fix)
    - **Property 1: Expected Behavior** - Modular Architecture Achieved
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected modular architecture
    - When these tests fail, it confirms the modular architecture is achieved
    - Run architectural defect tests from step 1
    - **EXPECTED OUTCOME**: Tests FAIL (confirms modular architecture is in place)
    - Verify that strategies are now in separate modules
    - Verify that file size check fails (no single 55KB file)
    - Verify that importing `AI` does NOT load `BuilderSynergyMatrix`
    - Verify that new strategies can be added without modifying existing files
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.20 Verify preservation tests still pass (confirming no regressions)
    - **Property 2: Preservation** - Behavioral Compatibility Maintained
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify all 8 strategies produce identical buy decisions
    - Verify all 8 strategies produce identical place decisions
    - Verify parameter resolution is identical
    - Verify strategy logger hooks fire identically
    - Verify `BuilderSynergyMatrix` behavior is identical
    - Verify `_economy_phase_controls()` returns identical results
    - Verify all imports work without modification
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

---

## Phase 4: Final Validation

- [x] 4. Checkpoint - Ensure all tests pass and refactoring is complete
  - Run full test suite (unit tests, integration tests, property-based tests)
  - Verify all 8 strategies work correctly in game simulations
  - Verify no performance regressions (import time, runtime performance)
  - Verify documentation is updated (if any references to old structure exist)
  - Ask the user if questions arise or if additional validation is needed
  - _Requirements: All requirements (1.1-3.10)_

---

## Notes

**Testing Strategy:**
- Phase 1 tests confirm the architectural defects exist (tests PASS on unfixed code)
- Phase 2 tests capture baseline behavior to preserve (tests PASS on unfixed code)
- Phase 3 implements the refactoring
- Phase 3.19 verifies architectural defects are fixed (Phase 1 tests now FAIL)
- Phase 3.20 verifies behavior is preserved (Phase 2 tests still PASS)

**Key Constraints:**
- This is a pure refactoring - zero behavioral changes
- All existing imports must continue to work
- No new features, no parameter tuning, no logic changes
- Property-based testing is recommended for preservation checking
- Exploration tests use "Bug Condition" terminology but verify architectural defects, not runtime bugs

**Module Dependencies:**
- `config.py` has no internal dependencies (only stdlib and external imports)
- `utils.py` depends on `config.py` (for parameter access)
- `base.py` depends on all strategy modules (for `STRATEGY_MAP`)
- Strategy modules depend on `base.py` (for `BaseStrategy`) and `utils.py` (for shared functions)
- `parameterized.py` depends on `base.py` and `config.py`
- `__init__.py` depends on `base.py`, `parameterized.py`, and `config.py`

**Creation Order:**
1. Create directory structure
2. Create `config.py` (no dependencies)
3. Create `utils.py` (depends on config)
4. Create `base.py` (without strategy imports initially)
5. Create all strategy modules (depend on base and utils)
6. Update `base.py` to import strategies and populate `STRATEGY_MAP`
7. Create `parameterized.py` (depends on base and config)
8. Create `__init__.py` (depends on base, parameterized, config)
9. Delete `ai.py`
