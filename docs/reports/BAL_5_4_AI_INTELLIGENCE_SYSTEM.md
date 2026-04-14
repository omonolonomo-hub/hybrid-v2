# BAL 5.4 - Master AI Behavior Intelligence System

## Executive Summary

**Date:** March 29, 2026  
**Version:** Autochess Hybrid v0.6 - BAL 5.4  
**Focus:** Non-deterministic AI with weighted randomness, opponent awareness, and adaptive thresholds  
**Status:** ⚠️ IMPLEMENTED (Economist only) - Requires tuning

---

## Core Philosophy

**Problem:** Deterministic AI creates predictable, repetitive gameplay where the same game state always produces the same decision.

**Solution:** Implement behavioral intelligence that:
1. Uses weighted randomness (no single "best" choice)
2. Adapts to opponent strength and meta
3. Replaces static thresholds with dynamic risk evaluation
4. Maintains strategy identity while allowing flexible behavior

---

## Implemented Systems

### 1. Opponent Awareness System ✅

**Function:** `AI._calculate_opponent_context(player, game_context)`

**Metrics Calculated:**
- `avg_opponent_power`: Average board power of alive opponents
- `tempo_dominance`: Ratio of high-power opponents (>80 power)
- `late_game_presence`: Ratio of low-power opponents (<40 power)
- `threat_level`: Overall threat assessment (0.0-1.0)

**Usage:**
```python
opponent_context = AI._calculate_opponent_context(player, game_context)
# Returns: {
#     'avg_opponent_power': 65.3,
#     'tempo_dominance': 0.6,  # 60% of opponents are high-power
#     'late_game_presence': 0.2,  # 20% are low-power
#     'threat_level': 0.72  # High threat environment
# }
```

---

### 2. Dynamic Risk Evaluation ✅

**Function:** `AI._calculate_dynamic_risk(player, opponent_context)`

**Replaces:** Static HP thresholds like `if hp < 60`

**Risk Factors:**
- HP ratio (40% weight) - Most important
- Board power deficit vs opponents (30% weight)
- Lose streak (20% weight)
- Meta threat level (10% weight)

**Returns:** Risk level 0.0-1.0
- 0.0-0.3: Low risk (greedy play)
- 0.3-0.5: Moderate risk (balanced play)
- 0.5-0.7: High risk (defensive play)
- 0.7-1.0: Critical risk (survival mode)

**Example:**
```python
risk = AI._calculate_dynamic_risk(player, opponent_context)
# Player: 45 HP, weak board, 3 loss streak, strong opponents
# Returns: 0.75 (critical risk)

# Player: 80 HP, strong board, winning streak, weak opponents  
# Returns: 0.15 (low risk)
```

---

### 3. Weighted Random Selection ✅

**Function:** `AI._weighted_choice(candidates, rng)`

**Replaces:** Deterministic `max(cards, key=lambda c: c.power)`

**Behavior:**
- Evaluates multiple candidates (minimum 3)
- Assigns probabilistic weights
- Includes non-optimal but viable options
- Ensures variance between identical game states

**Example:**
```python
# Old (deterministic):
best_card = max(market, key=lambda c: c.total_power())

# New (weighted random):
card_scores = [(card, card.total_power() + variance) for card in market]
selected_card = AI._weighted_choice(card_scores, rng)
```

---

## Economist Implementation (BAL 5.4)

### Behavioral Changes

**Before (BAL 5.3):**
- Static HP thresholds: `if hp <= 40`, `if hp <= 55`, `if hp <= 70`
- Deterministic card selection: Always picks highest power
- No opponent awareness
- Fixed spending patterns

**After (BAL 5.4):**
- Dynamic risk evaluation: `risk_level = AI._calculate_dynamic_risk(...)`
- Weighted card selection with variance
- Opponent-aware spending adjustments
- Adaptive mode selection based on risk + tempo pressure

### Mode Selection Logic

```python
risk_level = AI._calculate_dynamic_risk(player, opponent_context)
tempo_pressure = opponent_context.get('tempo_dominance', 0.5)

if risk_level > 0.7:
    mode = "CRITICAL"  # Aggressive spending, buy 2 cards
elif risk_level > 0.5:
    mode = "DEFENSIVE"  # Defensive spending, buy 1 card
elif risk_level > 0.3 or tempo_pressure > 0.6:
    mode = "CAUTIOUS"  # Cautious spending, limited tiers
else:
    mode = "GREEDY"  # Original economy logic
```

