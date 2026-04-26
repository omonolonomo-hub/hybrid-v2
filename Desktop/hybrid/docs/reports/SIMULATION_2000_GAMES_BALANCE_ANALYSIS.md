# Autochess Hybrid - 2000 Game Balance Analysis Report
## Executive Summary

**Simulation Parameters:**
- Total Games: 2000
- Players per Game: 8
- Total Matches: 16,000 player instances
- Card Pool: 101 unique cards
- Average Game Length: 27.8 turns (Range: 21-35 turns)

**Critical Finding:** 
The early game damage cap (BAL 5) implementation has NOT successfully nerfed the Tempo strategy. Tempo remains dominant with a 47.7% win rate, nearly double the second-place Builder strategy (29.2%).

---

## 1. STRATEGY PERFORMANCE ANALYSIS

### Win Rate Distribution

| Strategy | Wins | Win Rate | Top 4 Rate | Status |
|----------|------|----------|------------|--------|
| **Tempo** | 954 | **47.7%** | N/A | 🔴 OVERPOWERED |
| **Builder** | 585 | **29.2%** | N/A | 🟡 STRONG |
| **Rare Hunter** | 127 | 6.3% | N/A | 🟢 BALANCED |
| **Warrior** | 115 | 5.8% | N/A | 🟢 BALANCED |
| **Balancer** | 73 | 3.6% | N/A | 🔵 WEAK |
| **Evolver** | 69 | 3.5% | N/A | 🔵 WEAK |
| **Economist** | 64 | 3.2% | N/A | 🔵 WEAK |
| **Random** | 13 | 0.7% | N/A | 🔵 BASELINE |

### Combat Performance Metrics

| Strategy | Avg Damage Dealt | Avg Kills | Avg Final HP | Performance |
|----------|------------------|-----------|--------------|-------------|
| **Tempo** | **294.5** | **9.4** | **35.8** | Dominant |
| **Builder** | 261.2 | 6.5 | 26.4 | Strong |
| Rare Hunter | 132.3 | 9.0 | 2.4 | Aggressive |
| Warrior | 126.7 | 8.0 | 2.2 | Aggressive |
| Evolver | 121.5 | 8.1 | 1.2 | Weak |
| Economist | 114.7 | 7.7 | 1.0 | Weak |
| Balancer | 113.6 | 8.0 | 1.2 | Weak |
| Random | 85.5 | 5.2 | 0.2 | Baseline |

### Economy & Synergy Analysis

| Strategy | Avg Synergy | Economy Efficiency | Playstyle |
|----------|-------------|-------------------|-----------|
| Economist | 5.59 | **2.55x** | Greedy/Late Game |
| Builder | 5.56 | **1.91x** | Economic/Scaling |
| Random | 5.79 | 1.55x | Baseline |
| Warrior | 5.81 | 1.12x | Aggressive |
| Evolver | 5.91 | 1.17x | Scaling |
| Balancer | 5.82 | 1.13x | Flexible |
| Rare Hunter | 6.07 | 1.12x | Quality Focus |
| **Tempo** | 5.37 | 1.15x | Early Aggression |

---

## 2. PROBLEM ANALYSIS: WHY TEMPO STILL DOMINATES

### Issue 1: Early Game Damage Cap is Insufficient


**Current Implementation (BAL 5):**
- Turn 1-5: 50% damage multiplier
- Turn 6-15: Linear scaling from 0.5x to 1.0x
- Turn 1-10: Hard cap at 15 damage maximum

**Why It's Not Working:**
1. **Tempo doesn't rely on early eliminations** - The strategy focuses on building board strength and winning consistently, not on dealing massive early damage
2. **Mid-game advantage compounds** - By turn 11+, Tempo has already established board superiority
3. **Economy efficiency is competitive** - Tempo's 1.15x economy efficiency is sufficient to maintain pressure
4. **Synergy advantage** - While Tempo has lower average synergy (5.37), it compensates with consistent wins

### Issue 2: Builder Strategy Also Strong

Builder's 29.2% win rate (second place) suggests:
- Economic strategies CAN work when properly executed
- Builder's 1.91x economy efficiency allows it to scale effectively
- The gap between Builder and Tempo is still too large (18.5 percentage points)

### Issue 3: Late-Game Strategies Underperforming

**Economist, Evolver, and Balancer** all have <4% win rates:
- Economist has the BEST economy efficiency (2.55x) but only 3.2% win rate
- This indicates the game ends before late-game strategies can capitalize
- Average game length (27.8 turns) may be too short for scaling strategies

---

## 3. CARD PERFORMANCE ANALYSIS

### Top Performing Cards (100% Win Rate in Combat)

