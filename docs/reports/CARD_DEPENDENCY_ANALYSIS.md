# Card Class & Related Functions - Dependency Analysis

## Overview
This document analyzes the dependencies of the Card class and related functions (`build_card_pool`, `evolve_card`, `apply_micro_buff_to_weak_cards`) to determine safe extraction order for refactoring.

---

## 1. Card Class Dependencies

### Location
- File: `engine_core/autochess_sim_v06.py`
- Lines: 117-232

### External Constants Used
From `constants.py`:
- `STAT_TO_GROUP` - Maps stat names to group names (EXISTENCE, MIND, CONNECTION)
- `RARITY_TAVAN` - Target power values by rarity (used indirectly via evolved cards)
- `EVOLVED_TAVAN` - Target power values for evolved cards by base rarity

### Helper Functions Used
None - Card class is self-contained

### Standard Library Dependencies
- `dataclasses.dataclass` - Class decorator
- `dataclasses.field` - For default factory
- `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Tuple` - Type hints
- `collections.defaultdict` - Used in `dominant_group()` method

### Player/Board Dependencies
**NONE** - Card class has zero dependencies on Player or Board classes

### Methods Analysis

#### Pure Methods (no external dependencies):
- `__post_init__()` - Initializes edges from stats
- `edge_val(d)` - Returns edge value at direction d
- `total_power()` - Sums all non-internal stats
- `is_eliminated()` - Checks if card is eliminated
- `lose_highest_edge()` - Zeros highest edge
- `apply_edge_debuff(d, amount)` - Applies debuff to specific edge
- `strengthen(copy_num)` - Strengthens highest edge
- `clone()` - Creates deep copy
- `__repr__()` - String representation

#### Methods Using External Constants:
- `edge_group(d)` - Uses `STAT_TO_GROUP`
- `dominant_group()` - Uses `STAT_TO_GROUP`
- `get_group_composition()` - Uses `STAT_TO_GROUP`

### Extraction Safety
**SAFE TO EXTRACT FIRST** - Card class can be extracted independently with only constants module dependency.

---

## 2. build_card_pool() Function

### Location
- File: `engine_core/autochess_sim_v06.py`
- Lines: 235-253

### External Constants Used
From `constants.py`:
- `_LEGACY_RARITY_TO_ID` - Maps diamond symbols to numeric rarity IDs

### Helper Functions Used
- `_normalize_rarity(rarity)` - Line 80-81
- `_load_card_entry(entry)` - Line 84-89

### Standard Library Dependencies
- `os.path` - File path operations
- `json` - JSON parsing
- `typing.List` - Type hints

### Data File Dependencies
- `assets/data/cards.json` - Card data file (relative path: `../assets/data/cards.json`)

### Player/Board Dependencies
**NONE** - Function only creates Card instances

### Extraction Safety
**SAFE TO EXTRACT SECOND** - Requires Card class and helper functions to be available.

---

## 3. apply_micro_buff_to_weak_cards() Function

### Location
- File: `engine_core/autochess_sim_v06.py`
- Lines: 255-326

### External Constants Used
**NONE** - No constants imported

### Helper Functions Used
**NONE** - Self-contained logic

### Standard Library Dependencies
- `typing.List` - Type hints

### Card Class Dependencies
- Reads `card.stats` dictionary
- Modifies `card.stats` dictionary
- Rebuilds `card.edges` list

### Player/Board Dependencies
**NONE** - Only operates on Card instances

### Extraction Safety
**SAFE TO EXTRACT THIRD** - Requires Card class to be available. Can be extracted after Card class.

---

## 4. evolve_card() Function

### Location
- File: `engine_core/autochess_sim_v06.py`
- Lines: 328-365

### External Constants Used
From `constants.py`:
- `EVOLVED_TAVAN` - Target power values for evolved cards by base rarity
- `RARITY_TAVAN` - Fallback target power values

### Helper Functions Used
**NONE** - Self-contained logic

### Standard Library Dependencies
- `typing.Dict` - Type hints

### Card Class Dependencies
- Reads `base_card.stats`, `base_card.rarity`, `base_card.category`, `base_card.passive_type`
- Creates new Card instance

### Player/Board Dependencies
**NONE** - Only operates on Card instances

### Extraction Safety
**SAFE TO EXTRACT FOURTH** - Requires Card class to be available. Can be extracted after Card class.

---

## 5. Helper Functions

### _normalize_rarity()
- **Location**: Lines 80-81
- **Dependencies**: `_LEGACY_RARITY_TO_ID` constant
- **Safety**: Extract with `build_card_pool()`

### _load_card_entry()
- **Location**: Lines 84-89
- **Dependencies**: None (pure function)
- **Safety**: Extract with `build_card_pool()`

### _create_passive_log()
- **Location**: Lines 75-77
- **Dependencies**: `collections.defaultdict`
- **Safety**: Not needed for Card extraction (used by game logic)

---

## 6. Module-Level Variables

