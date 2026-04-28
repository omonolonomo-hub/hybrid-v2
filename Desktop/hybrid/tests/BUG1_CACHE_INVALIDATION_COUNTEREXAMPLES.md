# Bug 1: Cache Invalidation Performance Leak - Counterexamples

## Bug Summary

The UIAdapter.build_public_state() performance leak has been confirmed through exploration tests. The bug manifests as monolithic cache invalidation where ANY signal (economy_changed, inventory_changed, turn_started, board_mutated) invalidates the ENTIRE PublicState cache, forcing expensive full rebuilds with BFS + DB + triple-iteration.

## Counterexamples Found

### Counterexample 1: economy_changed Signal
**Test**: `test_economy_changed_triggers_unnecessary_cache_invalidation`

**Scenario**: Player's gold changes (economy_changed signal fires)

**Expected Behavior**: Only HUD component should be invalidated and recomputed

**Actual Behavior**: 
- Entire `_cached_public_state` is set to `None`
- Next `get_public_state()` call triggers full `build_public_state()` rebuild
- Full rebuild includes: BFS (synergy calculation) + DB lookups + triple-iteration over shop/hand/board

**Impact**: Unnecessary BFS run and full state reconstruction when only gold/HP display needs updating

---

### Counterexample 2: inventory_changed Signal
**Test**: `test_inventory_changed_triggers_unnecessary_cache_invalidation`

**Scenario**: Player's hand changes (inventory_changed signal fires)

**Expected Behavior**: Only hand component should be invalidated and recomputed

**Actual Behavior**:
- Entire `_cached_public_state` is set to `None`
- Next `get_public_state()` call triggers full rebuild
- Synergy BFS runs despite board being unchanged

**Impact**: Unnecessary BFS run when only hand card info needs updating

---

### Counterexample 3: turn_started Signal
**Test**: `test_turn_started_triggers_unnecessary_cache_invalidation`

**Scenario**: New turn starts (turn_started signal fires)

**Expected Behavior**: Only shop component should be invalidated and recomputed

**Actual Behavior**:
- Entire `_cached_public_state` is set to `None`
- Next `get_public_state()` call triggers full rebuild
- Synergy BFS runs despite board being unchanged

**Impact**: Unnecessary BFS run when only shop window needs updating

---

### Counterexample 4: Multiple Signals (Performance Leak)
**Test**: `test_multiple_signals_trigger_multiple_cache_invalidations`

**Scenario**: Simulated start_turn() with 16 signals:
- 7x inventory_changed (AI purchases)
- 8x economy_changed (income for each player)
- 1x turn_started

**Expected Behavior**: Granular invalidation should result in ≤1 full rebuild

**Actual Behavior**:
- **16 full `build_public_state()` calls**
- Each call includes BFS + DB + triple-iteration
- With 8+ cards on board, each rebuild takes 5-8ms
- Total: 80-128ms for 16 rebuilds (exceeds 16ms frame budget at 60 FPS)

**Impact**: Frame rate drops during turn transitions, especially with AI players

---

## Root Cause Analysis

The root cause is in `GameState._invalidate_cache()` (v2/core/game_state.py):

```python
def _invalidate_cache(self, **kwargs) -> None:
    """Invalidate cache on any mutation."""
    pid = kwargs.get("pid")
    if pid is not None and pid != self._store.view_index:
        # Only invalidate for viewed player
        return
        
    self._cached_public_state = None  # ← MONOLITHIC INVALIDATION
```

**Problem**: Setting `_cached_public_state = None` discards the ENTIRE PublicState, including:
- Synergy data (requires expensive BFS)
- Shop card info (requires DB lookups)
- Hand card info (requires DB lookups)
- Board card info (requires DB lookups)
- HUD data (gold, HP, turn number)

**Missing**: No granular tracking of which components are stale. All signals trigger the same monolithic invalidation.

---

## Expected Fix

The fix should implement granular cache invalidation as specified in the design document:

1. **Replace monolithic cache** with granular cache tracking:
   - `_cached_public_state: Optional[PublicState]` (full cached state)
   - `_synergy_stale: bool` (set by board_mutated)
   - `_board_stale: bool` (set by board_mutated)
   - `_shop_stale: bool` (set by turn_started)
   - `_hand_stale: bool` (set by inventory_changed)
   - `_hud_stale: bool` (set by economy_changed)

2. **Signal-to-cache mapping**:
   - board_mutated → `_synergy_stale = True` + `_board_stale = True`
   - economy_changed → `_hud_stale = True`
   - inventory_changed → `_hand_stale = True`
   - turn_started → `_shop_stale = True`

3. **Selective recomputation** in `build_public_state()`:
   - Only run BFS if `_synergy_stale == True`
   - Only fetch shop data if `_shop_stale == True`
   - Only fetch hand data if `_hand_stale == True`
   - Only fetch board data if `_board_stale == True`
   - Only fetch HUD data if `_hud_stale == True`
   - Reuse cached components for non-stale data

---

## Test Results

All 4 exploration tests **FAILED as expected**, confirming the bug exists:

```
FAILED test_economy_changed_triggers_unnecessary_cache_invalidation
FAILED test_inventory_changed_triggers_unnecessary_cache_invalidation
FAILED test_turn_started_triggers_unnecessary_cache_invalidation
FAILED test_multiple_signals_trigger_multiple_cache_invalidations
PASSED test_board_mutated_should_invalidate_cache (correct behavior)
```

The tests will PASS after the fix is implemented, validating that the expected behavior is satisfied.

---

## Performance Impact

**Current (Unfixed)**:
- 16 signals during start_turn() → 16 full rebuilds
- Each rebuild: 5-8ms with 8+ cards
- Total: 80-128ms (exceeds 16ms frame budget)
- Result: Frame rate drops, stuttering during turn transitions

**After Fix (Expected)**:
- 16 signals during start_turn() → Granular invalidation
- Only affected components recomputed
- BFS runs only when board changes (0 times for non-board signals)
- Total: <1ms for non-board signals
- Result: Smooth 60 FPS even during turn transitions

---

## Next Steps

1. ✅ Task 1 Complete: Bug condition exploration test written and run
2. ⏭️ Task 2: Write preservation unit tests (before implementing fix)
3. ⏭️ Task 3: Implement the fix (granular cache invalidation)
4. ⏭️ Task 3.4: Verify exploration tests now PASS
5. ⏭️ Task 3.5: Verify preservation tests still PASS
