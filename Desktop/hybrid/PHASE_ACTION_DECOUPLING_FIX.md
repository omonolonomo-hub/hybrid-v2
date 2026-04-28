# Phase-Action Decoupling Fix

## The Problem

Two architectural violations in phase management:

### 1. Private Method Access Violation
```python
# ShopController calling private method
self._game_state._mirror_phase(new_phase)  # ← Accessing _private method
```
- `_mirror_phase()` was private but had no logical reason to be
- Single-line implementation: `self._store.phase = phase`
- External access violated encapsulation

### 2. Phase-Action Coupling
```python
if new_phase == "STATE_COMBAT":
    self._game_state.run_combat_phase()  # ← Phase change + combat trigger tightly coupled
```
- Phase transition and combat execution happened in single method
- Impossible to:
  - Dry-run phase changes without triggering combat
  - Preview combat without committing phase change
  - Defer combat execution to next frame
  - Test phase transitions independently

## The Fix

### 1. Make Phase Mirroring Public
```python
# GameState - now public API
def mirror_phase(self, phase: str) -> None:
    """Set the game phase without triggering side effects.
    
    Public API for phase synchronization. Does not trigger combat or other actions.
    """
    self._store.phase = phase
```

### 2. Separate Combat Trigger
```python
# ShopController - new method
def trigger_combat(self) -> None:
    """Trigger combat execution independently of phase change.
    
    Separated from handle_phase_change() to allow:
    - Dry-run phase transitions without combat
    - Deferred combat execution
    - Combat preview/simulation
    """
    self._game_state.run_combat_phase()
```

### 3. Updated Phase Handler
```python
if new_phase == "STATE_COMBAT":
    self.trigger_combat()  # ← Now explicitly separated
    state = self.refresh_public_state()
    return ShopControllerResult(...)
```

## Benefits

### Encapsulation
- No more private method access from external classes
- Clear public API boundary

### Flexibility
- Phase changes can be previewed without side effects
- Combat can be triggered independently
- Enables dry-run testing patterns

### Future-Proofing
- Combat preview UI can call `mirror_phase()` without triggering actual combat
- Replay systems can step through phases without executing actions
- Test suites can verify phase transitions independently

## Example Use Cases

### Dry-Run Phase Change
```python
# Preview what would happen without executing
controller._game_state.mirror_phase("STATE_COMBAT")
preview_state = controller.refresh_public_state()
# ... analyze preview ...
controller._game_state.mirror_phase("STATE_PREPARATION")  # Rollback
```

### Deferred Combat
```python
# Set phase now, execute combat later
controller._game_state.mirror_phase("STATE_COMBAT")
# ... UI animations, player notifications ...
controller.trigger_combat()  # Execute when ready
```

### Independent Testing
```python
# Test phase transitions without combat side effects
game_state.mirror_phase("STATE_COMBAT")
assert game_state.get_public_state().phase == "STATE_COMBAT"
# No combat executed, pure state test
```
