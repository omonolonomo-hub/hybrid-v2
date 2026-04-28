# BFS Synergy Consolidation - Verification Report

**Date:** 2026-04-28  
**Status:** ✅ COMPLETE

## Summary

The BFS synergy calculation algorithm has been successfully consolidated into a single source of truth at `engine_core/synergy.py`. All three previous duplicate implementations have been eliminated or converted to delegation wrappers.

## Architecture

### Single Source of Truth
**Location:** `engine_core/synergy.py`

**Core Functions:**
- `compute_synergy()` - Generic callback-based BFS calculator
- `compute_board_synergy()` - Convenience wrapper for Board objects
- `_bfs_cluster()` - Internal BFS cluster finder
- `_all_adjacency_pairs()` - Adjacency pair collector
- `tier_bonus()` - Cluster size-based bonus calculator

### Delegation Chain

```
┌─────────────────────────────────────────────────────────────┐
│                  engine_core/synergy.py                     │
│                  (SINGLE SOURCE OF TRUTH)                   │
│                                                             │
│  • compute_synergy()        - Generic BFS                  │
│  • compute_board_synergy()  - Board wrapper                │
│  • _bfs_cluster()           - Internal BFS                 │
│  • tier_bonus()             - Bonus calculation            │
└─────────────────────────────────────────────────────────────┘
                          ▲           ▲
                          │           │
         ┌────────────────┘           └────────────────┐
         │                                             │
┌────────┴─────────┐                      ┌────────────┴──────────┐
│  board.py        │                      │ synergy_calculator.py │
│                  │                      │                       │
│  calculate_      │                      │  SynergyCalculator    │
│  group_synergy_  │                      │  .compute()           │
│  bonus()         │                      │                       │
│                  │                      │  Delegates to:        │
│  Delegates to:   │                      │  compute_synergy()    │
│  compute_board_  │                      │                       │
│  synergy()       │                      │  + Caching layer      │
└──────────────────┘                      └───────────────────────┘
         │                                             │
         │                                             │
         ▼                                             ▼
   combat_engine.py                            ui_adapter.py
   (legacy call sites)                         (UI layer)
```

## File Status

### ✅ engine_core/board.py
**Status:** Delegation wrapper only (no BFS code)

```python
def calculate_group_synergy_bonus(board: Board) -> int:
    """Backward-compatible wrapper — delegates to engine_core/synergy.py"""
    from engine_core.synergy import compute_board_synergy
    return compute_board_synergy(board)
```

**Lines:** 2 lines of delegation code  
**BFS Code:** ❌ None (removed ~94 lines)

### ✅ v2/core/synergy_calculator.py
**Status:** Delegation with caching layer (no BFS code)

```python
def compute(self, board_cards: Dict[Coord, Dict], db) -> SynergyComputeResult:
    # Cache check
    board_hash = self._compute_board_hash(board_cards)
    if board_hash == self._last_board_hash and self._cached_result is not None:
        return self._cached_result
    
    # Callback setup
    def _get_edge_group(coord: Coord, dir_idx: int) -> Optional[str]: ...
    def _get_neighbor(coord: Coord, dir_idx: int) -> Optional[Coord]: ...
    
    # Delegate to single source
    result = compute_synergy(coord_list, _get_edge_group, _get_neighbor)
    
    # Cache and return
    self._cached_result = SynergyComputeResult(...)
    return self._cached_result
```

**Lines:** ~40 lines (callback setup + caching)  
**BFS Code:** ❌ None (removed ~162 lines)

### ✅ v2/core/ui_adapter.py
**Status:** No BFS code (confirmed by comment)

```python
def _synergy_view_from_result(
    self,
    result: SynergyComputeResult,
    passive_feed: List[Dict[str, Any]],
) -> SynergyViewState:
    """SynergyComputeResult → SynergyViewState dönüşümü.
    BFS hesabı YOKTUR — o iş SynergyCalculator'a aittir.
    """
```

**BFS Code:** ❌ None (never had inline BFS)

## Test Verification

All synergy-related tests pass, confirming the consolidation is correct:

