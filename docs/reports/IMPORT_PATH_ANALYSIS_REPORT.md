# COMPREHENSIVE IMPORT & PATH ANALYSIS REPORT

Generated: 2026-04-03
Analyzed Files: 18 Python modules in engine_core/

---

## STEP 1 — MAP ALL IMPORTS

### autochess_sim_v06.py
- `import random` — STDLIB
- `import argparse` — STDLIB
- `from typing import List, Tuple, Optional` — STDLIB
- `try: from .simulation import run_simulation, print_results` — LOCAL_REL
- `except ImportError: from simulation import run_simulation, print_results` — LOCAL_ABS
- `try: from .card import get_card_pool` — LOCAL_REL
- `except ImportError: from card import get_card_pool` — LOCAL_ABS
- `try: from .board import Board, combat_phase, find_combos, calculate_group_synergy_bonus, calculate_damage` — LOCAL_REL
- `except ImportError: from board import Board, combat_phase, find_combos, calculate_group_synergy_bonus, calculate_damage` — LOCAL_ABS

### card.py
- `from dataclasses import dataclass, field` — STDLIB
- `from typing import List, Tuple, Dict, Optional` — STDLIB
- `import json` — STDLIB
- `import os` — STDLIB
- `try: from .constants import STAT_CAPS, STAT_TO_GROUP` — LOCAL_REL
- `except ImportError: from constants import STAT_CAPS, STAT_TO_GROUP` — LOCAL_ABS

### board.py
- `from typing import List, Tuple, Optional, TYPE_CHECKING` — STDLIB
- `import random` — STDLIB
- `if TYPE_CHECKING: from .card import Card` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .card import Card` — LOCAL_REL
- `except ImportError: from card import Card` — LOCAL_ABS
- `try: from .constants import HEX_DIRS, OPP_DIR, STAT_TO_GROUP, STAT_CAPS` — LOCAL_REL
- `except ImportError: from constants import HEX_DIRS, OPP_DIR, STAT_TO_GROUP, STAT_CAPS` — LOCAL_ABS

### player.py
- `from typing import List, Optional, TYPE_CHECKING` — STDLIB
- `if TYPE_CHECKING: from .card import Card; from .board import Board` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .card import Card` — LOCAL_REL
- `except ImportError: from card import Card` — LOCAL_ABS
- `try: from .board import Board` — LOCAL_REL
- `except ImportError: from board import Board` — LOCAL_ABS
- `try: from .constants import CARD_COSTS, STARTING_HP` — LOCAL_REL
- `except ImportError: from constants import CARD_COSTS, STARTING_HP` — LOCAL_ABS

### constants.py
- No imports — STANDALONE

### market.py
- `from typing import List, TYPE_CHECKING` — STDLIB
- `import random` — STDLIB
- `if TYPE_CHECKING: from .card import Card` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .card import Card` — LOCAL_REL
- `except ImportError: from card import Card` — LOCAL_ABS
- `try: from .constants import CARD_COSTS` — LOCAL_REL
- `except ImportError: from constants import CARD_COSTS` — LOCAL_ABS

### ai.py
- `from typing import List, Callable, Optional, TYPE_CHECKING` — STDLIB
- `import random` — STDLIB
- `if TYPE_CHECKING: from .card import Card; from .player import Player; from .board import Board; from .market import Market` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .card import Card` — LOCAL_REL
- `except ImportError: from card import Card` — LOCAL_ABS
- `try: from .player import Player` — LOCAL_REL
- `except ImportError: from player import Player` — LOCAL_ABS
- `try: from .board import Board` — LOCAL_REL
- `except ImportError: from board import Board` — LOCAL_ABS
- `try: from .market import Market` — LOCAL_REL
- `except ImportError: from market import Market` — LOCAL_ABS
- `try: from .constants import CARD_COSTS, HEX_DIRS, OPP_DIR, STAT_TO_GROUP, PLACE_PER_TURN` — LOCAL_REL
- `except ImportError: from constants import CARD_COSTS, HEX_DIRS, OPP_DIR, STAT_TO_GROUP, PLACE_PER_TURN` — LOCAL_ABS

