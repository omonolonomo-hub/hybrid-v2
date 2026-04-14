# Implementation Tasks: run-game-scene-integration

## Overview

This document contains the implementation tasks for migrating the monolithic `run_game.py` (730+ lines) into the Scene-based architecture. The migration is divided into 4 phases with 39 total tasks, each designed to be 10-45 minutes of work.

## Task Format

Each task follows this format:
- `[ ] TX.N — Title`: Task checkbox with phase and number
- **Files**: Files to modify
- **What**: Detailed description of what to implement
- **Why**: Rationale for the task
- **Gap**: Which gap from gap analysis this addresses (if applicable)
- **Blocked by**: Dependencies (must complete before this task)
- **Test**: How to verify the task is complete

## Phase Summary

- **Phase 1**: Game Bootstrap (Minimum Playable) - 14 tasks
- **Phase 2**: Turn System Integration - 7 tasks
- **Phase 3**: Combat Loop Integration - 9 tasks
- **Phase 4**: Cleanup & Finalization - 5 tasks

---

## Phase 1: Game Bootstrap (Minimum Playable)

**Goal**: Create GameLoopScene and establish basic turn flow

### Tasks

**Priority 1: Visibility (Rendering/UI must exist first)**

- [x] T1.1 — Add locked_coords_per_player to CoreGameState
  - **Files**: `core/core_game_state.py`
  - **What**: Add `locked_coords_per_player: Dict[int, Set[Tuple[int, int]]]` field to `CoreGameState.__init__()`. Add `clear_locked_coords(player_id: int)` method that clears the set for the given player ID. Initialize with `{p.pid: set() for p in game.players}` when CoreGameState is created. NOTE: Accessor methods (`current_player`, `turn`, `alive_players`) already exist as properties — do NOT re-implement them.
  - **Why**: Locked coordinates need to persist across scene transitions (Combat → GameLoop → Combat)
  - **Gap**: G2 (CoreGameState missing locked_coords_per_player)
  - **Blocked by**: None
  - **Test**: Verify field exists and `clear_locked_coords()` works for all player IDs

- [x] T1.2 — Extract drawing functions to ui/hud_renderer.py
  - **Files**: `ui/hud_renderer.py` (new), `run_game.py`
  - **What**: Create new file `ui/hud_renderer.py`. Extract these functions from `run_game.py`: `_draw_cv_hud()` → `draw_cyber_victorian_hud()`, `_draw_player_panel()` → `draw_player_panel()`, `_draw_player_info()` → `draw_player_info()`, `_draw_combat_breakdown()` → `draw_combat_breakdown()`, `_draw_turn_popup()` → `draw_turn_popup()`, `_draw_game_over()` → `draw_game_over()`, `_draw_passive_buff_panel()` → `draw_passive_buff_panel()`, `_draw_synergy_hud()` → `draw_synergy_hud()`, `_active_synergy_counts()` → helper function, `hp_color()` → helper function. Keep function signatures compatible with existing calls. Add HUDRenderer class to encapsulate state (fonts, colors).
  - **Why**: GameLoopScene and CombatScene need to render HUD elements
  - **Gap**: G4 (HUDRenderer extraction mentioned but not tasked)
  - **Blocked by**: None
  - **Test**: Import and call each function, verify visual output matches run_game.py

- [x] T1.4 — Define Lobby → GameLoop strategy handoff protocol
  - **Files**: `scenes/lobby_scene.py`, `scenes/game_loop_scene.py`, `main.py`
  - **What**: Protocol Decision: Use scene transition kwargs for strategy passing. `LobbyScene.on_exit()` stores selected strategies in transition kwargs: `{"strategies": selected_strategies}`. SceneManager passes kwargs to GameLoopScene factory. GameLoopScene factory calls `build_game(strategies)` and creates CoreGameState. CRITICAL: Currently `build_game()` is called in ShopScene factory in main.py — this will be moved to GameLoopScene factory. ShopScene will receive an already-initialized CoreGameState.
  - **Why**: Strategies need to flow from Lobby to GameLoop without circular dependencies
  - **Gap**: G3 (Lobby → GameLoop strategy handoff protocol undefined)
  - **Blocked by**: None
  - **Test**: Verify strategies flow from Lobby → build_game() → GameLoopScene

