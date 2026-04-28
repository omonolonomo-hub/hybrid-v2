# AI Strategy Decoupling Bugfix Design

## Overview

The AI strategy system in `engine_core/ai.py` currently violates the Open/Closed Principle by housing all 8 strategy implementations in a single 55KB monolithic file. This design creates unnecessary coupling, makes the codebase difficult to extend, and loads resources (like `BuilderSynergyMatrix`) even when not needed.

This bugfix decouples the strategies into separate modules following the Strategy pattern, eliminating architectural defects while preserving all existing behavior. The refactoring transforms the monolithic structure into a modular architecture where:

- Each strategy lives in its own module under `engine_core/ai/strategies/`
- Shared utilities are extracted to `engine_core/ai/base.py` and `engine_core/ai/utils.py`
- The public API remains unchanged (`from engine_core.ai import AI, ParameterizedAI`)
- All existing imports continue to work without modification
- Zero behavioral changes — all strategies execute identically

**Key Architectural Principle:** This is a pure refactoring. No logic changes, no new features, no parameter tuning. The goal is to decouple the architecture while maintaining 100% behavioral compatibility.

## Glossary

- **Strategy Pattern**: Design pattern where algorithms are encapsulated in separate classes with a common interface, allowing runtime selection without conditional logic
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification — new strategies should be addable without editing existing code
- **Monolithic File**: A single large file containing multiple unrelated concerns, making maintenance difficult
- **Module**: A separate Python file containing related functionality
- **Public API**: The interface exposed to external code (`from engine_core.ai import ...`)
- **Backward Compatibility**: Ensuring existing code continues to work without modification
- **BaseStrategy**: Abstract interface defining `buy_cards()` and `place_cards()` methods that all strategies must implement
- **STRATEGY_MAP**: Dictionary mapping strategy names to strategy instances for runtime dispatch
- **ParameterizedAI**: Wrapper class providing parameter injection for all strategies
- **BuilderSynergyMatrix**: Session-level synergy memory used exclusively by the builder strategy
- **TRAINED_PARAMS**: Hardcoded default parameters for all strategies
- **load_all_strategy_params()**: Function loading strategy parameters from `trained_params.json`
- **_economy_phase_controls()**: Shared economy engine used by economist and builder strategies
- **Strategy Logger**: Logging system for tracking AI decisions during buy/place operations


## Bug Details

### Bug Condition

The bug manifests when the codebase structure violates the Open/Closed Principle by coupling all AI strategies in a single file. The `engine_core/ai.py` file contains 8 different strategy implementations (economist, warrior, builder, evolver, balancer, rare_hunter, tempo, random) along with shared utilities, configuration loading, and the `BuilderSynergyMatrix` class.

**Formal Specification:**
```
FUNCTION isBugCondition(codebase)
  INPUT: codebase structure
  OUTPUT: boolean
  
  RETURN (all_strategies_in_single_file(codebase, "engine_core/ai.py") == TRUE)
         AND (file_size(codebase, "engine_core/ai.py") >= 55000 bytes)
         AND (adding_new_strategy_requires_modifying_existing_file(codebase) == TRUE)
         AND (importing_any_strategy_loads_all_dependencies(codebase) == TRUE)
END FUNCTION
```

### Examples

**Example 1: Adding a New Strategy (Current Defect)**
- **Current Behavior**: Developer must open `engine_core/ai.py`, add a new `_buy_newstrategy()` method, add a new `NewStrategyStrategy` class, and update `STRATEGY_MAP`
- **Expected Behavior**: Developer creates `engine_core/ai/strategies/newstrategy.py`, implements the strategy, and registers it in `STRATEGY_MAP` without touching existing strategy files

**Example 2: Importing Builder Strategy (Current Defect)**
- **Current Behavior**: `from engine_core.ai import AI` loads the entire 55KB file including `BuilderSynergyMatrix`, all 8 strategy implementations, and all helper functions
- **Expected Behavior**: Importing `AI` loads only the base classes and dispatcher; `BuilderSynergyMatrix` is loaded only when builder strategy is actually used

**Example 3: Navigating to Economist Implementation (Current Defect)**
- **Current Behavior**: Developer opens `engine_core/ai.py` (1400+ lines), searches for `_buy_economist`, scrolls through unrelated code
- **Expected Behavior**: Developer opens `engine_core/ai/strategies/economist.py` directly, sees only economist-related code (~100 lines)

