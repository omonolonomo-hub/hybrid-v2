# BAL 5.2 - Comprehensive Balance Patch Analysis

## Executive Summary

**Date:** March 29, 2026  
**Version:** Autochess Hybrid v0.6 - BAL 5.2  
**Status:** ⚠️ MIXED RESULTS - Tempo still dominant, unexpected side effects

## Changes Implemented

### 1. Win Streak Gold Nerf ❌ INEFFECTIVE
**Goal:** Reduce Tempo's economic advantage from winning streaks

**Implementation:**
```python
# Old (BAL 5.1): +1 gold per 3 wins
streak_bonus = self.win_streak // 3

# New (BAL 5.2): +1 gold per 6 wins, max 2 gold
streak_bonus = min(2, self.win_streak // 6)
```

**Result:** 50% reduction in win streak bonus, capped at 2 gold maximum

---

### 2. Lose Streak Bonus (Comeback Mechanic) ✅ IMPLEMENTED
**Goal:** Help late-game strategies survive early losses

**Implementation:**
```python
# BAL 5.2: +1 gold per 2 consecutive losses (max 3 gold)
lose_streak_bonus = min(3, self.lose_streak // 2)
```

**Mechanics:**
- 2 losses: +1 gold
- 4 losses: +2 gold
- 6+ losses: +3 gold (capped)

---

### 3. Dynamic Unit Scaling (Coordination Penalty) ⚠️ PROBLEMATIC
**Goal:** Prevent stat-check dominance from large boards

**Implementation:**
```python
# Calculate board size difference
size_diff = abs(board_size_a - board_size_b)

# Apply penalty if 3+ unit advantage
if size_diff >= 3:
    extra_units = size_diff - 2
    coordination_penalty = max(0.5, 1.0 - (extra_units * 0.05))
    # Apply to combo bonuses and kill points
```

**Mechanics:**
- 3-unit advantage: No penalty
- 4-unit advantage: -5% power
- 5-unit advantage: -10% power
- 6-unit advantage: -15% power
- Maximum penalty: -50% power (at 13+ unit advantage)

---

## Results Comparison

### BAL 5.1 vs BAL 5.2 (1000 Games Each)

| Strategy | BAL 5.1 | BAL 5.2 | Change | Status |
|----------|---------|---------|--------|--------|
| **Tempo** | 44.8% | **46.2%** | +1.4% | 🔴 WORSE |
| **Builder** | 26.1% | **29.8%** | +3.7% | 🟡 STRONGER |
| Rare Hunter | 9.0% | 7.6% | -1.4% | 🔵 WEAKER |
| Warrior | 5.0% | 5.9% | +0.9% | 🟢 STABLE |
| Evolver | 5.5% | 3.6% | -1.9% | 🔴 WEAKER |
| Economist | 4.3% | 3.0% | -1.3% | 🔴 WEAKER |
| Balancer | 4.5% | 3.2% | -1.3% | 🔴 WEAKER |
| Random | 0.8% | 0.7% | -0.1% | 🔵 BASELINE |

---

## Detailed Analysis

### Why Did Tempo Get STRONGER? 🔴

**Hypothesis 1: Win Streak Nerf Insufficient**
- Tempo wins so consistently that even nerfed win streak still provides advantage
- Old: 6 wins = 2 gold, 9 wins = 3 gold
- New: 6 wins = 1 gold, 12 wins = 2 gold
- Tempo averages 10+ win streak, so only loses ~1-2 gold per game

**Hypothesis 2: Dynamic Unit Scaling Hurts Opponents More**
- Tempo doesn't rely on massive boards (avg 7-8 units)
- Builder and Rare Hunter build larger boards (8-10 units)
- Coordination penalty hurts Builder's scaling strategy
- This indirectly helps Tempo by weakening its main competitor

**Hypothesis 3: Lose Streak Bonus Came Too Late**
- Late-game strategies already eliminated before lose streak bonus kicks in
- Need 4+ losses for meaningful bonus (2 gold)
- By then, HP is too low to recover

---

### Why Did Builder Get STRONGER? 🟡

**Unexpected Benefit:**
- Builder's economy efficiency IMPROVED: 1.99x → 1.78x (wait, that's worse!)
- But win rate increased: 26.1% → 29.8%

**Possible Explanations:**
1. **Relative Advantage:** Other strategies weakened more than Builder
2. **Synergy Cap Benefit:** Builder's 30% synergy cap less impactful with coordination penalty
3. **Economic Resilience:** Builder's strong economy (1.78x) still competitive

---

### Why Did Late-Game Strategies Get WEAKER? 🔴

| Strategy | BAL 5.1 | BAL 5.2 | Change |
|----------|---------|---------|--------|
| Economist | 4.3% | 3.0% | -1.3% |
| Evolver | 5.5% | 3.6% | -1.9% |
| Balancer | 3.2% | 3.2% | 0.0% |

**Problems:**
1. **Win streak nerf didn't slow Tempo enough**
2. **Lose streak bonus insufficient** - need 6 losses for 3 gold
3. **Coordination penalty hurts everyone** - including late-game strategies trying to scale
4. **Games still too short** - 28.2 turns average (same as BAL 5.1)

---

## Performance Metrics

### Tempo Strategy Deep Dive

| Metric | BAL 5.1 | BAL 5.2 | Change |
|--------|---------|---------|--------|
| Win Rate | 44.8% | 46.2% | +1.4% 🔴 |
| Avg Damage | 257.1 | 288.5 | +31.4 🔴 |
| Avg Kills | 10.7 | 7.9 | -2.8 ✅ |
| Avg Final HP | 25.5 | 33.2 | +7.7 🔴 |
| Avg Synergy | 4.91 | 5.31 | +0.40 🔴 |
| Economy Eff. | 1.44x | 1.13x | -0.31x ✅ |

