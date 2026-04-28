# EngineAdapter Exception Refactor

## Problem: Silent Failures

The original `EngineAdapter` used a "return None on error" pattern that led to delayed failures:

```python
# BEFORE: Silent failure
player = adapter.get_player(999)  # Returns None
gold = player.gold  # AttributeError: 'NoneType' object has no attribute 'gold'
```

The error happens several lines away from the root cause, making debugging difficult. The stack trace points to `player.gold`, not the invalid index 999.

## Solution: Explicit Exceptions

The refactored code raises explicit exceptions immediately:

```python
# AFTER: Immediate failure
player = adapter.get_player(999)  # Raises PlayerNotFoundError immediately
# PlayerNotFoundError: Player at index 999 not found (valid range: 0-3)
```

The error happens at the source with a clear, actionable message.

## Exception Hierarchy

All exceptions inherit from `EngineAdapterError` for easy catching:

```python
EngineAdapterError (base)
├── PlayerNotFoundError
├── MarketNotAvailableError
├── InvalidSlotError
├── InvalidCoordinateError
├── InsufficientResourcesError
├── PlayerDeadError
├── InvalidGameStateError
└── CardDataError

# Legacy exceptions (for backward compatibility)
AutochessException (base)
├── DatabaseError
├── AssetLoadError
└── EngineException
```

### Usage Examples

**Catch specific errors:**
```python
try:
    player = adapter.get_player(index)
except PlayerNotFoundError as e:
    print(f"Invalid player: {e.index}")
```

**Catch all adapter errors:**
```python
try:
    adapter.perform_buy_card(player_index, slot_index)
except EngineAdapterError as e:
    print(f"Adapter error: {e}")
```

**Let exceptions propagate:**
```python
# For critical operations, let exceptions bubble up
player = adapter.get_player(index)  # Will raise if invalid
market = adapter.get_market()  # Will raise if unavailable
```

## Migration Strategy

### Breaking Changes

These methods now **raise exceptions** instead of returning None:

- `get_player(index)` → raises `PlayerNotFoundError`
- `get_market()` → raises `MarketNotAvailableError`
- `get_shop_window(player_index)` → raises `PlayerNotFoundError` or `MarketNotAvailableError`
- `get_hand(player_index)` → raises `PlayerNotFoundError`

### Backward Compatible

These methods still **return safe defaults** for backward compatibility:

- `get_player_hp(index)` → returns 0 if player not found
- `get_player_gold(index)` → returns 0 if player not found
- `is_shop_locked(index)` → returns False if player not found
- `get_eliminated_coords(index)` → returns [] if player not found
- `get_passive_buff_log(index)` → returns [] if player not found
- `get_pool_copies()` → returns {} if market not available
- `get_rarity_weight(rarity, turn)` → returns 0.0 if market not available

### ActionResult Methods

Methods that return `ActionResult` enum continue to do so for backward compatibility:

- `perform_buy_card()` → returns `ActionResult.ERR_ENGINE_EXCEPTION` on adapter errors
- `perform_placement()` → returns `ActionResult.ERR_ENGINE_EXCEPTION` on adapter errors
- `perform_reroll()` → returns `False` on adapter errors

These methods **log** exceptions but don't raise them, maintaining existing error handling flow.

## Benefits

### 1. Immediate Error Detection
Errors are caught at the source, not several lines later.

### 2. Clear Error Messages
```python
# Before: AttributeError: 'NoneType' object has no attribute 'gold'
# After: PlayerNotFoundError: Player at index 999 not found (valid range: 0-3)
```

### 3. Type Safety
No more `if player is None:` checks scattered everywhere. Type checkers can now verify that `get_player()` always returns a valid player object.

### 4. Structured Error Handling
```python
try:
    player = adapter.get_player(index)
    market = adapter.get_market()
    # ... operations ...
except PlayerNotFoundError:
    # Handle invalid player
except MarketNotAvailableError:
    # Handle market issues
except EngineAdapterError:
    # Handle any other adapter error
```

### 5. Better Debugging
Exception attributes provide context:
```python
except PlayerNotFoundError as e:
    print(f"Invalid index: {e.index}")
    print(f"Valid range: 0-{e.player_count - 1}")
```

## Testing

Run the test suite to verify exception behavior:

```bash
pytest v2/core/test_exceptions.py -v
```

Tests cover:
- Invalid player indices (positive, negative, out of range)
- Missing or invalid market
- Corrupted engine state
- Exception hierarchy
- Backward compatibility
- Real-world scenarios

## Code Review Checklist

When reviewing code that uses EngineAdapter:

- [ ] Are `get_player()` calls wrapped in try/except or guaranteed valid?
- [ ] Are `get_market()` calls wrapped in try/except or guaranteed valid?
- [ ] Do error handlers catch specific exceptions (not bare `except:`)?
- [ ] Are exception messages logged for debugging?
- [ ] Do tests verify exception behavior?

## Future Improvements

1. **Add more specific exceptions** as patterns emerge (e.g., `ShopLockedError`, `PhaseViolationError`)
2. **Migrate ActionResult methods** to raise exceptions once all callers are updated
3. **Add exception context** (e.g., attach player object to `PlayerNotFoundError`)
4. **Create exception middleware** for UI layers to convert exceptions to user-friendly messages

## References

- Exception definitions: `v2/core/exceptions.py`
- Updated adapter: `v2/core/engine_adapter.py`
- Test suite: `v2/core/test_exceptions.py`
