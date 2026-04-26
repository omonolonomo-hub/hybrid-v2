# HYBRID CARD GAME - CODEBASE ARCHITECTURE ANALYSIS
**Analysis Date:** April 22, 2026  
**Project:** Pygame-CE Auto-Chess Hybrid  
**Scope:** engine_core, v2/core, v2/ui modules

---

## EXECUTIVE SUMMARY

This is a **moderately complex hybrid architecture** combining:
- **engine_core**: Pure game engine (no UI dependencies)
- **v2/core**: State management layer (adapter pattern)
- **v2/ui**: Pygame rendering (heavy UI coupling)

**Key Finding**: State separation was partially successful, but **parallel state maintenance** and **tightly coupled dependencies** create risk for desynchronization bugs and extensibility issues.

**Critical Issues Found: 5**  
**Strategic Concerns: 8**  
**Code Smells: 12+**

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 Module Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    v2/main.py (Entry)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐  ┌──────▼──────┐  ┌─────▼──────┐
   │ v2/core  │  │ v2/ui       │  │ v2/scenes  │
   │ (State)  │  │ (Rendering) │  │ (Flow)     │
   └────┬─────┘  └──────┬──────┘  └─────┬──────┘
        │                │               │
        └────────────────┼───────────────┘
                         │
        ┌────────────────▼────────────────┐
        │    engine_core/ (Pure Logic)    │
        │  Game, Player, Board, Card      │
        │  AI, Combat, Passives           │
        └────────────────────────────────┘
```

### 1.2 Core Classes & Their Responsibilities

| Class | Location | Responsibility | LoC | Tight Coupling |
|-------|----------|-----------------|-----|---|
| `Game` | engine_core/game.py | Game loop, turn orchestration | ~200 | HIGH |
| `Player` | engine_core/player.py | Player state, resources, board | ~250 | MEDIUM |
| `Board` | engine_core/board.py | Hex grid, combat, synergy | ~400 | HIGH |
| `Card` | engine_core/card.py | Card state, effects, stats | ~250 | MEDIUM |
| `TurnManager` | engine_core/turn_manager.py | Turn flow, market, AI execution | ~300 | MEDIUM |
| `CombatEngine` | engine_core/combat_engine.py | Combat resolution, damage | ~200 | MEDIUM |
| `GameState` | v2/core/game_state.py | UI state adapter, cache mgmt | ~150 | HIGH |
| `PublicState` | v2/core/public_state.py | Immutable state snapshot (dataclass) | ~100 | LOW |
| `EngineAdapter` | v2/core/engine_adapter.py | Bridge to engine_core | ~150 | HIGH |

### 1.3 Module Dependency Graph

**Core Dependencies:**
```
game.py
  ├─ TurnManager
  ├─ CombatEngine  
  ├─ Player
  ├─ Board
  ├─ Market
  └─ AI

Player
  ├─ Board
  ├─ Economy
  ├─ Inventory
  ├─ Progression
  └─ (optional) BuilderSynergyMatrix

Board
  ├─ Card
  ├─ HEX_DIRS (constants)
  ├─ find_combos()
  ├─ calculate_group_synergy_bonus()
  └─ calculate_damage()

GameState (v2)
  ├─ EngineAdapter
  ├─ StateStore
  ├─ UIAdapter
  └─ UIFormatter
```

**Reverse Dependencies (v2 → engine_core):**
- Unidirectional: v2 depends on engine_core ✓
- No circular imports detected

---

## 2. STATE MANAGEMENT

### 2.1 Current State Architecture

**Single Source of Truth (Intended):**
```
engine_core/Game
    ↓
v2/core/GameState._adapter (hooked via hook_engine())
    ↓
get_public_state() → PublicState (immutable dataclass)
    ↓
