# GameState Accessor Refactor — God Object Cleanup

## Problem Statement

`GameState` has **two parallel read APIs**:

1. **Modern (cached)**: `get_public_state()` → `PublicState`
2. **Legacy (inconsistent)**: 8 direct accessor methods

### The 8 Legacy Accessors

```python
get_board_cards(player_index=None) -> dict
get_board_rotations(player_index=None) -> dict
get_hp(player_index=None) -> int
get_gold(player_index=None) -> int
get_hand(player_index=None) -> list
get_shop(player_index=None) -> list
get_strategy(player_index=None) -> str
get_interest_multiplier(player_index=None) -> float
```

### Cache Inconsistency

- `get_hp(None)` → uses `PublicState` cache
- `get_hp(1)` → bypasses cache, calls `EngineAdapter.get_player_hp(1)` directly

This creates:
- **Maintenance burden**: Two code paths for same data
- **Cache bugs**: AI player data always fresh, human player data sometimes stale
- **API confusion**: Which method should callers use?

## Solution

**Remove all 8 legacy accessors.** Force all readers through `get_public_state()`.

### Migration Pattern

**Before:**
```python
hp = game_state.get_hp(0)
gold = game_state.get_gold()
```

**After:**
```python
state = game_state.get_public_state()
hp = state.active_player.hp
gold = state.active_player.gold
```

## Impact Analysis

### Files Requiring Changes

1. **v2/core/game_state.py** — Remove 8 methods
2. **tests/test_card_effect_pipeline.py** — 1 usage
3. **tests/test_e2e_3_turn_integration_contract.py** — 2 usages
4. **tests/test_engine_core_contracts.py** — 5 usages
5. **tests/test_shop_scene_master_integration.py** — 5 usages
6. **tests/test_spectate_tdd.py** — 3 usages
7. **tests/test_phase5_integration.py** — 2 usages

### Internal Usage (No Change Needed)

- `get_board_rotations()` calls `get_board_cards()` internally — both will be removed
- `ui_adapter.py` uses `adapter.get_hand()` (EngineAdapter, not GameState) — safe

## Refactor Steps

1. ✅ Identify all call sites
2. ✅ Update test files to use `get_public_state()`
3. ✅ Remove 8 accessor methods from `GameState`
4. ✅ Run test suite to verify (49 tests passed)
5. ✅ Update documentation

## Completion Summary

**Date**: 2026-04-26
**Status**: ✅ COMPLETE

### Changes Made

**Removed Methods** (8 total):
- `get_board_cards(player_index=None)`
- `get_board_rotations(player_index=None)`
- `get_hp(player_index=None)`
- `get_gold(player_index=None)`
- `get_hand(player_index=None)`
- `get_shop(player_index=None)`
- `get_strategy(player_index=None)`
- `get_interest_multiplier(player_index=None)`

**Files Modified**:
- `v2/core/game_state.py` — Removed 8 methods, updated docstring
- `tests/test_card_effect_pipeline.py` — 1 call site migrated
- `tests/test_e2e_3_turn_integration_contract.py` — 2 call sites migrated
- `tests/test_engine_core_contracts.py` — 5 call sites migrated
- `tests/test_shop_scene_master_integration.py` — 5 call sites migrated
- `tests/test_spectate_tdd.py` — 3 call sites migrated
- `tests/test_phase5_integration.py` — 2 call sites migrated

**Test Results**: 49 passed, 0 failed

### Code Reduction

- **Lines removed**: ~70 lines of duplicate accessor logic
- **API surface area**: Reduced from 10+ read methods to 1 (`get_public_state()`)
- **Cache consistency**: 100% (all reads now use same cache path)

## Post-Refactor API

### GameState Public Interface

**Mutations:**
- `buy_card_from_slot(player_index, slot_index)`
- `reroll_market(player_index)`
- `toggle_lock_shop(player_index)`
- `place_card(hand_index, coord, rotation, player_index)`
- `commit_human_turn()`
- `start_turn()`
- `run_combat_phase()`
- `remove_eliminated_cards(player_index, coords)`

**Reads:**
- `get_public_state()` → `PublicState` (single source of truth)
- `get_pool_copies()` → dict (special case, not in PublicState)

**Properties:**
- `view_index` (read/write)
- `place_locked` (read/write)

## Benefits

- ✅ Single read API
- ✅ Consistent caching behavior
- ✅ Reduced code surface area
- ✅ Clear separation: mutations vs reads
- ✅ Easier to reason about state flow

## Timeline

**Estimated effort**: 30 minutes
**Risk level**: Low (all changes in test code)
