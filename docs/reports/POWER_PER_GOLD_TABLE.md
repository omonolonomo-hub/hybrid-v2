# Power Per Gold Efficiency Table

## Quick Reference

### Before Rebalance

```
╔════════╦═══════════╦══════╦═════════════╦═══════════════════╗
║ Rarity ║ Avg Power ║ Cost ║ Power/Gold  ║ Efficiency vs r1  ║
╠════════╬═══════════╬══════╬═════════════╬═══════════════════╣
║   r1   ║   29.00   ║  1g  ║    29.00    ║   1.00x (base)    ║
║   r2   ║   32.76   ║  2g  ║    16.38    ║      0.56x        ║
║   r3   ║   38.03   ║  3g  ║    12.68    ║      0.44x        ║
║   r4   ║   44.31   ║  8g  ║     5.54    ║   0.19x ⚠️ BROKEN ║
║   r5   ║   49.33   ║ 10g  ║     4.93    ║   0.17x ⚠️ BROKEN ║
╚════════╩═══════════╩══════╩═════════════╩═══════════════════╝
```

### After Rebalance

```
╔════════╦═══════════╦══════╦═════════════╦═══════════════════╗
║ Rarity ║ Avg Power ║ Cost ║ Power/Gold  ║ Efficiency vs r1  ║
╠════════╬═══════════╬══════╬═════════════╬═══════════════════╣
║   r1   ║   29.00   ║  1g  ║    29.00    ║   1.00x (base)    ║
║   r2   ║   32.76   ║  2g  ║    16.38    ║      0.56x        ║
║   r3   ║   38.03   ║  3g  ║    12.68    ║      0.44x        ║
║   r4   ║   44.31   ║  5g  ║     8.86    ║   0.31x ✅ FIXED  ║
║   r5   ║   49.33   ║  7g  ║     7.05    ║   0.24x ✅ FIXED  ║
╚════════╩═══════════╩══════╩═════════════╩═══════════════════╝
```

## Comparison

```
╔════════╦═════════╦═════════╦═════════╦═════════╦══════════╗
║ Rarity ║ Old PPG ║ New PPG ║  Change ║ Old Eff ║ New Eff  ║
╠════════╬═════════╬═════════╬═════════╬═════════╬══════════╣
║   r1   ║  29.00  ║  29.00  ║   +0%   ║  1.00x  ║  1.00x   ║
║   r2   ║  16.38  ║  16.38  ║   +0%   ║  0.56x  ║  0.56x   ║
║   r3   ║  12.68  ║  12.68  ║   +0%   ║  0.44x  ║  0.44x   ║
║   r4   ║   5.54  ║   8.86  ║  +60%   ║  0.19x  ║  0.31x   ║
║   r5   ║   4.93  ║   7.05  ║  +43%   ║  0.17x  ║  0.24x   ║
╚════════╩═════════╩═════════╩═════════╩═════════╩══════════╝
```

## Cost Changes

```
╔════════╦══════════╦══════════╦═══════════════╗
║ Rarity ║ Old Cost ║ New Cost ║    Change     ║
╠════════╬══════════╬══════════╬═══════════════╣
║   r1   ║    1g    ║    1g    ║  unchanged    ║
║   r2   ║    2g    ║    2g    ║  unchanged    ║
║   r3   ║    3g    ║    3g    ║  unchanged    ║
║   r4   ║    8g    ║    5g    ║  -37.5% ✅    ║
║   r5   ║   10g    ║    7g    ║  -30.0% ✅    ║
╚════════╩══════════╩══════════╩═══════════════╝
```

## Strategy Impact: rare_hunter

```
╔═══════════════╦════════╦════════╦═══════════╗
║    Metric     ║ Before ║ After  ║  Change   ║
╠═══════════════╬════════╬════════╬═══════════╣
║  Win Rate     ║  10%   ║  20%   ║  +100%    ║
║  Avg HP       ║  14.3  ║  24.5  ║   +71%    ║
║  Avg Damage   ║ 121.2  ║ 159.0  ║   +31%    ║
║  Status       ║ Stalls ║ Viable ║  FIXED ✅ ║
╚═══════════════╩════════╩════════╩═══════════╝
```

## Implementation

```python
# OLD
CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 8, "5": 10, "E": 0}

# NEW
CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0}
```

## Key Takeaways

✅ r4 efficiency improved by 60% (5.54 → 8.86 power/gold)  
✅ r5 efficiency improved by 43% (4.93 → 7.05 power/gold)  
✅ rare_hunter win rate doubled (10% → 20%)  
✅ Rare cards now accessible mid-game  
✅ Better cost/power balance across all rarities  
✅ Shop roll odds unchanged  
✅ Card power values intact  

---

Generated: 2026-03-29  
Analysis Tool: `tools/analyze_rarity_balance.py`
