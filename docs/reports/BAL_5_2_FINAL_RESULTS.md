# BAL 5.2 - Final Results (2000 Games Total)

## Test Summary

**Total Games:** 2,000 (2x 1000-game tests)  
**Players per Game:** 8  
**Total Player Instances:** 16,000  
**Date:** March 29, 2026  
**Version:** Autochess Hybrid v0.6 - BAL 5.2

---

## Implemented Changes

### 1. Win Streak Gold Nerf
- **Old:** +1 gold per 3 wins (unlimited)
- **New:** +1 gold per 6 wins (max 2 gold cap)
- **Reduction:** 50% nerf + hard cap

### 2. Lose Streak Bonus (Comeback Mechanic)
- **New:** +1 gold per 2 consecutive losses (max 3 gold)
- **Goal:** Help late-game strategies survive

### 3. Dynamic Unit Scaling (Coordination Penalty)
- **Mechanic:** -5% power per extra unit beyond 3-unit advantage
- **Max Penalty:** -50% power (at 13+ unit advantage)
- **Goal:** Prevent stat-check dominance

---

## Final Results (Average of 2000 Games)

| Strategy | Test 1 | Test 2 | Average | vs BAL 5.1 | Status |
|----------|--------|--------|---------|------------|--------|
| **Tempo** | 46.2% | 44.3% | **45.3%** | +0.5% | 🔴 STILL DOMINANT |
| **Builder** | 29.8% | 30.4% | **30.1%** | +4.0% | 🟡 STRONGER |
| Rare Hunter | 7.6% | 7.4% | **7.5%** | -1.5% | 🔵 WEAKER |
| Warrior | 5.9% | 7.3% | **6.6%** | +1.6% | 🟢 IMPROVED |
| Economist | 3.0% | 4.4% | **3.7%** | -0.6% | 🔵 WEAKER |
| Evolver | 3.6% | 3.3% | **3.5%** | -2.0% | 🔴 MUCH WEAKER |
| Balancer | 3.2% | 2.4% | **2.8%** | -1.7% | 🔴 MUCH WEAKER |
| Random | 0.7% | 0.5% | **0.6%** | -0.2% | 🔵 BASELINE |

---

## Performance Metrics Comparison

### Tempo Strategy

| Metric | BAL 5.1 | BAL 5.2 (Avg) | Change |
|--------|---------|---------------|--------|
| Win Rate | 44.8% | 45.3% | +0.5% 🔴 |
| Avg Damage | 257.1 | 286.3 | +29.2 🔴 |
| Avg Kills | 10.7 | 7.9 | -2.8 ✅ |
| Avg Final HP | 25.5 | 32.5 | +7.0 🔴 |
| Avg Synergy | 4.91 | 5.29 | +0.38 🔴 |
| Economy Eff. | 1.44x | 1.13x | -0.31x ✅ |

**Analysis:**
- ✅ Economy nerfed successfully (-0.31x efficiency)
- ✅ Kill count reduced (coordination penalty working)
- 🔴 But win rate INCREASED (+0.5%)
- 🔴 Damage output INCREASED (+29.2)
- 🔴 Final HP INCREASED (+7.0)

**Conclusion:** Economic nerfs worked but were overcompensated by combat advantages

---

### Builder Strategy

| Metric | BAL 5.1 | BAL 5.2 (Avg) | Change |
|--------|---------|---------------|--------|
| Win Rate | 26.1% | 30.1% | +4.0% 🔴 |
| Avg Damage | 257.3 | 257.6 | +0.3 |
| Avg Kills | 6.4 | 6.0 | -0.4 |
| Avg Final HP | 25.0 | 26.7 | +1.7 |
| Avg Synergy | 5.42 | 5.47 | +0.05 |
| Economy Eff. | 1.99x | 1.79x | -0.20x |

**Analysis:**
- Win rate increased significantly (+4.0%)
- Economy slightly nerfed but still strong (1.79x)
- Combat stats stable
- Benefited from other strategies being weakened

---

### Late-Game Strategies (Combined)

| Strategy | BAL 5.1 | BAL 5.2 | Change |
|----------|---------|---------|--------|
| Economist | 4.3% | 3.7% | -0.6% |
| Evolver | 5.5% | 3.5% | -2.0% |
| Balancer | 4.5% | 2.8% | -1.7% |
| **Total** | **14.3%** | **10.0%** | **-4.3%** 🔴 |

**Critical Finding:** Late-game strategies COLLAPSED from 14.3% to 10.0%

---

## Game Flow Analysis

### Average Game Length
- **BAL 5.1:** 28.9 turns
- **BAL 5.2:** 28.2 turns
- **Change:** -0.7 turns ❌

Games are SHORTER, not longer!

### Economy Efficiency

| Strategy | BAL 5.1 | BAL 5.2 | Change |
|----------|---------|---------|--------|
| Economist | 2.55x | 2.67x | +0.12x |
| Builder | 1.99x | 1.79x | -0.20x |
| Random | 1.56x | 1.73x | +0.17x |
| Tempo | 1.44x | 1.13x | -0.31x ✅ |

**Observation:** Tempo's economy nerfed most (-0.31x), but Economist's economy IMPROVED (+0.12x)

---

## Why BAL 5.2 Failed