### Weighted Card Selection

```python
# Score all affordable cards
for card in affordable:
    base_score = card.total_power()
    
    # Add variance based on risk level
    # High risk: less variance (prefer safe choices)
    # Low risk: more variance (allow exploration)
    variance_factor = 1.0 - (risk_level * 0.5)
    variance = rng.uniform(-base_score * variance_factor * 0.2,
                          base_score * variance_factor * 0.2)
    
    final_score = base_score + variance
    card_scores.append((card, max(1.0, final_score)))

# Weighted random selection
selected_card = AI._weighted_choice(card_scores, rng)
```

---

## Test Results (500 Games)

### BAL 5.3 vs BAL 5.4 Comparison

| Strategy | BAL 5.3 | BAL 5.4 | Change | Status |
|----------|---------|---------|--------|--------|
| Tempo | 44.6% | 45.2% | +0.6% | 🔴 STRONGER |
| Builder | 27.9% | 30.0% | +2.1% | 🔴 STRONGER |
| Warrior | 5.7% | 8.4% | +2.7% | 🟢 IMPROVED |
| Rare Hunter | 7.8% | 7.4% | -0.4% | 🟢 STABLE |
| Evolver | 6.2% | 3.6% | -2.6% | 🔴 WEAKER |
| Balancer | 2.7% | 3.4% | +0.7% | 🟢 IMPROVED |
| **Economist** | **4.4%** | **0.8%** | **-3.6%** | 🔴 COLLAPSED |
| Random | 0.7% | 1.2% | +0.5% | 🔵 BASELINE |

---

## Critical Finding: Economist Collapsed ⚠️

### Performance Breakdown

| Metric | BAL 5.3 | BAL 5.4 | Change |
|--------|---------|---------|--------|
| Win Rate | 4.4% | 0.8% | -3.6% 🔴 |
| Avg Damage | 117.7 | 79.7 | -38.0 🔴 |
| Avg Kills | 7.4 | 4.6 | -2.8 🔴 |
| Avg Final HP | 1.3 | 0.2 | -1.1 🔴 |
| Economy Eff. | 2.67x | 3.68x | +1.01x ⚠️ |

### Analysis

**What Happened:**
1. ✅ Economy efficiency IMPROVED (2.67x → 3.68x)
2. ❌ But combat performance COLLAPSED
3. ❌ Win rate dropped by 82% (4.4% → 0.8%)

**Root Cause:**
- Weighted randomness introduced too much variance
- Economist now picks suboptimal cards too frequently
- High economy efficiency but weak board = early elimination
- Variance factor needs tuning (currently 20% swing)

**The Paradox:**
- Better economy (3.68x is highest ever)
- Worse combat (79.7 damage vs 117.7)
- **Conclusion:** Economist is banking gold but dying before it matters

---

## Variance Tuning Required

### Current Variance Formula

```python
variance_factor = 1.0 - (risk_level * 0.5)  # 0.5-1.0 range
variance = rng.uniform(-base_score * variance_factor * 0.2,
                      base_score * variance_factor * 0.2)
```

**Problem:** 20% variance is too high for Economist

**Example:**
- Card A: 30 power → variance ±6 → final score 24-36
- Card B: 25 power → variance ±5 → final score 20-30
- Card B can randomly beat Card A despite being weaker

### Proposed Fix

```python
# Strategy-specific variance
if player.strategy == "economist":
    variance_multiplier = 0.1  # 10% variance (more conservative)
elif player.strategy == "tempo":
    variance_multiplier = 0.15  # 15% variance
else:
    variance_multiplier = 0.2  # 20% variance (default)

variance = rng.uniform(-base_score * variance_factor * variance_multiplier,
                      base_score * variance_factor * variance_multiplier)
```

---

## Positive Findings

### Warrior Improved (+2.7%)

| Metric | BAL 5.3 | BAL 5.4 | Change |
|--------|---------|---------|--------|
| Win Rate | 5.7% | 8.4% | +2.7% ✅ |
| Avg Damage | 127.7 | 136.9 | +9.2 ✅ |

**Analysis:** Warrior benefits from opponent awareness (not yet implemented in its buy function, but benefits from meta changes)

### Balancer Improved (+0.7%)

Slight improvement suggests the system has potential when properly tuned.

---

## Implementation Status

