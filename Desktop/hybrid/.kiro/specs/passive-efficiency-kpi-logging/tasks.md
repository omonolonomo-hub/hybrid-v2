# Implementation Plan: Passive Efficiency KPI Logging

## Overview

This implementation replaces real-time passive event logging with in-memory aggregation, improving simulation performance by eliminating per-trigger file I/O. A new KPI_Aggregator class handles all computation logic, while StrategyLogger is updated to delegate computation and handle only file I/O operations.

## Tasks

- [x] 1. Create KPI_Aggregator class with core data structures
  - Create new file `engine_core/kpi_aggregator.py`
  - Implement `__init__()` with `_passive_game_data` dictionary
  - Define dictionary key structure: (game_id, strategy, card_name, passive_type)
  - Define value structure: {total_triggers, raw_value, normalized_value, game_won}
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 1.1 Write unit tests for KPI_Aggregator initialization
  - Test empty dictionary initialization
  - Test data structure types
  - _Requirements: 2.1_

- [x] 2. Implement value normalization logic
  - [x] 2.1 Implement `normalize_passive_value()` method
    - Define VALUE_CONVERSION table with empirical ratios
    - Implement conversion logic: economy (10.0), combat (1.0), combo (1.0), copy (1.0), synergy_field (1.0), survival (15.0)
    - Handle unknown passive types (return 0.0)
    - Add docstring with references to simulation data
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.10_

  - [ ]* 2.2 Write unit tests for value normalization
    - Test economy conversion: 5 gold → 50.0 value
    - Test combat conversion: 10 points → 10.0 value
    - Test copy conversion: 3 stats → 3.0 value
    - Test survival conversion: 1 trigger → 15.0 value
    - Test synergy_field conversion: 2 stats → 2.0 value
    - Test unknown passive type returns 0.0
    - Test negative values and zero handling
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [x] 3. Implement passive_buff_log aggregation
  - [x] 3.1 Implement `aggregate_passive_buff_log()` method
    - Check for `passive_buff_log` attribute existence
    - Iterate through player's passive_buff_log entries
    - Extract card, passive, delta from each entry
    - Create or update dictionary entry for (game_id, strategy, card_name, passive_type)
    - Increment total_triggers counter
    - Accumulate raw_value from delta
    - Calculate and accumulate normalized_value using `normalize_passive_value()`
    - Store game_won status
    - _Requirements: 2.2, 2.3, 6.1, 6.2, 6.3, 6.5_

  - [ ]* 3.2 Write unit tests for aggregation logic
    - Test single player with single passive trigger
    - Test multiple triggers for same card/passive combination
    - Test multiple games with different strategies
    - Test win/loss tracking accuracy
    - Test missing passive_buff_log attribute handling
    - Test malformed passive_buff_log entries (missing fields)
    - _Requirements: 2.2, 2.3, 6.1, 6.5_

- [x] 4. Implement KPI record generation
  - [x] 4.1 Implement `get_kpi_records()` method
    - Iterate through `_passive_game_data` dictionary
    - Calculate efficiency_score: normalized_value / total_triggers (handle division by zero)
    - Round efficiency_score to 4 decimal places
    - Format records with all required fields: game_id, strategy, card_name, passive_type, total_triggers, raw_value, normalized_value, efficiency_score, game_won
    - Sort records by key for consistent output
    - Return list of dictionaries
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 11.8, 11.9_

  - [ ]* 4.2 Write unit tests for record generation
    - Test empty aggregation returns empty list
    - Test single record formatting
    - Test multiple records sorting
    - Test efficiency_score calculation with zero triggers
    - Test efficiency_score rounding (4 decimal places)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Checkpoint - Ensure KPI_Aggregator tests pass
  - Run all KPI_Aggregator unit tests
  - Verify all test cases pass
  - Ask the user if questions arise