**Analysis:**
- Win rate INCREASED despite economy nerf
- Damage output INCREASED (+31.4)
- Final HP INCREASED (+7.7) - winning more decisively
- Kill count DECREASED (-2.8) - coordination penalty working
- Economy efficiency DECREASED (-0.31x) - win streak nerf working
- **Conclusion:** Economic nerfs worked, but combat buffs (from weakening opponents) overcompensated

---

### Builder Strategy Deep Dive

| Metric | BAL 5.1 | BAL 5.2 | Change |
|--------|---------|---------|--------|
| Win Rate | 26.1% | 29.8% | +3.7% |
| Avg Damage | 257.3 | 255.0 | -2.3 |
| Avg Kills | 6.4 | 6.0 | -0.4 |
| Avg Final HP | 25.0 | 26.0 | +1.0 |
| Avg Synergy | 5.42 | 5.49 | +0.07 |
| Economy Eff. | 1.99x | 1.78x | -0.21x |

**Analysis:**
- Win rate INCREASED significantly (+3.7%)
- Combat stats relatively stable
- Economy efficiency DECREASED but still strong (1.78x)
- **Conclusion:** Builder benefited from other strategies being weakened

---

## Game Flow Analysis

### Average Game Length
- **BAL 5.1:** 28.9 turns
- **BAL 5.2:** 28.2 turns
- **Change:** -0.7 turns ❌

Games are actually SHORTER now, opposite of intended effect!

### Draw Statistics
- **BAL 5.1:** 10,454 draws
- **BAL 5.2:** 9,940 draws
- **Change:** -514 draws (-4.9%)

Fewer draws = more decisive combat = benefits dominant strategies

---

## Root Cause Analysis

### Why BAL 5.2 Failed

**1. Win Streak Nerf Too Weak**
- 50% reduction sounds significant but Tempo's win rate is so high that it still accumulates gold
- Need more aggressive nerf (75% reduction or complete removal)

**2. Coordination Penalty Backfired**
- Intended to nerf Tempo/Builder's large boards
- Actually hurt mid-tier strategies more (Rare Hunter, Evolver)
- Tempo doesn't rely on board size advantage - relies on card quality

**3. Lose Streak Bonus Too Slow**
- Need 6 losses for 3 gold bonus
- By then, player has ~40-50 HP left
- Not enough to mount comeback

**4. Systemic Issue: Tempo's Core Strength Untouched**
- Tempo's advantage comes from EARLY GAME card quality, not economy
- Economic nerfs don't address the root problem
- Need to nerf Tempo's card selection or early game power directly

---

## Recommendations for BAL 5.3

### Priority 1: REVERT Dynamic Unit Scaling 🔴 CRITICAL
The coordination penalty hurt the wrong strategies. Remove it entirely.

```python
# REMOVE THIS CODE
if size_diff >= 3:
    coordination_penalty = ...
```

### Priority 2: Aggressive Win Streak Nerf 🔴 CRITICAL
Current nerf insufficient. Options:

**Option A: Remove Win Streak Bonus Entirely**
```python
streak_bonus = 0  # No win streak bonus
```

**Option B: Inverse Win Streak (Diminishing Returns)**
```python
# First 3 wins: +1 gold each
# Next 3 wins: +0 gold
# Caps at 3 gold total
if self.win_streak <= 3:
    streak_bonus = self.win_streak
else:
    streak_bonus = 3
```

### Priority 3: Buff Lose Streak Bonus 🟡 HIGH
Current bonus too slow. Make it more aggressive:

```python
# Old: +1 gold per 2 losses (max 3)
# New: +1 gold per 1 loss (max 4)
lose_streak_bonus = min(4, self.lose_streak)
```

### Priority 4: Nerf Tempo's Early Game DIRECTLY 🔴 CRITICAL
Economic nerfs don't work. Attack the source:

**Option A: Extend Early Game Restriction**
```python
# In _buy_tempo()
if turn <= 12:  # Extended from turn 8
    max_cards = 1
    # Only buy cards costing <= 2 gold (reduced from 3)
```

**Option B: Add "Tempo Tax"**
```python
# Tempo pays 1 extra gold for all cards
if player.strategy == "tempo":
    card_cost = CARD_COSTS[card.rarity] + 1
```

### Priority 5: Increase Starting HP 🟢 MEDIUM
Give late-game strategies more time:

```python
STARTING_HP = 120  # Increased from 100
```

---

## Conclusion

BAL 5.2 was a **FAILURE**. The patch made Tempo STRONGER (44.8% → 46.2%) instead of weaker.

**Key Learnings:**
1. ✅ Economic nerfs work (Tempo's economy efficiency dropped)
2. ❌ But economic nerfs don't reduce win rate
3. ❌ Coordination penalty hurt wrong strategies
4. ❌ Lose streak bonus too weak/slow
5. ❌ Need to attack Tempo's CORE STRENGTH (early game card quality)

**Next Steps:**
1. Revert coordination penalty
2. Remove or drastically nerf win streak bonus
3. Buff lose streak bonus
4. Directly nerf Tempo's early game buying power
5. Increase starting HP to 120

**Success Criteria for BAL 5.3:**
- Tempo win rate: <35%
- Late-game strategies combined: >15%
- Game length: 30+ turns
- Win rate spread: <25 percentage points

---

*Report Generated: March 29, 2026*  
*Simulation Engine: Autochess Hybrid v0.6*  
*Balance Patch: BAL 5.2 (FAILED)*