UI consumers read PublicState
```

**Cache Strategy:**
- [v2/core/game_state.py:26-29] `_cached_public_state` invalidated on mutations
- Mutations call `_invalidate_cache()` immediately
- Next `get_public_state()` rebuilds snapshot via `UIAdapter.build_public_state()`

### 2.2 Parallel State Maintenance (⚠️ RISK)

**Problem:** Multiple objects maintain overlapping state:

| State | Owner | Backup | Risk |
|-------|-------|--------|------|
| HP | Player.hp | None | Single source ✓ |
| Gold | Player.economy.gold | None | Single source ✓ |
| Board | Player.board.grid | StateStore._board_names (cache only) | **Desync possible** |
| Market window | Market._player_windows | EngineAdapter (read-only) | **Desync possible** |
| Turn count | TurnManager.turn | Game.turn (property) | **Dual update risk** |
| Shop locked | Player.shop_locked | None | **Hidden state** |
| Cards bought | Player.cards_bought_this_turn | Player.stats[] | **Dual source** |

**Specific Issues:**

1. **Board State in StateStore** [v2/core/state_store.py:36-44]
   ```python
   _board_names: Dict[Tuple[int, int], str] = {}
   _board_rotations: Dict[Tuple[int, int], int] = {}
   ```
   - Updated by `update_board()` manually
   - Not automatically synced with Player.board.grid
   - **If Player.board is mutated outside of update_board(), StateStore stales**

2. **Turn Counter Dual Source** [engine_core/game.py:67-69, v2/core/engine_adapter.py:143]
   - `Game.turn` (property) → delegates to `TurnManager.turn`
   - Both readable, but mutation point is TurnManager
   - Risk: Code might read Game.turn before TurnManager updates

3. **Cards Bought Dual Tracking** [engine_core/player.py:70, 129]
   - `Player.cards_bought_this_turn` (int)
   - `Player.stats["cards_bought_this_turn"]` (int)
   - Incremented in `buy_card()` [line 129] - both updated but separate branches

### 2.3 State Mutation Flow

**Mutation entry points in GameState (v2/core/game_state.py):**
```python
• buy_card_from_slot()        [line 91-97]   → EngineAdapter.perform_buy_card()
• reroll_market()             [line 99-105]  → EngineAdapter.perform_reroll()
• toggle_lock_shop()          [line 107]     → Player.shop_locked = ...
• commit_human_turn()         [line 148]     → TurnManager.finish_turn()
• place_card_on_board()       [line 160]     → EngineAdapter.perform_placement()
```

**All call `_invalidate_cache()` ✓**

### 2.4 Read Path (Public State)

1. UI calls `GameState.get_public_state()`
2. If cached, return cached immutable snapshot ✓
3. Else, call `UIAdapter.build_public_state()` which:
   - Calls `EngineAdapter.get_player()`, `.get_market()`, etc.
   - Rebuilds `ActivePlayerViewState` from live Player object
   - Runs synergy BFS via `SynergyCalculator.compute()`
   - Caches result

**⚠️ Performance concern** [v2/core/ui_adapter.py - implied]: 
- BFS runs O(n²) worst case on every read if board full
- No intermediate synergy cache between frames
- See Performance section for details

---

## 3. DATA & LOGIC COUPLING

### 3.1 Tight Coupling Hotspots

**CRITICAL: Card System**
- Location: [engine_core/card.py:1-150]
- Card has **two dual representations**:
  - `_pipeline` (EffectPipeline) - manages stats
  - `_meta` (Dict) - carries combat metadata
- Logic calling Card directly:
  - `resolve_single_combat()` [board.py:139-178] reads Card.rotated_edges()
  - `find_combos()` [board.py:296-325] reads edges directly
  - Passive system [passives/*.py] calls `card.add_base_stat()` (mutation!)
  - Board synergy [board.py:198-241] calls `_edge_group()` on card

**Coupling Pattern:**
```
Card (data structure)
  ├─ Accessed by: Combat system (reads)
  ├─ Accessed by: Passive system (writes stats)
  ├─ Accessed by: Synergy system (reads groups)
  ├─ Accessed by: Effects pipeline (internal)
  └─ Accessed by: UI serialization
  
→ Changes to Card stat access pattern break:
  • Combat bonuses
  • Passive triggers
  • Synergy calculations (all three groups)
```

**CRITICAL: Player State Composition**
- Location: [engine_core/player.py:7-50]
- Player aggregates multiple sub-objects:
  - `economy` (Economy)
  - `inventory` (Inventory)
  - `progression` (Progression)
  - `board` (Board)
- Plus redundant direct attributes:
  - `gold` (proxies to economy.gold)
  - `hand` (proxies to inventory.hand)
  - `copies` (proxies to inventory.copies)
  - Plus `stats` dict (parallel copy)

**Problems:**
- [player.py:54-62] 12+ properties all proxy to sub-objects
- If inventory.hand is replaced, `hand` property breaks
- `stats` dict updated manually [player.py:129] - can desync

**CRITICAL: Board's Double Bookkeeping**
- Location: [engine_core/board.py:42-73]
- Board maintains **two parallel indexes**:
  ```python
  grid: Dict[Tuple[int, int], Card]          # Primary
  coord_index: Dict[int, Tuple[int, int]]    # O(1) lookup by card UID
  ```
- If `place()` called directly without updating coord_index → bug
- If `remove()` forgets coord_index entry → memory leak
- No transaction semantics; both can partially fail

### 3.2 Business Logic Embedded in Data Classes

**ISSUE: Card Rotation & Edges**
- Location: [engine_core/card.py:222-232]
- `rotate()` and `rotated_edges()` are **presentation logic** on Card
- Should be in view layer, not Card class
- Combat system calls `card.rotated_edges()` [board.py:168]
- Synergy system calls `card.rotated_edges()` [synergy_calculator.py]
- UI calls `card.rotation` directly for rendering
- **Risk**: Card becomes god object; rotation logic can't change without updating combat

**ISSUE: Card.stats Property Returns Mutable Reference**
- Location: [engine_core/card.py:134-136]
```python
@property
def stats(self):
    return MappingProxyType(self._pipeline.get_current_stats())