- [x] 6. Update StrategyLogger to use KPI_Aggregator
  - [x] 6.1 Add KPI_Aggregator integration to StrategyLogger.__init__()
    - Import KPI_Aggregator class
    - Add `kpi_aggregator` parameter with Optional[KPI_Aggregator] type hint
    - Initialize `self._kpi_aggregator` (create new instance if None)
    - _Requirements: 8.1, 8.4_

  - [x] 6.2 Update log_passive() method
    - Remove `_passive_buf.append()` call (if exists)
    - Remove any file write operations for passive events
    - Keep existing `_strat` and `_passive_card` summary updates
    - _Requirements: 1.1, 1.2, 8.4_

  - [x] 6.3 Update end_game() method
    - After existing game_endings.jsonl logic, iterate through game.players
    - For each player, determine game_won status (player.pid == winner.pid)
    - Call `self._kpi_aggregator.aggregate_passive_buff_log(player, self._game_id, game_won)`
    - Wrap in try-except to handle errors gracefully
    - Print warning if aggregation fails for a player
    - _Requirements: 2.5, 5.1, 5.2, 6.5, 8.1_

  - [ ]* 6.4 Write unit tests for StrategyLogger integration
    - Test KPI_Aggregator injection in __init__()
    - Test end_game() calls aggregate_passive_buff_log() correctly
    - Test error handling when aggregation fails
    - Test disabled logger (enabled=False) has zero overhead
    - _Requirements: 8.1, 8.4_

- [x] 7. Implement passive efficiency KPI file writing
  - [x] 7.1 Create `_write_passive_efficiency_kpi()` method in StrategyLogger
    - Check if logging is enabled
    - Get records from `self._kpi_aggregator.get_kpi_records()`
    - Define file path: `self.output_dir / "passive_efficiency_kpi.jsonl"`
    - Open file with UTF-8 encoding
    - Write each record as JSON line with `ensure_ascii=False`
    - Wrap in try-except for IOError and general exceptions
    - Print warning if file write fails
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 7.2, 7.3, 7.4, 10.4_

  - [x] 7.2 Update flush() method
    - After existing flush logic, call `self._write_passive_efficiency_kpi()`
    - _Requirements: 3.1, 8.1_

  - [ ]* 7.3 Write unit tests for file I/O
    - Test file creation in non-existent directory
    - Test JSONL format correctness
    - Test UTF-8 encoding with special characters
    - Test file write failure handling
    - Test relative path resolution
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.3, 10.1_

- [x] 8. Remove passive_events.jsonl generation
  - Search for any code that writes to `passive_events.jsonl`
  - Remove file write operations for `passive_events.jsonl`
  - Remove `_passive_buf` buffer if it exists and is only used for passive_events.jsonl
  - Verify no references to `passive_events.jsonl` remain in StrategyLogger
  - _Requirements: 1.1, 1.2, 3.5_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Run all unit tests for KPI_Aggregator and StrategyLogger
  - Verify no regressions in existing functionality
  - Ask the user if questions arise

- [x] 10. Integration testing with full simulation
  - [x] 10.1 Run a small simulation (10-20 games) with logging enabled
    - Verify `passive_efficiency_kpi.jsonl` is created
    - Verify file contains expected records
    - Verify existing summary files still generate correctly
    - Verify no `passive_events.jsonl` file is created
    - _Requirements: 3.1, 3.5, 8.2, 8.3_

  - [ ]* 10.2 Write integration test for full simulation flow
    - Test trigger → aggregate → write flow
    - Test backward compatibility with existing log_passive() calls
    - Test flush() generates all expected files
    - Test multiple games with multiple players
    - _Requirements: 8.2, 8.3, 8.4_

- [x] 11. Update passive_summary.json to reference new KPI file
  - Modify `_write_passive_summary()` method
  - Add reference to `passive_efficiency_kpi.jsonl` in summary metadata
  - Document that detailed KPI data is in separate file
  - _Requirements: 8.3_

- [x] 12. Final checkpoint - Verify complete integration
  - Run full simulation (100+ games) and verify performance improvement
  - Verify all output files are generated correctly
  - Verify learning system can consume `passive_efficiency_kpi.jsonl`
  - Ensure all tests pass
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- KPI_Aggregator is a pure computation class with no file I/O (easily testable)
- StrategyLogger handles only file I/O operations (separation of concerns)
- Existing passive trigger detection logic remains unchanged
- Player.passive_buff_log structure is leveraged without modification
