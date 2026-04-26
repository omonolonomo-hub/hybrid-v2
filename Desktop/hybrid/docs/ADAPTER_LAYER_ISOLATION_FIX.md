# Adapter Layer Isolation Fix

## Problem Statement

The adapter pattern exists to provide layer isolation between the UI/view layer and the engine core. However, `UIAdapter` and `ShopScene` were bypassing `EngineAdapter` and directly importing from `engine_core`, breaking encapsulation and creating hidden dependencies.

### Violations Identified

1. **UIAdapter → engine_core Direct Import**
   ```python
   # v2/core/ui_adapter.py lines 1-10
   from engine_core.constants import (
       STARTING_HP, CATEGORY_DISPLAY_MAP, COPY_THRESH, COPY_THRESH_C, SYNERGY_THRESHOLDS
   )
   from engine_core.synergy import tier_bonus as _engine_tier_bonus
   ```
   
   UI layer was directly importing engine constants and functions, bypassing EngineAdapter.

2. **ShopScene → CardDatabase Direct Access**
   ```python
   # _handle_mouse_down, _add_board_flip, _spawn_placement_float
   from v2.core.card_database import CardDatabase
   card_data = CardDatabase.get().lookup(card_name)
   ```
   
   View layer was directly accessing infrastructure layer (CardDatabase) without going through EngineAdapter.

### The Jenga Tower Problem

When `CardDatabase` singleton pattern changes (e.g., lazy loading replaced with injection), all three `CardDatabase.get()` calls in ShopScene must be manually tracked down. These hidden dependencies are invisible without grep and break when the underlying implementation changes.

## Solution

### 1. Extended EngineAdapter API

Added methods to `EngineAdapter` to provide controlled access to engine data:

```python
class EngineConstants(NamedTuple):
    """Immutable snapshot of engine constants."""
    STARTING_HP: int
    CATEGORY_DISPLAY_MAP: Dict[str, str]
    COPY_THRESH: Tuple[int, int]
    COPY_THRESH_C: Tuple[int, int]
    SYNERGY_THRESHOLDS: Tuple[int, ...]
    CARD_COSTS: Dict[str, int]
    BOARD_RADIUS: int

class CardDataSnapshot(NamedTuple):
    """Immutable snapshot of card data."""
    name: str
    category: str
    rarity: str
    stats: Dict[str, int]
    passive_type: str
    passive_effect: str
    synergy_group: str

@staticmethod
def get_constants() -> EngineConstants:
    """Return immutable snapshot of engine constants."""
    
@staticmethod
def get_card_info(name: str) -> Optional[CardDataSnapshot]:
    """Return immutable snapshot of card data from CardDatabase."""
    
@staticmethod
def tier_bonus(threshold: int) -> int:
    """Calculate tier bonus for a given threshold."""

@staticmethod
def get_hex_coords(radius: int) -> List[Tuple[int, int]]:
    """Return list of valid hex coordinates for the given radius."""
```

### 2. Refactored UIAdapter

- Removed direct `engine_core` imports
- Added `_constants` cache in `__init__()` to store `EngineAdapter.get_constants()`
- Replaced all `STARTING_HP`, `CATEGORY_DISPLAY_MAP`, `COPY_THRESH`, etc. with `self._constants.*`
- Replaced `_engine_tier_bonus()` calls with `EngineAdapter.tier_bonus()`

**Before:**
```python
from engine_core.constants import STARTING_HP, CATEGORY_DISPLAY_MAP
from engine_core.synergy import tier_bonus as _engine_tier_bonus

hp=STARTING_HP
category = CATEGORY_DISPLAY_MAP.get(card.category)
bonus = _engine_tier_bonus(threshold)
```

**After:**
```python
from v2.core.engine_adapter import EngineAdapter

self._constants = EngineAdapter.get_constants()
hp=self._constants.STARTING_HP
category = self._constants.CATEGORY_DISPLAY_MAP.get(card.category)
bonus = EngineAdapter.tier_bonus(threshold)
```

### 3. Refactored ShopScene

Replaced all three `CardDatabase.get().lookup()` calls with `EngineAdapter.get_card_info()`:

**Before:**
```python
from v2.core.card_database import CardDatabase
card_data = CardDatabase.get().lookup(card_name)
evolved = bool(db and getattr(db, "rarity", None) == "E")
```

**After:**
```python
from v2.core.engine_adapter import EngineAdapter
card_data = EngineAdapter.get_card_info(card_name)
evolved = bool(card_data and card_data.rarity == "E")
```

### 4. Refactored hex_grid.py

Replaced direct `engine_core` imports with `EngineAdapter`:

**Before:**
```python
from engine_core.constants import BOARD_RADIUS
from engine_core.board import hex_coords

VALID_HEX_COORDS = set(hex_coords(BOARD_RADIUS))
```

**After:**
```python
from v2.core.engine_adapter import EngineAdapter

_ENGINE_CONSTANTS = EngineAdapter.get_constants()
BOARD_RADIUS = _ENGINE_CONSTANTS.BOARD_RADIUS
VALID_HEX_COORDS = frozenset(EngineAdapter.get_hex_coords(BOARD_RADIUS))
```

## Benefits

1. **Single Source of Truth**: All engine data access goes through `EngineAdapter`
2. **Testability**: `EngineAdapter` tests now cover all engine interactions
3. **Refactor Safety**: Changing `CardDatabase` implementation only requires updating `EngineAdapter.get_card_info()`
4. **Layer Isolation**: UI layer has no knowledge of engine internals
5. **Immutability**: `EngineConstants` and `CardDataSnapshot` are immutable NamedTuples, preventing accidental mutations

## Verification

All direct `engine_core` imports removed from UI/view layer:
- ✅ `v2/core/ui_adapter.py` - No `from engine_core` imports
- ✅ `v2/scenes/shop.py` - No `from v2.core.card_database` imports
- ✅ `v2/ui/hex_grid.py` - No `from engine_core` imports
- ✅ All diagnostics pass
- ✅ Game starts and runs successfully

Remaining `engine_core` imports are in appropriate locations:
- ✅ `v2/main.py` - Entry point (acceptable)
- ✅ `v2/core/engine_adapter.py` - The adapter itself (required)
- ✅ `v2/core/synergy_calculator.py` - Core adapter layer (acceptable)

## Impact

- **Files Modified**: 4
  - `v2/core/engine_adapter.py` - Added `get_constants()`, `get_card_info()`, `tier_bonus()`, `get_hex_coords()`
  - `v2/core/ui_adapter.py` - Removed direct engine imports, uses `EngineAdapter`
  - `v2/scenes/shop.py` - Removed direct `CardDatabase` access, uses `EngineAdapter`
  - `v2/ui/hex_grid.py` - Removed direct engine imports, uses `EngineAdapter`

- **Breaking Changes**: None (internal refactor only)
- **Performance**: Negligible (constants cached at module/instance level)
- **Test Results**: ✅ All diagnostics pass, game runs successfully

## Future Work

Consider extending this pattern to other potential violations:
- Check if other scenes have direct engine imports
- Audit `v2/ui/` components for hidden dependencies
- Add linting rule to prevent `from engine_core` in `v2/` layer