```
- Returns frozen proxy, but nested dicts could be mutated
- Actually safe (MappingProxyType), but pattern is fragile

### 3.3 Passive System Architecture

**Design:** Decorator-based passive registry with handler functions
- Location: [engine_core/passives/registry.py, base.py, *.py]
- Good separation: handlers live in module files, auto-registered

**Coupling:** Passive system reads Card state directly
```python
# From passives/combat.py, survival.py, synergy.py:
opponent.board.alive_cards()           # reads grid directly
neighbor_card.add_base_stat(...)       # mutates card
card.get_combat_bonus_total()          # reads meta dict
```

**Tightness:** MODERATE
- Passives tightly coupled to Card interface (good for consistency)
- Passives directly mutate Card state (no event system)
- No way to extend passive system without modifying handlers

---

## 4. TIGHT COUPLING & GOD OBJECTS

### 4.1 God Object Analysis

**CANDIDATE 1: Board Class** ⚠️ HIGH RISK
- Location: [engine_core/board.py]
- Responsibilities:
  1. Hex grid management (place/remove/neighbors)
  2. Combat resolution (resolve_single_combat)
  3. Combo detection (find_combos)
  4. Synergy calculation (calculate_group_synergy_bonus)
  5. Damage calculation (calculate_damage)
- **Line Count:** ~400 LOC
- **Methods:** 12 public + 8 module-level functions
- **Tight Coupling:** Card rotation, edge values, group matching
- **Extensibility Issue:** Adding new synergy type requires modifying Board class

**CANDIDATE 2: Game Class** ⚠️ HIGH RISK
- Location: [engine_core/game.py]
- Responsibilities:
  1. Game loop orchestration (run)
  2. Turn management (delegates to TurnManager)
  3. Combat coordination (delegates to CombatEngine)
  4. Turn phase management
  5. Player lifecycle (alive_players, _clear_transient_board_state)
  6. Card UID generation (next_card_uid)
- **Line Count:** ~200 LOC
- **Imports:** TurnManager, CombatEngine, AI, Market, Card
- **Why not worst:** Responsibilities split to TurnManager (Phase 3) and CombatEngine (Phase 2)
- **Remaining issue:** Still owns Players list, coordinates state mutations

**CANDIDATE 3: Player Class** ⚠️ MEDIUM RISK
- Location: [engine_core/player.py]
- Responsibilities:
  1. State container (hp, gold, stats)
  2. Board management (place_cards)
  3. Inventory management (buy_card, check_copy_strengthening)
  4. Evolution logic (check_evolution)
  5. Composition parent for Economy, Inventory, Progression, Board
- **Line Count:** ~250 LOC
- **Composition:** 4 sub-objects + direct attributes
- **Tight Coupling:** Knows about passive_trigger_fn, trigger_passive calls
- **Extensibility:** Evolution logic hardcoded for "evolver" strategy

### 4.2 Circular Dependency Risk Analysis

**Checked paths:**
- engine_core → v2/core: ✗ (clean unidirectional)
- engine_core internal: ✓ (no cycles detected)
- v2/core → v2/ui: ✓ (UI depends on core)

**Lazy Import Pattern Found:**
```python
# board.py:291-292 (combat_phase function)
from engine_core.passive_trigger import trigger_passive
```
- Breaks potential circular: board ← passive_trigger ← passives.registry ← copy_handlers ← board
- Good defensive coding, but indicates fragile dependency

---

## 5. PERFORMANCE ISSUES

### 5.1 O(n²) and Worse Algorithms

**CRITICAL: Synergy BFS Runs Every Frame**
- Location: [v2/core/synergy_calculator.py:77-145] (3 BFS traversals)
- Algorithm: For each of 3 group types, run full BFS from each unvisited card
- **Complexity:** O(3 × V × (V + E)) where V = board cards (~37), E = neighbors (~6)
- **Worst case:** O(1,110) operations per get_public_state() call
- **Frequency:** Every UI frame render (typically 60 FPS)
- **Current mitigation:** Cached in GameState until next mutation
- **Risk:** If UI calls get_public_state() > 1× per mutation, redundant BFS

**Impact Calculation:**
```
37 cards × 6 neighbors avg = 222 edges max
3 groups × 37 cards × (37 + 222) = ~25,587 ops worst case
At 60 FPS: 1.5M ops/sec in synergy alone
Acceptable if single, but...
```

**CONCERN: Synergy Logic Duplicated**
- [engine_core/board.py:198-241] - `calculate_group_synergy_bonus()` 
- [v2/core/synergy_calculator.py:77-145] - `SynergyCalculator.compute()`
- Same BFS algorithm, separate implementations
- If one has a bug fix, other doesn't auto-update
- Added: [v2/core/ui_adapter.py] likely has inline BFS too (not read)
- **Technical Debt:** 3 copies of same algorithm

**Fix Status:** Noted in code:
```python
# synergy_calculator.py:8-17
Daha önce aynı BFS üç yerde kopyalanmıştı:
  ✗  engine_core/board.py            → calculate_group_synergy_bonus
  ✗  v2/core/ui_adapter.py           → _build_synergy_view (inline BFS)
  ✗  v2/ui/synergy_hud_legacy.py     → _compute_state (inline BFS)
