# SynergyCalculator Memory Leak Fix - Class-Level Singleton Cache

## Problem Identification

**Date:** 2026-04-26  
**Severity:** Critical - Memory leak + data race risk

### The Class-Level Cache Problem

```python
class SynergyCalculator:
    _last_board_hash: Optional[int] = None    # ← class variable
    _cached_result: Optional[SynergyComputeResult] = None  # ← class variable
```

### Root Causes

1. **Memory Leak on Restart:**
   - Class variables are shared across ALL SynergyCalculator instances
   - When GameState is destroyed and recreated (restart scenario), the old `_cached_result` remains in memory
   - `SynergyComputeResult` contains `adjacency_pairs: List[Tuple]` with references to old card objects
   - Old board state persists indefinitely in class-level cache

2. **Data Race Risk:**
   - If two GameState instances exist simultaneously (parallel simulations, unit tests)
   - Second `compute()` call silently overwrites first instance's cache
   - Not thread-safe, causes unpredictable behavior

3. **Implicit Coupling:**
   - All UIAdapter instances share the same cache
   - No isolation between different game sessions
   - Test isolation broken (tests can interfere with each other)

### The "Kickstarter Killer" Scenario

1. User plays game for 30 turns
2. User clicks "Restart Game" button
3. New ShopScene created with new GameState
4. Old GameState destroyed, but `SynergyCalculator._cached_result` still holds:
   - Old adjacency_pairs with 30+ card references
   - Old group_counts and group_bonuses dicts
   - Old board hash
5. Memory accumulates with each restart

## Solution

### Convert to Instance-Level Caching

#### Step 1: Add __init__ and Convert to Instance Methods ✅

**File:** `v2/core/synergy_calculator.py`

```python
class SynergyCalculator:
    def __init__(self):
        """Initialize instance-level cache."""
        self._last_board_hash: Optional[int] = None
        self._cached_result: Optional[SynergyComputeResult] = None

    def _compute_board_hash(self, board_cards: Dict[Coord, Dict]) -> int:
        # Changed from @classmethod to instance method
        ...

    def invalidate_cache(self) -> None:
        # Changed from @classmethod to instance method
        self._last_board_hash = None
        self._cached_result = None

    def compute(self, board_cards: Dict[Coord, Dict], db) -> SynergyComputeResult:
        # Changed from @classmethod to instance method
        # Use self._last_board_hash and self._cached_result
        ...
```

#### Step 2: UIAdapter Holds SynergyCalculator Instance ✅

**File:** `v2/core/ui_adapter.py`

```python
class UIAdapter:
    def __init__(self):
        """Initialize UIAdapter with instance-level SynergyCalculator."""
        self._synergy_calculator = SynergyCalculator()

    def _build_active_player(self, ...):
        # Use instance method instead of class method
        syn_result = self._synergy_calculator.compute(board_cards, db)
```

#### Step 3: Update Tests ✅

**File:** `tests/test_synergy_cache.py`

```python
class TestSynergyCache:
    def setup_method(self):
        """Create a fresh calculator instance before each test."""
        self.calculator = SynergyCalculator()

    def test_cache_returns_same_result_for_same_input(self):
        result1 = self.calculator.compute(board_cards, _MockDB())
        result2 = self.calculator.compute(board_cards, _MockDB())
        assert result1 is result2  # same object from cache
    
    def test_instance_isolation(self):
        """Different calculator instances should have separate caches."""
        calc1 = SynergyCalculator()
        calc2 = SynergyCalculator()
        
        result1 = calc1.compute(board, db)
        result2 = calc2.compute(board, db)
        
        # Different instances compute independently
        assert result1 is not result2
```

**File:** `tests/conftest.py`

Removed SynergyCalculator cache invalidation since it's now instance-level.

## Verification

### Cleanup Chain

1. User exits scene or restarts game
2. `SceneManager` calls `ShopScene.on_exit()`
3. `ShopScene.on_exit()` calls `GameState.cleanup()`
4. `GameState.cleanup()` sets `self._adapter = None`
5. `GameState` becomes garbage collectable
6. `UIAdapter` (held by GameState) becomes garbage collectable
7. `SynergyCalculator` (held by UIAdapter) becomes garbage collectable
8. `_cached_result` (held by SynergyCalculator) becomes garbage collectable
9. All adjacency_pairs and card references freed immediately

### Files Modified

- `v2/core/synergy_calculator.py` - Converted to instance-level caching
- `v2/core/ui_adapter.py` - Added `__init__` with SynergyCalculator instance
- `tests/test_synergy_cache.py` - Updated tests for instance-level caching
- `tests/conftest.py` - Removed class-level cache invalidation

### Test Results

```
tests/test_synergy_cache.py::TestSynergyCache::test_empty_board_returns_empty_result PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_cache_returns_same_result_for_same_input PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_cache_invalidated_on_board_change PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_explicit_cache_invalidation PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_cache_hash_stability PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_rotation_change_invalidates_cache PASSED
tests/test_synergy_cache.py::TestSynergyCache::test_instance_isolation PASSED

7 passed in 0.67s ✅
```

## Benefits

1. **No Memory Leak** - Cache is destroyed with GameState instance
2. **Thread-Safe** - Each instance has its own cache
3. **Test Isolation** - Tests don't interfere with each other
4. **Clear Ownership** - GameState → UIAdapter → SynergyCalculator ownership chain
5. **Immediate Cleanup** - Cache freed as soon as GameState is destroyed
6. **Parallel Simulation Safe** - Multiple GameState instances can coexist

## Combined Impact with GameState Fix

Both memory leaks are now fixed:

1. **GameState Signal Circular Reference** - Fixed by removing `__del__` and using explicit `cleanup()`
2. **SynergyCalculator Class-Level Cache** - Fixed by converting to instance-level caching

Together, these fixes ensure:
- No circular references
- No class-level state leaks
- Deterministic cleanup on scene exit
- Immediate memory reclamation
- Safe for parallel simulations and unit tests

## Notes

- The cache is still effective - same board state returns cached result within a single GameState lifetime
- Cache invalidation happens automatically when board changes (hash-based)
- Explicit `invalidate_cache()` still available if needed
- Performance characteristics unchanged - only ownership model improved