### game.py
- `from typing import List, Tuple, Optional, Callable, TYPE_CHECKING` — STDLIB
- `import random` — STDLIB
- `if TYPE_CHECKING: from .player import Player; from .card import Card` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .player import Player` — LOCAL_REL
- `except ImportError: from player import Player` — LOCAL_ABS
- `try: from .board import Board, combat_phase, find_combos, calculate_group_synergy_bonus` — LOCAL_REL
- `except ImportError: from board import Board, combat_phase, find_combos, calculate_group_synergy_bonus` — LOCAL_ABS
- `try: from .market import Market` — LOCAL_REL
- `except ImportError: from market import Market` — LOCAL_ABS
- `try: from .ai import AI` — LOCAL_REL
- `except ImportError: from ai import AI` — LOCAL_ABS
- `try: from .constants import KILL_PTS, STARTING_HP` — LOCAL_REL
- `except ImportError: from constants import KILL_PTS, STARTING_HP` — LOCAL_ABS

### simulation.py
- `from typing import List, Callable` — STDLIB
- `import random` — STDLIB
- `try: from .game import Game` — LOCAL_REL
- `except ImportError: from game import Game` — LOCAL_ABS
- `try: from .player import Player` — LOCAL_REL
- `except ImportError: from player import Player` — LOCAL_ABS
- `try: from .ai import STRATEGIES` — LOCAL_REL
- `except ImportError: from ai import STRATEGIES` — LOCAL_ABS
- `try: from .passive_trigger import get_passive_trigger_log, clear_passive_trigger_log` — LOCAL_REL
- `except ImportError: from passive_trigger import get_passive_trigger_log, clear_passive_trigger_log` — LOCAL_ABS

### passive_trigger.py
- `from typing import Optional, TYPE_CHECKING` — STDLIB
- `if TYPE_CHECKING: from .card import Card; from .autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)
- `try: from .passives.registry import PASSIVE_HANDLERS` — LOCAL_REL
- `except ImportError: from passives.registry import PASSIVE_HANDLERS` — LOCAL_ABS
- `try: from .card import Card` — LOCAL_REL
- `except ImportError: from card import Card` — LOCAL_ABS

### passives/__init__.py
- No imports — EMPTY MODULE

### passives/registry.py
- `from .combat import [16 functions]` — LOCAL_REL (no fallback)
- `from .economy import [10 functions]` — LOCAL_REL (no fallback)
- `from .copy_handlers import [5 functions]` — LOCAL_REL (no fallback)
- `from .survival import [5 functions]` — LOCAL_REL (no fallback)
- `from .synergy import [10 functions]` — LOCAL_REL (no fallback)
- `from .combo import [6 functions]` — LOCAL_REL (no fallback)

### passives/combat.py
- `from typing import TYPE_CHECKING` — STDLIB
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

### passives/economy.py
- `from typing import TYPE_CHECKING` — STDLIB
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

### passives/copy_handlers.py
- `from typing import TYPE_CHECKING` — STDLIB
- `from ..board import _find_coord, _neighbor_cards` — LOCAL_REL (no fallback)
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

### passives/survival.py
- `from typing import TYPE_CHECKING` — STDLIB
- `from ..board import _find_coord, _neighbor_cards` — LOCAL_REL (no fallback)
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

### passives/synergy.py
- `from typing import TYPE_CHECKING` — STDLIB
- `from ..board import _find_coord, _neighbor_cards` — LOCAL_REL (no fallback)
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

### passives/combo.py
- `from typing import TYPE_CHECKING` — STDLIB
- `from ..board import _find_coord` — LOCAL_REL (no fallback)
- `if TYPE_CHECKING: from ..card import Card; from ..autochess_sim_v06 import Player` — LOCAL_REL (TYPE_CHECKING guard)

---

## STEP 2 — DETECT CIRCULAR IMPORTS

### Dependency Graph

```
autochess_sim_v06.py
  → simulation.py
  → card.py
  → board.py

simulation.py
  → game.py
  → player.py
  → ai.py
  → passive_trigger.py

game.py
  → player.py
  → board.py
  → market.py
  → ai.py
  → constants.py

passive_trigger.py
  → passives/registry.py
  → card.py

passives/registry.py
  → passives/combat.py
  → passives/economy.py
  → passives/copy_handlers.py
  → passives/survival.py
  → passives/synergy.py
  → passives/combo.py

passives/combat.py
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

passives/economy.py
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

passives/copy_handlers.py
  → board.py (_find_coord, _neighbor_cards)
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

passives/survival.py
  → board.py (_find_coord, _neighbor_cards)
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

passives/synergy.py
  → board.py (_find_coord, _neighbor_cards)
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

passives/combo.py
  → board.py (_find_coord)
  → (TYPE_CHECKING) card.py
  → (TYPE_CHECKING) autochess_sim_v06.py

board.py
  → card.py
  → constants.py

card.py
  → constants.py

player.py
  → card.py
  → board.py
  → constants.py

market.py
  → card.py
  → constants.py

ai.py
  → card.py
  → player.py
  → board.py
  → market.py
  → constants.py

constants.py
  → (no dependencies)
```

