# Replay Attack Protection - Quick Reference

## TL;DR

Add `"seq": <number>` to your actions. Server rejects duplicates.

```python
# ✅ Good
{"type": "end_turn", "seq": 1}
{"type": "end_turn", "seq": 2}
{"type": "end_turn", "seq": 3}

# ❌ Bad (replay attack)
{"type": "end_turn", "seq": 1}
{"type": "end_turn", "seq": 1}  # Rejected!
```

## For Client Developers

### Option 1: Use NetworkClient (Automatic)

```python
from engine_core.network_client import NetworkClient

# Sequence numbers added automatically
client = NetworkClient(pid=0, use_seq=True)  # default
await client.send_action({"type": "end_turn"})
# Sends: {"type": "end_turn", "seq": 1}
```

### Option 2: Manual Implementation

```python
class MyClient:
    def __init__(self):
        self.seq = 0
    
    async def send_action(self, action):
        self.seq += 1
        action["seq"] = self.seq
        await self.websocket.send(json.dumps({
            "type": "action",
            "action": action
        }))
```

## For Server Developers

### No Changes Needed

Server automatically validates sequence numbers:

```python
orchestrator = ServerOrchestrator(session)
result = orchestrator.submit_action(pid, action)
# Returns ERR_ENGINE_EXCEPTION if replay detected
```

## Protocol

### Request
```json
{
  "type": "action",
  "action": {
    "type": "end_turn",
    "seq": 42
  }
}
```

### Response (Success)
```json
{
  "type": "action_result",
  "ok": true,
  "error": null
}
```

### Response (Replay Detected)
```json
{
  "type": "action_result",
  "ok": false,
  "error": "ERR_ENGINE_EXCEPTION"
}
```

## Rules

1. **Strictly Increasing**: Each seq must be > previous seq
2. **Per-Player**: Each player has independent sequence numbers
3. **Optional**: Backward compatible - works without seq
4. **Integer Only**: Must be int (not bool, string, float)
5. **Start Anywhere**: Can start at 0, 1, or any number

## Testing

```bash
# Run all replay protection tests
pytest tests/test_replay_attack_protection.py -v

# Run demo
python -m examples.replay_attack_demo
```

## Common Mistakes

### ❌ Reusing Sequence Numbers
```python
# Wrong - same seq for different actions
send({"type": "buy", "slot": 0, "seq": 1})
send({"type": "end_turn", "seq": 1})  # Rejected!
```

### ✅ Increment for Every Action
```python
# Correct - increment for each action
send({"type": "buy", "slot": 0, "seq": 1})
send({"type": "end_turn", "seq": 2})  # OK
```

### ❌ Resetting Sequence Numbers
```python
# Wrong - don't reset mid-game
self.seq = 5
send({"type": "end_turn", "seq": 5})
self.seq = 0  # Don't do this!
send({"type": "end_turn", "seq": 0})  # Rejected!
```

### ✅ Keep Incrementing
```python
# Correct - never reset
self.seq = 5
send({"type": "end_turn", "seq": 5})
self.seq = 6
send({"type": "end_turn", "seq": 6})  # OK
```

## Debugging

### Check Last Seen Sequence
```python
session = GameSession(game)
last_seq = session.get_last_seq(player_id)
print(f"Last seq for player {player_id}: {last_seq}")
```

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Will show: "_handle_end_turn: replay attack from pid=X"
```

## FAQ

**Q: Do I need to use sequence numbers?**  
A: Optional but strongly recommended for multiplayer games.

**Q: What happens if I don't use seq?**  
A: Actions still work, but no replay protection.

**Q: Can I start at seq=0?**  
A: Yes, any starting number works (initial value is -1).

**Q: Do sequence numbers reset each turn?**  
A: No, keep incrementing throughout the game.

**Q: What if I skip a number (1, 2, 4)?**  
A: Currently allowed. Gap detection is a future enhancement.

**Q: Can different players use the same seq?**  
A: Yes, sequence numbers are tracked per-player independently.

## More Info

- Full docs: `docs/security/REPLAY_ATTACK_PROTECTION.md`
- Implementation: `docs/security/REPLAY_ATTACK_FIX_SUMMARY.md`
- Demo: `examples/replay_attack_demo.py`