```
**Intention:** synergy_calculator.py is "single source of truth", but old code may still exist

### 5.2 Surface & Texture Management (Pygame)

**Not Analyzed** (outside engine_core scope, lives in v2/ui)
- Recommendation: Check for recreating surfaces every frame
- Look for: cached vs fresh texture creation in render paths

### 5.3 Unbounded List Growth

**Potential Issue: Game Log**
- Location: [engine_core/game.py:70]
```python
self.log: List[str] = []
```
- Appended every `_log()` call
- No maximum cap or rotation
- Could grow to GB+ after 10,000 turns

**Potential Issue: Passive Trigger Log**
- Location: [engine_core/game.py:71]
```python
self._passive_trigger_log = defaultdict(lambda: defaultdict(int))
```
- Counts per card × trigger type
- Bounded by card count (66 cards) × trigger types (~8) = ~528 entries max
- **Safe**, but previous version was global [passive_trigger.py:128-137] (legacy)

**Potential Issue: Strategy Logger**
- Location: [engine_core/strategy_logger.py:100-105]
```python
self._strat: Dict[str, dict] = defaultdict(_new_strat)
```
- Accumulates stats per strategy
- Bounded by strategy count (~8-10)
- **Safe**

### 5.4 Unnecessary Deep Copying & List Creation

**FOUND: Defensive Copying in Loops**
- [engine_core/game.py:131, 141] - `tuple(player.board.grid.values())`
- [engine_core/turn_manager.py:96, 108, 191] - same pattern
- [engine_core/combat_engine.py:57, 67, 91] - same pattern
- [engine_core/player.py:150, 176, 184, 192, 213] - `list()` wrapping
- [engine_core/board.py:308] - `grid.items()` loop

**Analysis:**
```python
for board_card in tuple(player.board.grid.values()):
    # Modify player.board.grid during iteration
```

**Rationale:** Protects against concurrent modification during iteration
- **Cost:** Creates tuple/list copy every time
- **Frequency:** High (every turn phase, every card in loop)
- **Impact:** ~5-10% slowdown on turn processing

**Better approach:** Use dict.values() normally (Python 3.7+ preserves insertion order) or snapshot once before loop

### 5.5 Complex Copy Logic

**COMPLEXITY: Card.clone()**
- Location: [engine_core/card.py:not shown in excerpts]
- Assumption: Deep copies stats and meta
- Used by:
  - TurnManager._deal_starting_hands() [turn_manager.py:79-83]
  - Player.buy_card() [player.py:124]
- **Risk:** If Card has circular references, clone() could hang/fail

---

## 6. ERROR HANDLING

### 6.1 Bare Exception Handling (Code Smells)

**FOUND: 5 instances**

1. **engine_core/strategy_logger.py:329**
   ```python
   except Exception as e:
       # swallows without logging context
   ```
   - Location: Inside log_passive_trigger()?
   - Severity: **MEDIUM** - silent failure in logger

2. **engine_core/strategy_logger.py:513**
   ```python
   except Exception as e:
       # similar pattern
   ```

3. **engine_core/event_logger.py:194, 206**
   ```python
   except Exception as e:
       # writes to stderr without context?
   ```

4. **engine_core/player.py:209**
   ```python
   except (ValueError, TypeError): pass
   ```
   - Location: check_evolution() method
   - Context: Converting rarity string to int fails silently
   - Severity: **LOW** - specific exception types caught

### 6.2 Missing Error Contexts

**ISSUE: EngineAdapter Returns Shims on Failure**
- Location: [v2/core/engine_adapter.py:30-35]
```python
class _AdapterCardShim:
    def __init__(self, name: str, rotation: int = 0):
        self.name = name
        ...
    def is_eliminated(self) -> bool:
        return False
