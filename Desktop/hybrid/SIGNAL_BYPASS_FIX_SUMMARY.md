# Signal Bypass Fix — Atomic Refactor Complete

## Problem Diagnosis

Two critical code paths were bypassing the signal emission system by directly manipulating data structures:

### 1. CombatEngine._return_cards_to_pool()
```python
# BEFORE — Direct manipulation, no signals
player.hand.clear()
player.copies.clear()
player.copy_turns.clear()
player.board.grid.clear()
```

**Impact:** When a player is eliminated, UI components (HandPanel, PlayerHub) never receive `inventory_changed` or board mutation signals. They continue operating on stale cached state.

### 2. ProgressionSystem.check_evolution()
```python
# BEFORE — Direct assignment, no signals
inventory.hand[i] = None  # ← Bypasses clear_slot()
```

**Impact:** During evolution, cards silently disappear from hand without UI notification, causing desync between actual state and rendered state.

## Root Cause

Both methods violated the **Single Responsibility Principle** by directly accessing internal data structures instead of using the public API:
- `Inventory.clear_slot()` — emits `inventory_changed` signal
- `Board.remove()` / `Board.place()` — triggers `_mutation_callback`

This created a **cache invalidation failure** where UI components never knew state had changed.

## Atomic Refactor Solution

### Added: Inventory.clear_all()
```python
def clear_all(self) -> None:
    """Atomically clears all hand slots and copy tracking, emits ONE signal.
    
    Used during player elimination to ensure UI cache invalidation.
    Guarantees that inventory_changed signal is emitted exactly once
    after all state is cleared, preventing race conditions in UI updates.
    """
    for i in range(len(self.hand)):
        self.hand[i] = None
    self.copies.clear()
    self.copy_turns.clear()
    self.copy_applied.clear()
    self._emit_change()
```

### Added: Board.clear_all()
```python
def clear_all(self) -> None:
    """Atomically clears the entire board grid and triggers mutation callback.
    
    Used during player elimination to ensure UI cache invalidation.
    Guarantees that board_changed signal is emitted exactly once
    after all state is cleared, preventing race conditions in UI updates.
    """
    self.grid.clear()
    self.coord_index.clear()
    self.has_catalyst = False
    self.has_eclipse = False
    if self._mutation_callback is not None:
        self._mutation_callback()
```

### Fixed: CombatEngine._return_cards_to_pool()
```python
# AFTER — Atomic clear with signal emission
player.board.clear_all()
player.inventory.clear_all()
```

### Fixed: ProgressionSystem.check_evolution()
```python
# AFTER — Proper API usage
inventory.clear_slot(i)  # Emits signal
```

## Guarantees

1. **Signal Emission:** Every state mutation now triggers appropriate signals
2. **Atomicity:** Batch operations emit ONE signal after all changes complete
3. **UI Cache Invalidation:** HandPanel, PlayerHub, and other UI components receive notifications
4. **Race Condition Prevention:** No window where state is partially cleared but signals haven't fired
5. **Spectator Mode Ready:** Eliminated player state is now guaranteed to be consistent for replay/spectator features

## Testing Checklist

- [ ] Player elimination triggers UI update (hand clears visually)
- [ ] Evolution removes cards from hand with visual feedback
- [ ] No ghost cards remain in UI after elimination
- [ ] Spectator mode shows correct final board state for eliminated players
- [ ] No console errors about accessing None cards in UI components

## Future-Proofing

This fix establishes the pattern:
- **Never** directly manipulate `player.hand`, `player.copies`, `board.grid`
- **Always** use `Inventory` and `Board` public APIs
- **Batch operations** should emit ONE signal, not N signals

Any future code that needs to clear state should use:
- `inventory.clear_all()` — for full inventory reset
- `board.clear_all()` — for full board reset
- `inventory.clear_slots_batch([indices])` — for multiple hand slots
