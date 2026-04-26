# Code Cleanup Fixes Summary

## Changes Made

### 1. Fixed Duplicate Condition in `_passive_frida_kahlo`

**Issue:** The condition had a duplicate: `if trigger in ("combat_lose", "combat_lose"):`

**Fix:**
```python
def _passive_frida_kahlo(card, trigger, owner, opponent, ctx):
    # Fires on combat_lose (originally in both combat and survival passive_type branches)
    if trigger == "combat_lose":
        for i, (s, v) in enumerate(card.edges):
            if v == 0:
                card.edges[i] = (s, 1)
                card.stats[s] = 1
                break
    return 0
```

**Explanation:** 
- Changed from `if trigger in ("combat_lose", "combat_lose"):` to `if trigger == "combat_lose":`
- Added comment explaining that this handler covers both the combat and survival passive_type contexts
- Functionally equivalent (same trigger name in both original branches), but cleaner code

### 2. Optimized `trigger_passive()` Function

**Issue:** The `safe_name` computation appeared to be only for verbose output, but it's actually used for both verbose printing and the `_passive_trigger_log`.

**Current Implementation:**
```python
def trigger_passive(card: "Card", trigger: str, owner, opponent, ctx: dict, verbose: bool = False) -> int:
    # Compute safe_name only once (used for logging and verbose output)
    safe_name = card.name.encode('ascii', 'ignore').decode('ascii')
    if verbose:
        print(f"[PASSIVE] {safe_name} | {trigger}")
    res = _trigger_passive_impl(card, trigger, owner, opponent, ctx)
    if verbose:
        print(f"[EFFECT] {safe_name} -> {res}")
    # Log passive trigger
    _passive_trigger_log[safe_name][trigger] += 1
    return res
```

**Explanation:**
- Added comment clarifying that `safe_name` is computed once and reused
- Cannot move inside verbose guard because it's also needed for `_passive_trigger_log`
- The `_passive_trigger_log` is used for game statistics reporting (passive trigger counts, combat win rates)
- Current implementation is already optimal: compute once, use twice

### 3. Documented `verbose=False` in `Player.buy_card()`

**Issue:** The `trigger_passive` call for `card_buy` hardcodes `verbose=False` without explanation.

**Fix:**
```python
turn = self.turns_played if self.turns_played > 0 else 1
for board_card in self.board.alive_cards():
    # card_buy fires per-purchase; kept silent to avoid log flood
    trigger_passive(board_card, "card_buy", self, None, {
        "turn": turn,
        "bought_card": cloned
    }, verbose=False)
```

**Explanation:**
- Added comment explaining why `verbose=False` is hardcoded
- `card_buy` can fire multiple times per turn (once per card purchased)
- Keeping it silent prevents log flooding during verbose mode
- Player class has no `verbose` attribute, so this is the correct approach

## Verification

All changes verified:
- ✓ No syntax errors
- ✓ No diagnostic issues
- ✓ Code clarity improved
- ✓ No functional changes to game logic
- ✓ Comments added for better code documentation

## Files Modified

1. `src/autochess_sim_v06.py`
   - `_passive_frida_kahlo()`: Fixed duplicate condition, added comment
   - `trigger_passive()`: Added clarifying comment about safe_name usage
   - `Player.buy_card()`: Added comment explaining verbose=False
