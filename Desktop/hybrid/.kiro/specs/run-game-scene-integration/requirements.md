# Requirements Document: run-game-scene-integration

## Introduction

This document specifies the functional and non-functional requirements for migrating the monolithic `run_game.py` (730+ lines) into the Scene-based architecture. The migration decomposes the single-file game loop into modular scenes (GameLoopScene, CombatScene, ShopScene, GameOverScene) while preserving all existing functionality and avoiding state duplication or timing conflicts.

## Glossary

- **Scene**: A self-contained game state with its own update/render logic (e.g., LobbyScene, ShopScene, CombatScene)
- **SceneManager**: Orchestrates scene transitions and lifecycle management
- **CoreGameState**: SAVEABLE state shared across all scenes (game instance, view_player_index, fast_mode)
- **UIState**: THROWAWAY state specific to a scene (animations, selections, hovers)
- **GameLoopScene**: New scene that orchestrates turn flow and player switching
- **CombatScene**: Existing scene for card placement on the hex board
- **ShopScene**: Existing scene for buying cards from the market
- **GameOverScene**: New scene for displaying winner and final stats
- **HUDRenderer**: Utility class for rendering UI elements (player panel, HUD, popups)
- **InputState**: Centralized input handling with intent-based mappings
- **Locked_Coordinates**: Hexes where placed cards cannot be moved until turn end
- **Fast_Mode**: Game speed setting that auto-advances turns and skips shop
- **PLACE_PER_TURN**: Constant limiting card placements per turn (currently 1)
- **AI_Player**: Computer-controlled player that buys and places cards automatically
- **Combat_Phase**: Game logic that resolves battles between all players
- **Preparation_Phase**: Game logic that handles income, shop, and placement for all players

## Requirements

### Requirement 1: Core State Management

**User Story:** As a developer, I want a clear separation between saveable and throwaway state, so that the system is maintainable and state duplication is avoided.

#### Acceptance Criteria

1. THE CoreGameState SHALL contain only SAVEABLE state: game instance, view_player_index, fast_mode, locked_coords_per_player
2. WHEN a scene is created, THE Scene SHALL receive a reference to CoreGameState (not a copy)
3. THE UIState SHALL contain only THROWAWAY state specific to each scene
4. WHEN a scene transitions, THE CoreGameState SHALL maintain the same object identity across scenes
5. THE CoreGameState SHALL provide accessor methods for derived state: current_player, turn, alive_players

### Requirement 2: GameLoopScene Creation

**User Story:** As a player, I want a central hub for turn orchestration, so that I can advance turns, switch players, and see game status.

#### Acceptance Criteria

1. THE GameLoopScene SHALL extend the Scene base class
2. THE GameLoopScene SHALL display turn counter, player list with HP/status, and turn advancement button
3. WHEN the player presses SPACE, THE GameLoopScene SHALL advance the turn
4. WHEN the player presses keys 1-8, THE GameLoopScene SHALL switch the viewed player
5. THE GameLoopScene SHALL detect game over conditions and transition to GameOverScene
6. THE GameLoopScene SHALL orchestrate the turn flow: income → shop/combat → AI turns → combat phase → results

### Requirement 3: Turn Flow Management

**User Story:** As a player, I want turns to advance in a predictable sequence, so that the game progresses correctly.

#### Acceptance Criteria

1. WHEN a turn advances, THE System SHALL increment the turn counter by exactly 1
2. WHEN a turn starts, THE System SHALL clear the passive trigger log
3. WHEN a turn advances in normal mode, THE System SHALL transition to ShopScene for the human player
4. WHEN a turn advances in fast mode, THE System SHALL skip ShopScene and process all players via AI
5. WHEN all players complete preparation, THE System SHALL trigger the combat phase
6. WHEN combat completes, THE System SHALL display combat results popup for 3 seconds
7. WHEN a turn ends, THE System SHALL clear locked coordinates for all players

### Requirement 4: Fast Mode

**User Story:** As a player, I want to auto-advance turns without manual interaction, so that I can quickly simulate multiple turns.

#### Acceptance Criteria

1. WHEN the player presses F, THE System SHALL toggle fast_mode on/off
2. WHILE fast_mode is True, THE System SHALL auto-advance turns every 600ms
3. WHILE fast_mode is True, THE System SHALL skip ShopScene transitions
4. WHILE fast_mode is True, THE System SHALL process all players via AI (income, buy, place)
5. THE System SHALL display a fast mode indicator when fast_mode is True

### Requirement 5: Player Switching

**User Story:** As a player, I want to view different players' boards, so that I can observe their strategies and card placements.

