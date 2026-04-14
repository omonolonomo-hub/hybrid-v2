# Copy Strengthening vs Evolution Fix

## Date: 2026-03-29

## Problem

Copy strengthening sistemi tüm stratejilere eşit avantaj veriyordu, bu da evolver stratejisinin unique mekanizmasını (evolution) zayıflatıyordu.

### Conflict Details

1. **Evolver Strategy**: 3 kopya topladığında evolution tetiklenir
   - 2 kopya consume edilir, 1 evolved card oluşur
   - `copies[base_name] -= 2` → copies = 1
   - Copy strengthening bonuslarını alamaz (özellikle copy_3)

2. **Other Strategies**: 2-3 kopya toplayarak copy strengthening alır
   - 2 copies → +2 stats (turn 4)
   - 3 copies → +3 stats (turn 7)
   - Evolution riski olmadan güçlenme

3. **Result**: Evolver'ın unique avantajı azalıyor
   - Diğer stratejiler daha düşük riskle benzer güçlenme alıyor
   - Evolution mekanizması cazibesini kaybediyor

### Statistics (1000 games)

- copy_2 triggers: 30,984
- copy_3 triggers: 2,428
- Ratio: 12.8:1

Çoğu oyuncu 3. kopya eşiğine ulaşamıyor, ama evolver 3 kopya topladığında evolve ediyor ve copy_3 bonusunu kaçırıyor.

---

## Solution

Copy strengthening'i **sadece evolver dışındaki stratejilere** özel yaptık.

### Implementation

```python
def check_copy_strengthening(self, turn: int, passive_log=None):
    """Strengthen cards when copy thresholds are reached.
    
    v0.7: Copy strengthening is DISABLED for evolver strategy.
    Evolver uses evolution system instead (3 copies -> evolved card).
    Other strategies use copy strengthening (2 copies -> +2, 3 copies -> +3).
    """
    # Evolver strategy uses evolution, not copy strengthening
    if self.strategy == "evolver":
        return
    
    # ... rest of copy strengthening logic ...
```

### Strategy Differentiation

| Strategy | 2 Copies | 3 Copies |
|----------|----------|----------|
| **Evolver** | No bonus | Evolution (consume 2, get evolved card) |
| **All Others** | +2 stats (turn 4) | +3 stats (turn 7) |

---

## Benefits

1. **Clear Strategy Identity**
   - Evolver: High-risk, high-reward evolution path
   - Others: Safer copy strengthening path

2. **Balanced Risk/Reward**
   - Evolution: Consume 2 copies, get powerful evolved card
   - Copy strengthening: Keep all copies, get incremental bonuses

3. **Strategic Diversity**
   - Each strategy has unique progression mechanics
   - No overlap between evolution and copy strengthening

4. **Better Game Balance**
   - Evolver's unique mechanic is now truly unique
   - Other strategies have their own progression path

---

## Testing

### Test Results (50 games)

```
Strategy        Wins    Win Rate    Avg HP
----------------------------------------
tempo           17      34.0%       83.0
economist       8       16.0%       19.4
builder         6       12.0%       19.9
evolver         5       10.0%       5.0
balancer        5       10.0%       12.7
rare_hunter     5       10.0%       14.3
warrior         4       8.0%        6.8
random          0       0.0%        0.0
```

Copy triggers:
- copy_2: 610 (50 games)
- copy_3: 101 (50 games)
- Ratio: 6:1

### Observations

1. Evolver no longer receives copy strengthening bonuses
2. Other strategies benefit from copy strengthening
3. Evolution remains evolver's exclusive mechanic
4. Tempo strategy dominates (separate balance issue)

---

## Files Modified

1. `engine_core/autochess_sim_v06.py`
   - Updated `Player.check_copy_strengthening()` to skip evolver strategy
   - Added docstring explaining the strategy-specific behavior

---

## Future Considerations

### Potential Enhancements

1. **Evolver-specific bonuses**: Give evolver unique pre-evolution bonuses
   - Example: +1 stat per copy collected (before evolution)
   - Reward copy collection without conflicting with evolution

2. **Evolution timing control**: Let evolver choose when to evolve
   - Manual trigger instead of automatic at 3 copies
   - Strategic decision: evolve now or wait for better timing

3. **Partial evolution**: Keep 1 copy after evolution
   - Current: 3 copies → 1 evolved (2 consumed)
   - Alternative: 3 copies → 1 evolved + 1 base (1 consumed)
   - Allows continued copy strengthening post-evolution

### Balance Monitoring

Track these metrics in future simulations:
- Evolver win rate vs other strategies
- Evolution frequency per game
- Average turn of first evolution
- Evolved card survival rate

---

## Conclusion

Copy strengthening is now exclusive to non-evolver strategies, giving evolver a unique identity through the evolution mechanic. This creates clearer strategic differentiation and better game balance.

The fix successfully separates two progression systems that were previously conflicting, allowing each strategy to have its own path to power.
