# Bugfix Requirements Document

## Introduction

This document specifies requirements for Phase 1 (ACIL/IMMEDIATE) fixes from OMNISCIENT AUDIT V7. These are zero-risk, immediate fixes that address critical bugs without requiring refactoring. The fixes target three distinct issues:

1. **Signal.emit() Fatal Crash** - RuntimeError during observer notification when observers disconnect mid-iteration
2. **K_v Shortcut Bypass** - Debug shortcut that bypasses critical game logic causing state corruption
3. **StateStore.phase Validation Missing** - Silent acceptance of invalid phase strings leading to guard failures

All fixes are single-location changes with no architectural impact, designed for immediate deployment this week.

---

## Bug Analysis

### Current Behavior (Defect)

#### Bug 1: Signal.emit() Fatal Crash

1.1 WHEN Signal.emit() is called AND an observer disconnects itself during the notification loop THEN the system crashes with RuntimeError: "dictionary changed size during iteration"

1.2 WHEN Signal.emit() is called AND an observer disconnects another observer during the notification loop THEN the system crashes with RuntimeError: "dictionary changed size during iteration"

#### Bug 2: K_v Shortcut Bypass

1.3 WHEN the user presses K_v in ShopScene THEN the system directly calls phase_machine.transition_to("STATE_VERSUS"), bypassing commit_human_turn()

1.4 WHEN K_v shortcut bypasses commit_human_turn() THEN the AI opponent does not play its turn

1.5 WHEN K_v shortcut bypasses commit_human_turn() THEN the market does not clean up properly

1.6 WHEN K_v shortcut bypasses commit_human_turn() THEN pool_copies state becomes corrupted

#### Bug 3: StateStore.phase Validation Missing

1.7 WHEN StateStore.phase is set to an invalid string (e.g., "STATE_GARBAGE") THEN the system accepts it silently without validation

1.8 WHEN StateStore.phase contains an invalid value THEN phase guards fail silently, causing unpredictable behavior downstream

---

### Expected Behavior (Correct)

#### Bug 1: Signal.emit() Fatal Crash

2.1 WHEN Signal.emit() is called AND an observer disconnects itself during the notification loop THEN the system SHALL complete the notification loop without crashing by iterating over a snapshot of the observer list

2.2 WHEN Signal.emit() is called AND an observer disconnects another observer during the notification loop THEN the system SHALL complete the notification loop without crashing by iterating over a snapshot of the observer list

#### Bug 2: K_v Shortcut Bypass

2.3 WHEN the user presses K_v in ShopScene AND DEBUG_MODE is False THEN the system SHALL ignore the shortcut (no action taken)

2.4 WHEN the user presses K_v in ShopScene AND DEBUG_MODE is True THEN the system SHALL execute the shortcut (for development testing only)

2.5 WHEN K_v shortcut is disabled in production THEN commit_human_turn() SHALL execute normally, ensuring AI plays, market cleans up, and pool_copies remains consistent

#### Bug 3: StateStore.phase Validation Missing

2.6 WHEN StateStore.phase is set to an invalid string (e.g., "STATE_GARBAGE") THEN the system SHALL raise ValueError with a clear error message listing valid phases

2.7 WHEN StateStore.phase is set to a valid phase string THEN the system SHALL accept it and update the phase property

---

### Unchanged Behavior (Regression Prevention)

#### Bug 1: Signal.emit() Fatal Crash

3.1 WHEN Signal.emit() is called AND no observers disconnect during notification THEN the system SHALL CONTINUE TO notify all observers in the original order

3.2 WHEN Signal.emit() is called with arguments THEN the system SHALL CONTINUE TO pass those arguments to all observer callbacks

3.3 WHEN observers are connected or disconnected outside of emit() THEN the system SHALL CONTINUE TO manage the observer list correctly

#### Bug 2: K_v Shortcut Bypass

3.4 WHEN the user interacts with ShopScene through normal UI (buy, sell, reroll, lock, commit) THEN the system SHALL CONTINUE TO process those actions correctly

3.5 WHEN commit_human_turn() is called through normal flow THEN the system SHALL CONTINUE TO execute AI turn, market cleanup, and state transitions correctly

3.6 WHEN other debug shortcuts exist (if any) THEN the system SHALL CONTINUE TO function as currently implemented

#### Bug 3: StateStore.phase Validation Missing

3.7 WHEN StateStore.phase is set to a valid phase string from the defined set THEN the system SHALL CONTINUE TO accept and store the value

3.8 WHEN other StateStore properties are accessed or modified THEN the system SHALL CONTINUE TO function as currently implemented

3.9 WHEN phase guards check the current phase THEN the system SHALL CONTINUE TO return the stored phase value for comparison
