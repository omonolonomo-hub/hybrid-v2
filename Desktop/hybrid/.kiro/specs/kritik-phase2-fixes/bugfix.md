# Bugfix Requirements Document

## Introduction

This document specifies requirements for Phase 2 (CRITICAL) fixes from OMNISCIENT AUDIT V7. These are critical bugs requiring architectural intervention but still well-scoped and focused. Phase 1 (ACIL/IMMEDIATE) has been completed with 3 zero-risk single-line fixes. Phase 2 addresses 5 critical bugs:

1. **UIAdapter.build_public_state() Performance Leak** - Cache invalidation triggers expensive full BFS + DB + triple-iteration on every frame
2. **MOUSEBUTTONDOWN Redundant get_card_info() Call** - Every hand card click creates new CardDataSnapshot when data already cached
3. **SceneManager Singleton Memory Leak** - Singleton pattern prevents GC, causing RAM explosion on scene transitions
4. **ShopController.handle_phase_change() Not Atomic** - Phase transitions lack transaction pattern, leaving inconsistent state on exception
5. **frozen=True Dataclass with Mutable Dicts** - Mutable dicts inside frozen dataclass bypass immutability, causing state corruption

All fixes require architectural changes but maintain backward compatibility and zero regressions.

---

## Bug Analysis

### Current Behavior (Defect)

#### Bug 1: UIAdapter.build_public_state() Performance Leak

1.1 WHEN any buy/place/reroll action occurs THEN the system invalidates the entire cache, causing full BFS + DB + triple-iteration on next frame

1.2 WHEN start_turn() is called with 7 AI purchases + income signals + inventory signals THEN the system triggers 15-20 cache invalidations

1.3 WHEN build_public_state() runs with 8+ cards THEN the system takes 5-8ms, approaching the 16ms frame budget at 60 FPS

1.4 WHEN economy_changed or inventory_changed signals fire THEN the system unnecessarily runs SynergyCalculator.compute() BFS even though board hasn't changed

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

1.5 WHEN a hand card is clicked THEN the system calls EngineAdapter.get_card_info(card_name) → CardDatabase.get() → creates new CardDataSnapshot object

1.6 WHEN the card data already exists in _public_state.active_player.hand_card_info[idx] from last mutation THEN the system ignores the cached data and fetches it again

#### Bug 3: SceneManager Singleton Memory Leak

1.7 WHEN set_scene() is called THEN the system calls old scene's on_exit() but GameState references, Pygame Surfaces, and UI components are not GC'd

1.8 WHEN Main Menu → Game → Main Menu loop occurs THEN the system creates new GameState and Game each time but old ShopScene (with all Pygame Surfaces) survives through SceneManager

1.9 WHEN 3-4 scene transition loops occur THEN the system experiences RAM explosion

1.10 WHEN tests need isolation THEN the system requires monkey-patching SceneManager._instance = None

#### Bug 4: ShopController.handle_phase_change() Not Atomic

1.11 WHEN STATE_PREPARATION transition calls mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn() in sequence AND any step throws exception THEN the system leaves phase already mirrored but turn hasn't started

1.12 WHEN phase is in inconsistent state THEN the system remains in "PREPARATION" phase but market window isn't open

1.13 WHEN next action runs after exception THEN the system operates in inconsistent state with unpredictable behavior

#### Bug 5: frozen=True Dataclass with Mutable Dicts

1.14 WHEN ActivePlayerViewState(frozen=True) contains stats: Dict, board_cards: Dict, copies_by_name: Dict THEN the system allows dict content mutation despite frozen=True

1.15 WHEN UI code executes state.active_player.stats["bonus"] = 99 THEN the system mutates the cached object without triggering invalidation

1.16 WHEN Save/Load system serializes state THEN the system includes mutable dicts with 'temporary' data, causing reload to start from wrong state

---

### Expected Behavior (Correct)

#### Bug 1: UIAdapter.build_public_state() Performance Leak

2.1 WHEN any buy/place/reroll action occurs THEN the system SHALL use granular cache with separate _cached_synergy, _cached_shop, _cached_hand

2.2 WHEN each signal fires THEN the system SHALL only invalidate its own cache (board_mutated → _cached_synergy + _cached_board, economy_changed → _cached_hud, inventory_changed → _cached_hand, turn_started → _cached_shop)

2.3 WHEN economy_changed or inventory_changed or turn_started signals fire THEN the system SHALL NOT run SynergyCalculator.compute() BFS

