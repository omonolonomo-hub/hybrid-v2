# Phase 2 (CRITICAL) Fixes Bugfix Design

## Overview

This design document addresses five critical bugs identified in Phase 2 (CRITICAL) of OMNISCIENT AUDIT V7. These bugs require architectural intervention but remain well-scoped and focused. Phase 1 (ACIL/IMMEDIATE) has been completed with 3 zero-risk single-line fixes. Phase 2 addresses more complex issues:

1. **UIAdapter.build_public_state() Performance Leak** - Cache invalidation triggers expensive full BFS + DB + triple-iteration on every frame
2. **MOUSEBUTTONDOWN Redundant get_card_info() Call** - Every hand card click creates new CardDataSnapshot when data already cached
3. **SceneManager Singleton Memory Leak** - Singleton pattern prevents GC, causing RAM explosion on scene transitions
4. **ShopController.handle_phase_change() Not Atomic** - Phase transitions lack transaction pattern, leaving inconsistent state on exception
5. **frozen=True Dataclass with Mutable Dicts** - Mutable dicts inside frozen dataclass bypass immutability, causing state corruption

All fixes maintain backward compatibility and zero regressions while addressing critical performance, memory, and state consistency issues.

## Glossary

- **Bug_Condition (C)**: The condition that triggers each bug
- **Property (P)**: The desired behavior when the bug condition is met
- **Preservation**: Existing behavior that must remain unchanged by the fix
- **UIAdapter.build_public_state()**: The method in `v2/adapters/ui_adapter.py` that builds the complete UI state snapshot
- **Cache Invalidation**: The process of marking cached data as stale, forcing recomputation on next access
- **BFS (Breadth-First Search)**: The graph traversal algorithm used by SynergyCalculator.compute() to find synergy chains
- **CardDataSnapshot**: Immutable data object containing card information from CardDatabase
- **SceneManager**: Singleton class in `v2/core/scene_manager.py` that manages scene lifecycle and transitions
- **GC (Garbage Collection)**: Python's automatic memory management system that reclaims unused objects
- **Singleton Pattern**: Design pattern ensuring only one instance of a class exists globally
- **PhaseTransactionContext**: Optional context manager pattern for atomic phase transitions (not required for this fix)
- **StateStore._phase**: The internal phase property that stores the current game phase string
- **frozen=True**: Dataclass parameter that makes instances immutable (prevents attribute assignment)
- **MappingProxyType**: Python's types.MappingProxyType - a read-only proxy for dictionaries
- **Signal**: Event notification system where observers subscribe to state changes
- **board_mutated**: Signal fired when board state changes (card placed, removed, upgraded)
- **economy_changed**: Signal fired when player gold or HP changes
- **inventory_changed**: Signal fired when hand cards change
- **turn_started**: Signal fired when a new turn begins
- **_cached_synergy**: Cache for synergy calculation results (BFS output)
- **_cached_board**: Cache for board card information
- **_cached_shop**: Cache for market/shop window data
- **_cached_hand**: Cache for hand card information
- **_cached_hud**: Cache for HUD display data (gold, HP, turn number)

## Bug Details

### Bug 1: UIAdapter.build_public_state() Performance Leak

#### Bug Condition

The bug manifests when any buy/place/reroll action occurs. The system invalidates the entire cache, causing full BFS + DB + triple-iteration on the next frame. During start_turn() with 7 AI purchases + income signals + inventory signals, the system triggers 15-20 cache invalidations. With 8+ cards, build_public_state() takes 5-8ms, approaching the 16ms frame budget at 60 FPS.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SignalEvent
  OUTPUT: boolean
  
  RETURN (input.signal IN [economy_changed, inventory_changed, turn_started])
         AND input.invalidates_entire_cache == True
         AND SynergyCalculator.compute() is called unnecessarily
         AND board_state_unchanged == True
END FUNCTION
```

#### Examples

- **Example 1**: Player buys a card → inventory_changed fires → Entire cache invalidated → BFS runs even though board unchanged → 5-8ms wasted
- **Example 2**: start_turn() with 7 AI purchases → 15-20 cache invalidations → Multiple BFS runs → Frame rate drops
- **Example 3**: Player gains income → economy_changed fires → Entire cache invalidated → BFS runs even though only gold changed → Unnecessary computation
- **Edge Case**: Multiple signals fire in same frame → Cache invalidated multiple times → Multiple BFS runs before next render

#### Expected Behavior

**Correct Behavior:**
When signals fire, the system SHALL use granular cache invalidation:
- **board_mutated** → Invalidate _cached_synergy + _cached_board only
- **economy_changed** → Invalidate _cached_hud only (gold/HP display)
- **inventory_changed** → Invalidate _cached_hand only
- **turn_started** → Invalidate _cached_shop only (market window)

**Important Note:** turn_started affects both _cached_shop (market window) AND the turn number in PlayerHudViewState.turn. However, in practice, economy_changed fires for each player's income, so _cached_hud gets invalidated anyway. This means there's no conflict - the turn number will be updated when _cached_hud is recomputed due to economy_changed.

SynergyCalculator.compute() BFS SHALL only run when board_mutated fires, not for economy/inventory/turn changes.

#### Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Monolithic Cache**: UIAdapter uses a single cache flag instead of separate flags for synergy, shop, hand, board, and HUD
2. **Signal-to-Cache Mapping Missing**: No mapping exists between signals and which cache components they should invalidate
3. **Overly Aggressive Invalidation**: All signals invalidate the entire cache, causing unnecessary BFS runs
4. **No Granular Recomputation**: build_public_state() recomputes everything instead of selectively rebuilding only invalidated components

### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

#### Bug Condition

The bug manifests when a hand card is clicked. The system calls EngineAdapter.get_card_info(card_name) → CardDatabase.get() → creates new CardDataSnapshot object, even though the card data already exists in _public_state.active_player.hand_card_info[idx] from the last mutation.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type MouseEvent
  OUTPUT: boolean
  
  RETURN input.type == MOUSEBUTTONDOWN
         AND input.target == hand_card
         AND card_data_exists_in_cache(_public_state.active_player.hand_card_info[idx])
         AND EngineAdapter.get_card_info(card_name) is called
END FUNCTION
```

#### Examples

- **Example 1**: Player clicks hand card → get_card_info() called → New CardDataSnapshot created → Cached data ignored
- **Example 2**: Player clicks same card twice → get_card_info() called twice → Two identical CardDataSnapshot objects created
- **Example 3**: Player clicks multiple hand cards rapidly → Multiple redundant get_card_info() calls → Unnecessary DB lookups
- **Edge Case**: Card data in cache is stale (card was just added to hand) → get_card_info() needed → Should use cached data after first access

#### Expected Behavior

**Correct Behavior:**
When a hand card is clicked, the system SHALL use cached data from self._current_public_state().active_player.get_card_info("hand", idx). The system SHALL NOT call EngineAdapter.get_card_info(card_name) when card data already exists in _public_state.

#### Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Cache Unawareness**: The mouse event handler doesn't know that card data is already cached in _public_state
2. **Direct DB Access Pattern**: The code follows a pattern of "always fetch from DB" instead of "check cache first"
3. **Missing Cache Accessor**: No helper method exists to retrieve cached card data from _public_state

### Bug 3: SceneManager Singleton Memory Leak

#### Bug Condition

The bug manifests when set_scene() is called. The system calls old scene's on_exit() but GameState references, Pygame Surfaces, and UI components are not GC'd. When Main Menu → Game → Main Menu loop occurs, the system creates new GameState and Game each time but old ShopScene (with all Pygame Surfaces) survives through SceneManager. After 3-4 scene transition loops, RAM explodes.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SceneTransition
  OUTPUT: boolean
  
  RETURN input.old_scene EXISTS
         AND input.old_scene.on_exit() called
         AND input.old_scene.references_not_cleared == True
         AND SceneManager._instance holds reference to old_scene
         AND GC cannot reclaim old_scene memory
END FUNCTION
```

#### Examples

- **Example 1**: Main Menu → Game → set_scene() called → old scene's on_exit() runs → GameState references survive → GC blocked
- **Example 2**: Game → Main Menu → new GameState created → old ShopScene with Pygame Surfaces survives → RAM increases
- **Example 3**: 3-4 scene transitions → Multiple GameState instances in memory → RAM explosion
- **Edge Case**: First set_scene() call has no old scene → Should not attempt cleanup → Avoid null scene operations

#### Expected Behavior

**Correct Behavior:**
When set_scene() is called AND a current scene exists, the system SHALL cleanup the current scene (call on_exit(), null references, delete fade surface) before replacing it. The system SHALL allow GC to clean up old scene's GameState, Pygame Surfaces, and UI components. Tests SHALL use dispose() method instead of monkey-patching SceneManager._instance = None.

**Important Note:** Only cleanup when current scene exists. The first set_scene() call has no scene to dispose, so we must avoid null scene operations.

#### Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Singleton Holds References**: SceneManager._instance holds strong references to scenes, preventing GC
2. **Incomplete Cleanup**: on_exit() is called but doesn't null out all references (GameState, Surfaces, UI components)
3. **No Explicit Disposal**: No dispose() method exists to break the singleton pattern for testing
4. **Fade Surface Leak**: The fade surface used for transitions is not deleted after use

### Bug 4: ShopController.handle_phase_change() Not Atomic

#### Bug Condition

The bug manifests when STATE_PREPARATION transition calls mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn() in sequence AND any step throws exception. The system leaves phase already mirrored but turn hasn't started. The phase is in inconsistent state - remains in "PREPARATION" phase but market window isn't open. Next action runs after exception with unpredictable behavior.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type PhaseTransition
  OUTPUT: boolean
  
  RETURN input.phase == "STATE_PREPARATION"
         AND input.sequence == [mirror_phase, cleanup_dead_cards, start_turn, reset_turn]
         AND exception_thrown_during_sequence == True
         AND StateStore._phase already modified
         AND turn_not_started == True
END FUNCTION
```

#### Examples

- **Example 1**: mirror_phase() succeeds → cleanup_dead_cards() throws exception → Phase already mirrored but turn not started → Inconsistent state
- **Example 2**: start_turn() throws exception → Phase mirrored, cards cleaned, but turn not started → Market window not open
- **Example 3**: reset_turn() throws exception → Phase mirrored, turn started, but reset incomplete → Unpredictable behavior
- **Edge Case**: Exception in mirror_phase() before phase change → Phase not modified → No rollback needed

#### Expected Behavior

**Correct Behavior:**
When STATE_PREPARATION transition calls mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn() AND any step throws exception, the system SHALL restore StateStore._phase to its previous value. Engine-level mutations (board, market) are NOT rolled back as they are idempotent or logged. No full undo mechanism is required - only StateStore._phase needs restoration.

**Important Note:** Only restore StateStore._phase on exception. Engine-level mutations like board/market changes are not rolled back because they are either idempotent (can be safely repeated) or logged (can be debugged). The goal is to prevent inconsistent phase state, not to implement full transaction rollback.

#### Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **No Exception Handling**: handle_phase_change() doesn't wrap the sequence in try/except
2. **Phase Modified Early**: StateStore._phase is modified before the sequence completes
3. **No Rollback Logic**: No mechanism exists to restore _phase to previous value on exception
4. **Partial Execution**: Some steps complete (mirror_phase, cleanup_dead_cards) but others don't (start_turn, reset_turn)

### Bug 5: frozen=True Dataclass with Mutable Dicts

#### Bug Condition

The bug manifests when ActivePlayerViewState(frozen=True) contains stats: Dict, board_cards: Dict, copies_by_name: Dict. The system allows dict content mutation despite frozen=True. UI code can execute state.active_player.stats["bonus"] = 99, mutating the cached object without triggering invalidation. Save/Load system serializes state with mutable dicts containing 'temporary' data, causing reload to start from wrong state.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type DataclassInstance
  OUTPUT: boolean
  
  RETURN input.frozen == True
         AND input.contains_mutable_dict == True
         AND dict_content_mutation_allowed == True
         AND cache_invalidation_not_triggered == True
END FUNCTION
```

#### Examples

- **Example 1**: state.active_player.stats["bonus"] = 99 → Dict mutated → frozen=True bypassed → Cache not invalidated
- **Example 2**: state.active_player.board_cards[coord]["hp"] = 999 → Nested dict mutated → State corruption
- **Example 3**: Save/Load serializes mutated state → Temporary data persists → Reload starts from wrong state
- **Edge Case**: board_cards: Dict[Coord, Dict[str, Any]] requires BOTH outer and inner dicts wrapped → MappingProxyType({k: MappingProxyType(v) for k, v in board_cards.items()})

#### Expected Behavior

**Correct Behavior:**
When ActivePlayerViewState(frozen=True) contains stats, board_cards, copies_by_name, the system SHALL wrap dicts with types.MappingProxyType to make them truly immutable. For nested dicts like board_cards: Dict[Coord, Dict[str, Any]], BOTH outer and inner dicts must be wrapped. When UI code attempts state.active_player.stats["bonus"] = 99, the system SHALL raise TypeError preventing mutation. Save/Load system SHALL only serialize immutable data, preventing temporary data from persisting.

**Important Note:** For nested dicts like board_cards, both levels must be wrapped:
```python
MappingProxyType({k: MappingProxyType(v) for k, v in board_cards.items()})
```

#### Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **frozen=True Only Prevents Attribute Assignment**: Python's frozen dataclass only prevents `state.attr = value`, not `state.attr[key] = value`
2. **Mutable Dict References**: Dicts are stored by reference, so frozen=True doesn't prevent mutation of dict contents
3. **No MappingProxyType Wrapping**: Dicts are not wrapped with types.MappingProxyType to enforce immutability
4. **Nested Dict Issue**: board_cards contains nested dicts, requiring both outer and inner dicts to be wrapped

## Correctness Properties

Property 1: Bug Condition - Granular Cache Invalidation

_For any_ signal event where economy_changed, inventory_changed, or turn_started fires, the fixed UIAdapter SHALL only invalidate the specific cache component related to that signal (economy_changed → _cached_hud, inventory_changed → _cached_hand, turn_started → _cached_shop), and SHALL NOT run SynergyCalculator.compute() BFS unless board_mutated fires.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Full State Computation

_For any_ build_public_state() call where no cache exists, the fixed UIAdapter SHALL produce exactly the same complete state with BFS + DB + triple-iteration as the original implementation, preserving all existing functionality for synergy calculations, shop data, hand data, and board data.

**Validates: Requirements 3.1, 3.2, 3.3**

Property 3: Bug Condition - Use Cached Card Data

_For any_ hand card click event where card data already exists in _public_state.active_player.hand_card_info[idx], the fixed mouse event handler SHALL use the cached data and SHALL NOT call EngineAdapter.get_card_info(card_name).

**Validates: Requirements 2.5, 2.6**

Property 4: Preservation - Card Click Actions

_For any_ card click event, the fixed code SHALL produce exactly the same game actions (drag, play, sell) as the original code, preserving all existing card interaction functionality.

**Validates: Requirements 3.4, 3.5, 3.6**

Property 5: Bug Condition - Scene Cleanup on Transition

_For any_ set_scene() call where a current scene exists, the fixed SceneManager SHALL cleanup the current scene (call on_exit(), null references, delete fade surface) before replacing it, allowing GC to reclaim memory.

**Validates: Requirements 2.7, 2.8, 2.9, 2.10**

Property 6: Preservation - Scene Lifecycle

_For any_ scene transition, the fixed SceneManager SHALL continue to call on_exit() on the old scene and SHALL continue to render and update scenes correctly, preserving all existing scene lifecycle functionality.

**Validates: Requirements 3.7, 3.8, 3.9**

Property 7: Bug Condition - Phase Rollback on Exception

_For any_ phase transition where an exception is thrown during the sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn), the fixed handle_phase_change() SHALL restore StateStore._phase to its previous value, preventing inconsistent phase state.

**Validates: Requirements 2.11, 2.12, 2.13**

Property 8: Preservation - Successful Phase Transitions

_For any_ phase transition that completes successfully without exceptions, the fixed handle_phase_change() SHALL execute the sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn) exactly as the original implementation, preserving all existing phase transition logic.

**Validates: Requirements 3.10, 3.11, 3.12**

Property 9: Bug Condition - Immutable Dict Enforcement

_For any_ attempt to mutate dict contents in ActivePlayerViewState (e.g., state.active_player.stats["bonus"] = 99), the fixed dataclass SHALL raise TypeError, preventing mutation of frozen dataclass contents.

**Validates: Requirements 2.14, 2.15, 2.16**

Property 10: Preservation - Dataclass Read Access

_For any_ read access to ActivePlayerViewState attributes (stats, board_cards, copies_by_name), the fixed dataclass SHALL return correct values exactly as the original implementation, preserving all existing dataclass operations (equality checks, hashing, serialization).

**Validates: Requirements 3.13, 3.14, 3.15**

## Fix Implementation

### Bug 1: UIAdapter.build_public_state() Performance Leak

**File**: `v2/adapters/ui_adapter.py`

**Class**: `UIAdapter`

**Specific Changes**:

1. **Replace Monolithic Cache with Granular Caches**:
   - Replace single `_cache_valid` flag with separate cache storage
   - Store cached PublicState components separately:
     - `_cached_public_state: Optional[PublicState]` (full state, reused when valid)
     - Track which components are stale with invalidation flags
   
   **Important Note**: PublicState is a frozen dataclass, so we cannot modify it in place. Instead, we'll cache the entire PublicState and track which signals have fired since last build. When building, we'll selectively recompute only the invalidated components and construct a new PublicState.

2. **Implement Signal-to-Cache Mapping**:
   - Track invalidation state with flags:
     - `_synergy_stale: bool` (set by board_mutated)
     - `_board_stale: bool` (set by board_mutated)
     - `_shop_stale: bool` (set by turn_started)
     - `_hand_stale: bool` (set by inventory_changed)
     - `_hud_stale: bool` (set by economy_changed)
   
   - Signal handlers:
     - **board_mutated** → Set `_synergy_stale = True` + `_board_stale = True`
     - **economy_changed** → Set `_hud_stale = True` (gold/HP display)
     - **inventory_changed** → Set `_hand_stale = True`
     - **turn_started** → Set `_shop_stale = True` (market window)
   
   **Important Note:** turn_started affects both _shop (market window) AND the turn number in PlayerHudViewState.turn. However, in practice, economy_changed fires for each player's income, so _hud gets invalidated anyway. This means there's no conflict - the turn number will be updated when HUD is recomputed due to economy_changed.

3. **Selective Recomputation in build_public_state()**:
   - Check each stale flag before recomputing
   - Only run SynergyCalculator.compute() BFS if `_synergy_stale == True`
   - Only fetch board card info if `_board_stale == True`
   - Only fetch shop data if `_shop_stale == True`
   - Only fetch hand card info if `_hand_stale == True`
   - Only fetch HUD data if `_hud_stale == True`
   - Reuse cached components for non-stale data
   - Construct new PublicState with mix of cached and fresh components

4. **Update Signal Handlers**:
   - Modify `_on_board_mutated()` to set only synergy + board stale flags
   - Modify `_on_economy_changed()` to set only HUD stale flag
   - Modify `_on_inventory_changed()` to set only hand stale flag
   - Modify `_on_turn_started()` to set only shop stale flag

**Why This Works**:
- Granular invalidation prevents unnecessary BFS runs
- Signal-to-cache mapping ensures only affected components are recomputed
- Selective recomputation reduces frame time from 5-8ms to <1ms for non-board changes
- turn_started/economy_changed interaction is handled naturally (economy_changed invalidates HUD anyway)

### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

**File**: `v2/scenes/shop.py` (or wherever hand card click is handled)

**Function**: Mouse event handler for hand card clicks

**Specific Changes**:

1. **Add Cache Accessor Method**:
   - Create helper method to retrieve cached card data:
   ```python
   def _get_cached_card_info(self, location: str, index: int) -> Optional[CardDataSnapshot]:
       """Retrieve cached card data from _public_state."""
       if location == "hand":
           hand_cards = self._current_public_state().active_player.hand_card_info
           if 0 <= index < len(hand_cards):
               return hand_cards[index]
       return None
   ```

2. **Modify Hand Card Click Handler**:
   - Replace direct `EngineAdapter.get_card_info(card_name)` call
   - Use `_get_cached_card_info("hand", idx)` instead
   - Only call `EngineAdapter.get_card_info()` if cache miss (shouldn't happen in normal flow)

3. **Example Implementation**:
   ```python
   # OLD CODE:
   card_data = self.engine_adapter.get_card_info(card_name)
   
   # NEW CODE:
   card_data = self._get_cached_card_info("hand", card_index)
   if card_data is None:
       # Fallback for edge cases (shouldn't happen)
       card_data = self.engine_adapter.get_card_info(card_name)
   ```

**Why This Works**:
- Cached data is already available in _public_state from last mutation
- No redundant DB lookup or CardDataSnapshot creation
- Fallback ensures robustness for edge cases
- Zero performance overhead (cache lookup is O(1))

### Bug 3: SceneManager Singleton Memory Leak

**File**: `v2/core/scene_manager.py`

**Class**: `SceneManager`

**Specific Changes**:

1. **Add Explicit Cleanup in set_scene()**:
   ```python
   def set_scene(self, new_scene: Scene):
       # Only cleanup if current scene exists (first set_scene() has no scene to dispose)
       if self._current is not None:
           # Call on_exit() as before
           self._current.on_exit()
           
           # Null out references to allow GC
           self._current = None
           
           # Delete fade surface if it exists
           if hasattr(self, '_fade_surface') and self._fade_surface is not None:
               del self._fade_surface
               self._fade_surface = None
       
       # Set new scene
       self._current = new_scene
       self._current.on_enter()
   ```

2. **Add dispose() Method for Testing**:
   ```python
   @classmethod
   def dispose(cls):
       """Dispose of singleton instance for testing. Replaces monkey-patching."""
       if cls._instance is not None:
           if cls._instance._current is not None:
               cls._instance._current.on_exit()
           cls._instance = None
   ```

3. **Update Scene on_exit() Methods**:
   - Ensure each scene's on_exit() nulls out heavy references:
     - GameState references
     - Pygame Surfaces
     - UI component references

**Why This Works**:
- Explicit cleanup breaks reference cycles
- Nulling references allows Python GC to reclaim memory
- dispose() method provides clean testing isolation without monkey-patching
- First set_scene() check prevents null scene operations

### Bug 4: ShopController.handle_phase_change() Not Atomic

**File**: `v2/core/shop_controller.py`

**Function**: `handle_phase_change()`

**Specific Changes**:

1. **Wrap Phase Transition in try/except**:
   ```python
   def handle_phase_change(self, new_phase: str):
       # Store previous phase for rollback
       # Note: GameState doesn't expose phase directly, so we get it from PublicState
       previous_phase = self._game_state.get_public_state().phase
       
       try:
           # Execute phase transition sequence
           if new_phase == "STATE_PREPARATION":
               self._game_state.mirror_phase(new_phase)
               self.cleanup_dead_cards()
               self._game_state.start_turn()
               self._game_state.reset_turn()
           # ... other phase transitions ...
           
       except Exception as e:
           # Rollback: restore phase to previous value
           # We need to call mirror_phase() again to restore the phase
           # Engine-level mutations (board, market) are NOT rolled back
           # They are idempotent or logged, so partial execution is acceptable
           self._game_state.mirror_phase(previous_phase)
           
           # Re-raise exception for logging/debugging
           raise
   ```

2. **Document Rollback Scope**:
   - Add comment explaining that only StateStore._phase is rolled back
   - Engine-level mutations (board changes, market updates) are NOT undone
   - This is intentional: they are idempotent or logged

**Why This Works**:
- try/except catches any exception during phase transition sequence
- Storing previous_phase allows restoration on exception
- Only StateStore._phase is rolled back (engine mutations are idempotent/logged)
- Re-raising exception preserves error visibility for debugging
- No full transaction pattern needed (PhaseTransactionContext optional)

### Bug 5: frozen=True Dataclass with Mutable Dicts

**File**: `v2/adapters/ui_adapter.py` (or wherever ActivePlayerViewState is defined)

**Class**: `ActivePlayerViewState`

**Specific Changes**:

1. **Import MappingProxyType**:
   ```python
   from types import MappingProxyType
   ```

2. **Wrap Dicts in __post_init__()**:
   ```python
   @dataclass(frozen=True)
   class ActivePlayerViewState:
       stats: Dict[str, Any]
       board_cards: Dict[Coord, Dict[str, Any]]
       copies_by_name: Dict[str, int]
       shop_card_info: Dict[int, Optional[CardData]]
       hand_card_info: Dict[int, Optional[CardData]]
       board_card_info: Dict[Coord, Optional[CardData]]
       # ... other fields ...
       
       def __post_init__(self):
           # Wrap simple dicts with MappingProxyType
           object.__setattr__(self, 'stats', MappingProxyType(self.stats))
           object.__setattr__(self, 'copies_by_name', MappingProxyType(self.copies_by_name))
           object.__setattr__(self, 'shop_card_info', MappingProxyType(self.shop_card_info))
           object.__setattr__(self, 'hand_card_info', MappingProxyType(self.hand_card_info))
           object.__setattr__(self, 'board_card_info', MappingProxyType(self.board_card_info))
           
           # Wrap nested dicts (both outer and inner) with MappingProxyType
           object.__setattr__(
               self,
               'board_cards',
               MappingProxyType({k: MappingProxyType(v) for k, v in self.board_cards.items()})
           )
   ```

3. **Handle All Dict Fields Correctly**:
   - **Simple dicts** (wrap with single MappingProxyType):
     - `stats: Dict[str, Any]`
     - `copies_by_name: Dict[str, int]`
     - `shop_card_info: Dict[int, Optional[CardData]]`
     - `hand_card_info: Dict[int, Optional[CardData]]`
     - `board_card_info: Dict[Coord, Optional[CardData]]`
   
   - **Nested dicts** (wrap both outer and inner with MappingProxyType):
     - `board_cards: Dict[Coord, Dict[str, Any]]` - requires both levels wrapped

**Why This Works**:
- MappingProxyType creates a read-only proxy for dicts
- Attempts to mutate (e.g., `stats["bonus"] = 99`) raise TypeError
- __post_init__() runs after __init__(), allowing modification of frozen dataclass
- object.__setattr__() bypasses frozen=True restriction during initialization
- Nested dict wrapping ensures both levels are immutable
- Save/Load system can only serialize immutable data

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fixes. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

#### Bug 1: UIAdapter.build_public_state() Performance Leak

**Test Plan**: Write tests that trigger economy_changed, inventory_changed, and turn_started signals, then measure whether SynergyCalculator.compute() BFS is called. Run these tests on the UNFIXED code to observe unnecessary BFS runs.

**Test Cases**:
1. **Economy Change Test**: Trigger economy_changed signal → Measure if BFS runs → Verify board unchanged (will fail on unfixed code - BFS runs unnecessarily)
2. **Inventory Change Test**: Trigger inventory_changed signal → Measure if BFS runs → Verify board unchanged (will fail on unfixed code - BFS runs unnecessarily)
3. **Turn Start Test**: Trigger turn_started signal → Measure if BFS runs → Verify board unchanged (will fail on unfixed code - BFS runs unnecessarily)
4. **Multiple Signal Test**: Trigger 15-20 signals in sequence → Measure total BFS runs → Verify performance degradation (will fail on unfixed code - multiple BFS runs)

**Expected Counterexamples**:
- SynergyCalculator.compute() is called when economy_changed fires (board unchanged)
- SynergyCalculator.compute() is called when inventory_changed fires (board unchanged)
- SynergyCalculator.compute() is called when turn_started fires (board unchanged)
- Possible causes: monolithic cache, no signal-to-cache mapping, overly aggressive invalidation

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

**Test Plan**: Write tests that simulate hand card clicks, then verify whether EngineAdapter.get_card_info() is called despite cached data existing. Run these tests on the UNFIXED code to observe redundant DB lookups.

**Test Cases**:
1. **Single Click Test**: Click hand card → Verify get_card_info() called → Verify cached data exists (will fail on unfixed code - redundant call)
2. **Multiple Click Test**: Click same card twice → Verify get_card_info() called twice → Verify cached data exists (will fail on unfixed code - redundant calls)
3. **Rapid Click Test**: Click multiple hand cards rapidly → Count get_card_info() calls → Verify all cached (will fail on unfixed code - multiple redundant calls)
4. **Cache Hit Test**: Verify _public_state.active_player.hand_card_info contains card data before click (will pass - confirms cache exists)

**Expected Counterexamples**:
- EngineAdapter.get_card_info() is called even when cached data exists
- New CardDataSnapshot objects are created unnecessarily
- Possible causes: cache unawareness, direct DB access pattern, missing cache accessor

#### Bug 3: SceneManager Singleton Memory Leak

**Test Plan**: Write tests that perform multiple scene transitions (Main Menu → Game → Main Menu), then measure RAM usage and verify old scene references survive. Run these tests on the UNFIXED code to observe memory leak.

**Test Cases**:
1. **Single Transition Test**: Main Menu → Game → Measure RAM → Verify old scene not GC'd (will fail on unfixed code - memory leak)
2. **Multiple Transition Test**: 3-4 scene transitions → Measure RAM growth → Verify RAM explosion (will fail on unfixed code - RAM increases)
3. **Reference Survival Test**: Transition scenes → Check if old GameState references survive → Verify GC blocked (will fail on unfixed code - references survive)
4. **First Transition Test**: First set_scene() call with no old scene → Verify no null scene operations (edge case - should pass)

**Expected Counterexamples**:
- Old scene's GameState, Pygame Surfaces, and UI components are not GC'd
- RAM increases with each scene transition
- SceneManager._instance holds strong references preventing GC
- Possible causes: singleton holds references, incomplete cleanup, no explicit disposal

#### Bug 4: ShopController.handle_phase_change() Not Atomic

**Test Plan**: Write tests that inject exceptions during phase transition sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn), then verify phase state is inconsistent. Run these tests on the UNFIXED code to observe partial execution.

**Test Cases**:
1. **Exception in cleanup_dead_cards Test**: mirror_phase() succeeds → cleanup_dead_cards() throws → Verify phase already mirrored but turn not started (will fail on unfixed code - inconsistent state)
2. **Exception in start_turn Test**: mirror_phase() + cleanup_dead_cards() succeed → start_turn() throws → Verify phase inconsistent (will fail on unfixed code - inconsistent state)
3. **Exception in reset_turn Test**: All steps succeed except reset_turn() → Verify phase inconsistent (will fail on unfixed code - inconsistent state)
4. **No Exception Test**: All steps succeed → Verify phase transitions correctly (should pass - confirms normal flow works)

**Expected Counterexamples**:
- Phase is modified before sequence completes
- Exception leaves phase in inconsistent state (mirrored but turn not started)
- No rollback mechanism exists
- Possible causes: no exception handling, phase modified early, no rollback logic

#### Bug 5: frozen=True Dataclass with Mutable Dicts

**Test Plan**: Write tests that attempt to mutate dict contents in ActivePlayerViewState (e.g., state.active_player.stats["bonus"] = 99), then verify mutation is allowed despite frozen=True. Run these tests on the UNFIXED code to observe immutability bypass.

**Test Cases**:
1. **Simple Dict Mutation Test**: state.active_player.stats["bonus"] = 99 → Verify mutation allowed (will fail on unfixed code - mutation succeeds)
2. **Nested Dict Mutation Test**: state.active_player.board_cards[coord]["hp"] = 999 → Verify mutation allowed (will fail on unfixed code - mutation succeeds)
3. **Cache Invalidation Test**: Mutate dict → Verify cache not invalidated → Verify stale data (will fail on unfixed code - cache not invalidated)
4. **Serialization Test**: Mutate dict → Serialize state → Verify temporary data persists (will fail on unfixed code - temporary data serialized)

**Expected Counterexamples**:
- Dict contents can be mutated despite frozen=True
- frozen=True only prevents attribute assignment, not dict mutation
- No MappingProxyType wrapping exists
- Possible causes: frozen=True limitation, mutable dict references, no immutability enforcement

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed functions produce the expected behavior.

#### Bug 1: UIAdapter.build_public_state() Performance Leak

**Pseudocode:**
```
FOR ALL signal WHERE signal IN [economy_changed, inventory_changed, turn_started] DO
  trigger_signal(signal)
  ASSERT SynergyCalculator.compute() NOT called
  ASSERT only relevant cache invalidated
END FOR

FOR ALL signal WHERE signal == board_mutated DO
  trigger_signal(signal)
  ASSERT SynergyCalculator.compute() IS called
  ASSERT _cached_synergy + _cached_board invalidated
END FOR
```

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

**Pseudocode:**
```
FOR ALL hand_card_click WHERE cached_data_exists DO
  result := handle_click_fixed(hand_card_click)
  ASSERT EngineAdapter.get_card_info() NOT called
  ASSERT cached data used
END FOR
```

#### Bug 3: SceneManager Singleton Memory Leak

**Pseudocode:**
```
FOR ALL scene_transition WHERE old_scene EXISTS DO
  initial_ram := measure_ram()
  set_scene_fixed(new_scene)
  final_ram := measure_ram()
  ASSERT old_scene references cleared
  ASSERT final_ram - initial_ram < threshold
END FOR
```

#### Bug 4: ShopController.handle_phase_change() Not Atomic

**Pseudocode:**
```
FOR ALL phase_transition WHERE exception_thrown DO
  previous_phase := state_store.phase
  TRY
    handle_phase_change_fixed(new_phase)
  CATCH Exception
    ASSERT state_store.phase == previous_phase
  END TRY
END FOR
```

#### Bug 5: frozen=True Dataclass with Mutable Dicts

**Pseudocode:**
```
FOR ALL mutation_attempt WHERE target == frozen_dataclass_dict DO
  TRY
    state.active_player.stats["bonus"] = 99
    FAIL "Should have raised TypeError"
  CATCH TypeError
    ASSERT mutation prevented
  END TRY
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed functions produce the same result as the original functions.

#### Bug 1: UIAdapter.build_public_state() Performance Leak

**Pseudocode:**
```
FOR ALL build_public_state_call WHERE no_cache_exists DO
  result_original := build_public_state_original()
  result_fixed := build_public_state_fixed()
  ASSERT result_original == result_fixed
  ASSERT synergy calculations correct
  ASSERT shop/hand/board data correct
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for full state computation (no cache), then write unit tests capturing that behavior.

**Test Cases**:
1. **Full State Computation Preservation**: Call build_public_state() with no cache → Verify complete state computed correctly
2. **Synergy Calculation Preservation**: Verify synergy data matches original implementation
3. **Shop/Hand/Board Data Preservation**: Verify card data matches original implementation

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call

**Pseudocode:**
```
FOR ALL card_click WHERE card_click triggers game_action DO
  result_original := handle_click_original(card_click)
  result_fixed := handle_click_fixed(card_click)
  ASSERT result_original == result_fixed
  ASSERT game actions (drag, play, sell) work correctly
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for card click actions, then write unit tests capturing that behavior.

**Test Cases**:
1. **Card Click Actions Preservation**: Verify drag, play, sell actions work correctly after fix
2. **Other Mouse Events Preservation**: Verify board clicks, shop clicks, drag operations work correctly
3. **Card Data Accuracy Preservation**: Verify cached data matches DB data

#### Bug 3: SceneManager Singleton Memory Leak

**Pseudocode:**
```
FOR ALL scene_transition WHERE scene_transition is normal DO
  result_original := set_scene_original(new_scene)
  result_fixed := set_scene_fixed(new_scene)
  ASSERT result_original == result_fixed
  ASSERT on_exit() called on old scene
  ASSERT scenes render and update correctly
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for normal scene transitions, then write unit tests capturing that behavior.

**Test Cases**:
1. **Scene Lifecycle Preservation**: Verify on_exit(), on_enter(), update(), render() work correctly
2. **Scene Transition Preservation**: Verify transitions work correctly after fix
3. **First Transition Preservation**: Verify first set_scene() call works correctly (no old scene to cleanup)

#### Bug 4: ShopController.handle_phase_change() Not Atomic

**Pseudocode:**
```
FOR ALL phase_transition WHERE no_exception_thrown DO
  result_original := handle_phase_change_original(new_phase)
  result_fixed := handle_phase_change_fixed(new_phase)
  ASSERT result_original == result_fixed
  ASSERT sequence executes correctly
  ASSERT game state updated correctly
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for successful phase transitions, then write unit tests capturing that behavior.

**Test Cases**:
1. **Successful Phase Transition Preservation**: Verify sequence (mirror_phase → cleanup_dead_cards → start_turn → reset_turn) executes correctly
2. **Phase State Update Preservation**: Verify game state updated correctly after transition
3. **Other ShopController Methods Preservation**: Verify other methods work correctly after fix

#### Bug 5: frozen=True Dataclass with Mutable Dicts

**Pseudocode:**
```
FOR ALL dataclass_operation WHERE operation is read_access DO
  result_original := access_attribute_original(state.active_player.stats)
  result_fixed := access_attribute_fixed(state.active_player.stats)
  ASSERT result_original == result_fixed
  ASSERT equality checks work correctly
  ASSERT hashing works correctly
  ASSERT serialization works correctly
END FOR
```

**Testing Approach**: Multiple explicit unit tests are recommended for preservation checking because:
- They cover the most common and critical use cases
- They are easier to debug when failures occur
- They don't require additional dependencies (hypothesis is not installed)

**Test Plan**: Observe behavior on UNFIXED code first for dataclass read access, then write unit tests capturing that behavior.

**Test Cases**:
1. **Dataclass Read Access Preservation**: Verify read access to stats, board_cards, copies_by_name works correctly
2. **Dataclass Operations Preservation**: Verify equality checks, hashing, serialization work correctly
3. **Dataclass Creation Preservation**: Verify ActivePlayerViewState creation works correctly with valid data

### Unit Tests

#### Bug 1: UIAdapter.build_public_state() Performance Leak
- Test economy_changed signal only invalidates _cached_hud
- Test inventory_changed signal only invalidates _cached_hand
- Test turn_started signal only invalidates _cached_shop
- Test board_mutated signal invalidates _cached_synergy + _cached_board and triggers BFS
- Test multiple signals in sequence (15-20) with performance measurement
- Test full state computation when no cache exists

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call
- Test hand card click uses cached data
- Test multiple clicks on same card use cached data
- Test rapid clicks on multiple cards use cached data
- Test cache miss fallback (edge case)
- Test card click actions (drag, play, sell) work correctly

#### Bug 3: SceneManager Singleton Memory Leak
- Test set_scene() cleans up old scene when it exists
- Test first set_scene() call with no old scene (no cleanup)
- Test multiple scene transitions (3-4) with RAM measurement
- Test dispose() method for testing isolation
- Test scene lifecycle methods (on_exit, on_enter, update, render) work correctly

#### Bug 4: ShopController.handle_phase_change() Not Atomic
- Test exception in cleanup_dead_cards() restores phase
- Test exception in start_turn() restores phase
- Test exception in reset_turn() restores phase
- Test successful phase transition executes sequence correctly
- Test phase state is consistent after exception

#### Bug 5: frozen=True Dataclass with Mutable Dicts
- Test simple dict mutation raises TypeError
- Test nested dict mutation raises TypeError
- Test read access to dicts works correctly
- Test dataclass operations (equality, hashing, serialization) work correctly
- Test MappingProxyType wrapping for both outer and inner dicts

### Property-Based Tests

**NOTE**: Property-based testing with `hypothesis` is NOT currently set up in this project. The following test cases should be implemented as standard unit tests with multiple explicit test cases covering the input domain. If property-based testing is desired in the future, add `pytest-hypothesis` to `requirements.txt` and configure `pytest.ini`.

#### Bug 1: UIAdapter.build_public_state() Performance Leak
- **Unit Test Approach**: Create multiple explicit test cases with different signal patterns
- Test case 1: economy_changed only → Verify BFS not called
- Test case 2: inventory_changed only → Verify BFS not called
- Test case 3: turn_started only → Verify BFS not called
- Test case 4: board_mutated only → Verify BFS called
- Test case 5: Mixed signals (15-20) → Verify BFS called only for board_mutated

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call
- **Unit Test Approach**: Create multiple explicit test cases with different click patterns
- Test case 1: Single click with cached data → Verify no DB call
- Test case 2: Multiple clicks on same card → Verify no DB calls
- Test case 3: Rapid clicks on different cards → Verify no DB calls
- Test case 4: Click with cache miss → Verify fallback works

#### Bug 3: SceneManager Singleton Memory Leak
- **Unit Test Approach**: Create multiple explicit test cases with different transition patterns
- Test case 1: Single transition → Verify cleanup
- Test case 2: Multiple transitions (3-4) → Verify RAM stable
- Test case 3: First transition → Verify no null scene operations
- Test case 4: dispose() call → Verify singleton reset

#### Bug 4: ShopController.handle_phase_change() Not Atomic
- **Unit Test Approach**: Create multiple explicit test cases with different exception points
- Test case 1: Exception in cleanup_dead_cards → Verify phase restored
- Test case 2: Exception in start_turn → Verify phase restored
- Test case 3: Exception in reset_turn → Verify phase restored
- Test case 4: No exception → Verify sequence completes

#### Bug 5: frozen=True Dataclass with Mutable Dicts
- **Unit Test Approach**: Create multiple explicit test cases with different mutation attempts
- Test case 1: Mutate stats dict → Verify TypeError
- Test case 2: Mutate board_cards outer dict → Verify TypeError
- Test case 3: Mutate board_cards inner dict → Verify TypeError
- Test case 4: Read access → Verify works correctly

### Integration Tests

#### Bug 1: UIAdapter.build_public_state() Performance Leak
- Test full game flow with multiple turns and signal patterns
- Test performance across 10+ turns with AI purchases and income
- Test that synergy calculations remain correct after fix
- Test that UI displays correct data after fix

#### Bug 2: MOUSEBUTTONDOWN Redundant get_card_info() Call
- Test full game flow with hand card interactions
- Test that card clicks trigger correct game actions
- Test that card data remains accurate across multiple turns
- Test that other mouse events (board, shop) work correctly

#### Bug 3: SceneManager Singleton Memory Leak
- Test full game flow with multiple scene transitions (Main Menu → Game → Main Menu loop)
- Test that RAM remains stable across 5+ transitions
- Test that scenes render correctly after transitions
- Test that game state is preserved correctly across transitions

#### Bug 4: ShopController.handle_phase_change() Not Atomic
- Test full game flow with phase transitions
- Test that exceptions during phase transitions don't corrupt game state
- Test that phase guards work correctly after fix
- Test that game continues normally after exception recovery

#### Bug 5: frozen=True Dataclass with Mutable Dicts
- Test full game flow with state serialization and deserialization
- Test that state remains immutable across multiple turns
- Test that Save/Load system works correctly with immutable dicts
- Test that UI cannot corrupt state through mutation attempts