| Card | Wins | Losses | Win Rate | Category |
|------|------|--------|----------|----------|
| Pulsar | 8 | 0 | 100% | MIND |
| Albert Einstein | 7 | 0 | 100% | MIND |
| Silk Road | 3 | 0 | 100% | CONNECTION |
| Black Death | 5 | 0 | 100% | CONNECTION |
| Evolved Silk Road | 3 | 0 | 100% | CONNECTION |

### High Win Rate Cards (>80%)

| Card | Wins | Losses | Win Rate | Notes |
|------|------|--------|----------|-------|
| Guernica | 20 | 1 | 95% | Exceptional |
| Space-Time | 13 | 1 | 93% | Very Strong |
| Blue Whale | 10 | 1 | 91% | Very Strong |
| Event Horizon | 8 | 1 | 89% | Very Strong |
| Kraken | 7 | 1 | 88% | Very Strong |
| French Revolution | 5 | 1 | 83% | Strong |
| Olympus | 5 | 1 | 83% | Strong |
| Yggdrasil | 10 | 2 | 83% | Strong |
| Gravity | 13 | 3 | 81% | Strong |
| Black Hole | 8 | 2 | 80% | Strong |

### Weakest Cards (0% Win Rate with 3+ Combats)

| Card | Wins | Losses | Win Rate | Status |
|------|------|--------|----------|--------|
| Tardigrade | 0 | 4 | 0% | 🔴 Needs Buff |
| Ballet | 0 | 4 | 0% | 🔴 Needs Buff |
| Rainforest | 0 | 5 | 0% | 🔴 Needs Buff |
| Impressionism | 0 | 3 | 0% | 🔴 Needs Buff |
| Jazz | 0 | 3 | 0% | 🔴 Needs Buff |
| Entropy | 0 | 6 | 0% | 🔴 Needs Buff |
| Quantum Mechanics | 0 | 5 | 0% | 🔴 Needs Buff |
| Cubism | 0 | 6 | 0% | 🔴 Needs Buff |
| Minotaur | 0 | 4 | 0% | 🔴 Needs Buff |
| World War II | 0 | 4 | 0% | 🔴 Needs Buff |
| Gothic Architecture | 0 | 5 | 0% | 🔴 Needs Buff |

---

## 4. GAME FLOW ANALYSIS

### Turn Distribution
- **Shortest Game:** 21 turns
- **Average Game:** 27.8 turns
- **Longest Game:** 35 turns
- **Standard Deviation:** ~3.5 turns (estimated)

### Draw Statistics
- **Total Draws:** 19,901 (across all players)
- **Average Draws per Strategy:**
  - Balancer: 5,564 draws (highest)
  - Evolver: 5,422 draws
  - Warrior: 5,493 draws
  - Random: 5,495 draws
  - Rare Hunter: 5,463 draws
  - Economist: 4,689 draws
  - Builder: 4,098 draws
  - **Tempo: 3,578 draws (lowest)** ← Wins before drawing

**Key Insight:** Tempo has the LOWEST draw count because it wins games outright rather than drawing. This indicates Tempo is ending games decisively.

---

## 5. PASSIVE TRIGGER ANALYSIS

### Most Triggered Passives (Sample from Game 1999)

| Card | Total Triggers | Most Common Trigger | Notes |
|------|----------------|---------------------|-------|
| Age of Discovery | 50+ | card_buy, income | Economic passive |
| Andromeda Galaxy | 53+ | pre_combat | Combat-focused |
| Frida Kahlo | 52+ | combat events | Versatile |
| Ottoman Empire | 56+ | combat_win | Strong performer |
| Pulsar | 58+ | combat_win | Dominant card |

### Passive Effectiveness
- **Economic passives** (Silk Road, Midas, Industrial Revolution) trigger frequently but don't translate to wins for Economist strategy
- **Combat passives** (Guernica, Black Death, Pulsar) show high win rates
- **Scaling passives** (Yggdrasil, Baobab) require survival time that Tempo doesn't allow

---

## 6. BALANCE RECOMMENDATIONS

### Priority 1: NERF TEMPO STRATEGY 🔴 CRITICAL

**Option A: Reduce Early Game Aggression**
```python
# Modify AI._buy_tempo() to be less aggressive in early turns
if turn <= 8:
    # Reduce card purchase priority
    max_cards = min(max_cards, 1)  # Buy only 1 card early
```

**Option B: Increase Early Game Damage Cap Duration**
```python
# Extend damage cap to turn 15 instead of turn 10
if turn <= 15:
    final_damage = min(final_damage, 15)
```

**Option C: Reduce Tempo's Mid-Game Power Spike**
```python
# Add turn-based multiplier to Tempo's card strength
if player.strategy == "tempo" and turn <= 12:
    # Reduce effectiveness of early cards
    card_power_multiplier = 0.85
```