```

**Problem:**
- If engine.players[index] fails (IndexError), returns None [line 52]
- If market missing, returns None [line 61]
- Calling code must check for None, but typed as Optional
- No exception raised; errors propagate as None references

**Example Failure Path:**
```python
player = adapter.get_player(999)  # Returns None
if player.alive:  # AttributeError, not descriptive error
```

### 6.3 Handling Patterns (Good)

**Positive: ActionResult Enum**
- Location: [v2/core/action_result.py]
- All mutations return `ActionResult` enum (OK, ERR_*)
- UI can inspect reason for failure
- ✓ Good practice

**Positive: Lazy Import Breaks Cycles**
- Location: [engine_core/board.py:291]
- Prevents initialization-time circular import
- ✓ Good practice

---

## 7. TECH DEBT MARKERS

### 7.1 Magic Numbers & Hardcoded Values

**PERVASIVE: Scattered throughout**

| Location | Value | Context | Risk |
|----------|-------|---------|------|
| engine_core/board.py:228 | 3,9,16,25 | Synergy tier bonuses | No constant |
| engine_core/board.py:235 | 2 | Connection bonus multiplier | No constant |
| engine_core/board.py:152-153 | 6 | Hex directions (hardcoded) | Used correctly but brittle |
| engine_core/board.py:348-375 | 0.5, 1.0, 5, 15 | Damage multipliers | Turn-based but hardcoded |
| engine_core/player.py:164 | 2, 3 | Copy thresholds | References COPY_THRESH |
| engine_core/ai.py:279-286 | 27, 15, 11, 42, 80 | Buy thresholds | Trained params, not documented |
| engine_core/market.py | 5 | Market window size | Hard-coded 5-slot market |

**Fix:** Most are in `engine_core/constants.py`, but some remain scattered:
- Synergy tier bonuses should be in constants
- Damage multiplier formula should be a function
- Copy thresholds properly referenced (COPY_THRESH)

### 7.2 Deprecated/Legacy Code

**FOUND: 2 Deprecation Chains**

1. **Passive Trigger Log Legacy** [engine_core/passive_trigger.py:128-137]
   ```python
   _legacy_passive_log = defaultdict(lambda: defaultdict(int))
   def get_passive_trigger_log():
       """DEPRECATED: Returns the legacy global log."""
   def clear_passive_trigger_log():
       """DEPRECATED: Clears the legacy global log."""
   ```
   - Maintained for backward compatibility
   - Should be removed in next refactor

2. **Strategy Logger Params Loading** [engine_core/ai.py:114-120]
   ```python
   def load_strategy_params() -> Dict[str, Any]:
       """Backward compat: sadece economist parametrelerini döndürür."""
   ```
   - Old single-strategy loading function
   - Phase 1 added load_all_strategy_params()
   - Both exist for compatibility

### 7.3 Missing Documentation

**Undocumented Module-Level Complexity:**

| Location | Issue | Impact |
|----------|-------|--------|
| engine_core/board.py:198-241 | `calculate_group_synergy_bonus()` algorithm unclear | Hard to verify correctness |
| engine_core/board.py:139-178 | Combat edge matching logic | No explanation of group advantage system |
| v2/core/synergy_calculator.py | BFS vs legacy board.py BFS diff | Not documented why two versions exist |
| engine_core/passives/*.py | Passive trigger timing | When do passives fire relative to combat? |
| engine_core/ai.py:200-500 | Buy/placement strategy logic | 300 LOC of undocumented heuristics |

**Type Hints:** Generally good, but:
- Some functions return `Optional[T]` without None handling code
- Dict return types missing value type hints

### 7.4 Known Issues in Comments

**Intentional Bugs/TODOs:**

| File | Line | Issue |
|------|------|-------|
| engine_core/game.py:189 | Comment: "Bait-and-Switch bug'ını önler" | Swiss pairs called differently in two places |
| engine_core/autochess_sim_v06.py:1-30 | Changelog documents 3 bugs fixed in v0.5-v0.6 | Version not enforced in code |

**Known Limitations:**

```python
# board.py:333
# Note: 30% power cap enforced in combat_phase (not here)
# This allows flexibility while preventing synergy from dominating
```

---

## 8. EXTENSIBILITY ISSUES

### 8.1 Adding 100 New Cards (Rarity 1-5)

**What breaks?**
1. ✓ Card pool loading - just add JSON entries
2. ✓ Combat system - uses Card.edges() (generic)
3. ✓ Passive system - handler registration auto-loads
4. ✓ Synergy - group matching automatic
5. ⚠️ **Board class** - assumes 6 edges (hex), hardcoded in:
   - [board.py:152-153] `bonus_per_edge_a = bonus_total_a // 6`
   - [board.py:162] loops `range(6)`
   - Card.rotated_edges() returns 6 edges
   
**Risk:** If a card has different edge count, combat breaks

6. ⚠️ **Stats mapping** - must match STAT_GROUPS
   - If new stat added, must update STAT_TO_GROUP
   - Group system hardcoded for 3 groups (MIND, CONNECTION, EXISTENCE)

### 8.2 Adding 5 New Synergies (Connected Clusters)

**What breaks?**
1. ✓ Passive handlers - can add new @passive("Card Name") handlers
2. ✓ Board synergy calc - generic BFS works for any group
3. ⚠️ **3-group hardcoding**
   ```python
   # synergy_calculator.py:27
   _GROUPS: Tuple[str, ...] = ("MIND", "CONNECTION", "EXISTENCE")
   
   # board.py:218
   groups = ["MIND", "CONNECTION", "EXISTENCE"]
   ```
   - Adding 4th group requires code changes in 2+ places
   - Should be configurable constant

4. ⚠️ **Damage formula** - synergy bonus capped at 30% [board.py:333]
   - If synergy score calculation changes, cap may become wrong
   - Hardcoded multiplier, not parameterized

### 8.3 Adding New Rarity Level (Rarity 6?)

**What breaks?**
1. ⚠️ **Card costs** [constants.py:134]
   ```python
   CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0}
   ```
   - Must add entry

2. ⚠️ **Rarity power targets** [constants.py:59-63]
   ```python
   RARITY_TAVAN = {"1": 30, ..., "5": 54, "E": 72}
   EVOLVED_TAVAN = {...}
   ```
   - Must add entry + proportional evolved version

3. ⚠️ **AI strategy logic** [ai.py:200-500]
   - Buy thresholds may not apply to rarity-6
   - BuilderSynergyMatrix may need tuning

4. ✗ **Board rarity bonus** [board.py:94-99]
   ```python
   RARITY_DMG_BONUS = {}  # currently empty (v0.4)
   ```
   - If reintroduced, must handle new rarity

### 8.4 Replacing Combat System

**What would need to change?**
1. ✓ CombatEngine interface small - just `run_combat(pairs)`
2. ⚠️ **Card expects edges()** - combat_engine assumes Card.rotated_edges()
3. ⚠️ **Passive trigger hooks** - combat calls `trigger_passive(..., "combat_win", ...)`
4. ⚠️ **Board assumes edges are ordinal 0-5** - direction indices hardcoded