- [x] T1.5 — Create GameLoopScene class skeleton
  - **Files**: `scenes/game_loop_scene.py` (new)
  - **What**: Create GameLoopScene class extending Scene. Implement `__init__(core_game_state, **kwargs)` constructor. Create GameLoopUIState dataclass with fields: `fast_timer: int = 0`, `popup_timer: int = 0`, `popup_data: List[dict] = []`, `last_breakdown: dict = None`, `game_over: bool = False`, `winner: Player = None`, `status_msg: str = ""`. Implement `on_enter()` and `on_exit()` lifecycle methods.
  - **Why**: GameLoopScene is the central hub for turn orchestration
  - **Gap**: None (core component)
  - **Blocked by**: T1.1, T1.2, T1.4
  - **Test**: Verify scene can be instantiated and entered

- [x] T1.8 — Implement basic GameLoopScene UI
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: Use HUDRenderer functions from T1.2. Display turn counter at top. Display player list with HP/status (reuse `draw_player_panel`). Add "ADVANCE TURN" button or SPACE key prompt. Render in `GameLoopScene.draw()` method.
  - **Why**: Players need to see game state and advance turns
  - **Gap**: None (core feature)
  - **Blocked by**: T1.2 (HUDRenderer), T1.5 (GameLoopScene)
  - **Test**: Verify UI elements render correctly

**Priority 2: Flow (Scene transitions must work before logic)**

- [x] T1.9 — Register GameLoopScene and GameOverScene factories in main.py
  - **Files**: `main.py`
  - **What**: Add factory registration: `scene_manager.register_scene_factory("game_loop", create_game_loop_scene)`. Add factory registration: `scene_manager.register_scene_factory("game_over", create_game_over_scene)`. Implement `create_game_loop_scene(core_game_state, **kwargs)` factory function. Implement `create_game_over_scene(core_game_state, **kwargs)` factory function.
  - **Why**: SceneManager needs factories to create scenes dynamically
  - **Gap**: G1 (main.py missing "game_loop" and "game_over" factory registrations)
  - **Blocked by**: T1.5 (GameLoopScene class exists)
  - **Test**: Verify factories are registered and can create scenes

- [x] T1.10 — Wire scene transition chain
  - **Files**: `scenes/lobby_scene.py`, `scenes/game_loop_scene.py`, `scenes/shop_scene.py`, `scenes/combat_scene.py`, `main.py`
  - **What**: Update LobbyScene to transition to "game_loop" (not "shop"). GameLoopScene transitions to "shop" on SPACE key (if not fast_mode). ShopScene transitions to "combat" on done. CombatScene transitions to "game_loop" on placement complete. GameLoopScene transitions to "game_over" when game over detected. BREAKING CHANGE: Move `build_game(strategies)` call from ShopScene factory to GameLoopScene factory (per T1.4). Update ShopScene factory to expect CoreGameState already initialized. This breaks existing Lobby → Shop flow but establishes correct Lobby → GameLoop → Shop flow.
  - **Why**: Establish correct scene flow: Lobby → GameLoop → Shop → Combat → GameLoop
  - **Gap**: G8 (Scene transition chain wired in spec but not in factories)
  - **Blocked by**: T1.9 (factories registered)
  - **Test**: Verify full cycle works: Lobby → GameLoop → Shop → Combat → GameLoop

**Priority 3: Control (Turn system and combat logic)**

- [x] T1.7 — Move turn orchestration logic to GameLoopScene
  - **Files**: `scenes/game_loop_scene.py`, `run_game.py` (reference)
  - **What**: Extract turn advancement logic from `run_game.py step_turn()` function. Implement in `GameLoopScene.advance_turn()` method. Handle: clear passive log (`game.passive_trigger_log.clear()`), increment turn (`game.turn += 1`), reset placement counters. Call `player.income()` for current player at turn start. After all players complete preparation (shop/combat), call `game.combat_phase()` and store results in `game.last_combat_results`. Clear locked coordinates for all players after combat.
  - **Why**: GameLoopScene orchestrates turn flow including income, combat, and cleanup
  - **Gap**: None (core feature, addresses Req 26 and Req 27)
  - **Blocked by**: T1.10 (transition chain wired)
  - **Test**: Verify turn counter increments, income applied, combat triggered, locked coords cleared

- [x] T1.13 — Implement combat phase triggering
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: After all players complete preparation (human player exits CombatScene, AI players complete via T2.5), call `game.combat_phase()` in `GameLoopScene.update()`. Store results in `game.last_combat_results`. Extract combat breakdown for current player. Trigger popup display (T2.4 will handle rendering). Clear locked coordinates for all players via `core_game_state.clear_locked_coords(pid)` for each player.
  - **Why**: Combat must resolve after all players prepare their boards
  - **Gap**: None (core feature, addresses Req 27)
  - **Blocked by**: T1.7 (turn orchestration), T1.1 (locked_coords_per_player)
  - **Test**: Verify combat_phase called, results stored, locked coords cleared