### Priority 2: BUFF LATE-GAME STRATEGIES 🟡 HIGH

**Economist Buffs:**
- Increase interest cap from 5 to 6 gold
- Add "compound interest" mechanic after turn 15
- Reduce market refresh cost for Economist (-1 gold)

**Evolver Buffs:**
- Reduce evolution cost by 1 gold
- Add "evolution bonus" stats (+1 to all edges)
- Allow evolution at 2 copies instead of 3 for rare+ cards

**Balancer Buffs:**
- Increase synergy bonus multiplier by 20%
- Add "balance bonus" when having equal group distribution
- Reduce level-up cost by 1 gold

### Priority 3: CARD BALANCE ADJUSTMENTS 🟢 MEDIUM

**Cards Needing Nerfs:**
- Guernica (95% win rate) - Reduce passive trigger frequency
- Space-Time (93% win rate) - Reduce stat bonuses
- Pulsar (100% win rate) - Increase rarity or reduce power

**Cards Needing Buffs:**
- Tardigrade (0% win rate) - Increase durability or add survival passive
- Entropy (0% win rate) - Strengthen debuff effects
- Quantum Mechanics (0% win rate) - Add combat advantage
- Gothic Architecture (0% win rate) - Increase base stats
- Cubism (0% win rate) - Rework passive ability

### Priority 4: GAME LENGTH EXTENSION 🟢 MEDIUM

**Current Issue:** Games end too quickly (27.8 avg turns) for late-game strategies

**Solutions:**
- Increase starting HP from 100 to 120
- Further reduce early game damage (extend cap to turn 15)
- Add "comeback mechanics" for players below 30 HP

---

## 7. DETAILED STATISTICS

### Strategy Win Rate Over Time (Estimated)

Based on average survival and final HP:

| Strategy | Early Game (T1-10) | Mid Game (T11-20) | Late Game (T21+) |
|----------|-------------------|-------------------|------------------|
| Tempo | Strong | **Dominant** | Strong |
| Builder | Weak | Growing | **Strong** |
| Rare Hunter | Medium | Medium | Medium |
| Warrior | Strong | Declining | Weak |
| Economist | Weak | Weak | Medium |
| Evolver | Weak | Medium | Medium |
| Balancer | Medium | Medium | Weak |

### Card Rarity Distribution in Winning Decks

(Based on passive trigger frequency and survival rates)

**Tempo Winning Compositions:**
- Focus on MIND and CONNECTION groups
- Prefer common/uncommon cards for early tempo
- Key cards: Gravity, Space-Time, Ottoman Empire, Age of Discovery

**Builder Winning Compositions:**
- Economic cards with scaling passives
- Key cards: Blue Whale, Pulsar, Gravity, Minimalism
- Higher average card survival time (20+ turns)

---

## 8. CONCLUSION

### Summary of Findings

1. **Tempo is still overpowered** (47.7% win rate) despite BAL 5 damage cap
2. **Builder is viable** (29.2% win rate) but still far behind Tempo
3. **Late-game strategies are unviable** (Economist, Evolver, Balancer all <4%)
4. **Card balance is highly skewed** (some cards 100% win rate, others 0%)
5. **Games are too short** for scaling strategies to work (27.8 avg turns)

### Recommended Action Plan

**Phase 1 (Immediate):**
1. Extend damage cap to turn 15 (currently turn 10)
2. Nerf Tempo's early card purchase aggression
3. Buff Economist interest mechanics

**Phase 2 (Short-term):**
1. Rebalance top 10 and bottom 10 cards
2. Increase starting HP to 120
3. Add comeback mechanics

**Phase 3 (Long-term):**
1. Rework Evolver strategy mechanics
2. Add more late-game focused cards
3. Implement dynamic difficulty scaling

### Success Metrics for Next Simulation

Target win rate distribution for 8-player games:
- Top strategy: <25% win rate
- Bottom strategy: >5% win rate
- Win rate spread: <20 percentage points
- Average game length: 32+ turns
- Late-game strategy viability: >10% combined win rate

---

## APPENDIX A: Raw Data Summary

**Total Games:** 2000
**Total Player Instances:** 16,000
**Total Draws:** 19,901
**Card Pool:** 101 cards
**Strategies Tested:** 8

**Win Distribution:**
- Tempo: 954 wins (47.7%)
- Builder: 585 wins (29.2%)
- Others: 461 wins (23.1%)

**Performance Spread:** 47.0 percentage points (Tempo 47.7% vs Random 0.7%)

---

*Report Generated: March 29, 2026*
*Simulation Engine: Autochess Hybrid v0.6*
*Analysis: Post-BAL 5 Implementation*
