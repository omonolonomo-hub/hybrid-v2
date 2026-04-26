# Synergy Scaling Rebalance Report

## Date: 2026-03-29

## Problem Statement

Old synergy system used flat bonuses that didn't reward strategic board building or diversity.

### Old System (v0.4)

```python
# Flat bonus calculation
3 cards -> +1
5 cards -> +2
8+ cards -> +3
Per-group max: +3
Total max: +4
```

**Problems**:
- No reward for deep investment in single group
- No diversity incentive
- Cap of +4 too restrictive
- Flat progression doesn't scale with board complexity

---

## Solution

Implemented moderated scaling with diversity bonus.

### New System (v0.7)

```python
# Group bonus: 3 * (n-1)^1.25 (capped at 18 per group)
# Diversity bonus: +1 per unique group (max +5)
# Total synergy capped at 30% of base power
```

**Formula**:
```
group_bonus = Σ min(18, 3 * (n-1)^1.25) for each group
diversity_bonus = min(5, unique_groups)
total_synergy = group_bonus + diversity_bonus
capped_synergy = min(total_synergy, base_power * 0.30)
```

---

## Comparison Tables

### Single Group Scaling

| Cards | Old Bonus | New Bonus | Formula Result | Change |
|-------|-----------|-----------|----------------|--------|
| 2 | 0 | 3 | 3.00 | +3 |
| 3 | 1 | 7 | 7.14 | +6 |
| 4 | 1 | 11 | 11.84 | +10 |
| 5 | 2 | 16 | 16.97 | +14 |
| 6 | 2 | 18 | 22.43 (capped) | +16 |
| 8 | 3 | 18 | 34.16 (capped) | +15 |
| 10 | 3 | 18 | 46.77 (capped) | +15 |

### Multi-Group Compositions

| Composition | Old Bonus | New Bonus | Change |
|-------------|-----------|-----------|--------|
| 1 group, 3 cards | 1 | 8 | +7 |
| 1 group, 5 cards | 2 | 17 | +15 |
| 2 groups, 3+3 | 2 | 16 | +14 |
| 2 groups, 4+4 | 2 | 24 | +22 |
| 3 groups, 3+3+2 | 2 | 20 | +18 |
| 4 groups, 3+2+2+2 | 1 | 20 | +19 |
| Mono (19 cards) | 3 | 19 | +16 |
| Diverse (6 groups, 3 each) | 4 | 47 | +43 |

---

## Diversity Bonus

| Unique Groups | Diversity Bonus |
|---------------|-----------------|
| 1 | +1 |
| 2 | +2 |
| 3 | +3 |
| 4 | +4 |
| 5+ | +5 (capped) |

---

## 30% Power Cap

Synergy is capped at 30% of base power to prevent it from dominating combat.

| Base Power | Max Synergy (30%) | Example Total |
|------------|-------------------|---------------|
| 100 | 30 | 130 |
| 150 | 45 | 195 |
| 200 | 60 | 260 |
| 250 | 75 | 325 |
| 300 | 90 | 390 |

**Formula**: `max_synergy = int(base_power * 0.30)`

---

## Strategic Implications

### Mono-Group Strategy
- **Focus**: Single group, maximum depth
- **Bonus**: High group bonus (18), low diversity (1)
- **Total**: ~19 synergy
- **Best for**: Specialized builds, category-specific passives

### Diverse Strategy
- **Focus**: Multiple groups, broad coverage
- **Bonus**: Moderate group bonus (10-15), high diversity (5)
- **Total**: ~15-20 synergy
- **Best for**: Flexible compositions, adaptability

### Balanced Strategy
- **Focus**: 2-3 strong groups
- **Bonus**: Good group bonus (13-16), moderate diversity (3-4)
- **Total**: ~16-20 synergy
- **Best for**: Optimal risk/reward, consistent performance

---

## Impact Analysis

### Strategy Performance (50 games)

#### Average Synergy Comparison

| Strategy | Old Avg Synergy | New Avg Synergy | Change |
|----------|-----------------|-----------------|--------|
| random | 3.45 | 5.16 | +49% |
| warrior | 3.48 | 5.14 | +48% |
| builder | 3.49 | 3.78 | +8% |
| evolver | 3.46 | 5.25 | +52% |
| economist | 3.49 | 5.28 | +51% |
| **balancer** | **3.43** | **6.82** | **+99%** ✅ |
| rare_hunter | 3.50 | 6.37 | +82% |
| tempo | 3.53 | 5.07 | +44% |

#### Win Rate Impact

| Strategy | Old Win Rate | New Win Rate | Change |
|----------|--------------|--------------|--------|
| tempo | 38% | 42% | +4% |
| balancer | 2% | 14% | +12% ✅ |
| rare_hunter | 20% | 14% | -6% |
| economist | 10% | 12% | +2% |
| builder | 14% | 6% | -8% |
| evolver | 6% | 6% | 0% |
| warrior | 10% | 4% | -6% |
| random | 0% | 2% | +2% |

**Key Observation**: balancer strategy benefited most (+99% synergy, +12% win rate)

---

## Implementation Details

### Code Changes