**Priority 4: Consistency (Human vs AI parity fixes)**

- [x] T1.12 — Implement human player preparation phase
  - **Files**: `scenes/shop_scene.py`, `scenes/combat_scene.py`
  - **What**: In `ShopScene.on_exit()`: call `player.apply_interest()` for current player after shop closes. In `CombatScene.on_exit()`: call `player.check_evolution()` and `player.check_copy_strengthening()` for current player after placement complete. These calls mirror the AI player logic from T2.5 but execute at scene boundaries for human player.
  - **Why**: Human player needs same economy and evolution logic as AI players
  - **Gap**: None (core feature, addresses Req 12 and Req 26)
  - **Blocked by**: T1.13 (combat phase working)
  - **Test**: Verify interest applied after shop, evolution/strengthening checked after combat

**Priority 5: Termination (Game over logic)**

- [x] T1.6 — Implement game_over detection and winner tracking
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: Add game_over detection logic to `GameLoopScene.update()`: check if `len(core_game_state.alive_players) <= 1`, check if `core_game_state.turn >= 50` (infinite loop guard). Store winner in `ui_state.winner = max(players, key=lambda p: p.hp)`. Set `ui_state.game_over = True` when condition met. Transition to "game_over" scene when game_over is True.
  - **Why**: Detect game end conditions and transition to GameOverScene
  - **Gap**: G9 (game_over/winner state placement described but not tasked)
  - **Blocked by**: T1.12 (core loop working)
  - **Test**: Simulate game over conditions, verify transition to GameOverScene

**Priority 6: Testing & Validation**

- [x] T1.14 — Integration test: Full turn cycle
  - **Files**: `tests/test_game_loop_scene.py`
  - **What**: Manual test: Start game, select strategies, advance turn, buy cards, place cards, return to GameLoop. Automated test: Simulate full cycle, assert all scenes visited in correct order. Verify income applied, interest applied, evolution checked, combat triggered, locked coords cleared.
  - **Why**: Verify basic turn flow works end-to-end with all economy and combat logic
  - **Gap**: None (testing)
  - **Blocked by**: T1.6 (game over detection)
  - **Test**: All tests pass

**Priority 7: Refactor (Non-critical improvements last)**

- [x] T1.3 — Resolve render system conflict (BoardRenderer vs HexSystem)
  - **Files**: `scenes/combat_scene.py`
  - **What**: Architectural Decision: CombatScene will use its existing HexSystem for board rendering. BoardRendererV3 from run_game.py will be deprecated for board display. CyberRenderer effects (draw_vfx_base, draw_priority_popup) will be preserved and integrated. Create adapter layer in CombatScene to use CyberRenderer for effects while keeping HexSystem for board.
  - **Why**: Avoid render system conflict between HexSystem and BoardRendererV3
  - **Gap**: G5 (CombatScene render system conflict)
  - **Blocked by**: T1.14 (everything else working)
  - **Test**: Verify visual consistency between old and new render paths

### Phase 1 Checkpoint

**Expected Behavior**: Can complete one full turn cycle (Lobby → GameLoop → Shop → Combat → GameLoop). GameLoopScene displays turn counter and player list. Game over detection works.

**Manual Test Steps**:
1. Start game from lobby
2. Select strategies
3. Reach GameLoopScene
4. Press SPACE to advance turn
5. Verify income applied to current player
6. Buy cards in ShopScene
7. Verify interest applied after shop closes
8. Place cards in CombatScene
9. Verify evolution/strengthening checked after placement
10. Return to GameLoopScene
11. Verify combat triggered, results displayed
12. Verify locked coords cleared
13. Verify turn counter incremented

**Must NOT Break**:
- Existing ShopScene functionality
- Existing CombatScene functionality
- LobbyScene strategy selection

---

## Phase 2: Turn System Integration

**Goal**: Integrate fast mode, player switching, and combat results display

### Tasks

- [x] T2.1 — Extend InputState with named intent mappings
  - **Files**: `core/input_state.py`
  - **What**: Add intent constants to InputState: `INTENT_TOGGLE_FAST_MODE` for K_F, `INTENT_OPEN_SHOP` for K_S, `INTENT_SWITCH_PLAYER_1` through `INTENT_SWITCH_PLAYER_8` for K_1 to K_8. Add methods: `is_fast_mode_toggled()`, `is_shop_requested()`, `get_player_switch_request() -> Optional[int]`. Update `InputState.update()` to populate these intents from raw key presses.
  - **Why**: Scenes need intent-based input handling instead of raw key checks for maintainability
  - **Gap**: G7 (InputState missing intent mappings)
  - **Blocked by**: None
  - **Test**: Press F/S/1-8 keys, verify each intent is correctly detected

