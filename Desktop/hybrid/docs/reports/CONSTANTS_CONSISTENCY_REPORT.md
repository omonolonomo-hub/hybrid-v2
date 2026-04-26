# Constants Consistency Fix Report

## Problem Identified

Tutarsızlık tespit edildi:
- `constants.py`: CARD_COSTS r4=5, r5=7, BOARD_RADIUS=3 (DOĞRU)
- `autochess_sim_v06.py`: CARD_COSTS r4=8, r5=10, BOARD_RADIUS=2 (ESKİ/YANLIŞ)

## Solution Applied

`autochess_sim_v06.py` dosyasındaki tüm constant tanımları kaldırıldı ve `constants.py`'den import edildi.

### Changes Made

1. **Removed duplicate constant definitions** from `autochess_sim_v06.py`:
   - STAT_GROUPS
   - STAT_TO_GROUP
   - _RARITY_DIAMOND
   - _LEGACY_RARITY_TO_ID
   - GROUP_BEATS
   - RARITY_TAVAN
   - EVOLVED_TAVAN
   - RARITY_DMG_BONUS
   - HEX_DIRS, DIR_NAME, OPP_DIR
   - BOARD_RADIUS (was 2, now imports 3)
   - STARTING_HP, KILL_PTS
   - COPY_THRESH, COPY_THRESH_C
   - BASE_INCOME, MARKET_REFRESH_COST
   - MAX_INTEREST, INTEREST_STEP
   - CARD_COSTS (was r4=8, r5=10, now imports r4=5, r5=7)
   - EVOLVE_COPIES_REQUIRED
   - HAND_LIMIT, PLACE_PER_TURN
   - STRATEGIES

2. **Added import statement** at the top of `autochess_sim_v06.py`:
   ```python
   # Import constants from constants module
   try:
       from .constants import (
           STAT_GROUPS, STAT_TO_GROUP, _RARITY_DIAMOND, _LEGACY_RARITY_TO_ID,
           GROUP_BEATS, RARITY_TAVAN, EVOLVED_TAVAN, RARITY_DMG_BONUS,
           HEX_DIRS, DIR_NAME, OPP_DIR, BOARD_RADIUS, STARTING_HP, KILL_PTS,
           COPY_THRESH, COPY_THRESH_C, BASE_INCOME, MARKET_REFRESH_COST,
           MAX_INTEREST, INTEREST_STEP, CARD_COSTS, EVOLVE_COPIES_REQUIRED,
           HAND_LIMIT, PLACE_PER_TURN, STRATEGIES
       )
       from .card import Card, build_card_pool, evolve_card, apply_micro_buff_to_weak_cards
       from .board import (
           Board, BOARD_COORDS, hex_coords, _find_coord, _neighbor_cards,
           CombatResult, resolve_single_combat, find_combos,
           calculate_group_synergy_bonus, calculate_damage
       )
   except ImportError:
       # Fall back to absolute import (when run as a script)
       from constants import (...)
       from card import (...)
       from board import (...)
   ```

## Verification

### Test Results

✅ **constants.py values (CORRECT)**:
- CARD_COSTS['4'] = 5
- CARD_COSTS['5'] = 7
- BOARD_RADIUS = 3

✅ **autochess_sim_v06.py now imports these values**:
- No duplicate definitions
- Single source of truth: `constants.py`
- All files use consistent values

### Impact

**Before Fix:**
- Inconsistent card costs across codebase
- Smaller board size (19 hex vs 37 hex)
- Potential gameplay balance issues
- Confusion for developers

**After Fix:**
- ✅ Single source of truth for all constants
- ✅ Consistent CARD_COSTS (r4=5, r5=7)
- ✅ Consistent BOARD_RADIUS (3 = 37 hex)
- ✅ No duplicate definitions
- ✅ Easier maintenance

## Files Modified

1. `engine_core/autochess_sim_v06.py`
   - Removed ~30 lines of duplicate constant definitions
   - Added import from `constants.py`
   - Added import from `card.py` and `board.py`

## Benefits

1. **Consistency**: All modules use same constant values
2. **Maintainability**: Change constants in one place (`constants.py`)
3. **Correctness**: Uses updated balance values (r4=5, r5=7, BOARD_RADIUS=3)
4. **Clarity**: Clear separation of concerns

## Developer Guidelines

### ⚠️ IMPORTANT: Where to Modify Constants

**DO NOT** add or modify constants in `autochess_sim_v06.py`!

All game constants are defined in `engine_core/constants.py`. To change a constant:

1. Open `engine_core/constants.py`
2. Modify the constant value
3. All modules will automatically use the new value

### Constant Categories

**Game Balance:**
- CARD_COSTS - Card purchase costs by rarity
- STARTING_HP - Player starting health
- KILL_PTS - Points per kill
- COPY_THRESH - Copy strengthening thresholds

**Board & Combat:**
- BOARD_RADIUS - Hex board size (3 = 37 hexes)
- HEX_DIRS - Hex direction vectors
- GROUP_BEATS - Combat advantage matrix

**Economy:**
- BASE_INCOME - Gold per turn
- MAX_INTEREST - Maximum interest gold
- INTEREST_STEP - Gold per interest tier

**Rules:**
- HAND_LIMIT - Maximum cards in hand
- PLACE_PER_TURN - Cards placed per turn
- EVOLVE_COPIES_REQUIRED - Copies for evolution

## Conclusion

Constants tutarsızlığı düzeltildi. Tüm modüller artık `constants.py`'den import ediyor ve tutarlı değerler kullanıyor:
- ✅ CARD_COSTS r4=5, r5=7 (eski 8, 10 değil)
- ✅ BOARD_RADIUS=3 (eski 2 değil)
- ✅ Tek kaynak: `constants.py`

---

**Generated**: 2026-04-03  
**Issue**: Constants inconsistency between constants.py and autochess_sim_v06.py  
**Resolution**: Removed duplicates, centralized in constants.py  
**Status**: ✅ RESOLVED
