# Hybrid Engine: Core vs Mock — Technical Analysis Report

**Date:** 13 Nisan 2026  
**Scope:** `engine_core/` (production engine) vs `v2/mock/` (UI simulation) vs `v2/core/` (bridge layer)  
**Project:** AutoChess Hybrid V2

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Engine Core Status (`engine_core/`)](#2-engine-core-status-engine_core)
3. [Architecture Overview](#3-architecture-overview)
4. [Mock Engine (`v2/mock/engine_mock.py`)](#4-mock-engine-v2mockengine_mockpy)
5. [Bridge Layer (`v2/core/`)](#5-bridge-layer-v2core)
6. [Key Differences: Core vs Mock](#6-key-differences-core-vs-mock)
7. [Combat Logic — Full Analysis](#7-combat-logic--full-analysis)
8. [UI Integration Path](#8-ui-integration-path)
9. [GameState — The Bridge Layer](#9-gamestate--the-bridge-layer)
10. [Event Bus & Communication](#10-event-bus--communication)
11. [Scene Management](#11-scene-management)
12. [The Real Gap: Bridge, Not Engine](#12-the-real-gap-bridge-not-engine)
13. [Roadmap: Connecting UI to Real Engine](#13-roadmap-connecting-ui-to-real-engine)

---

## 1. Executive Summary

The AutoChess Hybrid V2 project has **two completely separate engine layers** and a **bridge** between them:

1. **`engine_core/`** — The **production game engine**, 100% complete and battle-tested through simulation/training pipelines. Includes full combat resolution, passive effect system, 8 AI strategies, Swiss pairing, economy system, evolution mechanics, and card pool management.

2. **`v2/mock/`** — A lightweight simulation (~130 lines) designed to let UI developers build panels without depending on the real engine. Uses string card names instead of objects, no combat, no board.

3. **`v2/core/`** — The **bridge layer** that `v2/` UI components talk to. Currently hooks into MockGame but is designed to swap to `engine_core/` with a single `hook_engine()` call.

**The critical finding:** The game engine (`engine_core/`) is **fully complete**. The UI (`v2/`) is **~80% complete**. The remaining work is **not building engine features** — it's **connecting the two** via the bridge layer (`v2/core/`). This report has been restructured to reflect that reality.

---

## 2. Engine Core Status (`engine_core/`)

> **Status: COMPLETE** — Full game loop, combat, passives, AI, economy, evolution, Swiss pairing.
> **Location:** `engine_core/` (project root level, NOT under `v2/`)

### 2.1 File Inventory

| File | Lines | Component | Status |
|------|-------|-----------|--------|
| `game.py` | ~340 | Game loop, prep phase, combat phase, Swiss pairing | ✅ Complete |
| `card.py` | ~320 | Card model, edges, rotation, evolution, strengthening | ✅ Complete |
| `board.py` | ~310 | Hex grid, combat resolver, combo detection, synergy calc | ✅ Complete |
| `player.py` | ~330 | Player state, income, interest, evolution, copy tracking | ✅ Complete |
| `market.py` | ~160 | Pool management, weighted rarity sampling, windows | ✅ Complete |
| `ai.py` | ~1252 | 8 AI strategies, parameterized training, synergy matrix | ✅ Complete |
| `passive_trigger.py` | ~90 | Passive dispatch system | ✅ Complete |
| `constants.py` | ~100 | All game constants, stat groups, group beats | ✅ Complete |
| `passives/` | 9 files | Synergy, combat, combo, copy, economy, survival handlers | ✅ Complete |
| `simulation.py` | — | Match simulation runner | ✅ Complete |
| `game_factory.py` | — | Game instance factory | ✅ Complete |
| `kpi_aggregator.py` | — | KPI collection for training | ✅ Complete |
| `strategy_logger.py` | — | Strategy-level logging | ✅ Complete |
| `event_logger.py` | — | Event logging | ✅ Complete |

### 2.2 Completed Engine Features

#### Combat System ✅
- **Edge-to-edge combat:** `resolve_single_combat()` compares 6 edges with rotation awareness
- **Group advantage:** `GROUP_BEATS` rock-paper-scissors (+1 bonus)
- **Board-wide combat:** `combat_phase()` resolves all overlapping coordinates
- **Combo detection:** `find_combos()` finds same-dominant-group neighbor pairs
- **Synergy bonus:** `calculate_group_synergy_bonus()` — scaled formula: `3 * (n-1)^1.25` per group (cap 18) + diversity bonus (cap 5)
- **Damage formula:** `calculate_damage()` with turn-based scaling (0.5x early → 1.0x late), early-game cap (15 dmg turns 1-10)
- **Catalyst multiplier:** Doubles combo points when catalyst is on board
- **Kill points:** `KILL_PTS = 8` per eliminated card

#### Passive Effect System ✅
- **6 passive types:** `synergy_field`, `combat`, `combo`, `copy`, `survival`, `economy`
- **Registry-based dispatch:** `PASSIVE_HANDLERS` maps card names to specific handlers
- **Trigger lifecycle:** `pre_combat`, `combat_win`, `combat_lose`, `card_killed`, `income`, `market_refresh`, `card_buy`, `copy_2`, `copy_3`
- **Logging:** `passive_buff_log` tracks every trigger with turn/card/delta
- **Default fallback:** Unknown passives get default behavior

#### Economy System ✅
- **Income:** `BASE_INCOME=3` + win streak bonus (+1 per 3 wins) + HP bailout (low HP → +1/+3)
- **Interest:** +1 per 10 gold banked (max 5), economist gets 1.5x multiplier
- **Card costs:** R1=1, R2=2, R3=3, R4=5, R5=7, E=0
- **Rarity-weighted market:** Cards appear with turn-based weight curves (R4/R5 scarce early)
- **Hand overflow:** 7th buy drops oldest card (FIFO) back to pool

#### Evolution System ✅
- **3-copy threshold:** `EVOLVE_COPIES_REQUIRED = 3`
- **Evolver strategy only:** Auto-evolves when 3 copies collected
- **Rarity-based scaling:** `EVOLVED_TAVAN` — R1→40, R2→48, R3→56, R4→64, R5→72 total power
- **Pool management:** 2 consumed copies returned to market pool
- **Strengthen bonus:** Evolved cards get rarity-scaled power boost (+12%/+16%/+20%)

#### Copy Strengthening ✅
- **2nd copy:** +2 to highest edge (threshold: turn 4, or turn 3 with Catalyst)
- **3rd copy:** +3 to highest edge (threshold: turn 7, or turn 6 with Catalyst)
- **Turn-aware:** Strengthening waits `COPY_THRESH` turns before applying

#### Swiss Matchmaking ✅
- **HP-based pairing:** Sort by HP, jitter same-HP band, pair nearest opponents
- **Shuffle within jitter:** Pairings vary each turn
- **Elimination handling:** Dead players removed from pairing pool

#### AI Strategies (8 types) ✅
| Strategy | Behavior |
|----------|----------|
| `random` | Buys affordable cards randomly |
| `warrior` | Maximizes total power + rarity weight |
| `builder` | Combo-first scoring with synergy matrix memory |
| `evolver` | Prioritizes near-evolution cards, rarity-weighted |
| `economist` | 3-phase economy: GREED → SPIKE → CONVERT |
| `balancer` | Group-balanced purchases with power weight |
| `rare_hunter` | Chases high-rarity cards with fallback |
| `tempo` | Power-centric with center-hex combo bonus |

- **Parameterized training:** `ParameterizedAI` accepts `TRAINED_PARAMS` dict
- **Trained params:** `trained_params.json` at project root (auto-generated by `train_strategies.py`)
- **Builder synergy matrix:** Session-level adjacency memory with decay (0.97 per turn)

#### Card Pool Management ✅
- **3 copies per card** in shared pool
- **Weighted rarity curves:** Turn-based availability (R4 absent turns 1-4, R5 absent turns 1-7)
- **Elimination return:** Dead player's cards returned to pool immediately
- **Micro-buff system:** Weak cards get +1 to lowest stat if below global average

#### Board System ✅
- **37-hex grid** (radius 3 axial coordinates)
- **Card placement:** `place(coord, card)` with O(1) lookup via `coord_index` (uid-based)
- **Catalyst/Eclipse:** Special card slots (`has_catalyst`, `has_eclipse` flags)
- **Neighbor queries:** `neighbors(coord)` returns `(neighbor_coord, direction_index)` pairs

#### Card Model ✅
- **6-edge system:** Each stat maps to a hex edge direction
- **Rotation:** 0-5 steps (60° each), `rotated_edges()` for combat/rendering
- **Unique IDs:** `_next_card_uid()` prevents memory address collisions
- **Clone:** Deep clone with new UID
- **Edge debuff/strengthen:** Combat loss zeroes highest edge; strengthening adds to highest
- **Elimination check:** Card dies when all stats in a group are 0 (2+ stat group requirement)

### 2.3 What `engine_core/` Does NOT Have

| Feature | Status | Notes |
|---------|--------|-------|
| Pygame rendering | ❌ Out of scope | Engine is simulation-only; rendering is `v2/`'s job |
| Scene management | ❌ Out of scope | SceneManager lives in `v2/core/scene_manager.py` |
| Asset loading | ❌ Out of scope | AssetLoader lives in `v2/assets/loader.py` |
| Card database (JSON lookup) | ⚠️ Duplicate | `engine_core/card.py` loads cards.json directly; `v2/core/card_database.py` also loads it — **two separate loaders** |
| UI event bus | ❌ Out of scope | EventBus lives in `v2/core/event_bus.py` |
| HTTP/networking | ❌ Not planned | Single-player simulation only |

### 2.4 Key Architectural Insight

`engine_core/` uses **dependency injection** for critical systems:
```python
game = Game(
    players=players,
    trigger_passive_fn=trigger_passive,  # injected
    combat_phase_fn=combat_phase,         # injected
    card_pool=card_pool,                  # injected
    ai_override=parameterized_ai,         # injected for training
)
```

This design makes it **trivially wrappable** for UI integration — the engine doesn't care who calls it, as long as the interface contract is met.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                        pygame.main()                      │
│                         main.py                           │
├──────────────────────────────────────────────────────────┤
│                    SceneManager (Singleton)               │
│         set_scene() / transition_to() / update()          │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│ ShopScene│LobbyScene│CombatSc. │EndGameSc │VersusSplash  │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│                     UI Components                         │
│  ShopPanel │ HandPanel │ PlayerHub │ SynergyHud │ Lobby  │
├──────────────────────────────────────────────────────────┤
│                   GameState (Singleton)                   │
│              hook_engine(MockGame | RealEngine)           │
│         buy_card / place_card / reroll_market / etc.      │
├──────────────────────────────────────────────────────────┤
│           CardDatabase (v2/core/) — UI-side               │
│           cards.json → CardData lookup (hover info)       │
├──────────────────────────────────────────────────────────┤
│              EventBus (v2/core/)                          │
│         UIEvent.GOLD_UPDATED / PLACE_LOCKED / etc.        │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────┐    ┌──────────────────────────┐  │
│  │   MockGame         │    │   engine_core/ (COMPLETE) │  │
│  │  (v2/mock/)        │    │   ┌────────────────────┐  │  │
│  │  - String names    │    │   │ Game.run()         │  │  │
│  │  - No combat       │    │   │ Board + Card model │  │  │
│  │  - No board        │    │   │ Combat resolver    │  │  │
│  │  - Deterministic   │    │   │ Passive system     │  │  │
│  │    RNG (seed=42)   │    │   │ 8 AI strategies    │  │  │
│  │  - Shop stub       │    │   │ Swiss pairing      │  │  │
│  └────────────────────┘    │   │ Economy + Evolution│  │  │
│                            │   └────────────────────┘  │  │
│                            └──────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Mock Engine (`v2/mock/engine_mock.py`)

### 3.1 Purpose

The Mock engine exists to **enable UI development in parallel** with the core engine. It provides:

- Deterministic card data (strings from `CARD_POOL`)
- Simplified player state (HP, gold, hand, shop)
- Stub implementations for shop operations (buy, reroll, lock)
- No combat logic — `last_combat_results` is an empty list

### 3.2 Key Classes

#### `MockPlayer`
```python
class MockPlayer:
    name: str
    hp: int               # Simple integer (150 - i*15)
    gold: int             # Starts at 10
    hand: list[str|None]  # 6 slots, stores card NAMES (strings)
    win_streak: int
    alive: bool
    copies: dict          # card_name → count
    total_pts: int
    turn_pts: int
    passive_buff_log: list
    evolved_card_names: list
    stats: dict           # wins, losses, draws, market_rolls, etc.
```

**Notable:** `hand` stores **string card names**, not `Card` objects. This is a deliberate simplification — the mock doesn't need card rotation, board placement, or edge stat data.

#### `MockGame`
```python
class MockGame:
    turn: int                          # Starts at 1
    state: str                         # "SHOP" (never changes)
    players: list[MockPlayer]          # 8 players
    _shop_window: list[str|None]       # 5 slots
    _rng: random.Random(42)           # Deterministic
    last_combat_results: list          # Always empty (stub)
```

### 3.3 Shop Operations

| Method | Behavior |
|--------|----------|
| `_reroll_shop()` | Samples `SHOP_SIZE=5` cards from `CARD_POOL` excluding hand cards |
| `reroll_market()` | Deducts 2 gold, rerolls shop. Returns bool |
| `buy_card_from_slot()` | Moves card from shop slot to first empty hand slot. Increments `copies` |
| `toggle_lock_shop()` | **STUB** — does nothing |
| `get_shop_window()` | Returns copy of `_shop_window` |
| `get_hand()` | Returns copy of player's hand |

### 3.4 Deterministic Fixture

`initialize_deterministic_fixture()` creates 8 players with:
- HP: `max(150 - i*15, 30)` (Player 0 = 150, Player 7 = 30)
- Gold: 10 each
- Player 0 hand: first 2 cards from seeded RNG sample
- Shop: 5 cards from seeded RNG

**Seed = 42** ensures reproducible test runs.

---

## 5. Bridge Layer (`v2/core/`)

### 5.1 GameState (`game_state.py`)

The **central abstraction layer** — a singleton that bridges UI to any engine implementation.

#### `ActionResult` Enum
```python
class ActionResult(IntEnum):
    OK                     = 0
    ERR_INSUFFICIENT_GOLD  = 1
    ERR_SLOT_OCCUPIED      = 2
    ERR_POOL_EMPTY         = 3
    ERR_INVALID_COORD      = 4
    ERR_PLACE_LOCKED       = 5
    ERR_INVALID_HAND_IDX   = 6
    ERR_NOT_IN_PREP_PHASE  = 7
    ERR_ENGINE_EXCEPTION   = 99
```

#### Board System
```python
_board: dict[tuple[int, int], str]           # (q,r) → card_name
_board_rotations: dict[tuple[int, int], int] # (q,r) → rotation (0-5)
place_locked: bool                           # One placement per turn (Spec §2.1)
```

The board uses **axial hex coordinates** `(q, r)` with rotation support (0-5).

#### Key Methods

| Method | Description |
|--------|-------------|
| `hook_engine(engine)` | Connects MockGame or real engine to GameState |
| `buy_card_from_slot()` | Delegates to engine, returns `ActionResult` |
| `reroll_market()` | Delegates to engine, returns `ActionResult` |
| `place_card(hand_idx, coord, rotation)` | Places card on board with rotation. Enforces `place_locked` |
| `get_adjacency_pairs()` | Returns `[(coord_a, coord_b, group_a, group_b), ...]` for synergy rendering |
| `reset_turn()` | Resets `place_locked` at turn start |

#### `get_adjacency_pairs()` — Hex Edge Matching Logic

This method implements the **core synergy calculation**:
1. Iterates all board cards
2. For each hex direction, finds neighbor
3. Applies rotation to determine which edge faces which neighbor
4. Maps stat names to groups (`STAT_TO_GROUP`)
5. Returns deduplicated pairs with group info

```python
real_idx_a = (dir_idx - rot_a) % 6
real_idx_b = (OPP_DIR[dir_idx] - rot_b) % 6
group_a = STAT_TO_GROUP.get(edges_a[real_idx_a][0], "")
group_b = STAT_TO_GROUP.get(edges_b[real_idx_b][0], "")
```

### 5.2 CardDatabase (`card_database.py`)

Loads `cards.json` into memory with O(1) lookup by card name.

#### `CardData` Dataclass
```python
@dataclass
class CardData:
    name: str
    category: str           # "Science", "Mythology & Gods", etc.
    rarity: str             # "◆◆◆" or "3"
    stats: dict[str, int]   # {"Power": 7, "Durability": 6, ...} (6 edges)
    passive_type: str       # "synergy_field", "combat", "combo", etc.
    passive_effect: str     # Description text
    synergy_group: str      # Derived from CATEGORY_TO_SYNERGY
```

#### Properties
- `rarity_level` — Handles both `◆◆◆` (3) and `"3"` formats
- `passive_label` — UI-friendly passive type label
- `rarity_color` — Color tuple based on rarity (1=Grey, 5=Gold)

#### Category → Synergy Mapping
```python
CATEGORY_TO_SYNERGY = {
    "Mythology & Gods":    "EXISTENCE",
    "Science":             "MIND",
    "Art & Culture":       "CONNECTION",
    "History":             "CONNECTION",
    "Nature & Biology":    "EXISTENCE",
    "Cosmos & Space":      "MIND",
    "Science & Technology": "MIND",
}
```

### 5.3 SceneManager (`scene_manager.py`)

Manages scene transitions with **alpha-fade** effects.

#### State Machine
```
idle → fade_out → (scene switch) → fade_in → idle
```

#### Key Features
- During transitions, **input is blocked** (`handle_event` only fires in `idle` state)
- Supports legacy scenes with `render()` method alongside `draw()`
- Fade duration configurable (default 200ms)

### 5.4 EventBus (`event_bus.py`)

Simple pub/sub system for UI events:
```python
class UIEvent(Enum):
    GOLD_UPDATED      = 1
    PLACE_LOCKED      = 2
    PLAYER_ELIMINATED = 3
```

---

## 6. Key Differences: Mock vs Production Engine

| Aspect | Mock Engine (`v2/mock/`) | Production Engine (`engine_core/`) |
|--------|-------------------------|-----------------------------------|
| **Card Representation** | String names only | `Card` objects with edges, rotation, board placement |
| **Board** | None | Hex grid with `(q,r)` coordinates, rotation, edge matching |
| **Combat** | Stub (`last_combat_results = []`) | Full combat resolver with passive effects, synergy bonuses, damage calculation |
| **Shop** | Simple string list, no cost | Card objects with rarity-based pricing, lock mechanism |
| **Player Model** | Flat attributes, no board | Full model with `board` (has_catalyst, has_eclipse, interest_multiplier, turns_played) |
| **Matchmaking** | None | Swiss pairing system (`swiss_pairs()`) |
| **Market Pool** | Unlimited random sampling | `pool_copies` tracking (limited supply) |
| **Determinism** | Seeded RNG (42) | Deterministic simulation with fixed seed for replays |
| **State Machine** | Single "SHOP" state | Full cycle: SHOP → COMBAT → SHOP → ENDGAME |
| **Passive Effects** | `passive_buff_log` (unused) | Full passive effect resolution engine |
| **Evolution** | `evolved_card_names` list | 3-copy evolution system with stat upgrades |

### 6.1 Mock-Specific Simplifications (By Design)

1. **No `Card` objects**: Hand stores strings, not objects with `rotation` attribute
2. **No board**: `MockPlayer` has no `board` attribute — `GameState.place_card()` checks `hasattr(raw, 'rotation')` and skips board sync for mock
3. **No combat**: `last_combat_results` is always empty
4. **No Swiss pairing**: `get_current_pairings()` returns empty list
5. **No pool tracking**: `get_pool_copies()` returns empty dict
6. **Shop reroll is infinite**: No lock mechanic, no stock limitations

---

## 7. Combat Logic — Full Analysis

### 7.1 Status in Mock: **NOT IMPLEMENTED** (By Design)

The Mock engine intentionally stubs combat:
- `last_combat_results: list = []` — always empty
- `GameState.get_last_combat_results()` returns `[]`
- No combat resolver module exists in `v2/`

### 7.2 Status in `engine_core/`: **FULLY IMPLEMENTED** ✅

#### Combat Resolution Pipeline (Actual `engine_core/` Implementation)

```
1. Board snapshot → collect all placed cards (Board.grid)
2. Swiss pairing → pair opponents by HP with jitter
3. For each pair:
   a. Pre-combat passives fire (pre_combat trigger)
   b. Combo detection: find_combos() → same-group neighbor pairs
   c. Catalyst check: doubles combo points if has_catalyst
   d. Group synergy bonus: calculate_group_synergy_bonus()
   e. Board combat: combat_phase() resolves all overlapping coords
      - resolve_single_combat(): 6-edge comparison with rotation
      - Group advantage: GROUP_BEATS rock-paper-scissors (+1)
      - Loser: lose_highest_edge() → is_eliminated() → remove
      - Kill points: KILL_PTS=8 per eliminated card
   f. Score: kill_pts + combo_pts + synergy_pts
   g. Damage: calculate_damage() with turn scaling
   h. Post-combat: update stats, HP, win streaks
4. Results → last_combat_results (detailed dict per match)
```

#### Combat Result Structure (Actual)
```python
self.last_combat_results.append({
    "pid_a": p_a.pid, "pid_b": p_b.pid,
    "pts_a": pts_a, "pts_b": pts_b,
    "kill_a": kill_a, "kill_b": kill_b,
    "combo_a": combo_pts_a, "combo_b": combo_pts_b,
    "synergy_a": synergy_pts_a, "synergy_b": synergy_pts_b,
    "draws": draws,
    "winner_pid": result_winner, "dmg": result_dmg,
    "hp_before_a": hp_before_a, "hp_before_b": hp_before_b,
    "hp_after_a": p_a.hp, "hp_after_b": p_b.hp,
})
```

#### Group Advantage System
```python
GROUP_BEATS = {
    "EXISTENCE":  "CONNECTION",
    "MIND":       "EXISTENCE",
    "CONNECTION": "MIND",
}
```

#### Stat → Group Mapping
```python
STAT_TO_GROUP = {
    "Power": "EXISTENCE", "Durability": "EXISTENCE",
    "Size": "EXISTENCE", "Speed": "EXISTENCE",
    "Meaning": "MIND", "Secret": "MIND",
    "Intelligence": "MIND", "Trace": "MIND",
    "Gravity": "CONNECTION", "Harmony": "CONNECTION",
    "Spread": "CONNECTION", "Prestige": "CONNECTION",
}
```

#### Passive Effect Types
From `CardDatabase`:
- `synergy_field` — Board-wide synergy bonuses
- `combat` — Direct combat modifiers
- `combo` — Multi-card interaction effects
- `copy` — Evolution/duplication mechanics
- `survival` / `hayatta_kalma` — Defensive effects
- `economy` / `ekonomi` — Gold/interest modifiers

### 7.3 Bridge Layer Gap Analysis

> **Important:** The table below lists components that are **missing from `v2/core/` (the bridge layer)**, NOT from the project as a whole. Every single one of these exists in `engine_core/` and is fully functional.

| Component | In `v2/` | In `engine_core/` | Notes |
|-----------|----------|-------------------|-------|
| Combat resolver | ❌ Not present | ✅ `board.py:combat_phase()` | Bridge needs adapter to call it |
| Swiss pairing | ❌ Not present | ✅ `game.py:swiss_pairs()` | Bridge accessor exists: `get_current_pairings()` |
| Passive effect engine | ❌ Not present | ✅ `passive_trigger.py` + `passives/` | `passive_buff_log` is populated in engine |
| Damage calculator | ❌ Not present | ✅ `board.py:calculate_damage()` | Full turn-based scaling formula |
| Interest/economy | ❌ Not present | ✅ `player.py:income()`, `apply_interest()` | `get_interest_multiplier()` accessor ready |
| Evolution system | ❌ Not present | ✅ `player.py:check_evolution()` | `evolved_card_names` tracked in MockPlayer |
| Board model (real) | ⚠️ Partial | ✅ `board.py:Board` | `GameState._board` stores string names only; real engine uses `Card` objects |

**The real gap is not features — it's the adapter layer** that translates between `GameState`'s interface and `engine_core/`'s API.

---

## 8. UI Integration Path

### 8.1 Current Architecture

```
UI Components → GameState (Singleton) → MockGame (hooked engine)
```

All UI components read from `GameState`, which delegates to the hooked engine:

```python
# main.py bootstrap
mock_game = MockGame()
mock_game.initialize_deterministic_fixture()
GameState.get().hook_engine(mock_game)
```

### 8.2 UI Component Dependencies

| Component | Reads From | Writes To |
|-----------|-----------|-----------|
| `ShopPanel` | `GameState.get_shop()`, `get_gold()` | `reroll_market()`, `buy_card_from_slot()`, `toggle_lock_shop()` |
| `HandPanel` | `GameState.get_hand()` | N/A (read-only display) |
| `PlayerHub` | `GameState.get_gold()`, `get_hp()` | N/A |
| `SynergyHud` | `GameState.get_adjacency_pairs()`, `get_board_cards()` | N/A |
| `ShopScene` | All of above + `CardDatabase` | `place_card()`, triggers FloatingText |

### 8.3 Data Flow: Buy Card Example

```
1. User clicks shop slot → ShopPanel.handle_event()
2. ShopPanel calls: GameState.buy_card_from_slot(player_index=0, slot_index=idx)
3. GameState delegates: self._engine.buy_card_from_slot(player_index, slot_index)
4. MockGame executes:
   - Checks gold >= cost
   - Deducts gold
   - Moves card name from _shop_window to player.hand
   - Increments player.copies[card_name]
5. GameState returns ActionResult.OK
6. ShopPanel.sync() → re-reads shop from GameState
7. HandPanel.sync() → re-reads hand from GameState
8. PlayerHub.sync() → updates gold display
```

### 8.4 Data Flow: Place Card Example

```
1. User drags card from HandPanel → ShopScene handles drag state
2. User drops on hex → pixel_to_axial() converts to (q, r)
3. ShopScene calls: GameState.place_card(hand_idx, coord, rotation)
4. GameState executes:
   - Checks place_locked (Spec §2.1 — one placement per turn)
   - Checks coord not occupied
   - Validates hand_index
   - Writes to _board[(q,r)] = card_name
   - Writes to _board_rotations[(q,r)] = rotation % 6
   - Sets player.hand[hand_idx] = None
   - If real Card object: card.rotation = rotation, player.board.place(coord, card)
5. Returns ActionResult.OK
6. ShopScene._add_board_flip(coord) → creates CardFlip animator
7. HandPanel.sync() → removes card from hand display
8. FloatingText spawned: "+{delta} SYN" or "⬡ YERLEŞTİ"
```

### 8.5 Engine Swap Mechanism

To switch from Mock to Real engine:

```python
# Current (Mock):
from v2.mock.engine_mock import MockGame
mock_game = MockGame()
mock_game.initialize_deterministic_fixture()
GameState.get().hook_engine(mock_game)

# Future (Real Engine):
from v2.core.engine_core import EngineCore  # hypothetical
real_engine = EngineCore()
real_engine.initialize()
GameState.get().hook_engine(real_engine)
```

The UI components **don't need changes** — they only interact through `GameState`'s interface, which is engine-agnostic.

---

## 9. GameState — Deep Dive: The Bridge Layer

`GameState` is the **most critical architectural element** in this system. It provides:

### 9.1 Engine Abstraction

Every UI call goes through GameState, which delegates to `_engine`:

```python
def get_gold(self, player_index: int = 0) -> int:
    if not self._engine:
        return 0
    return self._engine.players[player_index].gold
```

This pattern allows:
- **Mock development**: UI team builds panels against MockGame
- **Core development**: Engine team builds combat logic independently
- **Zero-downtime swap**: Change engine without touching UI

### 9.2 Board Management

GameState maintains its own board representation (`_board`, `_board_rotations`) that:
- Works with both Mock (string names) and Core (Card objects)
- Provides `get_adjacency_pairs()` for synergy line rendering
- Enforces placement rules (`place_locked`)

### 9.3 Pass-Through Accessors

Most methods are thin wrappers:
```python
def get_turn(self) -> int:
    try:
        return self._engine.turn
    except Exception:
        return 1
```

This pattern ensures **graceful degradation** — if the engine is missing or incomplete, UI still gets default values.

### 9.4 Forward Compatibility

Methods like `has_catalyst()`, `has_eclipse()`, `get_interest_multiplier()` anticipate real engine features that MockGame doesn't implement. These return safe defaults when called against Mock.

---

## 10. Event Bus & Communication

### 10.1 Current Usage

The `EventBus` singleton exists but is **minimally used** in the current codebase. Defined events:

```python
class UIEvent(Enum):
    GOLD_UPDATED      = 1
    PLACE_LOCKED      = 2
    PLAYER_ELIMINATED = 3
```

### 10.2 Current Pattern: Direct Sync

Instead of events, UI components use **pull-based sync**:

```python
# ShopPanel.sync() — called after buy/reroll
def sync(self) -> None:
    new_names = GameState.get().get_shop(player_index=0)
    if new_names != self._card_names:
        self.assign_shop(new_names)
```

### 10.3 Recommended Event Usage

For the real engine, EventBus should be used for:
- **Gold changes** → notify ShopPanel, PlayerHub, HandPanel
- **HP changes** → notify PlayerHub, LobbyPanel
- **Player elimination** → notify LobbyPanel, trigger transition
- **Combat start/end** → trigger SceneManager transitions
- **Turn phase change** → SHOP → COMBAT → SHOP

This would eliminate the need for manual `sync()` calls after every action.

---

## 11. Scene Management

### 11.1 Scene Lifecycle

```
main.py → SceneManager.set_scene(ShopScene())  # No fade
ShopScene → SceneManager.transition_to(CombatScene())  # Fade 200ms
CombatScene → SceneManager.transition_to(ShopScene())  # Fade 200ms
ShopScene → SceneManager.transition_to(EndGameScene()) # Fade 200ms
```

### 11.2 Current Scenes

| Scene | Status | Notes |
|-------|--------|-------|
| `ShopScene` | ✅ Fully implemented | Shop, hand, board, synergy, lobby, floating text |
| `LobbyScene` | ⚠️ Partial | Referenced but not used (ShopScene embeds LobbyPanel) |
| `CombatScene` | ❌ Empty stub | `pass` only |
| `EndGameScene` | ❌ Not found | Referenced in imports but file missing |
| `VersusSplash` | ⚠️ Partial | Referenced in imports, not analyzed |

### 11.3 Transition Blocking

During `fade_out` and `fade_in` states, `SceneManager.handle_event()` **does not forward events** to the current scene. This prevents input during transitions (spec requirement).

---

## 12. Current Limitations & Technical Debt

### 12.1 Mock Limitations (By Design — Not Bugs)

The Mock engine is **intentionally incomplete**. These are not bugs — they are scope decisions that enabled parallel UI development:

1. **No card costs**: `buy_card_from_slot()` doesn't check card price — only checks gold >= 0
2. **No lock mechanic**: `toggle_lock_shop()` is a no-op
3. **No combat**: `last_combat_results` always empty
4. **No evolution**: `copies` dict is tracked but never triggers evolution
5. **No board**: Player has no `board` — placement skips board sync
6. **No Swiss pairing**: `swiss_pairs()` doesn't exist
7. **No pool tracking**: Cards are drawn from infinite `CARD_POOL`
8. **Fixed state**: `state` is always "SHOP" — never transitions

### 12.2 GameState Issues (Bridge Layer)

1. **Direct engine access**: Some methods access `self._engine.players[0]` directly instead of through engine methods
2. **Inconsistent error handling**: Mix of `if not self._engine` checks and bare `try/except`
3. **Board sync gap**: `place_card()` writes to `_board` (string names) but `engine_core`'s `Board.grid` uses `Card` objects — the adapter must handle bidirectional conversion

### 12.3 UI Debt

1. **Hardcoded mock data**: `ShopScene.render()` uses hardcoded `mock_players` list for LobbyPanel — should read from engine
2. **Manual sync calls**: Every action requires explicit `.sync()` on multiple panels
3. **No event-driven updates**: Pull-based sync is inefficient — should use EventBus
4. **FloatingText coordination**: Multiple spawn triggers scattered across ShopScene

### 12.4 The Real Architecture Gap: Bridge, Not Engine

The "missing components" narrative was misleading. The actual situation:

| Area | Status | What's Needed |
|------|--------|---------------|
| Game engine (`engine_core/`) | ✅ 100% complete | Nothing — it's done |
| UI rendering (`v2/ui/`, `v2/scenes/`) | ✅ ~80% complete | CombatScene, EndGameScene, VersusSplash |
| Bridge layer (`v2/core/game_state.py`) | ⚠️ Hooked to Mock | **EngineAdapter** that wraps `engine_core.Game` |
| Card database duplication | ⚠️ Two loaders | Unify or accept separation (UI-side vs engine-side) |
| Combat rendering | ❌ Not started | `CombatScene` that visualizes `last_combat_results` |
| Event-driven UI | ⚠️ EventBus exists, unused | Wire engine events to EventBus for push-based updates |

**In short: The remaining work is integration, not feature development.**

---

## 13. Roadmap: Connecting UI to Real Engine

### Phase 1: Foundation ✅ COMPLETE
- [x] GameState abstraction layer
- [x] CardDatabase with cards.json
- [x] SceneManager with fade transitions
- [x] UI panels wired to GameState
- [x] Hex board rendering with adjacency lines
- [x] Card placement with rotation
- [x] FloatingText milestone system

### Phase 2: Engine Adapter (The Bridge)
The single most impactful change: build an **EngineAdapter** that wraps `engine_core.Game` and exposes the same interface that `GameState` expects from MockGame.

- [ ] **`EngineAdapter` class** in `v2/core/engine_adapter.py`
  - Wraps `engine_core.Game` instance
  - Implements: `get_shop_window()`, `buy_card_from_slot()`, `reroll_market()`, `get_hand()`, `get_hp()`, `get_gold()`, `toggle_lock_shop()`
  - Translates between `GameState`'s string-based interface and `engine_core`'s `Card` objects
- [ ] **`hook_engine()` swap** in `main.py`
  - Replace `MockGame()` with `EngineAdapter()`
  - Keep MockGame behind a `--mock` CLI flag for debugging
- [ ] **Shop card costs** — adapter reads `CARD_COSTS` from engine constants
- [ ] **Pool tracking** — adapter exposes `market.pool_copies` to UI

### Phase 3: Turn Phase Management
- [ ] **Phase transitions**: SHOP → COMBAT → SHOP cycle in `GameState`
- [ ] **`CombatScene`** — renders `last_combat_results` with visual combat log
- [ ] **VersusSplash** — shows matchup before combat
- [ ] **Timer integration** — turn timer triggers phase transition

### Phase 4: Combat Visualization
- [ ] **Combat resolver visualization**: Edge-to-edge combat with floating damage numbers
- [ ] **Group advantage indicators**: Visual rock-paper-scissors feedback
- [ ] **Passive effect triggers**: Show passive activations during combat
- [ ] **Combo detection display**: Highlight combo pairs on board
- [ ] **Synergy bonus rendering**: Show group synergy contributions

### Phase 5: Live Data Integration
- [ ] **LobbyPanel**: Read real player data from engine (HP, gold, strategy, rank)
- [ ] **SynergyHud**: Use engine's `calculate_group_synergy_bonus()` instead of re-computing
- [ ] **IncomePreview**: Show engine-calculated income (base + streak + interest)
- [ ] **Copy count labels**: Read from `player.copies` directly
- [ ] **Player elimination**: EventBus event → LobbyPanel update → scene transition

### Phase 6: EventBus Integration
- [ ] **Engine events → EventBus**: Adapter publishes `UIEvent.GOLD_UPDATED`, `PLAYER_ELIMINATED`, etc.
- [ ] **UI components subscribe**: Replace manual `.sync()` calls with event subscriptions
- [ ] **Combat phase events**: `COMBAT_STARTED`, `COMBAT_ENDED` for scene transitions

### Phase 7: Polish Scenes
- [ ] **EndGameScene**: Winner display, final stats, rematch option
- [ ] **LobbyScene standalone**: Extract from ShopScene embedding
- [ ] **Settings panel**: Volume, display options

---

## Appendix A: Hex Coordinate System

The engine uses **axial coordinates** `(q, r)` for hex grid:

```
Direction indices:     N=0, NE=1, SE=2, S=3, SW=4, NW=5

ENGINE_HEX_DIRS = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]
OPP_DIR = {0:3, 1:4, 2:5, 3:0, 4:1, 5:2}  # Opposite directions
```

Rotation application:
```python
real_idx = (dir_idx - rotation) % 6
```

---

## Appendix B: Card Pool

Mock engine uses **105 unique cards** across categories:
- Mythology & Gods (Anubis, Athena, Odin, etc.)
- Science (DNA, Quantum Mechanics, Higgs Boson, etc.)
- Cosmos & Space (Black Hole, Nebula, Event Horizon, etc.)
- Art & Culture (Cubism, Baroque, Guernica, etc.)
- History (French Revolution, Silk Road, Cold War, etc.)
- Nature & Biology (Blue Whale, Coelacanth, Tardigrade, etc.)

---

## Appendix C: File Inventory

### Bridge Layer (`v2/core/`)
| File | Lines | Purpose |
|------|-------|---------|
| `v2/core/game_state.py` | ~260 | Engine abstraction, board management |
| `v2/core/card_database.py` | ~160 | Card data loading and lookup (UI-side) |
| `v2/core/scene_manager.py` | ~130 | Scene lifecycle with fade |
| `v2/core/event_bus.py` | ~35 | Pub/sub event system |
| `v2/core/clock.py` | ~3 | Stub (DeltaClock placeholder) |

### Production Engine (`engine_core/`)
| File | Lines | Purpose |
|------|-------|---------|
| `engine_core/game.py` | ~340 | Game loop, prep phase, combat phase, Swiss pairing |
| `engine_core/card.py` | ~320 | Card model, edges, rotation, evolution, strengthening |
| `engine_core/board.py` | ~310 | Hex grid, combat resolver, combo detection, synergy calc |
| `engine_core/player.py` | ~330 | Player state, income, interest, evolution, copy tracking |
| `engine_core/market.py` | ~160 | Pool management, weighted rarity sampling, windows |
| `engine_core/ai.py` | ~1252 | 8 AI strategies, parameterized training, synergy matrix |
| `engine_core/passive_trigger.py` | ~90 | Passive dispatch system |
| `engine_core/constants.py` | ~100 | All game constants, stat groups, group beats |
| `engine_core/passives/` | 9 files | Synergy, combat, combo, copy, economy, survival handlers |
| `engine_core/simulation.py` | — | Match simulation runner |
| `engine_core/game_factory.py` | — | Game instance factory |
| `engine_core/kpi_aggregator.py` | — | KPI collection for training |
| `engine_core/strategy_logger.py` | — | Strategy-level logging |
| `engine_core/event_logger.py` | — | Event logging |

### Mock Files
| File | Lines | Purpose |
|------|-------|---------|
| `v2/mock/engine_mock.py` | ~130 | MockGame, MockPlayer, shop ops |

### UI Files
| File | Purpose |
|------|---------|
| `v2/ui/shop_panel.py` | Shop display with buy/reroll/lock |
| `v2/ui/hand_panel.py` | Hand display with drag support |
| `v2/ui/player_hub.py` | Gold/HP display |
| `v2/ui/synergy_hud.py` | Synergy group counts |
| `v2/ui/lobby_panel.py` | 8-player scoreboard |
| `v2/ui/timer_bar.py` | Turn timer |
| `v2/ui/info_box.py` | Card hover info |
| `v2/ui/hex_grid.py` | Hex rendering, axial↔pixel conversion |
| `v2/ui/card_flip.py` | Card flip animation |
| `v2/ui/widgets.py` | FloatingText manager |
| `v2/ui/font_cache.py` | Font caching |
| `v2/ui/ui_utils.py` | Gradient panel utilities |
| `v2/ui/background_manager.py` | Dynamic background |
| `v2/ui/income_preview.py` | Income preview |
| `v2/ui/combat_terminal.py` | Combat log display (unused) |

### Scene Files
| File | Status |
|------|--------|
| `v2/scenes/shop.py` | ✅ Full implementation (~615 lines) |
| `v2/scenes/lobby.py` | ⚠️ Partial |
| `v2/scenes/combat.py` | ❌ Empty stub |
| `v2/scenes/endgame.py` | ❌ Not found |
| `v2/scenes/versus_splash.py` | ⚠️ Partial |

---

*Report generated from codebase analysis — 13 Nisan 2026*