#### Acceptance Criteria

1. WHEN the player presses keys 1-8, THE System SHALL switch view_player_index to the corresponding player
2. WHEN the player clicks a player in the player list panel, THE System SHALL switch to that player
3. WHEN player switching occurs, THE System SHALL clear any card selection state
4. WHEN player switching occurs, THE System SHALL update the board display to show the new player's board
5. THE System SHALL highlight the currently viewed player in the player list panel

### Requirement 6: Card Placement System

**User Story:** As a player, I want to select cards from my hand and place them on the hex board, so that I can build my board composition.

#### Acceptance Criteria

1. WHEN the player clicks a hand card, THE CombatScene SHALL select that card (or deselect if already selected)
2. WHEN a card is selected, THE CombatScene SHALL display a selection highlight and rotation indicator
3. WHEN the player presses R or right-clicks, THE CombatScene SHALL rotate the selected card by 60 degrees
4. WHEN the player clicks an empty hex with a selected card, THE CombatScene SHALL place the card at that hex with the pending rotation
5. WHEN a card is placed, THE CombatScene SHALL increment the placed_this_turn counter
6. WHEN placed_this_turn reaches PLACE_PER_TURN, THE CombatScene SHALL reject further placements
7. WHEN a card is placed, THE CombatScene SHALL add the hex coordinate to locked_coords_per_player for that player
8. WHEN the player attempts to place on a locked coordinate, THE CombatScene SHALL reject the placement

### Requirement 7: Locked Coordinates

**User Story:** As a player, I want placed cards to be immutable until turn end, so that I cannot accidentally move or remove them.

#### Acceptance Criteria

1. WHEN a card is placed on a hex, THE System SHALL add that hex to locked_coords_per_player for the current player
2. WHEN a hex is locked, THE System SHALL prevent placement on that hex
3. WHEN a hex is locked, THE System SHALL prevent removal of the card at that hex
4. WHEN a hex is locked, THE CombatScene SHALL display a locked indicator on that hex
5. WHEN a turn ends, THE GameLoopScene SHALL clear locked_coords_per_player for all players

### Requirement 8: Shop Integration

**User Story:** As a player, I want to buy cards from the market during my turn, so that I can expand my hand and build my strategy.

#### Acceptance Criteria

1. WHEN a turn advances in normal mode, THE GameLoopScene SHALL transition to ShopScene
2. WHEN ShopScene opens, THE System SHALL deal a market window for the current player
3. WHEN the player buys a card, THE ShopScene SHALL deduct gold and add the card to the player's hand
4. WHEN the player presses ENTER or clicks done, THE ShopScene SHALL return unsold cards to the market
5. WHEN ShopScene closes, THE System SHALL apply interest to the player's gold
6. WHEN ShopScene closes, THE System SHALL transition to CombatScene

### Requirement 9: Combat Results Display

**User Story:** As a player, I want to see combat results after each turn, so that I understand what happened during combat.

#### Acceptance Criteria

1. WHEN combat_phase completes, THE GameLoopScene SHALL store combat results in popup_data
2. WHEN combat results are available, THE GameLoopScene SHALL display a popup for 3 seconds
3. THE popup SHALL show: winner, damage dealt, kills, combos, synergies
4. THE popup SHALL fade out over the 3-second duration
5. WHEN the popup is visible, THE GameLoopScene SHALL extract the combat breakdown for the current player
6. THE GameLoopScene SHALL display the combat breakdown using draw_combat_breakdown

### Requirement 10: Game Over Detection

**User Story:** As a player, I want the game to end when a winner is determined, so that I can see final results and restart.

#### Acceptance Criteria

1. WHEN alive_players count is less than or equal to 1, THE GameLoopScene SHALL set game_over to True
2. WHEN turn count reaches 50, THE GameLoopScene SHALL set game_over to True (infinite loop guard)
3. WHEN game_over is True, THE GameLoopScene SHALL determine the winner as the player with maximum HP
4. WHEN game_over is True, THE GameLoopScene SHALL transition to GameOverScene
5. THE GameOverScene SHALL display the winner and final stats

### Requirement 11: HUD Rendering

**User Story:** As a player, I want to see game information displayed clearly, so that I can make informed decisions.

#### Acceptance Criteria

1. THE HUDRenderer SHALL provide functions for drawing: cyber_victorian_hud, player_panel, player_info, combat_breakdown, turn_popup, game_over, passive_buff_panel, synergy_hud
2. THE GameLoopScene SHALL render: turn counter, player list, fast mode indicator, combat results popup
3. THE CombatScene SHALL render: board, hand panel, synergy HUD, passive buff panel, placement preview
4. THE ShopScene SHALL render: market cards, hand buffer, refresh button, done button
5. THE GameOverScene SHALL render: winner announcement, final stats, restart button, quit button

