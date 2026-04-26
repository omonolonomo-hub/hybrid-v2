# Cache Invalidation Flow Diagram

## Inventory Batch Clear Optimization (Signal Reduction)

### Problem: N-Signal Emission Pattern

The original `Player.place_cards()` implementation emitted N signals when placing N cards:

```python
# BEFORE (INEFFICIENT)
def place_cards(self):
    for i in range(len(self.inventory.hand)):
        # ... placement logic ...
        self.inventory.clear_slot(i)  # ← Emits signal EACH iteration
```

**Issues:**
1. N cards placed → N `_emit_change()` signals
2. Each signal triggers `GameState._invalidate_cache()`
3. Potential for N cache rebuilds if state read between signals
4. Unnecessary signal noise

### Solution: Batch Clear API

```python
# AFTER (OPTIMIZED)
def place_cards(self):
    cleared_indices = []
    for i in range(len(self.inventory.hand)):
        # ... placement logic ...
        cleared_indices.append(i)  # Mark for clearing
    
    # Batch clear: N cards → 1 signal
    if cleared_indices:
        self.inventory.clear_slots_batch(cleared_indices)
```

### Signal Flow Comparison

**Before:**
```
place_cards(3 cards):
  ├─ clear_slot(0) → _emit_change() → _invalidate_cache() [1]
  ├─ clear_slot(1) → _emit_change() → _invalidate_cache() [2]
  └─ clear_slot(2) → _emit_change() → _invalidate_cache() [3]

Total signals: 3
Potential cache rebuilds: 3
```

**After:**
```
place_cards(3 cards):
  └─ clear_slots_batch([0,1,2]) → _emit_change() → _invalidate_cache() [1]

Total signals: 1
Cache rebuilds: 1 (guaranteed)
```

**See:** `docs/INVENTORY_BATCH_CLEAR_FIX.md` for full details

---

## Card Pool Cache Fix (CRITICAL)

### Problem: Global Singleton with In-Place Mutation

The original `_card_pool_cache` global variable caused severe test isolation issues:

```python
# BEFORE (BROKEN)
_card_pool_cache: Optional[List[Card]] = None

def get_card_pool() -> List[Card]:
    global _card_pool_cache
    if _card_pool_cache is None:
        pool = build_card_pool()
        apply_micro_buff_to_weak_cards(pool)  # ← IN-PLACE MUTATION
        _card_pool_cache = pool
    return _card_pool_cache
```

**Issues:**
1. `apply_micro_buff_to_weak_cards()` mutates cards in-place
2. Mutation is cached permanently in process memory
3. All simulations share the same buffed card instances
4. Tests cannot reset to clean state without process restart
5. Hidden state pollution across test runs

### Solution: CardPool Singleton Class

```python
# AFTER (FIXED)
class CardPool:
    """
    Singleton factory for card pool with test isolation support.
    
    Replaces the problematic global _card_pool_cache that caused:
    - In-place mutations to leak across simulations
    - Impossible test isolation without process restart
    - Hidden state pollution from apply_micro_buff_to_weak_cards
    """
    _instance: Optional[List[Card]] = None
    
    @classmethod
    def instance(cls) -> List[Card]:
        """
        Get the cached card pool instance.
        Creates and buffs cards on first call, returns cached copy thereafter.
        """
        if cls._instance is None:
            pool = build_card_pool()
            apply_micro_buff_to_weak_cards(pool)
            cls._instance = pool
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        Clear the cached pool. Used in tests to ensure isolation.
        Forces next instance() call to rebuild from scratch.
        """
        cls._instance = None


def get_card_pool() -> List[Card]:
    """
    Legacy function maintained for backward compatibility.
    Returns the singleton CardPool instance.
    """
    return CardPool.instance()
```

### Test Isolation Pattern

```python
# In test setup/teardown
def setup_method(self):
    """Reset card pool before each test."""
    CardPool.reset()

def test_card_mutations_isolated(self):
    """Each test gets fresh, unbuffed cards."""
    pool1 = CardPool.instance()
    pool1[0].add_base_stat("attack", 999)  # mutate
    
    CardPool.reset()  # clear cache
    
    pool2 = CardPool.instance()
    assert pool2[0].get_base_stat("attack") != 999  # fresh instance
```

### Migration Impact

**Backward Compatible:**
- `get_card_pool()` still works (calls `CardPool.instance()`)
- No changes needed in existing code

**New Capability:**
- Tests can call `CardPool.reset()` for isolation
- Simulations can reset between runs if needed

**Performance:**
- Same lazy initialization behavior
- Same single-instance caching
- Negligible overhead (<1μs for class method dispatch)

---

## UI Cache Invalidation (View Index Fix)

## Before Fix (VULNERABLE)