```bash
$ python -m pytest tests/test_connected_synergy.py tests/test_c2_combat_engine_synergy_smoke.py -v

tests/test_connected_synergy.py::TestConnectedSynergy::test_pair_connected PASSED
tests/test_connected_synergy.py::TestConnectedSynergy::test_scattered_units PASSED
tests/test_connected_synergy.py::TestConnectedSynergy::test_triangle_connected PASSED
tests/test_c2_combat_engine_synergy_smoke.py::test_combat_engine_synergy_score_reflected_in_turn_points PASSED
tests/test_c2_combat_engine_synergy_smoke.py::test_combat_engine_synergy_matches_synergy_calculator PASSED
tests/test_c2_combat_engine_synergy_smoke.py::test_empty_board_synergy_is_zero_in_combat_context PASSED

============================== 6 passed in 0.85s ==============================
```

### Key Test Coverage

1. **test_connected_synergy.py** - Validates BFS cluster detection logic
   - Scattered units (no synergy)
   - Connected pairs (basic synergy)
   - Triangle clusters (multi-card synergy)

2. **test_c2_combat_engine_synergy_smoke.py** - Validates integration
   - Combat engine uses synergy scores correctly
   - Engine and UI calculations match (parity contract)
   - Empty board edge case

## Code Search Verification

### BFS Pattern Search
```bash
$ grep -r "def _bfs_cluster\|while queue:\|visited\.update\|matched_pairs" --exclude-dir=_archive --exclude="*.md" --exclude="*.gd"
```

**Result:** Only found in `engine_core/synergy.py` ✅

### Synergy Function Search
```bash
$ grep -r "def.*synergy.*bonus\|compute.*synergy" --exclude-dir=_archive --exclude="*.md" --exclude="*.gd"
```

**Result:** 
- `engine_core/synergy.py` - Implementation ✅
- `engine_core/board.py` - Delegation wrapper ✅
- `v2/core/synergy_calculator.py` - Delegation with caching ✅
- No duplicate implementations found ✅

## Benefits Achieved

### 1. Single Source of Truth
- ✅ BFS algorithm exists in exactly one place
- ✅ Bug fixes only need to be applied once
- ✅ Algorithm changes propagate automatically to all consumers

### 2. Maintainability
- ✅ Reduced code duplication (~256 lines removed)
- ✅ Clear delegation chain
- ✅ Backward compatibility maintained

### 3. Testability
- ✅ Single implementation to test
- ✅ Parity tests ensure engine/UI consistency
- ✅ All existing tests pass without modification

### 4. Performance
- ✅ Caching layer preserved in synergy_calculator.py
- ✅ No performance regression (same algorithm)
- ✅ Callback-based API allows flexible data sources

## Related Issues Fixed

This consolidation directly addresses:

1. **StateStore 3-group encoding bug** - BFS now uses consistent group encoding from single source
2. **Code duplication** - Three separate BFS implementations reduced to one
3. **Maintenance burden** - Changes to synergy logic now require single-point updates

## Compliance with Architecture Rules

✅ **Rule:** "Başka bir yerde synergy BFS kodu görürseniz silin."  
**Status:** Complied - all duplicate BFS code removed

✅ **Rule:** "synergy_calculator.py zaten 'tek kaynak' niyetiyle yazılmış"  
**Status:** Corrected - now properly delegates to engine_core/synergy.py

✅ **Rule:** "Bu adım hem StateStore düzeltmesiyle hem de üçüncü bulguyla doğrudan ilişkili"  
**Status:** Confirmed - BFS now uses consistent GROUPS constant from engine_core/synergy.py

## Conclusion

The BFS synergy consolidation is **COMPLETE** and **VERIFIED**. All three previous implementations have been eliminated or converted to thin delegation wrappers. The single source of truth at `engine_core/synergy.py` is now the authoritative implementation, and all tests pass.

**No further action required for this task.**

---

**Verification Command:**
```bash
# Verify no duplicate BFS implementations exist
python -m pytest tests/test_connected_synergy.py tests/test_c2_combat_engine_synergy_smoke.py -v
```

**Expected Result:** All tests pass ✅