### CARD_POOL
- **Location**: Line 318
- **Definition**: `CARD_POOL: List[Card] = build_card_pool()`
- **Dependencies**: `build_card_pool()` function
- **Note**: Micro-buff applied immediately after (line 321)

### CARD_BY_NAME
- **Location**: Line 323
- **Definition**: `CARD_BY_NAME: Dict[str, Card] = {c.name: c for c in CARD_POOL}`
- **Dependencies**: `CARD_POOL`

---

## 7. Safe Extraction Order

### Phase 1: Card Class
**Extract First** - Zero dependencies on Player/Board
```
Card class (lines 117-232)
├── Requires: STAT_TO_GROUP constant
└── No Player/Board dependencies
```

### Phase 2: Helper Functions
**Extract Second** - Support card pool building
```
_normalize_rarity() (lines 80-81)
_load_card_entry() (lines 84-89)
├── Requires: _LEGACY_RARITY_TO_ID constant
└── No Player/Board dependencies
```

### Phase 3: Card Pool Builder
**Extract Third** - Creates card instances
```
build_card_pool() (lines 235-253)
├── Requires: Card class, helper functions
├── Requires: assets/data/cards.json file
└── No Player/Board dependencies
```

### Phase 4: Card Modifiers
**Extract Fourth** - Modifies card instances
```
apply_micro_buff_to_weak_cards() (lines 255-326)
evolve_card() (lines 328-365)
├── Requires: Card class
├── Requires: EVOLVED_TAVAN, RARITY_TAVAN constants
└── No Player/Board dependencies
```

### Phase 5: Module-Level Initialization
**Extract Last** - Initializes global card pool
```
CARD_POOL initialization (line 318)
apply_micro_buff_to_weak_cards(CARD_POOL) (line 321)
CARD_BY_NAME initialization (line 323)
├── Requires: All above functions
└── No Player/Board dependencies
```

---

## 8. Reverse Dependencies (What Uses These?)

### Card Class Used By:
- `Board.place()` - Stores Card instances
- `Board.alive_cards()` - Returns List[Card]
- `Player.buy_card()` - Adds Card to hand
- `Player.check_copy_strengthening()` - Calls `card.strengthen()`
- `Player.check_evolution()` - Uses `evolve_card()`
- `Market` - Manages Card pool
- `AI` strategies - Evaluates Card properties
- `combat_phase()` - Uses Card in battles
- `resolve_single_combat()` - Reads Card edges and stats

### build_card_pool() Used By:
- Module initialization (line 318)
- `Market.__init__()` - Uses CARD_POOL

### evolve_card() Used By:
- `Player.check_evolution()` - Creates evolved cards

### apply_micro_buff_to_weak_cards() Used By:
- Module initialization (line 321) - Applied once at startup

---

## 9. Critical Notes for Refactoring

### ✅ Safe to Extract (No Circular Dependencies)
1. Card class is completely independent of Player/Board
2. All card-related functions only depend on Card class and constants
3. No reverse dependencies that would create circular imports

### ⚠️ Important Considerations
1. **File Path**: `build_card_pool()` uses relative path `../assets/data/cards.json`
   - Must maintain correct relative path after extraction
   - Consider making path configurable

2. **Module-Level Initialization**: Lines 318-323 run at import time
   - CARD_POOL is created once at module load
   - Micro-buff is applied once at module load
   - CARD_BY_NAME dictionary is built once at module load

3. **Constants Dependency**: All functions depend on `constants.py`
   - Must ensure constants module is importable from new location

4. **Type Hints**: Card class uses forward references (`"Card"`)
   - These work correctly within the class definition

### 🎯 Recommended Extraction Target
Create new module: `engine_core/card.py`

**Contents**:
```python
# Imports
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import os
import json

# Constants import
from .constants import (
    STAT_TO_GROUP,
    _LEGACY_RARITY_TO_ID,
    EVOLVED_TAVAN,
    RARITY_TAVAN
)

# Helper functions
_normalize_rarity()
_load_card_entry()

# Card class
class Card: ...

# Card pool functions
build_card_pool()
apply_micro_buff_to_weak_cards()
evolve_card()

# Module-level initialization
CARD_POOL = build_card_pool()
apply_micro_buff_to_weak_cards(CARD_POOL)
CARD_BY_NAME = {c.name: c for c in CARD_POOL}
```

**Benefits**:
- Clean separation of concerns
- No circular dependencies
- Easy to test in isolation
- Maintains all existing functionality

---

## 10. Summary

### Dependencies Hierarchy
```
constants.py
    ↓
card.py (new module)
    ├── Card class
    ├── build_card_pool()
    ├── evolve_card()
    └── apply_micro_buff_to_weak_cards()
    ↓
autochess_sim_v06.py
    ├── Board class
    ├── Player class
    ├── AI class
    └── Game class
```

### Extraction Complexity: **LOW**
- No circular dependencies
- Clear separation of concerns
- Minimal refactoring needed in main file (just update imports)

### Risk Level: **MINIMAL**
- Card class is self-contained
- No Player/Board dependencies
- All functions are pure or only depend on Card class
