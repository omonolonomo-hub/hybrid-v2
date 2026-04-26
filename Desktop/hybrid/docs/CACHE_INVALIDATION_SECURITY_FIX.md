# Cache Invalidation & Phase Validation Security Fix

**Status:** CRITICAL  
**Date:** 2026-04-26  
**Severity:** Logic Exploit - Stale UI Data & Phase Bypass

---

## Executive Summary

Two critical security vulnerabilities have been identified in the game state management system:

1. **Cache Invalidation Bug**: Spectator UI shows stale data when viewing non-human players
2. **Phase Validation Gap**: Card purchases lack phase validation, allowing combat-phase purchases

Both issues stem from hardcoded assumptions about player index 0 being the only relevant player for UI updates.

---

## Vulnerability 1: Cache Invalidation Logic Exploit

### Root Cause

`GameState._invalidate_cache()` contains a hardcoded optimization:

```python
def _invalidate_cache(self, **kwargs) -> None:
    pid = kwargs.get("pid")
    if pid is not None and pid != 0:
        # AI oyuncuların mutasyonları UI cache'ini bozmaz
        return
    self._cached_public_state = None
```

**The Problem:** When `view_index != 0`, the UI displays a cached state that never updates.

### Attack Scenario

1. User is in lobby viewing their own board (`view_index=0`)
2. User clicks on Player 1's portrait → `view_index=1`
3. Turn advances, AI Player 1's board mutates
4. Signal fires: `signals.board_mutated.emit(pid=1)`
5. Cache invalidation checks: `pid=1, pid != 0` → **returns early, no cache invalidation**
6. User sees Player 1's **previous turn board state** (stale data)

### Impact

- **Spectator Mode Broken**: Cannot accurately observe other players
- **Strategic Information Loss**: Incorrect opponent board state affects decision-making
- **UI Integrity Violation**: Displayed state diverges from actual game state

---

## Vulnerability 2: Phase Validation Gap

### Root Cause

`GameState.buy_card_from_slot()` only validates player ownership, not game phase:

```python
def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
    if player_index != 0:
        return ActionResult.ERR_NOT_OWNER
    # ❌ NO PHASE CHECK HERE
    if not self._adapter:
        return ActionResult.ERR_ENGINE_EXCEPTION
    result = self._adapter.perform_buy_card(player_index, slot_index)
    self._invalidate_cache()
    return result
```

### Attack Scenario

If a timer-based auto-purchase feature is added:

```python
# Hypothetical timer callback
def on_timer_expired():
    # ❌ This could fire during combat phase!
    game_state.buy_card_from_slot(0, 2)
```

**Result:** Card purchase during combat phase, violating game rules.

### Additional Gold Validation Issue

`EngineAdapter.perform_buy_card()` has two separate gold checks:

```python
# Check 1: In adapter
if player.gold < cost:
    return ActionResult.ERR_INSUFFICIENT_GOLD

# Check 2: In player.buy_card() → economy.spend_gold()
player.buy_card(card, market=market, ...)
```

This creates a **race condition window** where gold could change between checks (though unlikely in single-threaded Python, it's architecturally unsound).

---

## The "Jenga Tower" Scenario

These bugs are currently dormant because:
- UI only allows purchases during prep phase
- No background timers exist
- Only human player (pid=0) is viewed during active play

**But adding ANY of these features triggers the exploit:**
- Auto-purchase timers
- Spectator mode during active games
- Multi-player simultaneous turns
- Background AI simulation with UI observation

---

## Fix Protocol

### Fix 1: Dynamic Cache Invalidation

**Before:**
```python
def _invalidate_cache(self, **kwargs) -> None:
    pid = kwargs.get("pid")
    if pid is not None and pid != 0:
        return
    self._cached_public_state = None
```

**After:**
```python
def _invalidate_cache(self, **kwargs) -> None:
    pid = kwargs.get("pid")
    # Only invalidate if mutation affects the currently viewed player
    if pid is not None and pid != self._store.view_index:
        return
    self._cached_public_state = None
```

**Rationale:** Cache should invalidate when the **viewed player** mutates, not just player 0.

---

### Fix 2: Phase Validation Guard

**Before:**
```python
def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
    if player_index != 0:
        return ActionResult.ERR_NOT_OWNER
    if not self._adapter:
        return ActionResult.ERR_ENGINE_EXCEPTION
    result = self._adapter.perform_buy_card(player_index, slot_index)
    self._invalidate_cache()
    return result
```

**After:**
```python
def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
    if player_index != 0:
        return ActionResult.ERR_NOT_OWNER
    if self._store.phase != "STATE_PREPARATION":
        return ActionResult.ERR_NOT_IN_PREP_PHASE
    if not self._adapter:
        return ActionResult.ERR_ENGINE_EXCEPTION
    result = self._adapter.perform_buy_card(player_index, slot_index)
    self._invalidate_cache()
    return result
```

**Rationale:** Enforce phase validation at the API boundary, not just in UI.

---

## Testing Strategy

### Test 1: Spectator Cache Invalidation

```python
def test_spectator_cache_updates():
    game_state = GameState()
    game_state.hook_engine(mock_engine)
    
    # View player 1
    game_state.view_index = 1
    initial_state = game_state.get_public_state()
    
    # Mutate player 1's board
    mock_engine.players[1].board.place((0, 0), Card("Test"))
    mock_engine.signals.board_mutated.emit(pid=1)
    
    # Cache should be invalidated
    updated_state = game_state.get_public_state()
    assert updated_state != initial_state
```

### Test 2: Phase Validation

```python
def test_buy_card_phase_validation():
    game_state = GameState()
    game_state.hook_engine(mock_engine)
    game_state._store.phase = "STATE_COMBAT"
    
    result = game_state.buy_card_from_slot(0, 0)
    assert result == ActionResult.ERR_NOT_IN_PREP_PHASE
```

---

## Deployment Notes

- **Backward Compatible:** No API signature changes
- **Performance Impact:** Negligible (one additional integer comparison)
- **Risk Level:** Low (defensive programming, no behavior change for current usage)

---

## Lessons Learned

1. **Never hardcode player indices** in core logic
2. **Always validate phase** at API boundaries, not just UI
3. **Cache invalidation** must respect dynamic view state
4. **Defensive programming** prevents "Jenga tower" scenarios

---

## References

- `v2/core/game_state.py` - Cache invalidation logic
- `v2/core/state_store.py` - View index management
- `v2/core/engine_adapter.py` - Gold validation
- `v2/scenes/shop.py` - Spectator view switching
