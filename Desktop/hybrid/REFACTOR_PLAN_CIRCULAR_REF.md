# Circular Reference Refactor Plan

## Problem Statement

`player.game = self` in `Game.__init__` creates a circular reference that:
- Prevents garbage collection (100 Game instances stay in memory during simulations)
- Breaks atomic transaction guarantees in `Player.buy_card()`
- Bypasses TurnManager's weakref protection

## Root Causes

1. **Game.__init__ line 61**: `p.game = self` creates strong circular reference
2. **Player.buy_card()**: Non-atomic operations (spend_gold → clone → add_to_hand)
3. **Direct access**: `CombatEngine`, `ProgressionSystem` access `player.game` directly

## Refactor Strategy

### Phase 1: Context Injection (CURRENT)
- Remove `player.game` assignment from `Game.__init__`
- Remove `self.game = None` from `Player.__init__`
- Pass game reference via `_ctx` dict in all trigger_passive calls
- Update all `player.game` access points to use context

### Phase 2: Atomic Transactions (FUTURE)
- Wrap `buy_card()` in transaction context manager
- Add rollback capability to Economy and Inventory
- Implement Command pattern for reversible actions

## Files to Modify

1. `engine_core/game.py` - Remove `p.game = self`
2. `engine_core/player.py` - Remove `self.game = None`, update buy_card
3. `engine_core/combat_engine.py` - Use context instead of player.game
4. `engine_core/progression_system.py` - Use context instead of player.game
5. `engine_core/turn_manager.py` - Already uses weakref, verify context passing

## Migration Path

1. Add deprecation warning when `player.game` is accessed
2. Update all internal code to use context
3. Remove `player.game` attribute
4. Add transaction safety (Phase 2)

## Testing Strategy

- Run existing simulation tests to verify no regressions
- Monitor memory usage in 100-game simulations
- Verify weakref cleanup with gc.collect()