**Example 4: Shared Helper Function Reuse (Current Defect)**
- **Current Behavior**: `_economy_phase_controls()` is buried in the monolithic `AI` class; reusing it requires importing the entire AI module
- **Expected Behavior**: `_economy_phase_controls()` lives in `engine_core/ai/utils.py` and can be imported independently


## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All existing imports must continue to work: `from engine_core.ai import AI, ParameterizedAI, TRAINED_PARAMS, load_all_strategy_params`
- `AI.buy_cards()` and `AI.place_cards()` must execute identical logic for all strategies
- Parameter resolution order must remain: hardcoded defaults < JSON overrides < manual params
- Strategy logger hooks must fire at the same points with identical data
- `BuilderSynergyMatrix` behavior must be identical (same scoring, same updates)
- All 8 strategies must produce identical buying and placement decisions
- `load_all_strategy_params()` crash-proof behavior must be preserved
- `ParameterizedAI` parameter merging logic must remain unchanged

**Scope:**
All code that currently imports from `engine_core.ai` should be completely unaffected by this refactoring. This includes:
- Game simulation code
- Training scripts
- Test suites
- Any external modules that use the AI system

The refactoring is purely internal to the `engine_core/ai` module structure.

## Hypothesized Root Cause

Based on the bug description and code analysis, the architectural defects stem from:

**1. Lack of Module Boundaries**
   - All strategies are implemented as static methods in a single `AI` class
   - No physical separation between strategy implementations
   - Shared utilities are mixed with strategy-specific code
   - Result: 1400+ line monolithic file that violates Single Responsibility Principle

**2. Eager Loading of All Dependencies**
   - `BuilderSynergyMatrix` is defined at module level
   - All strategy implementations are loaded when `engine_core.ai` is imported
   - No lazy loading mechanism for strategy-specific dependencies
   - Result: Memory overhead and slower import times

**3. Violation of Open/Closed Principle**
   - Adding a new strategy requires modifying the existing `AI` class
   - `STRATEGY_MAP` is defined in the same file as all implementations
   - No extension point for new strategies without touching existing code
   - Result: High risk of introducing bugs when adding features

