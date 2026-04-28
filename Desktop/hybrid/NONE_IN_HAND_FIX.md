# None-in-Hand AttributeError Fix

## Problem

The game was crashing with an `AttributeError: 'NoneType' object has no attribute 'rarity'` when AI strategies tried to place cards from the player's hand.

### Error Trace
```
File "engine_core/ai/strategies/random.py", line 73, in <lambda>
    key=lambda c: (1 if c.rarity == "E" else 0, c.total_power()),
                       ^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'rarity'
```

## Root Cause

The `Inventory` class uses `None` values as placeholders in `player.hand` to maintain positional integrity for UI drag-drop operations. When cards are removed from the hand (e.g., when placed on the board), the slot is set to `None` rather than removing the element from the list.

However, AI strategies were not filtering out these `None` values before processing the hand, causing them to try to access attributes on `None` objects.

## Solution

Updated all AI strategy placement functions to filter out `None` values before processing:

### Files Modified

1. **engine_core/ai/strategies/random.py**
   - `_place_smart_default()`: Added `valid_hand = [c for c in player.hand if c is not None]`
   - Changed hand removal from `player.hand.remove(card)` to setting the slot to `None`

2. **engine_core/ai/strategies/tempo.py**
   - `_place_aggressive()`: Added `valid_hand` filtering
   - Changed hand removal to use None-slot system

3. **engine_core/ai/strategies/builder.py**
   - `_place_fast_synergy()`: Added `hand_list` filtering
   - `_place_combo_optimized()`: Added `hand_list` filtering
   - Changed hand removal to use None-slot system in both functions

### Strategies Covered

The fix covers all AI strategies:
- ✅ **random** - Fixed directly in `_place_smart_default()`
- ✅ **warrior** - Uses `_place_smart_default()` (fixed)
- ✅ **economist** - Uses `_place_smart_default()` (fixed)
- ✅ **evolver** - Uses `_place_smart_default()` (fixed)
- ✅ **balancer** - Uses `_place_smart_default()` (fixed)
- ✅ **rare_hunter** - Uses `_place_smart_default()` (fixed)
- ✅ **tempo** - Fixed directly in `_place_aggressive()`
- ✅ **builder** - Fixed directly in `_place_fast_synergy()` and `_place_combo_optimized()`

## Testing

Created `test_none_hand_fix.py` to verify the fix:
- Tests all three placement function types with hands containing `None` values
- All tests pass successfully
- No more AttributeError when processing hands with None placeholders

## Impact

- **Backward Compatible**: The fix maintains the positional integrity system used by the UI
- **Performance**: Minimal impact - just adds a list comprehension filter
- **Reliability**: Prevents crashes when AI strategies process hands with empty slots