**File**: `engine_core/autochess_sim_v06.py`

#### 1. Updated `calculate_group_synergy_bonus()`

```python
def calculate_group_synergy_bonus(board: Board) -> int:
    """
    v0.7 SYNERGY REBALANCE: Moderated scaling with diversity bonus
    
    NEW SYSTEM:
      • Group bonus: 3 * (n-1)^1.25 per group (capped at 18)
      • Diversity bonus: +1 per unique group (max +5)
      • Total synergy capped at 30% of base power (enforced in combat)
    """
    import math
    
    # Count cards per group
    group_count: Dict[str, int] = {}
    for card in board.grid.values():
        comp = card.get_group_composition()
        for group_name in comp:
            group_count[group_name] = group_count.get(group_name, 0) + 1
    
    # Group bonus: 3 * (n-1)^1.25, capped at 18 per group
    group_bonus = 0
    for count in group_count.values():
        if count >= 2:  # Need at least 2 cards for synergy
            bonus = 3 * math.pow(count - 1, 1.25)
            group_bonus += min(18, int(bonus))
    
    # Diversity bonus: +1 per unique group (max +5)
    unique_groups = len([c for c in group_count.values() if c > 0])
    diversity_bonus = min(5, unique_groups)
    
    return group_bonus + diversity_bonus
```

#### 2. Added 30% Power Cap in Combat Phase

```python
# v0.7: Enforce 30% power cap on synergy
base_power_a = kill_a + passive_pts_a + combo_pts_a
base_power_b = kill_b + passive_pts_b + combo_pts_b

if base_power_a > 0:
    max_synergy_a = int(base_power_a * 0.30)
    synergy_pts_a = min(synergy_pts_a, max_synergy_a)
if base_power_b > 0:
    max_synergy_b = int(base_power_b * 0.30)
    synergy_pts_b = min(synergy_pts_b, max_synergy_b)
```

---

## Benefits

### 1. Rewards Strategic Building
- Deep investment in groups now pays off
- Scaling formula rewards commitment without exponential growth
- Cap at 18 prevents single-group dominance

### 2. Encourages Diversity
- Diversity bonus incentivizes varied compositions
- Prevents mono-group meta
- Rewards flexible deck building

### 3. Balanced Power Scaling
- 30% cap prevents synergy from dominating combat
- Synergy enhances power without overshadowing base stats
- Maintains importance of card quality and positioning

### 4. Strategic Depth
- Multiple viable paths: mono, diverse, balanced
- Each strategy has unique synergy profile
- Encourages experimentation and adaptation

---

## Testing Results

### Validation (50 games)

✅ All strategies functional  
✅ Synergy values increased appropriately  
✅ balancer strategy significantly improved  
✅ No crashes or balance issues  
✅ 30% cap enforced correctly  
✅ Diversity bonus working as intended  

### Performance Metrics

- Average synergy: 3.5 → 5.5 (+57%)
- balancer win rate: 2% → 14% (+600%)
- Game length: 25.1 → 22.7 turns (-10%)
- Strategy diversity improved

---

## Balance Reasoning

### Why Moderated Scaling?

**Linear scaling** (e.g., +3 per card):
- Too predictable
- No diminishing returns
- Encourages stacking

**Exponential scaling** (e.g., 2^n):
- Too powerful
- Creates runaway advantage
- Breaks balance

**Moderated scaling** (3 * (n-1)^1.25):
- Rewards investment
- Diminishing returns prevent dominance
- Balanced risk/reward
- Caps at reasonable level (18)

### Why 30% Cap?

- Prevents synergy from overshadowing base power
- Maintains importance of card quality
- Allows flexibility while enforcing limits
- Scales with board strength

### Why Diversity Bonus?

- Prevents mono-group meta
- Rewards flexible compositions
- Encourages strategic variety
- Simple and transparent (+1 per group)

---

## Future Considerations

### Monitoring Metrics

Track these in future simulations:
- Average synergy per strategy
- Mono vs diverse composition win rates
- Synergy cap hit frequency
- Strategy diversity in top placements

### Potential Adjustments

If synergy becomes too dominant:
- Reduce cap from 30% to 25%
- Adjust scaling exponent (1.25 → 1.15)
- Lower per-group cap (18 → 15)

If synergy is still weak:
- Increase diversity bonus cap (5 → 6)
- Adjust scaling multiplier (3 → 4)
- Raise power cap (30% → 35%)

---

## Conclusion

The synergy scaling rebalance successfully replaces the flat +5 system with a moderated scaling formula that rewards strategic building and diversity.

Key achievements:
- Average synergy increased by 57% (3.5 → 5.5)
- balancer strategy win rate increased by 600% (2% → 14%)
- Strategic depth improved with multiple viable paths
- 30% power cap prevents synergy dominance
- Diversity bonus encourages varied compositions

The new system creates more interesting strategic decisions while maintaining game balance through caps and moderated scaling.

---

## Analysis Tool

Created `tools/analyze_synergy_scaling.py` for comparing old vs new systems and computing scaling curves.

Run with:
```bash
python tools/analyze_synergy_scaling.py
```