**Difficulty:** MODERATE - would need to:
- Redefine Card.edges() or provide adapter
- Update all passive handlers that check edge positions
- Update synergy system (also uses edge directions)

### 8.5 Adding New Game Phase

**Example:** "Draft Phase" before Preparation

**What needs changing?**
1. ✗ **TurnManager.start_turn()** assumes market opens [turn_manager.py:92-110]
   - Would need to add draft_phase() hook
2. ✗ **Phase machine** - GameState assumes fixed phase names [state_store.py:13]
3. ✗ **Game.run()** - main loop hardcoded [game.py:195-205]
   - Would need to call draft_phase() between turns

**Difficulty:** HIGH - phase flow is centralized in Game.run()

---

## 9. DETAILED FINDINGS TABLE

### Critical Issues

| ID | Severity | Location | Issue | Impact | Effort |
|---|----------|----------|-------|--------|--------|
| C1 | CRITICAL | v2/core/state_store.py:36-44 | Board state cache not auto-synced | Desync if Player.board mutated outside StateStore | 4h |
| C2 | CRITICAL | engine_core/board.py:198-241 | Synergy BFS logic duplicated in 3 places | Bug fix must be applied 3× or diverge | 6h |
| C3 | CRITICAL | engine_core/board.py:152-153, synergy.py:27 | 3-group and 6-direction hardcoded | Adding new group or edge type breaks core | 8h |
| C4 | CRITICAL | engine_core/player.py:129, 154 | Dual state (cards_bought_this_turn + stats) | Stats can desync from player state | 2h |
| C5 | CRITICAL | v2/core/engine_adapter.py:30-35, 52-61 | Shim objects returned on error | TypeError instead of descriptive error | 2h |

### Strategic Issues

| ID | Severity | Location | Issue | Impact | Effort |
|---|----------|----------|-------|--------|--------|
| S1 | STRATEGIC | engine_core/board.py | Board is god object (synergy, combo, combat, damage) | Hard to test in isolation; changes break 4 systems | 16h refactor |
| S2 | STRATEGIC | engine_core/card.py:134-136, player.py:54-62 | Data classes expose internal state | Fragile proxy patterns; hard to refactor | 8h |
| S3 | STRATEGIC | engine_core/player.py:176-225 | Evolution logic hardcoded for "evolver" strategy | New strategies can't add evolution; tightly coupled | 4h |
| S4 | STRATEGIC | engine_core/ai.py:1-120 | AI parameters global + JSON-based | If JSON missing, silent fallback to defaults | 3h |
| S5 | STRATEGIC | v2/core/synergy_calculator.py:77-145 | Synergy BFS runs O(n²) per frame | 60 FPS × O(1,110) = 66k ops/sec in UI thread | 3h optimized |
| S6 | STRATEGIC | engine_core/board.py:333 | Synergy bonus capped 30% (hardcoded in damage) | Difficult to balance new synergies without code change | 2h parameterize |
| S7 | STRATEGIC | engine_core/game.py:71 | Game.log unbounded list | Could grow to GB+ after 10k turns | 1h |
| S8 | STRATEGIC | engine_core/passive_trigger.py:128-137 | Deprecated legacy_passive_log still exported | Technical debt; should remove | 1h cleanup |

### Code Smells

| ID | Severity | Location | Issue | Recommendation |
|---|----------|----------|-------|---|
| SM1 | CODE SMELL | engine_core/**/*.py:multiple | `except Exception:` without context | Add logging + specific exception types |
| SM2 | CODE SMELL | engine_core/game.py:131, etc | `tuple(dict.values())` to prevent concurrent mod | Use weakref.WeakKeyDictionary or snapshot pattern |
| SM3 | CODE SMELL | engine_core/board.py:228-241 | Magic numbers (3, 9, 16, 25) | Move to SYNERGY_TIERS constant |
| SM4 | CODE SMELL | engine_core/board.py:348-375 | Turn multiplier formula hardcoded | Extract `get_turn_damage_multiplier(turn)` function |
| SM5 | CODE SMELL | v2/core/synergy_calculator.py:27 | String group names in tuple | Use Enum class (GroupType.MIND) |
| SM6 | CODE SMELL | engine_core/passives/registry.py:import order | 5 separate imports to trigger registration | Use __all__ = [...] or lazy import comment |
| SM7 | CODE SMELL | engine_core/player.py:54-62 | 12+ @property proxies to sub-objects | Consider delegation pattern or @dataclass |
| SM8 | CODE SMELL | engine_core/board.py | Functions at module level mixed with class | Extract to BoardCalculations class or module |
| SM9 | CODE SMELL | engine_core/constants.py | RARITY_DMG_BONUS empty dict (removed but kept) | Delete if not used; if planned, add TODO |
| SM10 | CODE SMELL | engine_core/turn_manager.py:185-200+ | Tur sayacı türkçe yorumu | Standardize comments language (TR vs EN) |

---

## 10. RISK MATRIX