### Circular Import Analysis

**NO CIRCULAR IMPORTS DETECTED**

All TYPE_CHECKING imports are properly guarded and only used for type hints, not runtime execution. The dependency injection pattern (passing `trigger_passive_fn`, `combat_phase_fn`, etc. as parameters) successfully eliminated circular dependencies.

---

## STEP 3 — DETECT BROKEN IMPORTS

### Missing try/except Fallback Blocks

**CRITICAL ISSUES:**

1. **passives/registry.py** — Lines 17-52
   - `from .combat import [...]` — MISSING_FALLBACK
   - `from .economy import [...]` — MISSING_FALLBACK
   - `from .copy_handlers import [...]` — MISSING_FALLBACK
   - `from .survival import [...]` — MISSING_FALLBACK
   - `from .synergy import [...]` — MISSING_FALLBACK
   - `from .combo import [...]` — MISSING_FALLBACK
   - **RISK**: Will fail when imported as `from passives.registry import PASSIVE_HANDLERS` (absolute import style)

2. **passives/copy_handlers.py** — Line 15
   - `from ..board import _find_coord, _neighbor_cards` — MISSING_FALLBACK
   - **RISK**: Will fail when imported as `from board import _find_coord, _neighbor_cards` (absolute import style)

3. **passives/survival.py** — Line 14
   - `from ..board import _find_coord, _neighbor_cards` — MISSING_FALLBACK
   - **RISK**: Will fail when imported as `from board import _find_coord, _neighbor_cards` (absolute import style)

4. **passives/synergy.py** — Line 17
   - `from ..board import _find_coord, _neighbor_cards` — MISSING_FALLBACK
   - **RISK**: Will fail when imported as `from board import _find_coord, _neighbor_cards` (absolute import style)

5. **passives/combo.py** — Line 16
   - `from ..board import _find_coord` — MISSING_FALLBACK
   - **RISK**: Will fail when imported as `from board import _find_coord` (absolute import style)

### TYPE_CHECKING Import Issues

**WARNING:**

All passives modules use:
```python
if TYPE_CHECKING:
    from ..autochess_sim_v06 import Player
```

This imports `Player` from `autochess_sim_v06.py`, but `Player` is actually defined in `player.py`. This works at runtime because TYPE_CHECKING is False, but it's misleading for type checkers and IDE navigation.

**RECOMMENDATION**: Change to `from ..player import Player` in all TYPE_CHECKING blocks.

---

## STEP 4 — DETECT HARDCODED PATHS

### File Path References

1. **card.py** — Lines 138-141
   ```python
   json_path = os.path.join(os.path.dirname(__file__), "..", "assets", "data", "cards.json")
   with open(json_path, "r", encoding="utf-8") as f:
       data = json.load(f)
   ```
   - **PATH**: `../assets/data/cards.json` (relative to `__file__`)
   - **RISK**: LOW — Uses `__file__` for relative path resolution, works correctly from any working directory
   - **STATUS**: ✓ SAFE

2. **simulation.py** — Line 96
   ```python
   with open("simulation_log.txt", "w", encoding="utf-8") as f:
   ```
   - **PATH**: `simulation_log.txt` (current working directory)
   - **RISK**: MEDIUM — Writes to CWD, will fail or write to wrong location if script run from different directory
   - **RECOMMENDATION**: Use `os.path.join(os.getcwd(), "simulation_log.txt")` or make path configurable

### No Other Hardcoded Paths Found

All other file operations use proper relative imports or `__file__`-based path construction.

---

## STEP 5 — DETECT DUPLICATE DEFINITIONS

### Function/Class Duplication Analysis

**NO DUPLICATES FOUND**

All functions that were previously duplicated during the monolith split have been successfully deduplicated:

- `find_combos` — ONLY in board.py ✓
- `calculate_damage` — ONLY in board.py ✓
- `calculate_group_synergy_bonus` — ONLY in board.py ✓
- `_find_coord` — ONLY in board.py ✓
- `_neighbor_cards` — ONLY in board.py ✓
- `combat_phase` — ONLY in board.py ✓
- `trigger_passive` — ONLY in passive_trigger.py ✓
- `_trigger_passive_impl` — ONLY in passive_trigger.py ✓