2.4 WHEN board_mutated signal fires THEN the system SHALL run SynergyCalculator.compute() BFS only for board changes

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

2.5 WHEN a hand card is clicked THEN the system SHALL use cached data from self._current_public_state().active_player.get_card_info("hand", idx)

2.6 WHEN card data already exists in _public_state THEN the system SHALL NOT call EngineAdapter.get_card_info(card_name)

#### Bug 3: SceneManager Singleton Memory Leak

2.7 WHEN set_scene() is called AND a current scene exists THEN the system SHALL cleanup the current scene (call on_exit(), null references, delete fade surface) before replacing it

2.8 WHEN scene transitions occur THEN the system SHALL allow GC to clean up old scene's GameState, Pygame Surfaces, and UI components

2.9 WHEN tests need isolation THEN the system SHALL provide dispose() method instead of requiring monkey-patching

2.10 WHEN multiple scene transitions occur THEN the system SHALL maintain stable RAM usage without explosion

#### Bug 4: ShopController.handle_phase_change() Not Atomic

2.11 WHEN STATE_PREPARATION transition calls mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn() AND any step throws exception THEN the system SHALL restore StateStore._phase to its previous value (engine-level mutations like board/market are not rolled back as they are idempotent or logged)

2.12 WHEN phase transition logic is wrapped in try/except THEN the system SHALL restore phase to previous value on exception (PhaseTransactionContext pattern optional but not required for rollback)

2.13 WHEN exception occurs during phase transition THEN the system SHALL restore StateStore._phase to prevent inconsistent state (engine-level mutations are not undone but phase guard remains correct)

#### Bug 5: frozen=True Dataclass with Mutable Dicts

2.14 WHEN ActivePlayerViewState(frozen=True) contains stats, board_cards, copies_by_name THEN the system SHALL wrap dicts with types.MappingProxyType to make them truly immutable (for nested dicts like board_cards: Dict[Coord, Dict[str, Any]], both outer and inner dicts must be wrapped)

2.15 WHEN UI code attempts state.active_player.stats["bonus"] = 99 THEN the system SHALL raise TypeError preventing mutation

2.16 WHEN Save/Load system serializes state THEN the system SHALL only serialize immutable data, preventing temporary data from persisting

---

### Unchanged Behavior (Regression Prevention)

#### Bug 1: UIAdapter.build_public_state() Performance Leak

3.1 WHEN build_public_state() is called with no cache THEN the system SHALL CONTINUE TO compute full state with BFS + DB + triple-iteration

3.2 WHEN synergy data is needed for UI display THEN the system SHALL CONTINUE TO return correct synergy calculations

3.3 WHEN shop/hand/board card info is accessed THEN the system SHALL CONTINUE TO return correct card data

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

3.4 WHEN card data is accessed from cached _public_state THEN the system SHALL CONTINUE TO return the same CardDataSnapshot data as before

3.5 WHEN card clicks trigger game actions THEN the system SHALL CONTINUE TO process those actions correctly

3.6 WHEN other mouse events occur (drag, board clicks, shop clicks) THEN the system SHALL CONTINUE TO function as currently implemented

#### Bug 3: SceneManager Singleton Memory Leak

3.7 WHEN set_scene() transitions to a new scene THEN the system SHALL CONTINUE TO call on_exit() on the old scene

3.8 WHEN scenes are active THEN the system SHALL CONTINUE TO render and update correctly

3.9 WHEN scene lifecycle methods (on_enter, on_exit, update, render) are called THEN the system SHALL CONTINUE TO function as currently implemented

#### Bug 4: ShopController.handle_phase_change() Not Atomic

3.10 WHEN phase transitions complete successfully without exceptions THEN the system SHALL CONTINUE TO execute mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn() in sequence

3.11 WHEN phase transitions are successful THEN the system SHALL CONTINUE TO update game state correctly

3.12 WHEN other ShopController methods are called THEN the system SHALL CONTINUE TO function as currently implemented

#### Bug 5: frozen=True Dataclass with Mutable Dicts

3.13 WHEN ActivePlayerViewState is created with valid data THEN the system SHALL CONTINUE TO store and return that data correctly

3.14 WHEN frozen dataclass attributes are accessed (read-only) THEN the system SHALL CONTINUE TO return correct values

3.15 WHEN other dataclass operations occur (equality checks, hashing, serialization) THEN the system SHALL CONTINUE TO function as currently implemented
