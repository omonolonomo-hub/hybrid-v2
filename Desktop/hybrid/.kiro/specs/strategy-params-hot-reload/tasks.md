# Implementation Plan: Strategy Parameters Hot Reload

## Overview

This plan implements Phase 0 of the strategy parameters hot reload feature: a minimal, crash-proof parameter loading system for the economist AI strategy. The implementation adds JSON-based parameter loading with hot-reload at initialization while maintaining backward compatibility and zero-crash guarantees.

Key implementation goals:
- Add load_strategy_params() helper function with pathlib
- Create ParameterizedAI class with parameter injection
- Modify AI._buy_economist() to use parameterized values
- Ensure crash-proof operation (never raise exceptions)
- Maintain backward compatibility with existing code
- No logging, validation layers, or new dependencies

## Tasks

- [x] 1. Add load_strategy_params() helper function
  - Add necessary imports (pathlib.Path, json, typing)
  - Implement crash-proof file loading with try-except
  - Use pathlib for file path resolution (project_root/trained_params.json)
  - Return empty dict on any error (missing file, invalid JSON, I/O errors)
  - Place function after TRAINED_PARAMS definition in ai.py
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

- [ ]* 1.1 Write property test for load_strategy_params() exception safety
  - **Property 1: Exception Safety**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
  - Use hypothesis to generate various file states (missing, invalid JSON, random content)
  - Assert function always returns dict without raising exceptions
  - Tag: `# Feature: strategy-params-hot-reload, Property 1: Exception Safety`

- [ ] 2. Create ParameterizedAI class
  - [x] 2.1 Implement ParameterizedAI.__init__() with parameter resolution
    - Accept strategy and params arguments
    - Load defaults from TRAINED_PARAMS
    - Call load_strategy_params() for file parameters
    - Merge with priority: defaults < file_params < manual params
    - Cache resolved parameters in self.p
    - _Requirements: 3.1, 3.4, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 2.2 Write property test for parameter override priority
    - **Property 2: Parameter Override Priority**
    - **Validates: Requirements 4.1**
    - Use hypothesis to generate random override dictionaries
    - Assert manual overrides always present in resolved parameters
    - Tag: `# Feature: strategy-params-hot-reload, Property 2: Parameter Override Priority`

  - [ ]* 2.3 Write property test for partial parameter merging
    - **Property 3: Partial Parameter Merging**
    - **Validates: Requirements 4.4**
    - Use hypothesis to generate partial parameter dictionaries
    - Assert provided params override defaults and missing params use defaults
    - Tag: `# Feature: strategy-params-hot-reload, Property 3: Partial Parameter Merging`

  - [x] 2.4 Implement ParameterizedAI.buy_cards() delegation
    - Delegate to AI.buy_cards() with ai_instance=self
    - Pass through all parameters (player, market, max_cards, etc.)
    - _Requirements: 3.1_

  - [x] 2.5 Implement ParameterizedAI.place_cards() delegation
    - Delegate to AI.place_cards() with all parameters
    - _Requirements: 3.1_

- [x] 3. Modify AI._buy_economist() for parameterization
  - Add ai_instance parameter (default None for backward compatibility)
  - Create helper function get_param(key, default) for safe parameter access
  - Replace all hardcoded values with parameterized lookups
  - Update greed phase: greed_turn_end, greed_gold_thresh
  - Update spike phase: spike_turn_end, spike_r4_thresh, thresh_high, buy_2_thresh, spike_buy_count
  - Update convert phase: convert_r5_thresh, convert_buy_count
  - Ensure backward compatibility when ai_instance is None
  - _Requirements: 3.1, 4.1, 4.2, 4.3_

- [ ]* 3.1 Write unit tests for AI._buy_economist() parameterization
  - Test with ai_instance provided → uses parameterized values
  - Test with ai_instance=None → uses hardcoded defaults (backward compat)
  - Test parameter access for all phases (greed, spike, convert)
  - _Requirements: 3.1, 4.1_

- [x] 4. Modify AI.buy_cards() to pass ai_instance
  - Add ai_instance parameter (default None)
  - Pass ai_instance to _buy_economist() call
  - Ensure other strategies remain unchanged
  - _Requirements: 3.1_

- [x] 5. Checkpoint - Ensure all tests pass
  - Run all unit tests and property tests
  - Verify backward compatibility with existing code
  - Ensure no crashes with missing or invalid parameter files
  - Ask the user if questions arise

- [ ]* 6. Write integration tests for end-to-end behavior
  - [ ]* 6.1 Test file loading with valid JSON
    - Create trained_params.json with custom values
    - Initialize ParameterizedAI and verify parameters loaded
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1_

  - [ ]* 6.2 Test file loading with missing file
    - Remove trained_params.json
    - Initialize ParameterizedAI and verify defaults used
    - _Requirements: 1.1, 4.3_

  - [ ]* 6.3 Test file loading with invalid JSON
    - Create trained_params.json with invalid JSON
    - Initialize ParameterizedAI and verify defaults used
    - _Requirements: 1.2, 4.3_

  - [ ]* 6.4 Test parameter priority system
    - Create trained_params.json with values A
    - Initialize ParameterizedAI with manual overrides B
    - Verify manual overrides take precedence
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 6.5 Test backward compatibility
    - Use legacy AI class without ParameterizedAI
    - Run simulation and verify no crashes
    - Verify hardcoded defaults used
    - _Requirements: 3.1_

- [x] 7. Final checkpoint - Verify implementation complete
  - Ensure all tests pass
  - Verify no new dependencies added
  - Verify no logging or validation layers added
  - Confirm economist-only scope maintained
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from design
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end behavior with real file system
- Implementation uses Python stdlib only (pathlib, json, typing)
- No new infrastructure: no logging, no validation, no new dependencies
- Backward compatibility is critical: existing code must continue to work