### Requirement 12: AI Player Turns

**User Story:** As a player, I want AI players to take their turns automatically, so that the game progresses without manual intervention for each player.

#### Acceptance Criteria

1. WHEN a turn advances, THE GameLoopScene SHALL process AI player turns after the human player completes their turn
2. FOR EACH AI player, THE System SHALL: deal market window, apply income, call AI.buy_cards, return unsold cards, apply interest, check evolution, call AI.place_cards, check copy strengthening
3. THE AI player logic SHALL execute in the same order as the original run_game.py implementation
4. THE AI player turns SHALL complete before combat_phase is triggered

### Requirement 13: Scene Transition Chain

**User Story:** As a developer, I want scene transitions to follow a predictable flow, so that the game state remains consistent.

#### Acceptance Criteria

1. THE LobbyScene SHALL transition to GameLoopScene after strategy selection
2. THE GameLoopScene SHALL transition to ShopScene when a turn advances in normal mode
3. THE ShopScene SHALL transition to CombatScene when the player clicks done
4. THE CombatScene SHALL transition to GameLoopScene when placement is complete
5. THE GameLoopScene SHALL transition to GameOverScene when game_over is True
6. THE GameOverScene SHALL transition to LobbyScene when the player clicks restart

### Requirement 14: Input Handling

**User Story:** As a player, I want keyboard and mouse inputs to be handled consistently, so that controls are predictable.

#### Acceptance Criteria

1. THE InputState SHALL provide intent-based mappings for: INTENT_TOGGLE_FAST_MODE (F key), INTENT_OPEN_SHOP (S key), INTENT_SWITCH_PLAYER_1 through INTENT_SWITCH_PLAYER_8 (1-8 keys)
2. THE InputState SHALL provide methods: is_fast_mode_toggled, is_shop_requested, get_player_switch_request
3. THE GameLoopScene SHALL handle: SPACE (advance turn), F (toggle fast mode), 1-8 (switch player), ESC (quit)
4. THE CombatScene SHALL handle: left-click (select/place card), right-click (rotate card), R (rotate card), ESC (cancel selection)
5. THE ShopScene SHALL handle: left-click (buy card), ENTER (done), ESC (cancel)

### Requirement 15: Hand Panel Display

**User Story:** As a player, I want to see my hand cards during combat, so that I can select and place them on the board.

#### Acceptance Criteria

1. THE CombatScene SHALL display the hand panel on the left side of the screen
2. THE hand panel SHALL show: card image, rarity, group color, power, rotation, passive indicator
3. WHEN a card is selected, THE hand panel SHALL highlight that card with a selection border
4. WHEN the hand changes, THE hand panel SHALL update to reflect the new hand composition
5. THE hand panel SHALL calculate card rectangles using the _hand_card_rects helper function

### Requirement 16: Placement Preview

**User Story:** As a player, I want to see a preview of where my card will be placed, so that I can make informed placement decisions.

#### Acceptance Criteria

1. WHEN a card is selected and the player hovers over a hex, THE CombatScene SHALL highlight that hex
2. THE highlight SHALL use the C_SELECT color for valid placements
3. THE CombatScene SHALL render a card preview at the hovered hex with the pending rotation applied
4. THE card preview SHALL show edge stats rotated to match the pending rotation
5. THE CombatScene SHALL reuse the existing _render_placement_preview method

### Requirement 17: Scene Factory Registration

**User Story:** As a developer, I want scene factories to be registered in main.py, so that SceneManager can create scenes dynamically.

#### Acceptance Criteria

1. THE main.py SHALL register a factory for "game_loop" scene
2. THE main.py SHALL register a factory for "game_over" scene
3. THE create_game_loop_scene factory SHALL accept core_game_state and kwargs
4. THE create_game_over_scene factory SHALL accept core_game_state and kwargs
5. THE factories SHALL be registered before SceneManager.start is called

### Requirement 18: Strategy Handoff Protocol

**User Story:** As a developer, I want strategies to flow from LobbyScene to GameLoopScene, so that the game can be initialized with player-selected strategies.

#### Acceptance Criteria

1. WHEN LobbyScene exits, THE LobbyScene SHALL store selected strategies in transition kwargs
2. THE SceneManager SHALL pass transition kwargs to the GameLoopScene factory
3. THE GameLoopScene factory SHALL call build_game with the provided strategies
4. THE GameLoopScene factory SHALL create CoreGameState with the built game instance
5. THE GameLoopScene SHALL initialize with the created CoreGameState

