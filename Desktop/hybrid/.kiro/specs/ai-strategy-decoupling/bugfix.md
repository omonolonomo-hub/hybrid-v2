# Bugfix Requirements Document

## Introduction

The AI strategy system in `engine_core/ai.py` suffers from architectural defects that violate the Open/Closed Principle and cause performance and maintainability issues. The 55KB monolithic file contains 8 different AI strategies (economist, warrior, builder, evolver, balancer, rare_hunter, tempo, random) with strategy dispatch implemented through a `STRATEGY_MAP` dictionary that maps to strategy objects, but all strategy implementations remain tightly coupled in a single file. This architecture creates unnecessary coupling, makes the codebase difficult to extend, and loads resources (like `BuilderSynergyMatrix`) even when not needed.

This bugfix decouples the strategies into separate modules following the Strategy pattern, eliminating architectural defects while preserving all existing behavior.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the codebase is structured THEN all 8 AI strategies exist in a single 55KB `engine_core/ai.py` file

1.2 WHEN a new strategy needs to be added THEN the developer must modify the existing `ai.py` file, violating the Open/Closed Principle

1.3 WHEN any AI strategy is imported THEN the `BuilderSynergyMatrix` class is loaded into memory regardless of whether the builder strategy is used

1.4 WHEN the codebase needs maintenance THEN developers must navigate a 55KB file to find specific strategy implementations

1.5 WHEN strategy implementations are coupled THEN shared helper functions like `_economy_phase_controls` cannot be easily reused without importing the entire AI module

### Expected Behavior (Correct)

2.1 WHEN the codebase is structured THEN each AI strategy SHALL exist in its own separate module under `engine_core/ai/` directory

2.2 WHEN a new strategy needs to be added THEN the developer SHALL create a new strategy module without modifying existing strategy files

2.3 WHEN a specific AI strategy is imported THEN only the required strategy module and its dependencies SHALL be loaded into memory

2.4 WHEN the codebase needs maintenance THEN developers SHALL navigate to the specific strategy module file (e.g., `economist.py`, `warrior.py`) to find implementations

2.5 WHEN strategy implementations are decoupled THEN shared helper functions SHALL be accessible through a common base module without coupling to specific strategies

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `ParameterizedAI` is instantiated with any strategy name THEN the system SHALL CONTINUE TO create the AI instance with the same parameter resolution behavior (hardcoded defaults < JSON overrides < manual params)

3.2 WHEN `AI.buy_cards()` is called with a player using any strategy THEN the system SHALL CONTINUE TO execute the exact same buying logic as before refactoring

3.3 WHEN `AI.place_cards()` is called with a player using any strategy THEN the system SHALL CONTINUE TO execute the exact same placement logic as before refactoring

3.4 WHEN the economist strategy uses `_economy_phase_controls()` THEN the system SHALL CONTINUE TO return the same phase control decisions (greed/spike/convert/emergency)

3.5 WHEN the builder strategy uses `BuilderSynergyMatrix` THEN the system SHALL CONTINUE TO track and score synergies identically

3.6 WHEN `load_all_strategy_params()` is called THEN the system SHALL CONTINUE TO load parameters from `trained_params.json` with the same crash-proof behavior

3.7 WHEN any existing code imports `from engine_core.ai import AI, ParameterizedAI` THEN the import SHALL CONTINUE TO work without modification

3.8 WHEN `TRAINED_PARAMS` is accessed THEN the system SHALL CONTINUE TO provide the same hardcoded default parameters for all strategies

3.9 WHEN strategy logger hooks are called during buy/place operations THEN the system SHALL CONTINUE TO log events identically

3.10 WHEN the tempo strategy uses `power_center_thresh` and `combo_center_weight` parameters THEN the system SHALL CONTINUE TO read them from the parameter system with the same defaults