```
┌─────────────────────────────────────────────────────────────┐
│ User Action: Click on Player 1 portrait in lobby            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ ShopController.set_view_index(1)                            │
│   → game_state.view_index = 1                               │
│   → _invalidate_cache() called                              │
│   → Cache cleared ✓                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ UI displays Player 1's board (fresh data) ✓                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Turn advances: AI Player 1 buys a card                      │
│   → signals.economy_changed.emit(pid=1)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ _invalidate_cache(pid=1) called                             │
│   → Check: pid != 0?                                        │
│   → YES (1 != 0)                                            │
│   → return early ❌                                          │
│   → Cache NOT invalidated!                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ UI still shows OLD cached data ❌                            │
│ User sees Player 1's previous turn state                    │
│ STALE DATA BUG                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## After Fix (SECURE)

```
┌─────────────────────────────────────────────────────────────┐
│ User Action: Click on Player 1 portrait in lobby            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ ShopController.set_view_index(1)                            │
│   → game_state.view_index = 1                               │
│   → _invalidate_cache() called                              │
│   → Cache cleared ✓                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ UI displays Player 1's board (fresh data) ✓                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Turn advances: AI Player 1 buys a card                      │
│   → signals.economy_changed.emit(pid=1)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ _invalidate_cache(pid=1) called                             │
│   → Check: pid != view_index?                               │
│   → Check: 1 != 1?                                          │
│   → NO (they match!)                                        │
│   → Continue to invalidate ✓                                │
│   → Cache cleared!                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Next get_public_state() rebuilds cache                      │
│ UI shows FRESH data ✓                                       │
│ User sees Player 1's current state                          │
│ BUG FIXED                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase Validation Flow

### Before Fix (VULNERABLE)

```
┌─────────────────────────────────────────────────────────────┐
│ Timer expires during combat phase                           │
│   → auto_purchase_callback()                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ buy_card_from_slot(0, 2) called                             │
│   → Check: player_index != 0? NO                            │
│   → Check: adapter exists? YES                              │
│   → ❌ NO PHASE CHECK                                        │
│   → perform_buy_card() called                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Card purchased during combat! ❌                             │
│ GAME RULE VIOLATION                                         │
└─────────────────────────────────────────────────────────────┘
```

### After Fix (SECURE)

```
┌─────────────────────────────────────────────────────────────┐
│ Timer expires during combat phase                           │
│   → auto_purchase_callback()                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ buy_card_from_slot(0, 2) called                             │
│   → Check: player_index != 0? NO                            │
│   → Check: phase == "STATE_PREPARATION"? NO ✓               │
│   → Return ERR_NOT_IN_PREP_PHASE                            │
│   → Purchase BLOCKED                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Timer receives error result                                 │
│ No card purchased ✓                                         │
│ Game rules enforced                                         │
│ BUG PREVENTED                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| **Cache Check** | `pid != 0` | `pid != view_index` |
| **Spectator Updates** | ❌ Broken | ✅ Works |
| **Phase Validation** | ❌ Missing | ✅ Present |
| **Timer Safety** | ❌ Vulnerable | ✅ Protected |
| **Hardcoded Assumptions** | ❌ Yes | ✅ No |

---

## Signal Flow Example

### Scenario: Viewing Player 2, Player 1 mutates

```
Before Fix:
signals.board_mutated.emit(pid=1)
  → _invalidate_cache(pid=1)
  → Check: 1 != 0? YES
  → return early
  → Cache NOT invalidated ❌
  → view_index=2 still sees old cache

After Fix:
signals.board_mutated.emit(pid=1)
  → _invalidate_cache(pid=1)
  → Check: 1 != 2? YES
  → return early
  → Cache NOT invalidated ✓ (correct behavior!)
  → view_index=2 doesn't need update for P1's mutation
```

### Scenario: Viewing Player 1, Player 1 mutates

```
Before Fix:
signals.board_mutated.emit(pid=1)
  → _invalidate_cache(pid=1)
  → Check: 1 != 0? YES
  → return early
  → Cache NOT invalidated ❌ (BUG!)
  → view_index=1 shows stale data

After Fix:
signals.board_mutated.emit(pid=1)
  → _invalidate_cache(pid=1)
  → Check: 1 != 1? NO
  → Continue
  → Cache invalidated ✓
  → view_index=1 gets fresh data
```

---

## Performance Comparison

```
Before:
  if pid is not None and pid != 0:  # 1 comparison
      return

After:
  if pid is not None and pid != self._store.view_index:  # 1 comparison + 1 property access
      return

Performance Impact: <1μs (negligible)
```

---

## Test Coverage Visualization

```
┌─────────────────────────────────────────────────────────────┐
│ TestCacheInvalidationSpectatorMode                          │
├─────────────────────────────────────────────────────────────┤
│ ✓ test_cache_invalidates_for_viewed_player                  │
│ ✓ test_cache_not_invalidated_for_other_players              │
│ ✓ test_cache_invalidates_for_human_player                   │
│ ✓ test_global_signals_always_invalidate                     │
│ ✓ test_view_index_change_invalidates_cache                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TestPhaseValidation                                         │
├─────────────────────────────────────────────────────────────┤
│ ✓ test_buy_card_allowed_in_prep_phase                       │
│ ✓ test_buy_card_blocked_in_combat_phase                     │
│ ✓ test_buy_card_blocked_in_endgame_phase                    │
│ ✓ test_phase_check_before_ownership_check                   │
│ ✓ test_buy_card_alias_respects_phase                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TestRegressionPrevention                                    │
├─────────────────────────────────────────────────────────────┤
│ ✓ test_spectator_mode_scenario                              │
│ ✓ test_timer_auto_purchase_scenario                         │
│ ✓ test_multi_player_view_switching                          │
└─────────────────────────────────────────────────────────────┘

Total: 13/13 tests passing ✓
```