### Requirement 19: Render System Integration

**User Story:** As a developer, I want CombatScene to use HexSystem for board rendering, so that layout control and asset loading are consistent.

#### Acceptance Criteria

1. THE CombatScene SHALL use HexSystem for board rendering (not BoardRendererV3)
2. THE CombatScene SHALL use CyberRenderer for visual effects (draw_vfx_base, draw_priority_popup)
3. THE CombatScene SHALL create an adapter layer to integrate CyberRenderer effects with HexSystem board rendering
4. THE visual output SHALL be consistent with the original run_game.py rendering
5. THE BoardRendererV3 from run_game.py SHALL be deprecated for board display

### Requirement 20: Passive Buff and Synergy Panels

**User Story:** As a player, I want to see passive buffs and active synergies during combat, so that I understand my board's current state.

#### Acceptance Criteria

1. THE CombatScene SHALL display the PassiveBuffPanel below the hand panel
2. THE CombatScene SHALL display the SynergyHUD at the bottom of the screen
3. THE PassiveBuffPanel SHALL show passive buffs from placed cards
4. THE SynergyHUD SHALL show active synergies from board composition
5. THE CombatScene SHALL use HUDRenderer functions: draw_passive_buff_panel, draw_synergy_hud

### Requirement 21: Game Restart Flow

**User Story:** As a player, I want to restart the game after it ends, so that I can play again with new strategies.

#### Acceptance Criteria

1. WHEN the player presses R or clicks restart in GameOverScene, THE GameOverScene SHALL transition to LobbyScene
2. THE LobbyScene SHALL allow strategy selection for a new game
3. THE new game SHALL be built via the Lobby → GameLoop handoff protocol
4. WHEN the player presses ESC or clicks quit in GameOverScene, THE System SHALL call pygame.quit and sys.exit
5. THE restart flow SHALL create a fresh game instance (not reuse the old one)

### Requirement 22: Backward Compatibility

**User Story:** As a developer, I want to maintain backward compatibility during migration, so that the old system remains functional while the new system is being built.

#### Acceptance Criteria

1. THE run_game.py SHALL remain functional during migration
2. THE main.py SHALL provide a feature flag USE_SCENE_ARCHITECTURE to switch between old and new systems
3. WHEN USE_SCENE_ARCHITECTURE is True, THE System SHALL use SceneManager with GameLoopScene
4. WHEN USE_SCENE_ARCHITECTURE is False, THE System SHALL call run_game.main directly
5. THE run_game.py import SHALL be removed from main.py before the feature flag can work

### Requirement 23: State Persistence Across Scenes

**User Story:** As a developer, I want state to persist correctly across scene transitions, so that no data is lost during transitions.

#### Acceptance Criteria

1. WHEN a scene transition occurs, THE CoreGameState SHALL maintain the same object reference
2. WHEN a scene transition occurs, THE locked_coords_per_player SHALL persist from CombatScene to GameLoopScene
3. WHEN a scene transition occurs, THE view_player_index SHALL persist across all scenes
4. WHEN a scene transition occurs, THE fast_mode setting SHALL persist across all scenes
5. WHEN a scene exits, THE UIState SHALL be cleared to free memory

### Requirement 24: Placement Limit Enforcement

**User Story:** As a player, I want placement limits to be enforced, so that I cannot place more cards than allowed per turn.

#### Acceptance Criteria

1. THE CombatScene SHALL track placed_this_turn in UIState
2. WHEN CombatScene is entered, THE placed_this_turn counter SHALL be initialized to 0
3. WHEN a card is placed, THE placed_this_turn counter SHALL increment by 1
4. WHEN placed_this_turn reaches PLACE_PER_TURN, THE CombatScene SHALL reject further placements
5. WHEN CombatScene exits, THE placed_this_turn counter SHALL be reset to 0

### Requirement 25: Turn Popup Animation

**User Story:** As a player, I want combat results to fade in and out smoothly, so that the UI feels polished.

#### Acceptance Criteria

1. WHEN combat results are displayed, THE popup_timer SHALL be set to 3000ms
2. WHILE popup_timer is greater than 0, THE GameLoopScene SHALL decrement popup_timer by delta time
3. THE popup alpha SHALL be calculated as: min(255, int(popup_timer / 3000 * 510))
4. THE popup SHALL fade out as popup_timer approaches 0
5. WHEN popup_timer reaches 0, THE popup SHALL no longer be rendered

### Requirement 26: Economy System Integration