- [x] T2.2 — Add fast mode toggle and timer to GameLoopScene
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: Handle INTENT_TOGGLE_FAST_MODE in `handle_input()`. Toggle `core_game_state.fast_mode` on/off. Add `ui_state.fast_timer` counter (increments by dt). When `fast_timer >= FAST_DELAY` (600ms) and `fast_mode == True`: call `advance_turn()` automatically, skip shop scene, reset `fast_timer` to 0. Display fast mode indicator using HUDRenderer.
  - **Why**: Fast mode auto-advances turns without manual interaction
  - **Gap**: None (core feature)
  - **Blocked by**: T2.1 (InputState intents)
  - **Test**: Toggle fast mode, verify turns advance every 600ms, shop is skipped

- [x] T2.3a — Add player switching via 1-8 keys
  - **Files**: `scenes/game_loop_scene.py`, `core/core_game_state.py`
  - **What**: Handle `input_state.get_player_switch_request()` in `handle_input()`. When a valid player index (0-7) is returned, set `core_game_state.view_player_index = target_index` directly (do NOT use `switch_player(direction)` — that method takes direction +1/-1, not absolute index). Validate that target player exists before switching. Print debug message showing switch. OPTIONAL: Add `switch_to_player(index: int)` method to CoreGameState if you want encapsulation, but direct assignment is acceptable.
  - **Why**: Players need keyboard shortcuts to quickly switch between player views
  - **Gap**: None (core feature)
  - **Blocked by**: T2.1 (InputState intents)
  - **Test**: Press 1-8 keys, verify view_player_index changes, console shows switch message

- [x] T2.3b — Add clickable player panel UI
  - **Files**: `scenes/game_loop_scene.py`, `ui/hud_renderer.py`
  - **What**: Make the player panel clickable. In `handle_input()`, check if mouse click is within player panel bounds (right side of screen, x > screen_width - 300). Calculate which player was clicked based on Y coordinate. Call the same switching logic as T2.3a. Update `draw_player_panel()` in HUDRenderer to return player rectangles for hit testing, OR calculate rects in GameLoopScene based on panel layout. Highlight currently viewed player in the panel.
  - **Why**: Players need mouse-based UI for switching between player views
  - **Gap**: None (core feature)
  - **Blocked by**: T2.3a (keyboard switching logic exists)
  - **Test**: Click on different players in panel, verify view switches, clicked player is highlighted

- [x] T2.4 — Add combat results popup to GameLoopScene
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: Store combat results in `ui_state.popup_data` after `combat_phase()`. Set `ui_state.popup_timer = POPUP_DURATION` (3000ms). Decrement `popup_timer` by dt in `update()`. Render popup using `draw_turn_popup()` from HUDRenderer when `popup_timer > 0`. Calculate fade alpha: `min(255, int(popup_timer / POPUP_DURATION * 510))`. Extract `ui_state.last_breakdown` for current player from `popup_data`. Render breakdown using `draw_combat_breakdown()` from HUDRenderer.
  - **Why**: Players need to see combat results after each turn
  - **Gap**: None (core feature)
  - **Blocked by**: T1.2 (HUDRenderer exists)
  - **Test**: Verify popup appears after combat, fades out after 3 seconds

- [x] T2.5a — Implement AI player economy phase (income + shop)
  - **Files**: `scenes/game_loop_scene.py`, `run_game.py` (reference)
  - **What**: Create `GameLoopScene.process_ai_turns()` method. Extract AI turn loop from `run_game.py step_turn()` (lines 447-467). For each AI player (not current viewed player): deal market window, call `player.income()`, call `AI.buy_cards()`, return unsold cards to market, call `player.apply_interest()`. STOP HERE - do NOT implement placement/evolution yet. Call this method after human player completes shop phase.
  - **Why**: AI players need economy phase (income, shop, interest) to match human player
  - **Gap**: G6 (AI turn logic migration under-specified) - Part 1
  - **Blocked by**: T1.7 (turn orchestration exists)
  - **Test**: Verify AI players receive income, buy cards, and earn interest correctly. Check gold changes and hand size increases.

