# CardPool Prototype Mutation Fix

## The Problem

Two critical issues in the singleton pattern implementation:

### 1. Shared Prototype Mutation
- `CardPool._instance` stored a single list of Card objects
- `apply_micro_buff_to_weak_cards()` mutated these cards in-place on first call
- All simulations, all Game instances shared the same prototype pool
- While `Card.clone()` currently copies base stats safely, any future Card method that mutates the prototype would cause cross-game contamination

### 2. Dead Global Signal Bus
```python
# signals.py (bottom of file)
engine_signals = SignalBus()  # ← Never used
```
- No component connects to this global instance
- Real bus is `game.signals` (per-game instance)
- Misleading for future developers who might connect observers to the wrong bus

## The Fix

### CardPool: Return Fresh Copies
```python
@classmethod
def instance(cls) -> List[Card]:
    """
    Get a fresh copy of the card pool.
    Creates and buffs template cards on first call, returns cloned copies thereafter.
    
    Returns clones to prevent cross-game contamination from in-place mutations.
    """
    if cls._instance is None:
        pool = build_card_pool()
        apply_micro_buff_to_weak_cards(pool)
        cls._instance = pool  # Store as immutable template
    return [c.clone() for c in cls._instance]  # Return fresh copies
```

**Key change:** `return [c.clone() for c in cls._instance]` instead of `return cls._instance`

### signals.py: Remove Dead Global
Removed the unused `engine_signals = SignalBus()` global instance.

## Impact

- **Prevents future bugs:** If card crafting system is added (item + card fusion), mutations won't leak across games
- **Clearer architecture:** SignalBus is explicitly per-game, no misleading globals
- **Minimal performance cost:** Cloning ~100 cards per game initialization is negligible
- **Test isolation:** Each test gets truly independent card pools

## Future-Proofing

If card crafting/modification is implemented:
- Modifications happen on cloned instances only
- Original template pool remains pristine
- No cross-contamination between parallel simulations
