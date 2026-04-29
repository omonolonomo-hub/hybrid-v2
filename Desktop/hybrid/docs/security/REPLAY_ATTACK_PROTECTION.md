# Replay Attack Protection

## Overview

The game server implements sequence number-based replay attack protection to prevent malicious clients from re-sending the same action multiple times. This is critical for turn-based games where duplicate `end_turn` actions could cause unintended turn progression.

## The Vulnerability

**Before the fix:**
```python
# Client sends end_turn
{"type": "end_turn"}

# Malicious client replays the same packet
{"type": "end_turn"}  # Would be processed again!
```

If a client sent the same `end_turn` packet twice, the server would process it twice. In a 2-player game:
1. Player 0 sends `end_turn` (ready count: 1/2)
2. Player 0 replays `end_turn` (ready count: 2/2) ← **Turn advances prematurely!**
3. Player 1 never got a chance to act

## The Solution: Sequence Numbers

Each client action now includes an optional `seq` field with a strictly increasing integer:

```python
# Turn 1
{"type": "end_turn", "seq": 1}

# Turn 2
{"type": "end_turn", "seq": 2}

# Turn 3
{"type": "end_turn", "seq": 3}
```

The server tracks the last seen sequence number for each player and rejects any action with a sequence number ≤ the last seen value.

## Implementation

### GameSession

`GameSession` maintains a `_last_seq` dictionary mapping player IDs to their last seen sequence number:

```python
class GameSession:
    def __init__(self, game, dispatcher=None):
        # ...
        self._last_seq: Dict[int, int] = {player.pid: -1 for player in game.players}
    
    def mark_ready(self, pid: int, seq_no: Optional[int] = None) -> bool:
        # Replay attack protection
        if seq_no is not None:
            last_seq = self._last_seq.get(pid, -1)
            if seq_no <= last_seq:
                raise ValueError(f"Replay attack detected: pid={pid} sent seq_no={seq_no} but last_seq={last_seq}")
            self._last_seq[pid] = seq_no
        
        # ... rest of ready logic
```

### ServerOrchestrator

`ServerOrchestrator` extracts the `seq` field from actions and passes it to `GameSession`:

```python
def submit_action(self, pid: int, action: Dict[str, Any]) -> ActionResult:
    # Extract optional sequence number
    seq_no = action.get("seq")
    
    # Validate seq is integer (not bool, not string)
    if seq_no is not None and (isinstance(seq_no, bool) or not isinstance(seq_no, int)):
        return ActionResult.ERR_ENGINE_EXCEPTION
    
    if action_type == "end_turn":
        return self._handle_end_turn(pid, seq_no=seq_no)
```

### Error Handling

When a replay attack is detected:
1. `GameSession.mark_ready()` raises `ValueError`
2. `ServerOrchestrator._handle_end_turn()` catches it and returns `ActionResult.ERR_ENGINE_EXCEPTION`
3. Client receives `{"type": "action_result", "ok": false, "error": "ERR_ENGINE_EXCEPTION"}`

## Protocol

### Client → Server

```json
{
  "type": "action",
  "action": {
    "type": "end_turn",
    "seq": 42
  }
}
```

### Server → Client (Success)

```json
{
  "type": "action_result",
  "ok": true,
  "error": null
}
```

### Server → Client (Replay Attack Detected)

```json
{
  "type": "action_result",
  "ok": false,
  "error": "ERR_ENGINE_EXCEPTION"
}
```

## Client Implementation Guidelines

### Recommended: Always Use Sequence Numbers

```python
class GameClient:
    def __init__(self):
        self._seq = 0
    
    async def end_turn(self):
        self._seq += 1
        await self.send_action({
            "type": "end_turn",
            "seq": self._seq
        })
```

### Backward Compatible: Optional Sequence Numbers

For testing or local games, sequence numbers are optional:

```python
# Still works (no replay protection)
await client.send_action({"type": "end_turn"})
```

## Security Properties

### ✅ Prevents Replay Attacks
- Duplicate packets are rejected
- Out-of-order packets are rejected
- Each action can only be processed once

### ✅ Per-Player Tracking
- Each player's sequence numbers are independent
- Player 0 can use seq=1 while Player 1 uses seq=100

### ✅ Backward Compatible
- Sequence numbers are optional
- Existing clients without seq support still work
- No breaking changes to protocol

### ✅ Zero-Based or One-Based
- Clients can start at seq=0 or seq=1
- Initial value is -1, so both are valid

## Testing

Comprehensive test coverage in:
- `tests/test_replay_attack_protection.py` - GameSession level
- `tests/test_server_orchestrator_replay_protection.py` - Integration level

Key test cases:
- ✅ Duplicate sequence numbers rejected
- ✅ Lower sequence numbers rejected
- ✅ Valid increasing sequences accepted
- ✅ Per-player independence
- ✅ Backward compatibility (optional seq)
- ✅ Turn progression with seq protection
- ✅ Replay attacks don't trigger turn advancement

## Future Enhancements

### Potential Improvements

1. **Extend to All Actions**
   - Currently only `end_turn` uses seq_no
   - Could extend to `buy`, `reroll`, `place` for full protection

2. **Sequence Number Reset**
   - Consider resetting seq numbers at turn boundaries
   - Would allow smaller numbers (0-10 per turn vs 0-1000 per game)

3. **Gap Detection**
   - Detect missing sequence numbers (e.g., 1, 2, 4 - where's 3?)
   - Could indicate packet loss or client bugs

4. **Timestamp-Based Protection**
   - Add timestamp validation alongside seq numbers
   - Reject actions with timestamps too far in the past

## References

- [OWASP: Replay Attack](https://owasp.org/www-community/attacks/Replay_attack)
- [RFC 4949: Internet Security Glossary](https://tools.ietf.org/html/rfc4949)
- [Sequence Number Verification in Network Protocols](https://en.wikipedia.org/wiki/Sequence_number)
