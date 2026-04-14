# BAL 5.4.2: Evolver HP-Scaled Economy + Market Refresh Limits

**Date**: 2026-03-29  
**Test Size**: 1000 games, 8 players  
**Seed**: 42

---

## IMPLEMENTATION

### HP-Based Economy Weight
```python
if hp > 75:
    economy_weight = 1.0
    market_refresh_limit = 2
elif hp > 55:
    economy_weight = 0.5
    market_refresh_limit = 3
else:
    economy_weight = 0.0
    market_refresh_limit = 5
```

### Market Refresh Loop
- Evolver now evaluates market multiple times per turn
- High HP (>75): Conservative, only 2 market evaluations
- Medium HP (55-75): Moderate, 3 market evaluations
- Low HP (≤55): Aggressive, up to 5 market evaluations

### Economy Weight Application
- Minimum score threshold = 500 * economy_weight
- High HP: Only buy cards with score ≥ 500 (very selective)
- Medium HP: Only buy cards with score ≥ 250 (moderately selective)
- Low HP: Buy any card with score ≥ 0 (accept anything)

---

## RESULTS

### Win Rates (1000 games)

| Strategy    | Win Rate | Change from BAL 5.4.1 | Wins |
|-------------|----------|----------------------|------|
| **Tempo**       | 35.8%    | -8.0%                | 358  |
| **Evolver**     | 29.6%    | +23.4%               | 296  |
| **Builder**     | 16.5%    | +3.2%                | 165  |
| **Economist**   | 7.8%     | -4.0%                | 78   |
| **Warrior**     | 4.5%     | +0.7%                | 45   |
| **Rare Hunter** | 4.0%     | +0.2%                | 40   |
| **Balancer**    | 1.4%     | -0.1%                | 14   |

### Key Metrics

**Late-Game Combined**: 41.4% (Economist + Evolver + Rare Hunter)
- Previous (BAL 5.4.1): 17.9%
- **Improvement**: +23.5 percentage points (+131% relative)

**Tempo Dominance**: 35.8%
- Previous (BAL 5.4.1): 43.8%
- **Reduction**: -8.0 percentage points (-18% relative)

---

## ANALYSIS

### 🎯 MAJOR SUCCESS: Evolver Breakthrough

**Evolver: 6.2% → 29.6% (+376% improvement!)**

This is the most dramatic improvement we've seen in any balance patch:
- Evolver jumped from 6th place to 2nd place
- Now competitive with Tempo (35.8% vs 29.6%)
- Became the strongest late-game strategy

### Why It Worked

1. **HP-Scaled Aggression**
   - High HP: Evolver saves gold, waits for perfect evolution chains
   - Low HP: Evolver buys aggressively, prioritizes survival
   - This matches Evolver's natural playstyle (patient evolution)

2. **Market Refresh Limits**
   - More market evaluations = more chances to find evolution targets
   - Low HP gets 5 refreshes = desperate search for power
   - High HP gets 2 refreshes = selective, economy-focused

3. **Score Threshold Scaling**
   - High HP: Only buys cards with score ≥ 500 (2-copy or high-tier cards)
   - Low HP: Buys anything (score ≥ 0), including 1-copy cards
   - This prevents "dying rich" problem that plagued Economist

### 🔥 Unexpected Side Effect: Economist Decline

**Economist: 11.8% → 7.8% (-34% relative)**

Economist lost ground despite no direct changes. Possible reasons:
1. **Evolver Competition**: Evolver now competes for same late-game niche
2. **Market Pressure**: Evolver's increased market activity reduces card availability
3. **Meta Shift**: More aggressive Evolver means more early-game pressure

### 📊 Meta Balance

**Current Distribution**:
- Tempo (early-game): 35.8%
- Evolver (late-game): 29.6%
- Builder (mid-game): 16.5%
- Others: 18.1%

**Balance Assessment**:
- ✅ Late-game strategies now viable (41.4% combined)
- ✅ Tempo no longer overwhelming (35.8% vs previous 43.8%)
- ⚠️ Evolver might be slightly too strong (29.6% is high for a single strategy)
- ⚠️ Economist needs attention (7.8% is low)

---

## COMPARISON WITH PREVIOUS PATCHES

| Patch | Tempo | Evolver | Economist | Late-Game Total |
|-------|-------|---------|-----------|-----------------|
| BAL 5.3 | 46.2% | 6.2%    | 4.4%      | 13.3%           |
| BAL 5.4.1 | 43.8% | 6.2%    | 11.8%     | 17.9%           |
| **BAL 5.4.2** | **35.8%** | **29.6%**   | **7.8%**      | **41.4%**       |

**Progress**:
- Tempo reduced by 10.4 percentage points (22% relative reduction)
- Late-game improved by 28.1 percentage points (211% relative improvement)
- Meta diversity significantly improved

---

## TECHNICAL DETAILS

### Code Changes

**File**: `engine_core/autochess_sim_v06.py`  
**Function**: `AI._buy_evolver()`

**Changes**:
1. Added HP-based economy_weight calculation (3 thresholds: 75, 55)
2. Added market_refresh_limit based on HP (2/3/5)
3. Implemented market refresh loop (replaces single-pass buying)
4. Added score threshold scaling (500 * economy_weight)
5. Preserved all existing logic (bench efficiency, evolution priority, etc.)

**Lines Modified**: ~50 lines in `_buy_evolver()` function

### Negative Constraints Honored

✅ Did NOT change other strategy parameters  
✅ Did NOT modify risk evaluation beyond economy_weight  
✅ Did NOT change Rare Hunter, Balancer, Warrior, or Builder  
✅ Did NOT implement additional heuristics  
✅ Did NOT modify card evaluation logic  
✅ Preserved original Evolver decision flow  

---

## RECOMMENDATIONS

### Immediate Actions

1. **Monitor Evolver**: 29.6% is strong but not broken. Watch for dominance in larger samples.

2. **Investigate Economist**: Why did Economist decline? Possible fixes:
   - Reduce Economist's opportunity cost multipliers further
   - Adjust Economist's HP thresholds (currently 85/75/55/45/35)
   - Consider giving Economist similar market refresh limits

3. **Test Larger Sample**: Run 2000-game simulation to confirm results

### Future Considerations

1. **Evolver Tuning** (if needed):
   - Adjust HP thresholds (75/55 → 80/60?)
   - Reduce market_refresh_limit (2/3/5 → 2/3/4?)
   - Increase score threshold multiplier (500 → 600?)

2. **Economist Recovery**:
   - Apply similar market refresh logic to Economist
   - Reduce opportunity cost multipliers (2/4/6 → 1.5/3/4.5?)
   - Adjust HP thresholds for more aggressive play

3. **Meta Diversity**:
   - Consider buffing Rare Hunter (still at 4.0%)
   - Consider buffing Balancer (still at 1.4%)
   - Warrior and Builder seem reasonably balanced

---

## CONCLUSION

BAL 5.4.2 is a **major success** for Evolver strategy:
- Evolver improved by 376% (6.2% → 29.6%)
- Late-game strategies now viable (41.4% combined)
- Tempo dominance reduced (43.8% → 35.8%)
- Meta diversity significantly improved

The HP-scaled economy weight system proved highly effective for Evolver's playstyle. The market refresh limits gave Evolver the flexibility to adapt between patient evolution (high HP) and desperate survival (low HP).

**Next Steps**: Monitor Economist's decline and consider applying similar market refresh logic to help Economist recover.

---

**Implementation Status**: ✅ Complete  
**Testing Status**: ✅ Verified (1000 games)  
**Recommendation**: ✅ Keep changes, monitor Economist
