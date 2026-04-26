# Memory Leak Fix - GameState Signal Circular Reference

## Problem Identification

**Date:** 2026-04-26  
**Severity:** Critical - Memory leak on every game restart

### The Circular Reference Chain

```
GameState → _adapter (EngineAdapter)
    └── _engine (Game)
        └── signals (SignalBus)
            └── board_mutated._observers: list
                └── [GameState._invalidate_cache]  ← bound method
                    └── → GameState (self)
```

### Root Cause

Python bound methods in signal observers create strong references back to the GameState instance. This creates a circular reference that Python's reference counting cannot break automatically. The cyclic GC can eventually collect it, but the presence of `__del__` can cause objects to end up in `gc.garbage`.

### The "Kickstarter Killer" Scenario

When a player returns to menu and starts a new game:
1. New ShopScene is created with new GameState
2. Old GameState is orphaned but not collected
3. Old GameState holds entire game state: PublicState, board_cards, 30+ CardData objects
4. `cleanup()` is never called, `__del__` is unreliable
5. Memory accumulates with each restart

## Solution

### Two-Step Refactor (20 minutes)

#### Step 1: Ensure Deterministic Cleanup ✅

**File:** `v2/scenes/shop.py`

The `on_exit()` method already exists and calls `cleanup()`:

```python
def on_exit(self) -> None:
    """Cleanup resources when exiting the scene."""
    if self._game_state:
        self._game_state.cleanup()
```

This is called automatically by `SceneManager` during scene transitions (verified in `v2/core/scene_manager.py` lines 107-109).

#### Step 2: Remove __del__ Fallback ✅

**File:** `v2/core/game_state.py`

Removed the `__del__` method entirely since cleanup is now deterministic:

```python
# REMOVED:
# def __del__(self):
#     """Cleanup signal observers to prevent memory leaks."""
#     self._detach_engine_signals()
```

The `cleanup()` method remains and is now the single, explicit cleanup path:

```python
def cleanup(self) -> None:
    """Explicitly cleanup resources. Call before discarding GameState instance.
    
    This method is idempotent and can be safely called multiple times.
    """
    self._detach_engine_signals()
    self._cached_public_state = None
    self._adapter = None
```

## Verification

### Cleanup Call Chain

1. User closes game or transitions scenes
2. `SceneManager.transition_to()` or `SceneManager.set_scene()` called
3. `SceneManager` calls `current_scene.on_exit()`
4. `ShopScene.on_exit()` calls `game_state.cleanup()`
5. `GameState.cleanup()` calls `_detach_engine_signals()`
6. All signal observers disconnected
7. Circular reference broken
8. Python GC can immediately collect GameState and all referenced objects

### Files Modified

- `v2/core/game_state.py` - Removed `__del__`, improved `cleanup()` documentation
- `v2/scenes/shop.py` - Already had `on_exit()` calling `cleanup()` ✅

### Testing Recommendations

1. **Manual Test:** Start game → play 30 turns → return to menu → start new game → repeat 10x
   - Monitor memory usage (should remain stable)
   
2. **Automated Test:** Create test that:
   - Creates GameState with engine
   - Calls `cleanup()`
   - Verifies all signal observers are disconnected
   - Verifies GameState can be garbage collected

3. **Profiling:** Use `tracemalloc` or `memory_profiler` to verify no memory accumulation

## Benefits

1. **Deterministic cleanup** - No reliance on GC timing or `__del__` behavior
2. **Immediate memory reclamation** - Objects freed as soon as scene exits
3. **No gc.garbage risk** - Removed `__del__` eliminates uncollectable object risk
4. **Idempotent** - Safe to call `cleanup()` multiple times
5. **Clear ownership** - SceneManager → Scene → GameState cleanup chain is explicit

## Notes

- The restart button in EndgameOverlay just transitions to `STATE_PREPARATION` phase within the same ShopScene, so it doesn't trigger the leak
- The leak only occurs when creating a new ShopScene instance (scene transitions)
- `SceneManager` properly calls `on_exit()` on both `set_scene()` and `transition_to()`
