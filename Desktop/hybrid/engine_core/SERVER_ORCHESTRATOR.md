# ServerOrchestrator — Turn Flow Management

## Overview

`ServerOrchestrator` manages server-side turn orchestration for multiplayer games without any network code. It wraps a `GameSession` and handles:

- Action submission with validation
- Turn advancement when all players are ready
- State snapshot generation and distribution

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ServerOrchestrator                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │           GameSession                          │    │
│  │  ┌──────────────────────────────────────┐     │    │
│  │  │         Game (engine)                │     │    │
│  │  └──────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────┐     │    │
│  │  │    ICommandDispatcher                │     │    │
│  │  └──────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         Outbox (pid → snapshot dict)           │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Action Submission

Players submit actions as dicts:

```python
# Buy action
{"type": "buy", "slot": 2}

# Reroll action
{"type": "reroll"}

# Place action
{"type": "place", "hand_index": 1, "coord": [2, -1], "rotation": 3}

# End turn action
{"type": "end_turn"}
```

All actions are validated and executed through the dispatcher.

### 2. Turn Advancement

When all alive players submit "end_turn":
1. `GameSession.mark_ready()` returns `True`
2. `_advance_turn()` is triggered automatically
3. Turn progression sequence executes:
   - `game.finish_turn()` — commit boards, apply effects
   - `game.combat_phase()` — run combat
   - `game.start_turn()` — deal gold, refresh shops
4. Snapshots are generated for all alive players

### 3. State Snapshots

Two modes for snapshot generation:

**Minimal Mode (no state_builder):**
```python
orchestrator = ServerOrchestrator(session)
# Generates basic dicts with essential game state
```

**Full Mode (with GameState builder):**
```python
orchestrator = ServerOrchestrator(session, state_builder=game_state)
# Generates full PublicState snapshots via to_dict()
```

### 4. Outbox Pattern

Snapshots are queued in an outbox that the network layer polls:

```python
# Network layer polls for snapshots
snapshots = orchestrator.pop_outbox()  # Returns dict[pid, snapshot_dict]

# Distribute to clients
for pid, snapshot_dict in snapshots.items():
    send_to_client(pid, snapshot_dict)

# Outbox is cleared after pop
```

## Usage Example

```python
from engine_core.game import Game
from engine_core.game_session import GameSession
from engine_core.server_orchestrator import ServerOrchestrator
from v2.core.local_dispatcher import LocalCommandDispatcher
from v2.core.engine_adapter import EngineAdapter

# Setup game
game = Game(num_players=2)
adapter = EngineAdapter(game)
dispatcher = LocalCommandDispatcher(adapter)
session = GameSession(game, dispatcher)
orchestrator = ServerOrchestrator(session)

# Player 0 buys a card
result = orchestrator.submit_action(0, {"type": "buy", "slot": 2})
assert result == ActionResult.OK

# Player 0 ends turn
orchestrator.submit_action(0, {"type": "end_turn"})

# Player 1 ends turn (triggers turn advancement)
orchestrator.submit_action(1, {"type": "end_turn"})

# Network layer polls for snapshots
snapshots = orchestrator.pop_outbox()
# snapshots = {0: {...}, 1: {...}}
```

## Validation Rules

### Eliminated Players
Actions from eliminated players are rejected with `ERR_NOT_IN_PREP_PHASE`:

```python
# Player 1 is dead
result = orchestrator.submit_action(1, {"type": "buy", "slot": 0})
# Returns: ActionResult.ERR_NOT_IN_PREP_PHASE
```

### Invalid PIDs
Actions from non-existent players return `ERR_ENGINE_EXCEPTION`:

```python
result = orchestrator.submit_action(999, {"type": "buy", "slot": 0})
# Returns: ActionResult.ERR_ENGINE_EXCEPTION
```

### Coord Conversion
Place actions automatically convert coord lists to tuples:

```python
# JSON sends lists
orchestrator.submit_action(0, {
    "type": "place",
    "hand_index": 1,
    "coord": [2, -1],  # List from JSON
    "rotation": 3
})
# Internally converted to tuple (2, -1) for dispatcher
```

## Design Constraints

- **Zero network code** — pure turn orchestration
- **Transport-agnostic** — works with any network layer
- **Mutation safety** — all actions go through dispatcher
- **Thread-unsafe** — same as Game and GameSession

## Testing

See `tests/test_server_orchestrator.py` for comprehensive test coverage:

- Turn advancement triggers
- Snapshot generation and distribution
- Eliminated player handling
- Action delegation to dispatcher
- Coord list-to-tuple conversion
- Unknown action type handling
- Invalid PID handling
- Snapshot serialization round-trip

All tests pass with 100% coverage of core functionality.

## Next Steps

This module is ready for network layer integration. The network layer should:

1. Receive action messages from clients
2. Call `orchestrator.submit_action(pid, action_dict)`
3. Poll `orchestrator.pop_outbox()` periodically
4. Distribute snapshots to clients

No changes to ServerOrchestrator are needed for network integration.