**User Story:** As a player, I want gold, income, and interest to be tracked correctly, so that the economy system works as expected.

#### Acceptance Criteria

1. WHEN a turn starts, THE System SHALL call player.income to add income to player.gold
2. WHEN ShopScene closes, THE System SHALL call player.apply_interest to add interest to player.gold
3. THE HUDRenderer SHALL display player.gold in the cyber_victorian_hud
4. THE System SHALL track player.stats["gold_earned"] and player.stats["gold_spent"]
5. THE economy calculations SHALL match the original run_game.py implementation

### Requirement 27: Combat Phase Triggering

**User Story:** As a player, I want combat to trigger after all players complete preparation, so that battles are resolved correctly.

#### Acceptance Criteria

1. WHEN all players complete preparation, THE GameLoopScene SHALL call game.combat_phase
2. THE combat_phase SHALL resolve battles between all players
3. THE combat_phase SHALL store results in game.last_combat_results
4. THE GameLoopScene SHALL extract combat results from game.last_combat_results
5. THE combat results SHALL be displayed in the combat results popup

### Requirement 28: Visual Consistency

**User Story:** As a player, I want the new scene-based system to look identical to the old run_game.py system, so that the migration is seamless.

#### Acceptance Criteria

1. THE HUDRenderer functions SHALL produce visually identical output to the original _draw_* functions in run_game.py
2. THE CombatScene board rendering SHALL match the original BoardRendererV3 output
3. THE ShopScene SHALL maintain its existing visual style
4. THE GameLoopScene SHALL use the same fonts, colors, and layout as run_game.py
5. THE GameOverScene SHALL match the original _draw_game_over output

### Requirement 29: Performance Optimization

**User Story:** As a developer, I want the scene-based system to perform as well as the original run_game.py, so that frame rate is not impacted.

#### Acceptance Criteria

1. THE System SHALL reuse drawing functions from run_game.py (not re-implement)
2. THE System SHALL avoid re-creating surfaces every frame
3. THE System SHALL use dirty rectangle optimization for partial updates where possible
4. THE System SHALL cache font renders for static text
5. THE System SHALL minimize state copying between scenes (use references, not copies)

### Requirement 30: Error Handling

**User Story:** As a developer, I want clear error messages when invalid transitions occur, so that debugging is easier.

#### Acceptance Criteria

1. WHEN an invalid scene transition is requested, THE SceneManager SHALL log an error message
2. WHEN a scene factory is not registered, THE SceneManager SHALL raise a clear exception
3. WHEN CoreGameState is None, THE Scene SHALL raise a clear exception
4. WHEN a placement is invalid, THE CombatScene SHALL display a status message explaining why
5. WHEN game_over conditions are met, THE GameLoopScene SHALL log the game over reason

## Non-Functional Requirements

### NFR-1: Maintainability
THE System SHALL separate SAVEABLE state (CoreGameState) from THROWAWAY state (UIState) to avoid state duplication and improve maintainability.

### NFR-2: Testability
THE System SHALL provide clear interfaces for unit testing (CoreGameState methods), integration testing (scene transitions), and property-based testing (turn monotonicity, placement limits).

### NFR-3: Performance
THE System SHALL maintain frame rate equivalent to the original run_game.py implementation (target: 60 FPS).

### NFR-4: Backward Compatibility
THE System SHALL maintain backward compatibility with run_game.py during migration via a feature flag.

### NFR-5: Code Reuse
THE System SHALL reuse existing drawing functions, game logic, and asset loading to minimize code duplication.

### NFR-6: Modularity
THE System SHALL decompose the monolithic run_game.py into modular scenes with clear responsibilities.

### NFR-7: State Consistency
THE System SHALL ensure CoreGameState has the same object identity across all scenes to prevent state divergence.

### NFR-8: Transition Safety
THE System SHALL defer scene transitions until safe points (before update) to prevent timing conflicts.

## Constraints and Assumptions

### Constraints
1. The migration must preserve all existing functionality from run_game.py
2. The migration must not introduce state duplication between CoreGameState and UIState
3. The migration must maintain visual consistency with the original run_game.py
4. The migration must be completed in 3 phases to minimize risk
5. Each phase must be independently testable

### Assumptions
1. The existing Scene, SceneManager, CoreGameState, and UIState classes are stable and well-tested
2. The existing ShopScene and CombatScene are functional and can be extended
3. The pygame rendering pipeline is sufficient for the new scene-based architecture
4. The AI player logic can be extracted from run_game.py without modification
5. The locked_coords_per_player can be stored in CoreGameState without performance impact
