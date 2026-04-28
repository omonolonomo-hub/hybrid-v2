# Exception Refactor: Before & After Examples

## Example 1: Invalid Player Index

### ❌ Before (Silent Failure)

```python
# Code
player = adapter.get_player(999)
gold = player.gold

# Output
Traceback (most recent call last):
  File "shop.py", line 42, in buy_card
    gold = player.gold
AttributeError: 'NoneType' object has no attribute 'gold'
```

**Problems:**
- Error happens at line 42, but root cause is line 41
- Error message doesn't mention index 999
- No indication of valid range
- Debugging requires tracing back through code

### ✅ After (Explicit Exception)

```python
# Code
player = adapter.get_player(999)
gold = player.gold

# Output
Traceback (most recent call last):
  File "shop.py", line 41, in buy_card
    player = adapter.get_player(999)
  File "engine_adapter.py", line 81, in get_player
    raise PlayerNotFoundError(index, len(players))
PlayerNotFoundError: Player at index 999 not found (valid range: 0-3)
```

**Benefits:**
- Error happens at line 41 (the actual problem)
- Error message shows invalid index (999)
- Error message shows valid range (0-3)
- Immediate understanding of the problem

---

## Example 2: Missing Market

### ❌ Before (Silent Failure)

```python
# Code
market = adapter.get_market()
window = market.get_window(player.pid)

# Output
Traceback (most recent call last):
  File "shop.py", line 67, in refresh_shop
    window = market.get_window(player.pid)
AttributeError: 'NoneType' object has no attribute 'get_window'
```

**Problems:**
- Error at line 67, root cause at line 66
- Doesn't explain why market is None
- Could be initialization issue, timing issue, or corruption

### ✅ After (Explicit Exception)

```python
# Code
market = adapter.get_market()
window = market.get_window(player.pid)

# Output
Traceback (most recent call last):
  File "shop.py", line 66, in refresh_shop
    market = adapter.get_market()
  File "engine_adapter.py", line 92, in get_market
    raise MarketNotAvailableError("Market not initialized in engine")
MarketNotAvailableError: Market not initialized in engine
```

**Benefits:**
- Error at line 66 (the actual problem)
- Clear explanation: market not initialized
- Immediate action: check engine initialization

---

## Example 3: Structured Error Handling

### ❌ Before (Defensive Checks Everywhere)

```python
# Every caller needs defensive checks
player = adapter.get_player(index)
if player is None:
    logger.error("Invalid player index: %s", index)
    return ActionResult.ERR_INVALID_PLAYER

market = adapter.get_market()
if market is None:
    logger.error("Market not available")
    return ActionResult.ERR_MARKET_UNAVAILABLE

# ... actual logic ...
```

**Problems:**
- Boilerplate repeated everywhere
- Easy to forget checks
- Inconsistent error handling
- No type safety (player could still be None)

### ✅ After (Centralized Error Handling)

```python
# Clean, focused code
try:
    player = adapter.get_player(index)
    market = adapter.get_market()
    # ... actual logic ...
except PlayerNotFoundError as e:
    logger.error("Invalid player: %s", e)
    return ActionResult.ERR_INVALID_PLAYER
except MarketNotAvailableError as e:
    logger.error("Market error: %s", e)
    return ActionResult.ERR_MARKET_UNAVAILABLE
except EngineAdapterError as e:
    logger.error("Adapter error: %s", e)
    return ActionResult.ERR_ENGINE_EXCEPTION
```

**Benefits:**
- Clean separation of happy path and error handling
- Centralized error handling
- Type safety (player is guaranteed valid in try block)
- Consistent error handling across codebase

---

## Example 4: Debugging Production Issues

### ❌ Before (Unclear Logs)

```
ERROR: AttributeError: 'NoneType' object has no attribute 'gold'
  at shop.py:42 in buy_card
  at game_loop.py:156 in process_action
```

**Questions:**
- Which object is None?
- Why is it None?
- What was the input?
- Is this a bug or expected behavior?

### ✅ After (Clear Logs)

```
ERROR: PlayerNotFoundError: Player at index 999 not found (valid range: 0-3)
  at engine_adapter.py:81 in get_player
  at shop.py:41 in buy_card
  at game_loop.py:156 in process_action
```

**Answers:**
- Player object is missing
- Index 999 is out of range
- Valid range is 0-3
- This is a bug (invalid index)

---

## Example 5: Type Safety

### ❌ Before (No Type Safety)

```python
def process_player(adapter: EngineAdapter, index: int):
    player = adapter.get_player(index)  # Type: Optional[Player]
    
    # Type checker can't help here
    if player is None:
        return
    
    # player could still be None if we forget the check
    gold = player.gold  # Type checker says this is safe, but it's not!
```

### ✅ After (Type Safety)

```python
def process_player(adapter: EngineAdapter, index: int):
    player = adapter.get_player(index)  # Type: Player (never None)
    
    # No None check needed - type checker knows player is valid
    gold = player.gold  # Type checker confirms this is safe
```

**Benefits:**
- Type checker can verify correctness
- No need for None checks
- Clearer intent
- Fewer bugs

---

## Example 6: Testing

### ❌ Before (Testing Silent Failures)

```python
def test_invalid_player():
    adapter = create_adapter()
    player = adapter.get_player(999)
    
    # What are we testing?
    assert player is None  # Is None the correct behavior?
    
    # This will fail with AttributeError
    # gold = player.gold
```

### ✅ After (Testing Exceptions)

```python
def test_invalid_player():
    adapter = create_adapter()
    
    # Clear test intent
    with pytest.raises(PlayerNotFoundError) as exc_info:
        adapter.get_player(999)
    
    # Can verify exception details
    assert exc_info.value.index == 999
    assert "valid range" in str(exc_info.value)
```

**Benefits:**
- Clear test intent
- Verifiable exception details
- Tests document expected behavior
- Easier to maintain

---

## Summary

| Aspect | Before (Silent Failure) | After (Explicit Exception) |
|--------|------------------------|---------------------------|
| **Error Location** | Far from root cause | At the source |
| **Error Message** | Generic AttributeError | Specific, actionable |
| **Debugging** | Requires tracing | Immediate understanding |
| **Type Safety** | None (Optional types) | Full (non-None types) |
| **Code Clarity** | Defensive checks everywhere | Clean separation |
| **Testing** | Unclear intent | Clear expectations |
| **Production Logs** | Vague | Detailed |

The exception refactor transforms debugging from a detective investigation into a clear diagnosis.