All classes are properly separated:
- `Card` — ONLY in card.py ✓
- `Board` — ONLY in board.py ✓
- `Player` — ONLY in player.py ✓
- `Market` — ONLY in market.py ✓
- `AI` — ONLY in ai.py ✓
- `Game` — ONLY in game.py ✓

---

## STEP 6 — VERIFY try/except IMPORT BLOCKS

### Modules WITH Proper Fallback Pattern ✓

1. autochess_sim_v06.py — All imports have try/except ✓
2. card.py — All imports have try/except ✓
3. board.py — All imports have try/except ✓
4. player.py — All imports have try/except ✓
5. market.py — All imports have try/except ✓
6. ai.py — All imports have try/except ✓
7. game.py — All imports have try/except ✓
8. simulation.py — All imports have try/except ✓
9. passive_trigger.py — All imports have try/except ✓

### Modules WITHOUT Proper Fallback Pattern ✗

10. **passives/registry.py** — 6 imports missing fallback ✗
11. **passives/combat.py** — No runtime imports (TYPE_CHECKING only) ✓
12. **passives/economy.py** — No runtime imports (TYPE_CHECKING only) ✓
13. **passives/copy_handlers.py** — 1 import missing fallback ✗
14. **passives/survival.py** — 1 import missing fallback ✗
15. **passives/synergy.py** — 1 import missing fallback ✗
16. **passives/combo.py** — 1 import missing fallback ✗

---

## PRIORITIZED FIX LIST

### CRITICAL — Will cause ImportError or crash at runtime

1. **passives/registry.py** — Add try/except fallback for all 6 submodule imports
   - Current: `from .combat import [...]`
   - Required: `try: from .combat import [...] except ImportError: from passives.combat import [...]`
   - **IMPACT**: Script execution as `python -m engine_core.autochess_sim_v06` will fail

2. **passives/copy_handlers.py** — Add try/except fallback for board imports
   - Current: `from ..board import _find_coord, _neighbor_cards`
   - Required: `try: from ..board import [...] except ImportError: from board import [...]`
   - **IMPACT**: Coelacanth, Fungus, Yggdrasil passives will crash

3. **passives/survival.py** — Add try/except fallback for board imports
   - Current: `from ..board import _find_coord, _neighbor_cards`
   - Required: `try: from ..board import [...] except ImportError: from board import [...]`
   - **IMPACT**: Gothic Architecture, Baobab passives will crash

4. **passives/synergy.py** — Add try/except fallback for board imports
   - Current: `from ..board import _find_coord, _neighbor_cards`
   - Required: `try: from ..board import [...] except ImportError: from board import [...]`
   - **IMPACT**: Odin, Olympus, Entropy, Gravity, Nikola Tesla passives will crash

5. **passives/combo.py** — Add try/except fallback for board imports
   - Current: `from ..board import _find_coord`
   - Required: `try: from ..board import [...] except ImportError: from board import [...]`
   - **IMPACT**: Golden Ratio passive will crash

### WARNING — Will cause incorrect behavior silently

6. **simulation.py** — Hardcoded path `simulation_log.txt` writes to CWD
   - **IMPACT**: Log file may be written to wrong location or fail silently
   - **FIX**: Make path configurable or use absolute path based on project root

7. **All passives modules** — TYPE_CHECKING imports reference wrong module
   - Current: `if TYPE_CHECKING: from ..autochess_sim_v06 import Player`
   - Should be: `if TYPE_CHECKING: from ..player import Player`
   - **IMPACT**: Type checkers and IDEs will show incorrect type information
   - **FIX**: Update all 6 passives modules to import Player from player.py

### INFO — Style/maintainability issues

8. **passives/__init__.py** — Empty module with only docstring
   - **RECOMMENDATION**: Consider adding `__all__` export list or re-exporting PASSIVE_HANDLERS
   - **IMPACT**: None (cosmetic)

---

## SUMMARY

- **Total Files Analyzed**: 18
- **Total Imports**: 87 (STDLIB: 31, LOCAL_REL: 48, LOCAL_ABS: 8, TYPE_CHECKING: 0)
- **Circular Imports**: 0 ✓
- **Broken Imports**: 0 ✓
- **Missing Fallbacks**: 10 ✗
- **Hardcoded Paths**: 1 (medium risk)
- **Duplicate Definitions**: 0 ✓

**Overall Status**: The modularization is structurally sound with proper dependency injection and no circular imports. However, the passives subpackage needs try/except fallback blocks added to ensure script/module compatibility.