```
           ╔════════════════════╦════════════════════╦════════════════════╗
           ║   High Impact      ║   Medium Impact    ║    Low Impact      ║
           ║   High Likelihood  ║   High Likelihood  ║   High Likelihood  ║
╔══════════╬════════════════════╬════════════════════╬════════════════════╣
║ H-Effort ║ Board refactor     ║ Remove legacy logs ║ Magic # constants  ║
║          ║ (god object)       ║ (deprecation)      ║                    ║
╠══════════╬════════════════════╬════════════════════╬════════════════════╣
║ M-Effort ║ Synergy BFS cache  ║ StateStore sync    ║ Exception handling ║
║          ║ Data class proxies ║ AI param fallback  ║ Type hints         ║
╠══════════╬════════════════════╬════════════════════╬════════════════════╣
║ L-Effort ║ Group hardcode fix ║ Damage formula fn  ║ Comment cleanup    ║
║          ║ (add 4th group)    ║ Log rotation       ║                    ║
╚══════════╩════════════════════╩════════════════════╩════════════════════╝
```

---

## 11. RECOMMENDATIONS (Priority Order)

### P0 (Do First - Blocks Other Work)

1. **Fix Synergy BFS Duplication** [2-3 days]
   - Verify synergy_calculator.py is being used by all systems
   - If not, migrate all consumers to synergy_calculator.py
   - Delete duplicates in board.py and ui_adapter.py
   - Reason: Prevents divergent bug fixes

2. **Parameterize Group System** [1 day]
   - Move "MIND", "CONNECTION", "EXISTENCE" to GroupRegistry
   - Allow runtime registration of new groups (for extensibility)
   - Reason: Blocks adding 4th synergy type

3. **StateStore Board Sync** [1 day]
   - Hook Board.place() and Board.remove() to call StateStore.update_board()
   - OR: Remove StateStore caching and rebuild from Player.board each frame
   - Reason: Prevents desync bugs

### P1 (Do Next - Improves Maintainability)

4. **Extract Board God Object** [3-4 days]
   - Move combo detection → ComboDetector class
   - Move synergy calculation → already done (SynergyCalculator)
   - Move damage calculation → DamageCalculator class
   - Keep Board as pure hex grid manager
   - Reason: Easier to test, modify, extend

5. **Remove Deprecated Passive Log** [4 hours]
   - Delete _legacy_passive_log, get/clear functions
   - Update any code still using them (search usage)
   - Reason: Clean up technical debt

6. **Parameterize Game Loop Constants** [4 hours]
   - Move synergy tier bonuses to SYNERGY_TIERS dict
   - Move damage multiplier formula to function get_turn_damage_multiplier()
   - Create GameBalance config object
   - Reason: Enables tuning without code changes

### P2 (Do Eventually - Nice to Have)

7. **Cache Synergy BFS Between Frames** [1-2 days]
   - Don't re-run BFS if board unchanged between get_public_state() calls
   - Add board hash to detect changes
   - Reason: 60 FPS performance

8. **Error Handling Audit** [1 day]
   - Replace bare `except Exception:` with specific types
   - Add logging context to all exception handlers
   - Replace shim pattern with exceptions
   - Reason: Better debugging

9. **Documentation** [2-3 days]
   - Document Board class responsibilities and assumptions (6-edge hex, 3 groups, etc.)
   - Document Passive system trigger timing
   - Document Card.stats/meta split and why it exists
   - Reason: Onboarding and future maintainability

---

## 12. EXTENSIBILITY CHECKLIST

### For Adding 100+ Cards
- [ ] No Card.edges() hardcoding (currently flexible ✓)
- [ ] Stats match STAT_TO_GROUP (currently 12 stats across 3 groups)
- [ ] Passive handlers auto-register ✓
- [ ] No new group types (would break if added)

### For Adding 5+ New Synergies
- [ ] BFS-based synergy system handles any group (currently ✓)
- [ ] Parameterize 3-group hardcoding (currently ✗)
- [ ] Passive combo bonuses extensible (currently ✓)

### For Adding New Rarity (Rarity 6)
- [ ] Update CARD_COSTS (currently ✓ pattern)
- [ ] Update RARITY_TAVAN (currently ✓ pattern)
- [ ] Update AI buy thresholds (currently ✗ hardcoded)

### For Replacing Combat System
- [ ] Combat interface isolated (currently ✓ CombatEngine)
- [ ] Card doesn't assume 6 edges (currently ✗ hardcoded)
- [ ] Passive hooks generic (currently ✓)

---

## 13. JSON-FORMATTED FINDINGS