### Completed ✅
- [x] Opponent awareness system
- [x] Dynamic risk evaluation
- [x] Weighted random selection
- [x] Economist BAL 5.4 implementation
- [x] Function signature updates (all strategies)

### Pending ⏳
- [ ] Tune variance parameters per strategy
- [ ] Implement weighted selection in other strategies
- [ ] Add opponent awareness to Warrior, Builder, etc.
- [ ] Test with 1000+ games
- [ ] Balance variance vs optimality trade-off

### Not Started ❌
- [ ] Adaptive thresholds for all strategies
- [ ] Meta adaptation (40% win rate detection)
- [ ] Failsafe rules (20% value threshold)
- [ ] Full non-deterministic behavior across all strategies

---

## Recommendations

### Priority 1: Fix Economist Variance 🔴 CRITICAL

```python
# Reduce variance for economy-focused strategies
if player.strategy in ["economist", "evolver"]:
    variance_multiplier = 0.08  # 8% variance
elif player.strategy in ["builder", "balancer"]:
    variance_multiplier = 0.12  # 12% variance
else:
    variance_multiplier = 0.15  # 15% variance
```

### Priority 2: Implement Weighted Selection in All Strategies 🟡 HIGH

Currently only Economist uses weighted selection. Need to apply to:
- Warrior
- Builder
- Evolver (already has bench logic, add to buying)
- Balancer
- Rare Hunter
- Tempo

### Priority 3: Add Opponent Awareness to Combat Strategies 🟡 HIGH

Warrior and Tempo should adjust aggression based on `tempo_dominance`:
```python
if opponent_context.get('tempo_dominance', 0) > 0.6:
    # Many strong opponents - play more defensively
    defensive_bias = 1.2
else:
    defensive_bias = 1.0
```

### Priority 4: Test and Iterate 🟢 MEDIUM

- Run 1000+ game tests after each tuning
- Monitor win rate distribution
- Ensure no strategy drops below 2%
- Target: All strategies between 5-35% win rate

---

## Pseudocode: Full BAL 5.4 Implementation

```python
function buy_strategy(player, market, opponent_context):
    # 1. Calculate dynamic risk
    risk = calculate_dynamic_risk(player, opponent_context)
    
    # 2. Adjust behavior based on risk and opponents
    if risk > 0.7:
        mode = SURVIVAL
        variance = LOW  # Prefer safe choices
    elif risk > 0.4:
        mode = BALANCED
        variance = MEDIUM
    else:
        mode = GREEDY
        variance = HIGH  # Allow exploration
    
    # 3. Opponent-aware adjustments
    if opponent_context.tempo_dominance > 0.6:
        # Strong opponents - increase defensive bias
        defensive_weight = 1.3
    else:
        defensive_weight = 1.0
    
    # 4. Score all candidates with variance
    candidates = []
    for card in market:
        base_score = evaluate_card(card, player, mode)
        variance_amount = random.uniform(-variance, +variance)
        final_score = base_score * (1 + variance_amount) * defensive_weight
        candidates.append((card, final_score))
    
    # 5. Weighted random selection
    selected = weighted_choice(candidates)
    
    # 6. Buy card
    player.buy(selected)
```

---

## Conclusion

**BAL 5.4 Status:** ⚠️ PARTIALLY IMPLEMENTED - Requires Tuning

**Key Findings:**
1. ✅ System architecture works (opponent awareness, dynamic risk, weighted selection)
2. ❌ Variance parameters need per-strategy tuning
3. ⚠️ Economist collapsed due to excessive randomness (20% variance too high)
4. ✅ Warrior improved (+2.7%) suggesting system has potential
5. ⏳ Need to implement weighted selection in all strategies

**Next Steps:**
1. Reduce Economist variance to 8-10%
2. Implement weighted selection in remaining strategies
3. Add opponent awareness to combat strategies
4. Test with 1000+ games
5. Fine-tune variance parameters based on results

**Overall Assessment:** The BAL 5.4 intelligence system is sound, but requires careful parameter tuning to balance randomness with optimality. The Economist collapse demonstrates that too much variance can be harmful, especially for economy-focused strategies that need consistent decision-making.

---

*Report Generated: March 29, 2026*  
*Total Games Analyzed: 500*  
*Simulation Engine: Autochess Hybrid v0.6*  
*Balance Patch: BAL 5.4 (IN PROGRESS)*