### 1. Win Streak Nerf Insufficient
- Tempo wins so consistently that even 50% nerf doesn't matter
- Still accumulates 1-2 gold per game from streaks
- Need complete removal or inverse scaling

### 2. Coordination Penalty Backfired
- Hurt mid-tier strategies more than Tempo
- Tempo doesn't rely on board size (7-8 units avg)
- Builder/Rare Hunter build larger boards (8-10 units)
- Penalty weakened Tempo's competitors, indirectly helping Tempo

### 3. Lose Streak Bonus Too Weak
- Need 6 losses for 3 gold bonus
- By then, player has ~40-50 HP
- Too late to mount comeback
- Should be: +1 gold per loss (max 4)

### 4. Root Problem Unaddressed
- Tempo's strength comes from EARLY GAME card quality
- Economic nerfs don't address this
- Need to directly nerf Tempo's buying power or card selection

---

## Statistical Consistency

### Test Variance Analysis

| Strategy | Test 1 | Test 2 | Difference | Variance |
|----------|--------|--------|------------|----------|
| Tempo | 46.2% | 44.3% | 1.9% | Low ✅ |
| Builder | 29.8% | 30.4% | 0.6% | Very Low ✅ |
| Warrior | 5.9% | 7.3% | 1.4% | Medium |
| Rare Hunter | 7.6% | 7.4% | 0.2% | Very Low ✅ |
| Economist | 3.0% | 4.4% | 1.4% | Medium |
| Evolver | 3.6% | 3.3% | 0.3% | Low ✅ |
| Balancer | 3.2% | 2.4% | 0.8% | Low ✅ |

**Conclusion:** Results are highly consistent. BAL 5.2 effects are reproducible.

---

## Comparison: BAL 5.0 → 5.1 → 5.2

| Strategy | BAL 5.0 | BAL 5.1 | BAL 5.2 | Trend |
|----------|---------|---------|---------|-------|
| Tempo | 47.7% | 44.8% | 45.3% | ↓ then ↑ |
| Builder | 29.2% | 26.1% | 30.1% | ↓ then ↑↑ |
| Rare Hunter | 6.3% | 9.0% | 7.5% | ↑ then ↓ |
| Warrior | 5.8% | 5.0% | 6.6% | ↓ then ↑ |
| Economist | 3.2% | 4.3% | 3.7% | ↑ then ↓ |
| Evolver | 3.5% | 5.5% | 3.5% | ↑ then ↓↓ |
| Balancer | 3.6% | 4.5% | 2.8% | ↑ then ↓↓ |

**Key Insights:**
- BAL 5.1 successfully nerfed Tempo (47.7% → 44.8%)
- BAL 5.2 REVERSED the nerf (44.8% → 45.3%)
- Late-game strategies peaked in BAL 5.1, collapsed in BAL 5.2
- Builder is the only consistent winner across all patches

---

## Recommendations for BAL 5.3

### CRITICAL: Revert Coordination Penalty
The dynamic unit scaling hurt the wrong strategies. Remove it entirely.

### CRITICAL: More Aggressive Tempo Nerf
Options:
1. Remove win streak bonus completely
2. Extend early game restriction to turn 12
3. Reduce early game cost limit to 2 gold
4. Add "Tempo Tax" (+1 gold cost for all cards)

### HIGH: Buff Lose Streak Bonus
```python
# Current: +1 gold per 2 losses (max 3)
# Proposed: +1 gold per 1 loss (max 4)
lose_streak_bonus = min(4, self.lose_streak)
```

### MEDIUM: Increase Starting HP
```python
STARTING_HP = 120  # From 100
```

### MEDIUM: Extend Damage Cap
```python
# Current: Turn 1-15 capped at 15 damage
# Proposed: Turn 1-18 capped at 15 damage
if turn <= 18:
    final_damage = min(final_damage, 15)
```

---

## Success Criteria for BAL 5.3

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Tempo Win Rate | 45.3% | <35% | 🔴 Critical |
| Late-Game Combined | 10.0% | >15% | 🔴 Critical |
| Game Length | 28.2 turns | 30+ turns | 🟡 High |
| Win Rate Spread | 44.7% | <25% | 🟡 High |
| Builder Win Rate | 30.1% | 20-25% | 🟢 Medium |

---

## Conclusion

**BAL 5.2 Status:** ❌ FAILED

**Key Findings:**
1. Win streak nerf worked economically but didn't reduce win rate
2. Coordination penalty backfired, hurting wrong strategies
3. Lose streak bonus too weak to help late-game strategies
4. Tempo's core strength (early game card quality) remains untouched
5. Builder emerged as unexpected beneficiary

**Next Steps:**
1. Revert coordination penalty immediately
2. Implement more aggressive Tempo nerfs
3. Strengthen comeback mechanics
4. Increase game length (HP + damage cap)
5. Test BAL 5.3 with 2000+ games

**Overall Assessment:** BAL 5.2 made the meta WORSE. Tempo is still dominant, late-game strategies collapsed, and Builder became too strong. Fundamental approach needs revision.

---

*Report Generated: March 29, 2026*  
*Total Games Analyzed: 2,000*  
*Simulation Engine: Autochess Hybrid v0.6*  
*Balance Patch: BAL 5.2 (FAILED)*
