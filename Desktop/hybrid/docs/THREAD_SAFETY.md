# Thread Safety in NetworkServer

## Overview

The `NetworkServer` uses a **single-worker thread pool executor** to ensure thread-safe access to the game engine. This document explains why this is necessary and how it works.

## The Problem

### Game Engine is NOT Thread-Safe

The core game engine components (`Game`, `GameSession`, `ServerOrchestrator`) have **no internal locking** and assume **serial access**. They were designed for single-threaded execution.

### Async + Threading = Potential Race Conditions

`NetworkServer` uses asyncio for WebSocket I/O but offloads blocking game operations to a thread pool:

```python
# In _handle_message()
result = await loop.run_in_executor(
    executor,
    self._orchestrator.submit_action,
    pid,
    action
)
```

**Why use a thread pool?**
- `submit_action()` can trigger `_advance_turn()` → `finish_turn()` + `combat_phase()` + `start_turn()`
- These operations can take **50-500ms** (combat calculations, board updates, etc.)
- Running them in the event loop would **block all WebSocket handlers**
- Thread pool allows event loop to remain responsive

**The race condition risk:**

Without proper serialization, multiple threads could access game state simultaneously:

```python
# Thread A (Client 0 ends turn)
submit_action(0, end_turn)
  → _advance_turn()
    → combat_phase()
      → game.players[0].hp -= 10  # Writing

# Thread B (Client 1 ends turn, overlapping)
submit_action(1, end_turn)
  → _advance_turn()
    → combat_phase()
      → damage = game.players[0].hp  # Reading (stale/torn read!)
```

Even worse:

```python
# Thread A
_generate_snapshots()
  → self._outbox[pid] = snapshot  # Writing to dict

# Event loop thread (simultaneously)
_broadcast_snapshots()
  → snapshots = self._outbox  # Reading dict (race!)
```

### Python GIL is NOT Enough

While Python's Global Interpreter Lock (GIL) prevents some races, it does **not** guarantee safety for:

1. **Complex multi-step mutations** (combat calculations spanning multiple statements)
2. **Dict operations during resize** (can corrupt if accessed during rehashing)
3. **Future asyncio code** that might read game state directly from event loop

Example of GIL failure:

```python
# Thread A
game.players[0].hp = game.players[0].hp - 10  # Multiple bytecode ops

# Thread B (GIL can switch between bytecode ops!)
if game.players[0].hp > 0:  # Reads inconsistent state
    ...
```

## The Solution

### ThreadPoolExecutor(max_workers=1)

```python
# In NetworkServer.__init__()
self._executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="game_worker"
)
```

**Single worker = serial execution guarantee**

- Only **one** game operation runs at a time
- No parallel mutations possible
- Game engine never sees concurrent access
- `_outbox` dict is never accessed from multiple threads simultaneously

### Two-Layer Protection

The implementation uses **two complementary locks**:

#### 1. asyncio.Lock (Async-level serialization)

```python
async with self._action_lock:
    result = await loop.run_in_executor(...)
```

**Purpose:** Prevents race at the async level
- Ensures only one `_handle_message()` coroutine submits actions at a time
- Prevents double `_advance_turn()` when two clients send `end_turn` simultaneously

#### 2. ThreadPoolExecutor(max_workers=1) (Thread-level serialization)

**Purpose:** Prevents race at the thread level
- Ensures game engine is never accessed from multiple threads
- Guarantees serial execution of all game operations
- Protects `_outbox` dict from concurrent access

## Execution Flow

```
Client A sends action
  ↓
NetworkServer._handle_message(ws_a, pid=0, action)
  ↓
async with self._action_lock:  ← LOCK 1: Async serialization
  ↓
  await loop.run_in_executor(
      self._executor,  ← LOCK 2: Single-worker thread pool
      submit_action, 0, action
  )
  ↓
  [Thread pool worker executes:]
    submit_action(0, action)
      → _advance_turn()
        → finish_turn()  [50-100ms]
        → combat_phase()  [100-300ms]
        → start_turn()  [50-100ms]
        → _generate_snapshots()
          → self._outbox[0] = snapshot
          → self._outbox[1] = snapshot
  ↓
  [Back in event loop:]
  await _broadcast_snapshots()
    → snapshots = self._outbox  ← Safe: thread pool idle
    → send to clients
```

**Key insight:** When `_broadcast_snapshots()` reads `_outbox`, the thread pool worker is **guaranteed idle** because:
1. `await run_in_executor()` blocks until worker completes
2. Single worker means no other game operation can be running

## Performance Implications

### Does single-worker limit throughput?

**No, for this use case:**

1. **Game operations are inherently serial**
   - Turn advancement must happen in order
   - Combat calculations depend on current state
   - Parallel execution would cause non-determinism

2. **Event loop handles concurrency**
   - Multiple clients can connect simultaneously
   - WebSocket I/O is fully concurrent
   - Only game mutations are serialized

3. **Typical workload**
   - Most actions are fast (<10ms): buy, reroll, place
   - Slow operations (turn advancement) happen infrequently
   - Single worker is never a bottleneck

### Benchmark Results

From `test_network_nonblocking.py`:

```
Concurrent actions from 2 clients:
- Without thread pool: ~600ms (blocking)
- With thread pool: ~300-400ms (overlapping I/O)
- Event loop responsiveness: 15/20 checks completed (75%)
```

The thread pool **improves** performance by preventing event loop blocking.

## Future-Proofing

The single-worker executor protects against future bugs:

### Scenario 1: Direct State Access

```python
# Future code (hypothetical)
async def get_player_hp(pid):
    # BAD: Direct access from event loop
    return game.players[pid].hp  # Race if thread pool is mutating!
```

With single-worker: Safe, because game mutations are serialized.

### Scenario 2: Parallel Combat

```python
# Future optimization attempt (hypothetical)
async def parallel_combat():
    # BAD: Trying to parallelize combat
    await asyncio.gather(
        run_in_executor(combat_player_0),
        run_in_executor(combat_player_1)
    )
```

With single-worker: Automatically serialized, preventing data corruption.

## Testing

Thread safety is verified by:

1. **test_submit_action_runs_in_executor**
   - Verifies event loop remains responsive during slow operations

2. **test_concurrent_actions_dont_block_each_other**
   - Verifies multiple clients can submit actions concurrently

3. **test_event_loop_not_blocked_during_turn_advancement**
   - Verifies turn advancement doesn't block event loop

4. **test_submit_action_is_thread_safe**
   - Smoke test for basic thread safety

Run tests:
```bash
pytest tests/test_network_nonblocking.py -v
```

## Summary

| Component | Thread-Safe? | Protection Mechanism |
|-----------|--------------|---------------------|
| Game | ❌ No | Single-worker executor |
| GameSession | ❌ No | Single-worker executor |
| ServerOrchestrator | ❌ No | Single-worker executor |
| NetworkServer | ✅ Yes | asyncio.Lock + single-worker executor |

**Key takeaway:** The game engine is **not thread-safe by design**. `NetworkServer` provides thread safety through **controlled serialization** using a single-worker thread pool executor.

## References

- `engine_core/network_server.py` - Implementation
- `tests/test_network_nonblocking.py` - Thread safety tests
- Python threading docs: https://docs.python.org/3/library/threading.html
- asyncio executor docs: https://docs.python.org/3/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools
