# Scene-Based Architecture Migration

## Overview

This document describes the migration of the monolithic `run_game.py` (730+ lines) into a modular Scene-based architecture. The migration decomposes the single-file game loop into specialized scenes while preserving all existing functionality.

## Migration Status

**Current Phase**: Phase 4 - Cleanup & Finalization (In Progress)

### Completed Phases

- ✅ **Phase 1**: Game Bootstrap (Minimum Playable) - 14 tasks
- ✅ **Phase 2**: Turn System Integration - 7 tasks  
- ✅ **Phase 3**: Combat Loop Integration - 9 tasks
- 🔄 **Phase 4**: Cleanup & Finalization - 5 tasks (4/5 complete)

## Architecture Overview

### Scene Hierarchy

```
SceneManager
├── LobbyScene          # Strategy selection
├── GameLoopScene       # Turn orchestration hub (NEW)
├── ShopScene           # Card purchasing
├── CombatScene         # Card placement on hex board
└── GameOverScene       # Winner display and restart (NEW)
```

### Scene Transition Flow

```
Lobby → GameLoop → Shop → Combat → GameLoop → GameOver
  ↑                                              ↓
  └──────────────── Restart ────────────────────┘
```

## Scene Responsibilities

### GameLoopScene (NEW)
**Purpose**: Central hub for turn orchestration and game flow control

**Responsibilities**:
- Turn counter display and advancement
- Player switching UI (1-8 keys + clickable panel)
- Fast mode toggle and auto-advance timer
- Combat results popup display
- Game over detection
- Scene transition orchestration

**State**:
- UIState: `fast_timer`, `popup_timer`, `popup_data`, `last_breakdown`, `game_over`, `winner`, `status_msg`

### CombatScene (ENHANCED)
**Purpose**: Card placement on 37-hex board

**Responsibilities**:
- Hex board visualization (using HexSystem)
- Hand panel display (horizontal bottom bar, 175px height)
- Card selection and rotation
- Placement limit enforcement (1 per turn)
- Locked coordinates tracking
- Placement preview with rotation
- Passive buff panel and synergy HUD (left sidebar)

**State**:
- UIState: `selected_hand_idx`, `pending_rotation`, `placed_this_turn`

### ShopScene (EXISTING)
**Purpose**: Card purchasing from market

**Responsibilities**:
- Market card display
- Card buying logic
- Hand buffer display
- Refresh button
- Interest application on exit

### GameOverScene (NEW)
**Purpose**: Winner display and game restart

**Responsibilities**:
- Winner announcement
- Final stats display
- Restart button (returns to Lobby)
- Quit button

### LobbyScene (EXISTING)
**Purpose**: Strategy selection

**Responsibilities**:
- Strategy selection UI
- Handoff strategies to GameLoopScene via transition kwargs

## State Management Rules

### CoreGameState (SAVEABLE)
**Contains ONLY saveable state that persists across scenes**:
- `game: Game` - Game instance
- `view_player_index: int` - Currently viewed player
- `fast_mode: bool` - Game speed setting
- `locked_coords_per_player: Dict[int, Set[Tuple[int, int]]]` - Immutable placed cards

**Accessor Properties**:
- `current_player` - Returns `game.players[view_player_index]`
- `turn` - Returns `game.turn`
- `alive_players` - Returns `[p for p in game.players if p.hp > 0]`

### UIState (THROWAWAY)
**Contains scene-specific state that is discarded on scene exit**:
- Animations, timers, selections, hovers
- Each scene has its own UIState dataclass
- Cleared in `on_exit()` to free memory

### Critical Rules
1. **NO STATE DUPLICATION**: CoreGameState is passed by reference, never copied
2. **SAME OBJECT IDENTITY**: CoreGameState maintains the same object reference across all scenes
3. **CLEAR SEPARATION**: SAVEABLE state in CoreGameState, THROWAWAY state in UIState
4. **LIFECYCLE MANAGEMENT**: UIState is created in `on_enter()`, cleared in `on_exit()`

## Key Components

### HUDRenderer (`ui/hud_renderer.py`)
Utility class for rendering UI elements extracted from `run_game.py`:
- `draw_cyber_victorian_hud()` - Top HUD with turn/gold/HP
- `draw_player_panel()` - Right sidebar with all players
- `draw_player_info()` - Left sidebar with current player details
- `draw_combat_breakdown()` - Combat results breakdown
- `draw_turn_popup()` - Animated combat results popup
- `draw_game_over()` - Winner announcement
- `draw_passive_buff_panel()` - Passive buff log
- `draw_synergy_hud()` - Active synergy badges

### HandPanel (`ui/hand_panel.py`)
Horizontal bottom bar for hand card display in CombatScene:
- 6 hex-shaped card slots (88px width each, 8px gap)
- Detail panel (320px width) showing selected card info
- Visual features: rarity accent, passive indicator, group color, power label, rotation badge
- Header row: "HAND BUFFER" / "CARDS X/6" / "PLACED X/1" / "TURN N" / hints

### InputState (ENHANCED)
Intent-based input handling with named mappings:
- `INTENT_TOGGLE_FAST_MODE` (F key)
- `INTENT_OPEN_SHOP` (S key)
- `INTENT_SWITCH_PLAYER_1` through `INTENT_SWITCH_PLAYER_8` (1-8 keys)
- Methods: `is_fast_mode_toggled()`, `is_shop_requested()`, `get_player_switch_request()`

## Migration Phases

### Phase 1: Game Bootstrap (Minimum Playable)
**Goal**: Create GameLoopScene and establish basic turn flow

**Key Tasks**:
1. Add `locked_coords_per_player` to CoreGameState
2. Extract drawing functions to `ui/hud_renderer.py`
3. Resolve render system conflict (HexSystem vs BoardRendererV3)
4. Define Lobby → GameLoop strategy handoff protocol
5. Create GameLoopScene class skeleton
6. Implement game_over detection and winner tracking
7. Move turn orchestration logic to GameLoopScene
8. Implement basic GameLoopScene UI
9. Register GameLoopScene and GameOverScene factories
10. Wire scene transition chain
11. Move turn orchestration logic to GameLoopScene
12. Implement human player preparation phase
13. Implement combat phase triggering
14. Integration test: Full turn cycle

**Checkpoint**: Can complete one full turn cycle (Lobby → GameLoop → Shop → Combat → GameLoop)

### Phase 2: Turn System Integration
**Goal**: Integrate fast mode, player switching, and combat results display

**Key Tasks**:
1. Extend InputState with named intent mappings
2. Add fast mode toggle and timer to GameLoopScene
3. Add player switching via 1-8 keys and clickable panel
4. Add combat results popup to GameLoopScene
5. Implement AI player economy and placement phases
6. Implement conditional shop skip for fast mode
7. Integration test: Fast mode and player switching

**Checkpoint**: Fast mode auto-advances turns every 600ms, player switching works, combat results popup displays

### Phase 3: Combat Loop Integration
**Goal**: Integrate card placement, hand panel, and locked coordinates into CombatScene

**Key Tasks**:
1. Assign PassiveBuffPanel and SynergyHUD to CombatScene (left sidebar)
2. Add hand panel to CombatScene (horizontal bottom bar)
3. Move card selection logic to CombatScene
4. Move placement limit enforcement to CombatScene
5. Move locked coordinates tracking to CombatScene
6. Integrate placement preview with existing HexSystem
7. Move build_game to `engine_core/game_factory.py`
8. Implement restart flow in GameOverScene
9. Integration test: Card placement flow

**Checkpoint**: CombatScene displays hand panel, allows card selection/rotation, enforces placement limit, tracks locked coordinates

### Phase 4: Cleanup & Finalization
**Goal**: Remove run_game.py dependencies and finalize migration

**Key Tasks**:
1. Add backward compatibility flag to main.py
2. Remove run_game.py imports from all scenes
3. Deprecate BoardRendererV3 in favor of HexSystem
4. Final integration test: Full game playthrough
5. Update documentation and deprecation notices

**Checkpoint**: Scene-based architecture is fully functional, run_game.py is deprecated

## Testing Strategy

### Unit Tests
- CoreGameState accessor methods
- HUDRenderer drawing functions
- HandPanel click detection
- InputState intent mappings
- Placement limit enforcement
- Locked coordinates tracking

### Integration Tests
- Full turn cycle (Lobby → GameLoop → Shop → Combat → GameLoop)
- Fast mode auto-advance
- Player switching (keyboard + mouse)
- Combat results popup display
- Card placement flow
- Game over detection and restart

### Property-Based Tests
- Turn monotonicity: `turn_after >= turn_before`
- Placement limit: `placed_this_turn <= PLACE_PER_TURN`
- Locked coordinates immutability: `locked_coords_after >= locked_coords_before`
- State persistence: `CoreGameState object identity unchanged across scenes`

### Manual Tests
- Visual consistency with run_game.py
- Performance (60 FPS target)
- UI responsiveness
- Scene transition smoothness

## Known Issues and Limitations

### Resolved
- ✅ Render system conflict (HexSystem vs BoardRendererV3) - Resolved: Use HexSystem
- ✅ Lobby → GameLoop strategy handoff - Resolved: Use transition kwargs
- ✅ PassiveBuffPanel and SynergyHUD ownership - Resolved: Assigned to CombatScene
- ✅ AI turn logic migration - Resolved: Extracted to GameLoopScene.process_ai_turns()
- ✅ Restart flow - Resolved: GameOverScene transitions to Lobby

### Pending
- Player switching during shop: Currently disabled (shop must complete first)
- Fast mode visual feedback: Lightning bolt icon not yet implemented

## Backward Compatibility

### Feature Flag
`main.py` provides a feature flag `USE_SCENE_ARCHITECTURE` to switch between old and new systems:
- `USE_SCENE_ARCHITECTURE = True`: Use SceneManager with GameLoopScene (NEW)
- `USE_SCENE_ARCHITECTURE = False`: Call `run_game.main()` directly (LEGACY)

### Deprecation Timeline
1. **Phase 4 (Current)**: Both systems functional, flag available
2. **Phase 5 (Future)**: Scene-based architecture becomes default
3. **Phase 6 (Future)**: run_game.py removed entirely

## Developer Guidelines

### Adding New Scenes
1. Extend `Scene` base class
2. Define scene-specific UIState dataclass
3. Implement `on_enter()`, `on_exit()`, `update()`, `draw()`, `handle_input()`
4. Register factory in `main.py`
5. Wire transitions in adjacent scenes

### State Management
1. **SAVEABLE state**: Add to CoreGameState
2. **THROWAWAY state**: Add to scene's UIState
3. **Derived state**: Use CoreGameState accessor properties
4. **Never copy CoreGameState**: Always pass by reference

### Scene Transitions
1. Call `self.scene_manager.transition_to(scene_name, **kwargs)`
2. Pass data via kwargs (e.g., strategies, results)
3. Defer transitions until safe points (before update)
4. Clean up UIState in `on_exit()`

### Rendering
1. Reuse HUDRenderer functions for common UI elements
2. Use HexSystem for board rendering
3. Cache font renders for static text
4. Use dirty rectangle optimization for partial updates

## References

- **Spec Files**: `.kiro/specs/run-game-scene-integration/`
  - `requirements.md` - Functional requirements (30 requirements)
  - `design.md` - Architecture design and gap analysis
  - `tasks.md` - Implementation tasks (39 tasks across 4 phases)
- **Source Files**:
  - `scenes/game_loop_scene.py` - GameLoopScene implementation
  - `scenes/game_over_scene.py` - GameOverScene implementation
  - `ui/hud_renderer.py` - HUD rendering utilities
  - `ui/hand_panel.py` - Hand panel component
  - `engine_core/game_factory.py` - Game initialization
  - `main.py` - Scene factory registration and feature flag

## Contact

For questions about the migration, refer to:
- Design document: `.kiro/specs/run-game-scene-integration/design.md`
- Requirements document: `.kiro/specs/run-game-scene-integration/requirements.md`
- Task list: `.kiro/specs/run-game-scene-integration/tasks.md`