**4. Poor Code Organization**
   - Helper functions like `_economy_phase_controls()` are buried in the `AI` class
   - Strategy-specific logic (e.g., builder's synergy scoring) mixed with general logic
   - Configuration loading mixed with strategy implementations
   - Result: Difficult to navigate, understand, and maintain


## Correctness Properties

Property 1: Bug Condition - Modular Strategy Architecture

_For any_ codebase structure where strategies are decoupled into separate modules under `engine_core/ai/strategies/`, the system SHALL allow adding new strategies by creating new module files without modifying existing strategy implementations, and SHALL load only the required strategy module and its dependencies when a specific strategy is used.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Behavioral Compatibility

_For any_ existing code that imports from `engine_core.ai` or uses AI strategies, the refactored system SHALL produce exactly the same behavior as the original monolithic implementation, preserving all buying logic, placement logic, parameter resolution, strategy logger hooks, and `BuilderSynergyMatrix` behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**


## Fix Implementation

### Target Architecture

The refactored structure will follow this module organization:

```
engine_core/
├── ai/
│   ├── __init__.py              # Public API exports (AI, ParameterizedAI, TRAINED_PARAMS, etc.)
│   ├── base.py                  # BaseStrategy interface, STRATEGY_MAP, AI dispatcher class
│   ├── config.py                # TRAINED_PARAMS, load_all_strategy_params(), AIConfigError
│   ├── utils.py                 # Shared utilities (_economy_phase_controls, _get_param_with_fallback)
│   ├── parameterized.py         # ParameterizedAI class
│   └── strategies/
│       ├── __init__.py          # Empty or strategy registration
│       ├── random.py            # RandomStrategy + _buy_random, _place_smart_default
│       ├── warrior.py           # WarriorStrategy + _buy_warrior
│       ├── economist.py         # EconomistStrategy + _buy_economist
│       ├── builder.py           # BuilderStrategy + _buy_builder, BuilderSynergyMatrix, _place_fast_synergy
│       ├── evolver.py           # EvolverStrategy + _buy_evolver
│       ├── balancer.py          # BalancerStrategy + _buy_balancer
│       ├── rare_hunter.py       # RareHunterStrategy + _buy_rare_hunter
│       └── tempo.py             # TempoStrategy + _place_aggressive
```

### Changes Required

Assuming our root cause analysis is correct, the refactoring involves:

**File**: `engine_core/ai/__init__.py` (NEW)

**Purpose**: Maintain backward compatibility by re-exporting the public API

**Specific Changes**:
1. **Create Public API Module**: Create `__init__.py` that imports and re-exports all public symbols
   - Import `AI` from `base.py`
   - Import `ParameterizedAI` from `parameterized.py`
   - Import `TRAINED_PARAMS`, `load_all_strategy_params`, `load_strategy_params`, `AIConfigError` from `config.py`
   - Define `__all__` to explicitly list public exports

2. **Preserve Import Paths**: Ensure `from engine_core.ai import AI` continues to work identically

---

**File**: `engine_core/ai/config.py` (NEW)

**Purpose**: Isolate configuration loading and default parameters

**Specific Changes**:
1. **Move TRAINED_PARAMS**: Extract the entire `TRAINED_PARAMS` dictionary from `ai.py`
2. **Move Configuration Functions**: Extract `load_all_strategy_params()` and `load_strategy_params()`
3. **Move AIConfigError**: Extract the exception class
4. **Preserve Crash-Proof Behavior**: Ensure all error handling remains identical

---

**File**: `engine_core/ai/base.py` (NEW)

**Purpose**: Define the strategy interface and dispatcher

**Specific Changes**:
1. **Move BaseStrategy**: Extract the `BaseStrategy` abstract class
2. **Move AI Dispatcher**: Extract the `AI` class with `buy_cards()` and `place_cards()` static methods
3. **Move STRATEGY_MAP**: Extract the strategy registry dictionary
4. **Import Strategy Classes**: Import all strategy implementations from `strategies/` submodules
5. **Preserve Dispatch Logic**: Ensure `STRATEGY_MAP.get(strat_name, STRATEGY_MAP["random"])` behavior is identical

---

**File**: `engine_core/ai/utils.py` (NEW)

**Purpose**: Shared utility functions used by multiple strategies

**Specific Changes**:
1. **Move _economy_phase_controls**: Extract the shared economy engine used by economist and builder
2. **Move _get_param_with_fallback**: Extract the parameter fallback helper
3. **Add Module Constants**: Move `MAX_LOOKAHEAD_CARDS`, `MAX_COORD_CHECK`, `PLACEMENT_TIME_BUDGET_S`
4. **Preserve Function Signatures**: Ensure all parameters and return types remain identical

---

**File**: `engine_core/ai/parameterized.py` (NEW)

**Purpose**: Parameter injection wrapper for all strategies

**Specific Changes**:
1. **Move ParameterizedAI**: Extract the entire `ParameterizedAI` class
2. **Import Dependencies**: Import `AI` from `base.py`, `load_all_strategy_params` from `config.py`, `TRAINED_PARAMS` from `config.py`
3. **Preserve Parameter Merging**: Ensure the three-layer priority system (defaults < JSON < manual) remains identical
4. **Preserve get_param Logic**: Ensure parameter lookup behavior is unchanged

---

**File**: `engine_core/ai/strategies/random.py` (NEW)

**Purpose**: Random strategy implementation

**Specific Changes**:
1. **Create RandomStrategy Class**: Move `RandomStrategy` class from `ai.py`
2. **Move _buy_random**: Extract the `_buy_random` static method as a module-level function
3. **Move _place_smart_default**: Extract the `_place_smart_default` static method as a module-level function
4. **Update References**: Change `AI._buy_random` calls to `_buy_random`, `AI._place_smart_default` to `_place_smart_default`
5. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `PLACE_PER_TURN`, `get_strategy_logger`

---

**File**: `engine_core/ai/strategies/warrior.py` (NEW)

**Purpose**: Warrior strategy implementation

**Specific Changes**:
1. **Create WarriorStrategy Class**: Move `WarriorStrategy` class from `ai.py`
2. **Move _buy_warrior**: Extract the `_buy_warrior` static method as a module-level function
3. **Reuse _place_smart_default**: Import `_place_smart_default` from `random.py`
4. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`

---

**File**: `engine_core/ai/strategies/economist.py` (NEW)

**Purpose**: Economist strategy implementation

**Specific Changes**:
1. **Create EconomistStrategy Class**: Move `EconomistStrategy` class from `ai.py`
2. **Move _buy_economist**: Extract the `_buy_economist` static method as a module-level function
3. **Import _economy_phase_controls**: Import from `utils.py`
4. **Reuse _place_smart_default**: Import from `random.py`
5. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`

---

**File**: `engine_core/ai/strategies/builder.py` (NEW)

**Purpose**: Builder strategy implementation with synergy matrix

**Specific Changes**:
1. **Move BuilderSynergyMatrix**: Extract the entire `BuilderSynergyMatrix` class
2. **Create BuilderStrategy Class**: Move `BuilderStrategy` class from `ai.py`
3. **Move _buy_builder**: Extract the `_buy_builder` static method as a module-level function
4. **Move _place_fast_synergy**: Extract the `_place_fast_synergy` static method as a module-level function
5. **Move _place_combo_optimized**: Extract the `_place_combo_optimized` static method as a module-level function
6. **Import _economy_phase_controls**: Import from `utils.py`
7. **Import _get_param_with_fallback**: Import from `utils.py`
8. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `STAT_TO_GROUP`, `RARITY_TAVAN`, `get_strategy_logger`, `defaultdict`, `time`

---

**File**: `engine_core/ai/strategies/evolver.py` (NEW)

**Purpose**: Evolver strategy implementation

**Specific Changes**:
1. **Create EvolverStrategy Class**: Move `EvolverStrategy` class from `ai.py`
2. **Move _buy_evolver**: Extract the `_buy_evolver` static method as a module-level function
3. **Reuse _place_smart_default**: Import from `random.py`
4. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`

---

**File**: `engine_core/ai/strategies/balancer.py` (NEW)

**Purpose**: Balancer strategy implementation

**Specific Changes**:
1. **Create BalancerStrategy Class**: Move `BalancerStrategy` class from `ai.py`
2. **Move _buy_balancer**: Extract the `_buy_balancer` static method as a module-level function
3. **Reuse _place_smart_default**: Import from `random.py`
4. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`, `defaultdict`

---

**File**: `engine_core/ai/strategies/rare_hunter.py` (NEW)

**Purpose**: Rare hunter strategy implementation

**Specific Changes**:
1. **Create RareHunterStrategy Class**: Move `RareHunterStrategy` class from `ai.py`
2. **Move _buy_rare_hunter**: Extract the `_buy_rare_hunter` static method as a module-level function
3. **Reuse _place_smart_default**: Import from `random.py`
4. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `get_strategy_logger`

---

**File**: `engine_core/ai/strategies/tempo.py` (NEW)

**Purpose**: Tempo strategy implementation

**Specific Changes**:
1. **Create TempoStrategy Class**: Move `TempoStrategy` class from `ai.py`
2. **Move _place_aggressive**: Extract the `_place_aggressive` static method as a module-level function
3. **Reuse _buy_warrior**: Import from `warrior.py`
4. **Import Dependencies**: Import `BaseStrategy`, `Card`, `Player`, `CARD_COSTS`, `HEX_DIRS`, `PLACE_PER_TURN`, `get_strategy_logger`

---

**File**: `engine_core/ai.py` (DELETE after migration)

**Purpose**: Remove the monolithic file once all code is migrated

**Specific Changes**:
1. **Verify All Imports**: Ensure all external code has been updated to import from `engine_core.ai` (not `engine_core.ai.py`)
2. **Delete File**: Remove `engine_core/ai.py` completely
3. **Verify Tests Pass**: Ensure all tests continue to pass with the new structure


## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, capture the behavior of the unfixed (monolithic) code as a baseline, then verify the refactored code produces identical behavior. This is a pure refactoring with zero intended behavioral changes.

### Exploratory Bug Condition Checking

**Goal**: Confirm the architectural defects exist in the current codebase BEFORE implementing the fix.

**Test Plan**: Write tests that verify the current monolithic structure and its limitations. These tests will PASS on the unfixed code (confirming the bug exists) and FAIL on the fixed code (confirming the bug is resolved).

**Test Cases**:
1. **Monolithic File Test**: Verify that `engine_core/ai.py` exists and contains all 8 strategies (will pass on unfixed code, fail on fixed code)
2. **Import Overhead Test**: Measure that importing `AI` loads `BuilderSynergyMatrix` even when not using builder strategy (will pass on unfixed code, fail on fixed code)
3. **File Size Test**: Verify that `engine_core/ai.py` is >= 55KB (will pass on unfixed code, fail on fixed code)
4. **Extension Test**: Verify that adding a new strategy requires modifying `engine_core/ai.py` (will pass on unfixed code, fail on fixed code)

**Expected Counterexamples**:
- All strategies are defined in a single file
- Importing any strategy loads all dependencies
- Adding a new strategy requires modifying existing code
- File navigation requires searching through 1400+ lines

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (modular architecture), the fixed system allows extension without modification and loads only required dependencies.

**Pseudocode:**
```
FOR ALL codebase WHERE isBugCondition(codebase) == FALSE DO
  result := verify_modular_architecture(codebase)
  ASSERT result.strategies_in_separate_modules == TRUE
  ASSERT result.can_add_strategy_without_modifying_existing == TRUE
  ASSERT result.lazy_loading_enabled == TRUE
END FOR
```

**Test Cases**:
1. **Module Structure Test**: Verify that each strategy exists in its own module under `engine_core/ai/strategies/`
2. **Import Isolation Test**: Verify that importing `AI` does NOT load `BuilderSynergyMatrix`
3. **Extension Test**: Verify that a new strategy can be added by creating a new file without modifying existing strategy files
4. **Public API Test**: Verify that `from engine_core.ai import AI, ParameterizedAI` continues to work

### Preservation Checking

**Goal**: Verify that for all existing code and all strategy behaviors, the refactored system produces exactly the same results as the original monolithic implementation.

**Pseudocode:**
```
FOR ALL (player, market, strategy) IN test_scenarios DO
  original_result := monolithic_AI.buy_cards(player, market, strategy)
  refactored_result := modular_AI.buy_cards(player, market, strategy)
  ASSERT original_result == refactored_result
  
  original_placement := monolithic_AI.place_cards(player, strategy)
  refactored_placement := modular_AI.place_cards(player, strategy)
  ASSERT original_placement == refactored_placement
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all strategies and scenarios

**Test Plan**: Capture behavior on UNFIXED code first by running simulations and recording decisions, then write property-based tests that verify the refactored code produces identical decisions.

**Test Cases**:
1. **Buy Decision Preservation**: For each strategy, verify that `buy_cards()` makes identical purchasing decisions given the same player state and market
2. **Place Decision Preservation**: For each strategy, verify that `place_cards()` makes identical placement decisions given the same player state and hand
3. **Parameter Resolution Preservation**: Verify that `ParameterizedAI` resolves parameters identically (defaults < JSON < manual)
4. **Strategy Logger Preservation**: Verify that strategy logger hooks fire at the same points with identical data
5. **BuilderSynergyMatrix Preservation**: Verify that builder's synergy matrix updates and scores identically
6. **Economy Controls Preservation**: Verify that `_economy_phase_controls()` returns identical phase decisions for economist and builder
7. **Import Compatibility Preservation**: Verify that all existing imports continue to work without modification

### Unit Tests

- Test each strategy module independently with known inputs and expected outputs
- Test configuration loading with various JSON scenarios (missing file, invalid JSON, partial overrides)
- Test parameter fallback logic in `_get_param_with_fallback()`
- Test `BuilderSynergyMatrix` scoring and decay behavior
- Test `_economy_phase_controls()` phase transitions (greed → spike → convert)
- Test public API exports from `engine_core/ai/__init__.py`

### Property-Based Tests

- Generate random player states, markets, and strategies; verify buy decisions are identical between monolithic and modular implementations
- Generate random board states and hands; verify placement decisions are identical
- Generate random parameter configurations; verify parameter resolution is identical
- Test that all 8 strategies produce identical behavior across 1000+ random scenarios

### Integration Tests

- Run full game simulations with each strategy and verify identical outcomes (win rate, gold accumulation, board state)
- Test strategy switching mid-game (if supported) produces identical behavior
- Test that training scripts continue to work with the refactored structure
- Test that all existing test suites pass without modification

### Migration Validation

**Critical**: Before deleting `engine_core/ai.py`, verify:
1. All external imports have been updated or use the backward-compatible `engine_core.ai` path
2. All tests pass with the new structure
3. No references to `engine_core.ai.AI` (should be `engine_core.ai.AI` via `__init__.py`)
4. Documentation and comments reference the new structure