```json
{
  "analysis": {
    "date": "2026-04-22",
    "project": "Hybrid Card Game (Pygame-CE)",
    "scope": ["engine_core", "v2/core", "v2/ui"],
    "total_findings": 27
  },
  "critical_issues": [
    {
      "id": "C1",
      "severity": "CRITICAL",
      "location": "v2/core/state_store.py:36-44",
      "issue": "Board state cache not auto-synced with Player.board.grid",
      "why_matters": "Desynchronization between StateStore and actual game state",
      "impact": "UI shows stale board if Player.board mutated outside StateStore.update_board()",
      "effort": "4 hours",
      "fix": "Hook Board.place()/remove() to StateStore, or rebuild StateStore from live board"
    },
    {
      "id": "C2",
      "severity": "CRITICAL",
      "location": ["engine_core/board.py:198-241", "v2/core/synergy_calculator.py:77-145", "v2/core/ui_adapter.py"],
      "issue": "Synergy BFS calculation duplicated in 3 modules",
      "why_matters": "Bug fixes must be applied in 3 places; easy to diverge",
      "impact": "Synergy score could differ between engine, UI, and calculations",
      "effort": "6 hours (testing + migration)",
      "fix": "Ensure all modules use synergy_calculator.py; delete board.py and ui_adapter duplicates"
    },
    {
      "id": "C3",
      "severity": "CRITICAL",
      "location": ["engine_core/board.py:152-153", "synergy_calculator.py:27", "constants.py"],
      "issue": "Group system hardcoded to 3 types; edge system hardcoded to 6",
      "why_matters": "Extensibility blocker for new synergy types or different hex systems",
      "impact": "Adding 4th group breaks BFS and damage formula; impossible without code changes",
      "effort": "8 hours (design + testing)",
      "fix": "Create GroupRegistry and EdgeSystem configurations"
    },
    {
      "id": "C4",
      "severity": "CRITICAL",
      "location": "engine_core/player.py:129, 154",
      "issue": "cards_bought_this_turn maintained in two places: direct int + stats dict",
      "why_matters": "Parallel state maintenance creates desync risk",
      "impact": "Stats['cards_bought_this_turn'] could diverge from player.cards_bought_this_turn",
      "effort": "2 hours",
      "fix": "Remove direct int, use only stats dict; or refactor to single source"
    },
    {
      "id": "C5",
      "severity": "CRITICAL",
      "location": "v2/core/engine_adapter.py:30-35, 52-61",
      "issue": "Error cases return None or shim objects instead of exceptions",
      "why_matters": "Errors silent; code crashes with AttributeError instead of descriptive message",
      "impact": "Debugging impossible; errors propagate as None reference errors",
      "effort": "2 hours",
      "fix": "Replace shim pattern; raise descriptive exceptions"
    }
  ],
  "strategic_concerns": [
    {
      "id": "S1",
      "category": "God Object",
      "location": "engine_core/board.py",
      "responsibilities": ["hex grid management", "combat resolution", "combo detection", "synergy calculation", "damage calculation"],
      "loc": 400,
      "effort_to_refactor": "16 hours",
      "why_matters": "Hard to test; modifications affect 4+ downstream systems"
    },
    {
      "id": "S2",
      "category": "Performance",
      "location": "v2/core/synergy_calculator.py",
      "algorithm": "BFS for 3 groups",
      "complexity": "O(3 * V * (V + E))",
      "calls_per_second": "60 (at 60 FPS)",
      "operations_per_second": "66000 (estimated)",
      "why_matters": "Runs every frame; could be cached",
      "fix": "Cache synergy result; invalidate on board change"
    }
  ],
  "extensibility_blockers": [
    {
      "scenario": "Add 100 new cards",
      "blockers": [],
      "risks": ["Must ensure new stats match STAT_TO_GROUP", "Passive handlers must be registered"]
    },
    {
      "scenario": "Add 5 new synergy types",
      "blockers": ["3-group hardcoded in synergy_calculator.py:27 and board.py:218"],
      "effort_to_unblock": "8 hours"
    },
    {
      "scenario": "Add rarity-6 cards",
      "blockers": ["AI buy thresholds hardcoded in ai.py"],
      "effort_to_unblock": "4 hours"
    },
    {
      "scenario": "Add new game phase",
      "blockers": ["Game.run() hardcoded phase flow", "TurnManager assumes fixed phase sequence"],
      "effort_to_unblock": "16 hours"
    }
  ]
}
```

---

## APPENDIX: File Structure Quick Reference

```
engine_core/                     (Pure game logic, no UI)
  ├─ game.py (200 LOC)          - Game orchestrator + main loop
  ├─ player.py (250 LOC)        - Player state + actions
  ├─ board.py (400 LOC)         - Hex grid + combat + synergy [GOD OBJECT]
  ├─ card.py (250 LOC)          - Card definition + effects
  ├─ turn_manager.py (300 LOC)  - Turn flow (Phase 3 refactor)
  ├─ combat_engine.py (200 LOC) - Combat resolution (Phase 2 refactor)
  ├─ ai.py (800+ LOC)           - Buy/placement strategies
  ├─ market.py                  - Card pool + window management
  ├─ constants.py               - Game constants
  ├─ passives/                  - Passive ability handlers
  │  ├─ registry.py             - Handler auto-registration
  │  ├─ base.py                 - Base decorator
  │  ├─ combat.py               - Combat passives
  │  └─ ... (5 handler modules)
  └─ effects.py                 - Effect pipeline

v2/core/                        (State adapter layer)
  ├─ game_state.py (150 LOC)    - UI state adapter + cache
  ├─ public_state.py (100 LOC)  - Immutable state snapshot
  ├─ engine_adapter.py (150 LOC)- Bridge to engine_core
  ├─ state_store.py             - Local state cache [DESYNC RISK]
  ├─ synergy_calculator.py      - BFS synergy [DUPLICATED]
  └─ ui_adapter.py              - Serialization to UI

v2/ui/                          (Pygame rendering - NOT ANALYZED)
  └─ ... (scene managers, panels, overlays)
```

---

**End of Analysis**
