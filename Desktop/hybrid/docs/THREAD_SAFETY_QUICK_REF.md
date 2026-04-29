# Thread Safety Quick Reference

## TL;DR

**The game engine is NOT thread-safe. NetworkServer uses a single-worker thread pool to ensure serial execution.**

## For Developers

### ✅ Safe Patterns

```python
# Safe: Using NetworkServer's executor
async with self._action_lock:
    result = await loop.run_in_executor(
        self._executor,  # Single-worker executor
        self._orchestrator.submit_action,
        pid,
        action
    )
```

```python
# Safe: Reading after executor completes
result = await loop.run_in_executor(self._executor, game_operation)
# Executor is idle here, safe to read state
snapshot = self._orchestrator.pop_outbox()
```

### ❌ Unsafe Patterns

```python
# UNSAFE: Direct state access from event loop during executor operation
async def bad_example():
    task = asyncio.create_task(
        loop.run_in_executor(self._executor, game.combat_phase)
    )
    # BAD: combat_phase is still running in thread pool!
    hp = game.players[0].hp  # Race condition!
    await task
```

```python
# UNSAFE: Multiple workers
self._executor = ThreadPoolExecutor(max_workers=4)  # DON'T DO THIS!
# Multiple threads can now mutate game state simultaneously
```

```python
# UNSAFE: Bypassing the executor
def bad_handler():
    # BAD: Direct call from event loop (blocks) or another thread (race)
    self._orchestrator.submit_action(pid, action)
```

## Key Rules

1. **Always use `self._executor`** for game operations
2. **Never increase `max_workers`** beyond 1
3. **Never access game state directly** from event loop during executor operations
4. **Always await executor completion** before reading state
5. **Use `self._action_lock`** for async-level serialization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Event Loop Thread                                           │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ WebSocket A  │         │ WebSocket B  │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│         └────────┬───────────────┘                          │
│                  │                                           │
│         ┌────────▼────────┐                                 │
│         │ _action_lock    │ ◄── Async serialization        │
│         └────────┬────────┘                                 │
│                  │                                           │
│         ┌────────▼────────────────────────────┐             │
│         │ run_in_executor(self._executor, ...) │            │
│         └────────┬────────────────────────────┘             │
│                  │                                           │
└──────────────────┼───────────────────────────────────────────┘
                   │
                   │ Offload to thread pool
                   │
┌──────────────────▼───────────────────────────────────────────┐
│ Thread Pool (max_workers=1)                                  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Game Worker Thread                                     │  │
│  │                                                         │  │
│  │  submit_action()                                       │  │
│  │    → _advance_turn()                                   │  │
│  │      → finish_turn()      [50-100ms]                   │  │
│  │      → combat_phase()     [100-300ms]                  │  │
│  │      → start_turn()       [50-100ms]                   │  │
│  │      → _generate_snapshots()                           │  │
│  │        → _outbox[pid] = snapshot                       │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ← Only ONE operation runs at a time                         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Why Single Worker?

| Concern | Why Single Worker Solves It |
|---------|----------------------------|
| **Parallel mutations** | Only one thread can mutate game state at a time |
| **Outbox races** | `_generate_snapshots()` completes before `_broadcast_snapshots()` reads |
| **Inconsistent reads** | No concurrent mutations during reads |
| **Combat corruption** | Combat calculations never run in parallel |
| **Future bugs** | Prevents accidental concurrent access from new code |

## Performance

**Q: Doesn't single worker limit throughput?**

**A: No, because:**
- Game operations are inherently serial (turn-based)
- Event loop handles all I/O concurrency
- Only game mutations are serialized
- Typical actions are fast (<10ms)
- Slow operations (turn advancement) are infrequent

**Benchmark:** 2 clients, concurrent actions = ~300-400ms (vs ~600ms blocking)

## Testing

```bash
# Run thread safety tests
pytest tests/test_network_nonblocking.py -v

# Run all network tests
pytest tests/test_network_integration.py tests/test_network_nonblocking.py -v
```

## Debugging

### Check executor status
```python
# In NetworkServer
logger.debug(f"Executor workers: {self._executor._max_workers}")
logger.debug(f"Executor queue size: {self._executor._work_queue.qsize()}")
```

### Detect blocking
```python
# Add to _handle_message
start = time.time()
result = await loop.run_in_executor(...)
duration = time.time() - start
if duration > 0.5:
    logger.warning(f"Slow operation: {duration:.3f}s")
```

### Verify serialization
```python
# Add thread ID logging
import threading
logger.debug(f"Executing in thread: {threading.current_thread().name}")
```

## Common Questions

**Q: Can I use `asyncio.to_thread()` instead?**  
A: No, it uses the default executor. Use `run_in_executor(self._executor, ...)`.

**Q: Can I make the game engine thread-safe instead?**  
A: Possible but not recommended. Would require adding locks throughout, increasing complexity and reducing performance.

**Q: What if I need parallel game instances?**  
A: Create multiple `NetworkServer` instances, each with its own game and executor.

**Q: Does this work with multiprocessing?**  
A: No, game state is not shared across processes. Use threading only.

## See Also

- **Full documentation**: `docs/THREAD_SAFETY.md`
- **Implementation**: `engine_core/network_server.py`
- **Tests**: `tests/test_network_nonblocking.py`
- **Changelog**: `docs/CHANGELOG_THREAD_SAFETY.md`
