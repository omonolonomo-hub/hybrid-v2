# Serialization Layer Implementation

**Status:** ✅ Complete  
**Date:** 2026-04-28  
**Module:** `v2/core/serialization.py`  
**Tests:** `tests/test_serialization.py`

## Overview

Implemented JSON serialization layer for `PublicState` and `ActionLog` records with zero network code. Pure data transformation using standard library only.

## Implementation

### Core Functions

#### PublicState Serialization
- `to_dict(state: PublicState) → dict` - Convert PublicState to JSON-compatible dict
- `from_dict(data: dict) → PublicState` - Reconstruct PublicState from JSON dict

#### ActionLog Serialization
- `action_to_dict(record) → dict` - Convert ActionEntry to JSON-compatible dict
- `action_from_dict(data: dict) → record` - Reconstruct ActionEntry from JSON dict

### Key Features

1. **Lossless Round-Trip**
   - `from_dict(to_dict(state)) == state` guaranteed
   - All data types preserved correctly
   - No information loss during serialization

2. **Coordinate Handling**
   - Tuple coords `(q, r)` → string keys `"q,r"` in JSON
   - Restored to tuples on deserialization
   - Works for board_cards, board_rotations, board_card_info

3. **Nested Structures**
   - Handles nested dataclasses (ShopViewState, HandViewState, etc.)
   - Preserves tuple structures (pairings, adjacency_pairs, etc.)
   - Converts MappingProxyType to dict for JSON compatibility

4. **Standard Library Only**
   - Uses `json`, `dataclasses.asdict`
   - No external dependencies
   - No network code

## Test Coverage

### Test Suite (`tests/test_serialization.py`)

✅ **9 tests, all passing:**

1. `test_public_state_round_trip` - Full PublicState serialization with real game data
2. `test_action_entry_round_trip` - ActionEntry serialization
3. `test_coord_serialization` - Tuple coord conversion (q,r) ↔ "q,r"
4. `test_nested_tuples_preserved` - Pairings and adjacency_pairs structure
5. `test_shop_slots_preserved` - Shop/hand slots with None values
6. `test_synergy_groups_preserved` - Synergy groups with color tuples
7. `test_empty_board_serialization` - Edge case: no cards placed
8. `test_multiple_actions_serialization` - Multiple ActionEntry records
9. `test_card_info_serialization` - Card info dicts with coord keys

### Test Approach

- Uses real `Game` instances for realistic data
- Verifies JSON serialization with `json.dumps()` / `json.loads()`
- Checks equality after round-trip
- Validates specific field types and structures

## Usage Example

```python
from v2.core.serialization import to_dict, from_dict
from v2.core.ui_adapter import UIAdapter

# Build PublicState
adapter = EngineAdapter(game)
store = StateStore()
formatter = UIFormatter()
ui_adapter = UIAdapter()
state = ui_adapter.build_public_state(adapter, store, formatter)

# Serialize to JSON
state_dict = to_dict(state)
json_str = json.dumps(state_dict)

# Send over network...

# Deserialize from JSON
restored_dict = json.loads(json_str)
restored_state = from_dict(restored_dict)

# restored_state == state (guaranteed)
```

## ActionLog Example

```python
from v2.core.serialization import action_to_dict, action_from_dict
from engine_core.action_log import ActionEntry

# Create action
action = ActionEntry(
    action_type="place_card",
    params={"pid": 0, "hand_idx": 0, "coord": (0, 0), "rotation": 2},
    turn=5,
    sub_turn=3
)

# Serialize
action_dict = action_to_dict(action)
json_str = json.dumps(action_dict)

# Deserialize
restored_dict = json.loads(json_str)
restored_action = action_from_dict(restored_dict)

# Coord tuple preserved: restored_action.params["coord"] == (0, 0)
```

## Design Decisions

### Why String Keys for Coords?

JSON doesn't support tuple keys in objects. We use `"q,r"` format:
- Simple and readable
- Easy to parse back to tuples
- No ambiguity with comma separator

### Why MappingProxyType Handling?

`PublicState` uses `MappingProxyType` for immutability. We:
- Convert to dict during serialization (via `asdict()`)
- Restore as `MappingProxyType` via `ActivePlayerViewState.__post_init__()`
- Tests accept both `dict` and `MappingProxyType` as valid

### Why No Card Objects?

Card references are serialized as `card.name` strings only:
- Avoids circular references
- Reduces payload size
- Card data can be looked up from CardDatabase on client side

## Constraints Met

✅ Standard library only (json, dataclasses)  
✅ Tuple coords → list in JSON, restored to tuple  
✅ Card references → card.name string only  
✅ Lossless round-trip verified  
✅ Zero network code  
✅ No external dependencies  

## Next Steps

This serialization layer is ready for:
- Network protocol implementation
- Replay system
- State persistence
- Client-server synchronization

The layer is completely decoupled from network concerns and can be used with any transport mechanism (WebSockets, HTTP, etc.).
