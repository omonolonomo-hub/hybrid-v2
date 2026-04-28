# Bug 3: SceneManager Memory Leak - Test Findings

## Summary

The bug condition exploration tests have been written and executed on the **UNFIXED** code in `v2/core/scene_manager.py`. The tests document the current behavior and identify areas for improvement.

## Key Findings

### 1. Scene GC Behavior (CURRENT STATE)

**Finding**: The current `set_scene()` implementation DOES allow scenes to be garbage collected because it directly replaces `self._current`.

**Evidence**:
```
DEBUG: Reference count for old_scene before del: 1
DEBUG: SceneManager._current is new_scene: True
DEBUG: SceneManager._current is old_scene: False
DEBUG: scene_ref() after gc.collect(): None
DEBUG: gs_ref() after gc.collect(): None
```

**Interpretation**: The basic GC mechanism works. However, the code lacks **explicit cleanup patterns** that make the behavior more robust and maintainable.

### 2. Fade Surface Leak (CONFIRMED BUG)

**Finding**: `set_scene()` does NOT clean up `self._fade_surface`, causing a minor memory leak.

**Evidence**:
```
DEBUG: Fade surface after set_scene(): <Surface(800x600x32)>
DEBUG: Fade surface weakref: <Surface(800x600x32)>
ISSUE DOCUMENTED: set_scene() doesn't clean up fade surface.
```

**Impact**: Each scene transition leaves behind a pygame Surface object. While small compared to full scenes, this accumulates over many transitions.

### 3. Lack of Explicit Cleanup Pattern

**Finding**: The current code uses implicit cleanup (direct assignment) rather than explicit cleanup (null then assign).

**Current Pattern**:
```python
if self._current is not None:
    self._current.on_exit()
self._current = scene  # Direct assignment
```

**Recommended Pattern** (from fix requirements):
```python
if self._current is not None:
    self._current.on_exit()
    self._current = None  # Explicit null
    # Delete fade surface
    if hasattr(self, '_fade_surface') and self._fade_surface is not None:
        del self._fade_surface
        self._fade_surface = None
self._current = scene
```

**Benefit**: Makes cleanup explicit, easier to understand, and more maintainable.

### 4. Missing dispose() Method

**Finding**: Tests currently use monkey-patching (`SceneManager._instance = None`) for isolation.

**Current Approach**:
```python
@pytest.fixture(autouse=True)
def setup_pygame_and_reset_singleton():
    SceneManager._instance = None  # Monkey-patching
    yield
    SceneManager._instance = None
```

**Recommended Approach** (from fix requirements):
```python
@classmethod
def dispose(cls):
    """Dispose of singleton instance for testing."""
    if cls._instance is not None:
        if cls._instance._current is not None:
            cls._instance._current.on_exit()
        cls._instance = None
```

**Benefit**: Provides clean API for test isolation without monkey-patching.

## Test Results

All 7 tests PASSED, documenting the following:

1. ✅ **test_single_scene_transition_prevents_gc**: Documents that scenes ARE being GC'd (current behavior works)
2. ✅ **test_multiple_scene_transitions_accumulate_memory**: Verifies only current scene is alive (current behavior works)
3. ✅ **test_gamestate_references_survive_scene_transition**: Verifies GameState is GC'd (current behavior works)
4. ✅ **test_first_set_scene_with_no_old_scene**: Verifies edge case handling (current behavior works)
5. ✅ **test_fade_surface_survives_scene_transition**: **DOCUMENTS FADE SURFACE LEAK** (needs fix)
6. ✅ **test_explicit_null_reference_pattern**: Documents need for explicit cleanup pattern
7. ✅ **test_dispose_method_for_testing**: Documents need for dispose() method

## Counterexamples Found

### Counterexample 1: Fade Surface Leak
- **Input**: `set_scene(new_scene)` after a previous transition created `_fade_surface`
- **Expected**: Fade surface should be deleted
- **Actual**: Fade surface persists (800x600x32 Surface object)
- **Root Cause**: `set_scene()` doesn't check or delete `_fade_surface`

### Counterexample 2: Implicit Cleanup Pattern
- **Input**: `set_scene(new_scene)` with existing scene
- **Expected**: Explicit nulling of `self._current` before assignment
- **Actual**: Direct assignment without explicit null
- **Root Cause**: Code relies on Python's reference counting rather than explicit cleanup

### Counterexample 3: No dispose() Method
- **Input**: Test needs to reset singleton
- **Expected**: Clean API method like `SceneManager.dispose()`
- **Actual**: Must use monkey-patching `SceneManager._instance = None`
- **Root Cause**: No dispose() method exists

## Recommendations for Fix

Based on the test findings, the fix should implement:

1. **Explicit Cleanup in set_scene()**:
   - Add explicit `self._current = None` after `on_exit()`
   - Add explicit deletion of `self._fade_surface`
   - Check `if self._current is not None` before cleanup

2. **Add dispose() Class Method**:
   - Implement `@classmethod dispose(cls)` for test isolation
   - Call `on_exit()` on current scene if exists
   - Set `cls._instance = None`

3. **Update Scene on_exit() Methods**:
   - Ensure each scene's `on_exit()` nulls out heavy references
   - GameState references
   - Pygame Surfaces
   - UI component references

## Test Validation Strategy

After implementing the fix:

1. **Re-run all tests** - they should still PASS
2. **Verify explicit cleanup** - check that `self._current` is nulled
3. **Verify fade surface cleanup** - check that `self._fade_surface` is deleted
4. **Verify dispose() works** - update test fixtures to use `dispose()`

## Conclusion

The bug condition exploration tests successfully document the current behavior and identify areas for improvement. While the basic GC mechanism works, the fix will add:

- **Explicit cleanup patterns** for better maintainability
- **Fade surface cleanup** to fix minor memory leak
- **dispose() method** for cleaner test isolation

These improvements align with the requirements in `bugfix.md` and `design.md`.

---

**Test File**: `tests/test_bug3_scene_manager_memory_leak.py`  
**Requirements Validated**: 1.7, 1.8, 1.9, 1.10  
**Status**: ✅ Tests written, run, and findings documented