- [x] T2.5b — Implement AI player placement phase (place + evolution + strengthening)
  - **Files**: `scenes/game_loop_scene.py`, `run_game.py` (reference)
  - **What**: Extend `GameLoopScene.process_ai_turns()` method from T2.5a. Add placement logic for each AI player: call `AI.place_cards()`, call `player.check_evolution()`, call `player.check_copy_strengthening()`. This completes the AI turn loop started in T2.5a.
  - **Why**: AI players need placement and evolution logic to match human player
  - **Gap**: G6 (AI turn logic migration under-specified) - Part 2
  - **Blocked by**: T2.5a (AI economy phase working)
  - **Test**: Verify AI players place cards on board, check evolution, and strengthen copies. Check board state changes.

- [x] T2.6 — Implement conditional shop skip for fast mode
  - **Files**: `scenes/game_loop_scene.py`
  - **What**: In `GameLoopScene.advance_turn()`: if `core_game_state.fast_mode == True`, skip shop scene transition, call `game.preparation_phase()` directly (handles all players' shop phase via AI), transition directly to combat or run combat immediately. If `core_game_state.fast_mode == False`, transition to "shop" scene for human player.
  - **Why**: Fast mode should bypass shop interaction
  - **Gap**: None (core feature)
  - **Blocked by**: T2.2 (fast mode toggle), T2.5a (AI economy), T2.5b (AI placement)
  - **Test**: Verify shop is skipped in fast mode, shown in normal mode

- [x] T2.7 — Integration test: Fast mode and player switching
  - **Files**: `tests/test_game_loop_scene.py`
  - **What**: Manual test: Toggle fast mode, verify turns advance automatically every 600ms. Manual test: Press 1-8 keys, verify player view switches. Manual test: Click on player panel, verify player view switches. Automated test: Simulate fast mode for 10 turns, assert turn counter increments. Automated test: Simulate player switching via keyboard, assert `view_player_index` changes. Automated test: Simulate player switching via mouse click, assert `view_player_index` changes.
  - **Why**: Verify fast mode and player switching work correctly
  - **Gap**: None (testing)
  - **Blocked by**: T2.2, T2.3a, T2.3b, T2.5a, T2.5b, T2.6
  - **Test**: All tests pass

### Phase 2 Checkpoint

**Expected Behavior**: Fast mode auto-advances turns every 600ms, shop is skipped. Player switching (1-8 keys) works. Combat results popup displays after each turn.

**Manual Test Steps**:
1. Start game, reach GameLoopScene
2. Press F to toggle fast mode
3. Observe turns advancing automatically every 600ms
4. Press F again to disable fast mode
5. Press 1-8 keys to switch between players
6. Verify player view updates correctly
7. Advance turn manually, verify combat results popup appears

**Must NOT Break**:
- Existing ShopScene functionality
- Existing CombatScene functionality
- Turn counter increments correctly
- CoreGameState persists across scenes

---

## Phase 3: Combat Loop Integration

**Goal**: Integrate card placement, hand panel, and locked coordinates into CombatScene

### Tasks

- [x] T3.1 — Assign PassiveBuffPanel and SynergyHUD to CombatScene
  - **Files**: `scenes/combat_scene.py`, `ui/hud_renderer.py`
  - **What**: Add PassiveBuffPanel and SynergyHUD rendering to `CombatScene.draw()` using HUDRenderer functions (`draw_passive_buff_panel`, `draw_synergy_hud`). Position on LEFT SIDE of screen (vertical layout). SynergyHUD displays as compact badges with icons (not large bars) - similar to TFT/Underlords style. Position: x=20-30px, y=start below player info panel. PassiveBuffPanel shows passive buffs below synergy badges. Both panels use left edge positioning to avoid overlap with board and hand panel (bottom 175px reserved). Synergy badges: small icon + count (e.g., "📦 EX: 3", "🧠 MN: 2", "🔗 CN: 1"). Passive log: scrollable list of recent passive triggers with icons.
  - **Why**: Both panels display information about cards on the board (CombatScene's domain). Modern autochess layout uses left sidebar for synergy/buff info. Compact badges save space compared to large bars.
  - **Gap**: G10 (PassiveBuffPanel and SynergyHUD have no scene assignment)
  - **Blocked by**: T1.2 (HUDRenderer exists)
  - **Test**: Verify panels render correctly on left side, synergy badges are compact with icons, passive log displays below, no overlap with hand panel

- [x] T3.2 — Add hand panel to CombatScene (horizontal bottom bar)
  - **Files**: `ui/hand_panel.py` (new), `scenes/combat_scene.py`
  - **What**: Create new file `ui/hand_panel.py` with `HandPanel` class. Extract hand panel implementation from `combat_scene_alternative.py _draw_hand_panel()` - preserve exact visual design and schema. HandPanel class: PANEL_HEIGHT=175, MAX_SLOTS=6, HEX_SIZE=76, SLOT_WIDTH=88, SLOT_GAP=8, DETAIL_PANEL_WIDTH=320. Methods: `__init__(core_game_state, ui_state)`, `draw(screen)` - renders 6 hex-shaped card slots horizontally with detail panel, `get_card_at_position(mouse_x, mouse_y)` - returns card index at mouse position. Visual features: rarity accent bar, passive indicator dot, group color dot, power label, rotation badge, selection glow effect, header row with "HAND BUFFER"/"CARDS X/6"/"PLACED X/1"/"TURN N"/hints. Store slot rects in `self._hand_slot_rects` for click detection. In CombatScene: initialize `self.hand_panel = HandPanel(core_game_state, ui_state)` in `on_enter()`, call `self.hand_panel.draw(screen)` in `draw()`. Update BOTTOM_HUB_HEIGHT from 150 to 175 in CombatScene constants.
  - **Why**: Separate HandPanel class keeps CombatScene clean (already 2696 lines), enables reusability in other scenes, follows HUDRenderer pattern. Preserves exact visual design from alternative implementation.
  - **Gap**: None (core feature)
  - **Blocked by**: T1.2 (HUDRenderer exists), T3.1 (panel ownership decision)
  - **Test**: Verify hand panel renders horizontally at bottom with 175px height, 6 hex slots display left-to-right, detail panel shows selected card info, all visual features match alternative implementation exactly

- [x] T3.3 — Move card selection logic to CombatScene
  - **Files**: `scenes/combat_scene.py`, `ui/hand_panel.py`
  - **What**: Add `selected_hand_idx: Optional[int]` to CombatScene UIState. Add `pending_rotation: int` to CombatScene UIState (0-5 range). In CombatScene `handle_input()`: handle left-click on hand panel by calling `card_idx = self.hand_panel.get_card_at_position(mouse_x, mouse_y)`, if card_idx is not None: if same card clicked deselect (set selected_hand_idx to None), if different card clicked select (set selected_hand_idx to card_idx, copy card.rotation to pending_rotation). Handle R key or right-click: increment `pending_rotation` (mod 6), update UIState. HandPanel reads `ui_state.selected_hand_idx` to render selection glow effect (cyan ring around selected hex). Detail panel shows selected card info including rotation: "ROTATION: {rotation}° → {next_rot}°". Reference `combat_scene_alternative.py _get_card_at_hand_position()` for click detection logic.
  - **Why**: Players need to select cards from hand for placement. HandPanel provides click detection, CombatScene manages selection state.
  - **Gap**: None (core feature)
  - **Blocked by**: T3.2 (hand panel exists)
  - **Test**: Verify card selection works with hex slots, deselection works, rotation works, glow effect displays, detail panel updates

- [x] T3.4 — Move placement limit enforcement to CombatScene
  - **Files**: `scenes/combat_scene.py`
  - **What**: Add `placed_this_turn: int` to CombatScene UIState. Initialize to 0 in `on_enter()`. Increment when card is placed on board. Validate placement: if `placed_this_turn >= PLACE_PER_TURN`, reject placement. Display remaining placements in status message. Reset counter when transitioning back to GameLoopScene (`on_exit`).
  - **Why**: Enforce placement limit (1 card per turn)
  - **Gap**: None (core feature)
  - **Blocked by**: T3.3 (card selection exists)
  - **Test**: Verify placement limit enforced, counter resets on turn start

- [x] T3.5 — Move locked coordinates tracking to CombatScene
  - **Files**: `scenes/combat_scene.py`
  - **What**: Read `locked_coords` from `core_game_state.locked_coords_per_player[current_player.pid]`. When card is placed: add coord to locked set via `core_game_state.locked_coords_per_player[pid].add(coord)`. Prevent placement on locked coords: check if coord in locked set before allowing placement. Prevent removal of locked cards: disable click-to-remove on locked coords. Display locked indicator: render locked border color (C_LOCKED) on locked hexes.
  - **Why**: Prevent moving/removing placed cards until turn end
  - **Gap**: None (core feature)
  - **Blocked by**: T1.1 (locked_coords_per_player in CoreGameState), T3.4 (placement logic)
  - **Test**: Verify locked coords persist across scene transitions, cannot be moved

- [x] T3.6 — Integrate placement preview with existing HexSystem
  - **Files**: `scenes/combat_scene.py`
  - **What**: CombatScene already has placement preview via HexCardRenderer. Extend to show rotation preview for selected hand card. When hovering over valid hex with selected card: highlight hex with C_SELECT color, render card preview with `pending_rotation` applied, show edge stats rotated to match `pending_rotation`. Reuse existing `_render_placement_preview()` method.
  - **Why**: Players need visual feedback for card placement
  - **Gap**: None (core feature)
  - **Blocked by**: T3.3 (card selection exists)
  - **Test**: Verify preview shows correct rotation, updates on hover

- [x] T3.7 — Move build_game to engine_core/game_factory.py
  - **Files**: `engine_core/game_factory.py` (new), `run_game.py`, `main.py`
  - **What**: Create new file `engine_core/game_factory.py`. Move `build_game()` function from `run_game.py` to `game_factory.py`. Update all references to use new import path: `from engine_core.game_factory import build_game`. Remove `from run_game import build_game` import from `main.py`.
  - **Why**: Remove run_game.py import from main.py to enable backward compatibility flag
  - **Gap**: G11 (Backward compatibility flag blocked by run_game.py import)
  - **Blocked by**: None
  - **Test**: Verify main.py runs without importing run_game.py

- [x] T3.8 — Implement restart flow in GameOverScene
  - **Files**: `scenes/game_over_scene.py` (new)
  - **What**: Create GameOverScene class extending Scene. Display winner using `draw_game_over()` from HUDRenderer. Show final stats: HP, wins, losses, total points, win streak. Add "RESTART" button (R key or click). Add "QUIT" button (ESC key or click). On restart: transition to "lobby" scene (LobbyScene will handle strategy selection, new game will be built via Lobby → GameLoop handoff protocol from T1.4). On quit: call `pygame.quit()` and `sys.exit()`.
  - **Why**: Players need to restart the game after it ends
  - **Gap**: G12 (Restart flow has no scene owner)
  - **Blocked by**: T1.9 (GameOverScene factory registered)
  - **Test**: Verify restart returns to lobby, quit exits cleanly

- [x] T3.9 — Integration test: Card placement flow
  - **Files**: `tests/test_combat_scene.py`
  - **What**: Manual test: Click hand card, press R to rotate, click hex to place. Manual test: Verify locked card cannot be moved. Manual test: Verify placement limit enforced. Automated test: Simulate card selection, rotation, placement. Automated test: Verify locked coords persist after scene transition.
  - **Why**: Verify card placement system works correctly
  - **Gap**: None (testing)
  - **Blocked by**: T3.2, T3.3, T3.4, T3.5, T3.6
  - **Test**: All tests pass

### Phase 3 Checkpoint

**Expected Behavior**: CombatScene displays hand panel, allows card selection/rotation, enforces placement limit, tracks locked coordinates. GameOverScene displays winner and allows restart.

**Manual Test Steps**:
1. Start game, reach CombatScene
2. Verify hand panel displays on left side
3. Click a hand card to select it
4. Press R to rotate the card
5. Click an empty hex to place the card
6. Verify card is locked (cannot be moved)
7. Try to place another card (should be rejected - limit 1 per turn)
8. Return to GameLoopScene, verify locked coords persist
9. Trigger game over, verify GameOverScene displays winner
10. Press R to restart, verify returns to lobby

**Must NOT Break**:
- Existing HexSystem board rendering
- Existing ShopScene functionality
- GameLoopScene turn flow
- CoreGameState persistence

---

## Phase 4: Cleanup & Finalization

**Goal**: Complete backward compatibility, add feature flag, finalize documentation, and perform end-to-end testing

### Tasks

- [x] T4.1 — Add backward compatibility feature flag
  - **Files**: `main.py`
  - **What**: Add `USE_SCENE_ARCHITECTURE = True` flag at top of `main.py`. If True: use SceneManager with GameLoopScene (current implementation). If False: call `run_game.main()` directly (legacy path). Add conditional logic in `main()` to switch between paths. Document flag usage in comments.
  - **Why**: Allow switching between old and new architecture during migration
  - **Gap**: None (backward compatibility)
  - **Blocked by**: T3.7 (run_game.py import removed)
  - **Test**: Toggle flag, verify both paths work correctly

- [x] T4.2 — Complete HUDRenderer extraction
  - **Files**: `ui/hud_renderer.py`, `run_game.py`
  - **What**: Verify all drawing functions are extracted from `run_game.py` to `ui/hud_renderer.py`. Add missing functions if any: `_draw_hand_panel()` → `draw_hand_panel()`, `_hand_card_rects()` → helper function. Ensure HUDRenderer class encapsulates all state (fonts, colors, surfaces). Add docstrings to all functions.
  - **Why**: Complete the HUD rendering extraction started in T1.2
  - **Gap**: G4 (HUDRenderer extraction completion)
  - **Blocked by**: T1.2 (HUDRenderer skeleton exists)
  - **Test**: Import HUDRenderer, call all functions, verify visual output matches run_game.py

- [x] T4.3 — Add scene transition validation
  - **Files**: `core/scene_manager.py`
  - **What**: Add transition validation to SceneManager. Define valid transitions: `VALID_TRANSITIONS = {("lobby", "game_loop"), ("game_loop", "shop"), ("shop", "combat"), ("combat", "game_loop"), ("game_loop", "game_over"), ("game_over", "lobby")}`. In `request_transition()`, check if `(current_scene, target_scene)` is in VALID_TRANSITIONS. If invalid, log error and reject transition. Add override flag for testing.
  - **Why**: Prevent invalid scene transitions that could corrupt state
  - **Gap**: None (safety feature)
  - **Blocked by**: None
  - **Test**: Attempt invalid transition, verify rejection and error log

- [x] T4.4 — End-to-end integration test
  - **Files**: `tests/test_full_game_flow.py` (new)
  - **What**: Create comprehensive integration test covering full game flow: Lobby → GameLoopScene → ShopScene → CombatScene → GameLoopScene (repeat for multiple turns) → GameOverScene → Lobby. Test fast mode: verify shop skip, auto-advance. Test player switching: verify view updates. Test card placement: verify limit enforcement, locked coords. Test game over: verify winner detection, restart flow. Test state persistence: verify CoreGameState maintains identity across all transitions.
  - **Why**: Verify entire system works end-to-end
  - **Gap**: None (testing)
  - **Blocked by**: All previous tasks
  - **Test**: All integration tests pass

- [x] T4.5 — Update documentation and deprecation notices
  - **Files**: `README.md`, `run_game.py`, `MIGRATION.md` (new)
  - **What**: Add deprecation notice to `run_game.py` header: "DEPRECATED: This file is being migrated to Scene-based architecture. Use main.py with USE_SCENE_ARCHITECTURE=True instead." Create `MIGRATION.md` documenting: migration phases, scene responsibilities, state management rules, transition flow, testing strategy. Update `README.md` with new architecture overview and scene descriptions.
  - **Why**: Document migration for future developers
  - **Gap**: None (documentation)
  - **Blocked by**: All previous tasks
  - **Test**: Review documentation for completeness and accuracy

### Phase 4 Checkpoint

**Expected Behavior**: Backward compatibility flag works. All scenes integrated. Full game flow works end-to-end. Documentation complete.

**Manual Test Steps**:
1. Set `USE_SCENE_ARCHITECTURE = False`, verify old run_game.py works
2. Set `USE_SCENE_ARCHITECTURE = True`, verify new scene architecture works
3. Play full game: Lobby → GameLoop → Shop → Combat → GameLoop → GameOver → Lobby
4. Test fast mode for 10+ turns
5. Test player switching during game
6. Test card placement with limit enforcement
7. Test game over and restart
8. Verify no crashes, no state corruption

**Must NOT Break**:
- Legacy run_game.py path (when flag is False)
- Any existing functionality
- Visual consistency with original

---

## Summary

**Total Tasks**: 42 tasks across 4 phases (T2.5 split into T2.5a and T2.5b)
- Phase 1: 14 tasks (Game Bootstrap)
- Phase 2: 8 tasks (Turn System Integration) - T2.5 split into 2 sub-tasks
- Phase 3: 9 tasks (Combat Loop Integration)
- Phase 4: 5 tasks (Cleanup & Finalization)

**Gap Coverage**:
- All 12 identified gaps are addressed
- 3 Critical gaps resolved in Phase 1
- 3 High priority gaps resolved across Phase 1-2
- 4 Medium priority gaps resolved across Phase 1-3
- 2 Minor gaps resolved in Phase 3

**Critical Requirements Coverage**:
- Req 12 (AI Player Turns): T2.5a (economy), T2.5b (placement)
- Req 26 (Economy System): T1.7, T1.12, T2.5a
- Req 27 (Combat Phase Triggering): T1.13

**Estimated Time**: 42 tasks × 10-45 minutes = 7.0 to 31.5 hours total

The spec is complete. You can begin implementing tasks by opening this file and working through them sequentially.
