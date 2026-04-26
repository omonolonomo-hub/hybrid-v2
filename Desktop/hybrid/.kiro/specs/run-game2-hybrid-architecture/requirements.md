# Requirements Document: run_game2.py Hybrid Architecture

## Introduction

This document specifies the requirements for run_game2.py, a hybrid architecture that combines the proven game loop logic from run_game.py with the visual/UI capabilities of the scene-based system. The system treats scenes as modal UI components rather than loop controllers, maintaining deterministic turn flow in a single main loop while leveraging scene rendering for shop, combat visualization, and placement interfaces.

## Glossary

- **Game_Loop**: The main execution loop in run_game2.py that controls game flow
- **Modal_Scene**: A UI component that runs synchronously and returns control to the main loop when complete
- **Game_State**: The core game engine state including players, market, and turn counter
- **Hybrid_State**: Wrapper state containing view player, selected cards, and locked coordinates
- **Board_Renderer**: Component responsible for rendering the hex board and cards
- **Shop_Scene**: Modal interface for card purchasing
- **Placement_Scene**: Modal interface for card positioning on the hex board
- **Combat_Scene**: Modal interface for combat result visualization
- **Locked_Coordinate**: A hex coordinate where a card has been placed and cannot be moved
- **Turn_Phase**: One of: shop, placement, AI turns, combat, cleanup
- **AI_Logic**: Automated player decision-making for non-human players
- **Font_Cache**: Pre-loaded font objects reused across frames

## Requirements

### Requirement 1: Complete Game Feature Parity

**User Story:** As a player, I want all features from run_game.py to work in run_game2.py, so that I have a fully functional game experience.

#### Acceptance Criteria

1. WHEN the game starts, THE Game_Loop SHALL initialize with all players, market, and card pool
2. WHEN a turn executes, THE Game_Loop SHALL process shop phase, placement phase, AI turns, combat phase, and cleanup phase in sequence
3. WHEN AI players take turns, THE AI_Logic SHALL execute identically to run_game.py
4. WHEN combat occurs, THE Game_State SHALL calculate damage and update player HP identically to run_game.py
5. WHEN passive abilities trigger, THE Game_State SHALL apply effects identically to run_game.py
6. WHEN the game ends, THE Game_Loop SHALL display the winner with correct HP and statistics

### Requirement 2: Single Loop Architecture

**User Story:** As a developer, I want the game to use a single main loop without nested loops, so that the code is maintainable and debuggable.

#### Acceptance Criteria

1. THE Game_Loop SHALL contain no nested while loops
2. WHEN a Modal_Scene is invoked, THE Game_Loop SHALL call it as a synchronous function
3. WHEN a Modal_Scene completes, THE Modal_Scene SHALL return control immediately to the Game_Loop
4. WHEN a Modal_Scene returns, THE Game_Loop SHALL continue execution from the next statement
5. THE Game_Loop SHALL not use signal chains or event-driven scene transitions

### Requirement 3: Modal Scene Integration

**User Story:** As a developer, I want scenes to be reusable UI components, so that I can compose interfaces without complex control flow.

#### Acceptance Criteria

1. WHEN Shop_Scene is invoked, THE Shop_Scene SHALL run as a modal dialog and return purchase results
2. WHEN Placement_Scene is invoked, THE Placement_Scene SHALL run as a modal dialog and return placement results
3. WHEN Combat_Scene is invoked, THE Combat_Scene SHALL run as a modal dialog and return when visualization completes
4. WHEN a Modal_Scene executes, THE Modal_Scene SHALL not modify Game_State directly
5. WHEN a Modal_Scene returns, THE Game_Loop SHALL apply state changes based on returned results

### Requirement 4: Complete Rendering

**User Story:** As a player, I want to see all game information on screen, so that I can make informed decisions.

#### Acceptance Criteria

1. WHEN the main screen renders, THE Board_Renderer SHALL display the hex board with all placed cards
2. WHEN the main screen renders, THE Game_Loop SHALL display the hand panel with all cards in the current player's hand
3. WHEN the main screen renders, THE Game_Loop SHALL display the synergy HUD showing active synergies
4. WHEN the main screen renders, THE Game_Loop SHALL display player info panel with HP, gold, and turn number
5. WHEN the main screen renders, THE Game_Loop SHALL display the player panel showing all players' status
6. WHEN the main screen renders, THE Game_Loop SHALL display the passive log showing recent ability triggers
7. WHEN the main screen renders, THE Game_Loop SHALL display the cyber-victorian HUD with status messages

### Requirement 5: Card Placement System

**User Story:** As a player, I want to place cards on the hex board with rotation control, so that I can position my units strategically.

#### Acceptance Criteria

1. WHEN a player clicks a hand card, THE Hybrid_State SHALL mark that card as selected
2. WHEN a card is selected, THE Game_Loop SHALL display a yellow highlight around the selected card
3. WHEN a player presses R or right-clicks with a selected card, THE Hybrid_State SHALL rotate the card by 60 degrees
4. WHEN a player clicks an empty hex with a selected card, THE Game_Loop SHALL place the card at that coordinate with the current rotation
5. WHEN a card is placed, THE Hybrid_State SHALL add that coordinate to the locked coordinates set
6. WHEN a player clicks a locked coordinate, THE Game_Loop SHALL display a message that the card cannot be moved
7. WHEN a turn ends, THE Hybrid_State SHALL clear all locked coordinates for all players

### Requirement 6: Performance Optimization

**User Story:** As a developer, I want the game to run efficiently, so that it maintains smooth frame rates.

#### Acceptance Criteria

1. WHEN the game initializes, THE Game_Loop SHALL load all fonts once into Font_Cache
2. WHEN rendering occurs, THE Game_Loop SHALL reuse fonts from Font_Cache
3. WHEN rendering occurs, THE Game_Loop SHALL not recreate font objects per frame
4. WHEN card images are needed, THE Game_Loop SHALL load them once and cache in memory
5. WHEN the board renders, THE Board_Renderer SHALL only redraw changed elements where possible

### Requirement 7: Window Size Compatibility

**User Story:** As a player with a smaller monitor, I want the game to fit on a 1600x960 window, so that I can play without scrolling.

#### Acceptance Criteria

1. THE Game_Loop SHALL create a window with dimensions 1600x960 pixels
2. WHEN the game renders, THE Board_Renderer SHALL position the board at coordinates that fit within 1600x960
3. WHEN the game renders, THE Game_Loop SHALL position all UI panels within the 1600x960 window bounds
4. WHEN the game renders, THE Game_Loop SHALL ensure no UI elements are clipped or hidden

### Requirement 8: Input Handling

**User Story:** As a player, I want responsive keyboard and mouse controls, so that I can interact with the game efficiently.

#### Acceptance Criteria

1. WHEN the player presses SPACE, THE Game_Loop SHALL execute the next turn
2. WHEN the player presses S, THE Game_Loop SHALL open the Shop_Scene
3. WHEN the player presses F, THE Game_Loop SHALL toggle fast mode
4. WHEN the player presses 1-8, THE Game_Loop SHALL switch to viewing that player's board
5. WHEN the player presses R with no selected card, THE Game_Loop SHALL restart the game
6. WHEN the player presses R with a selected card, THE Hybrid_State SHALL rotate the selected card
7. WHEN the player presses ESC with a selected card, THE Hybrid_State SHALL deselect the card
8. WHEN the player presses ESC with no selected card, THE Game_Loop SHALL exit the game
9. WHEN the player left-clicks a hand card, THE Hybrid_State SHALL select or deselect that card
10. WHEN the player left-clicks an empty hex with a selected card, THE Game_Loop SHALL place the card
11. WHEN the player right-clicks with a selected card, THE Hybrid_State SHALL rotate the card

### Requirement 9: Turn Flow Determinism

**User Story:** As a developer, I want turn execution to be deterministic, so that game behavior is predictable and testable.

#### Acceptance Criteria

1. WHEN a turn executes with the same initial state and inputs, THE Game_Loop SHALL produce the same final state
2. WHEN AI_Logic executes, THE AI_Logic SHALL use the same random seed for reproducible behavior in tests
3. WHEN combat executes, THE Game_State SHALL calculate results deterministically based on board state
4. WHEN passive abilities trigger, THE Game_State SHALL apply effects in a consistent order
5. THE Game_Loop SHALL increment the turn counter by exactly 1 per turn

### Requirement 10: State Consistency

**User Story:** As a developer, I want game state to remain consistent across turn boundaries, so that bugs are minimized.

#### Acceptance Criteria

1. WHEN a turn ends, THE Hybrid_State SHALL clear locked coordinates for all players
2. WHEN a turn ends, THE Hybrid_State SHALL reset selected card index to None
3. WHEN a turn ends, THE Hybrid_State SHALL reset pending rotation to 0
4. WHEN a turn ends, THE Hybrid_State SHALL reset placed cards counter to 0
5. WHEN a player switches view, THE Hybrid_State SHALL clear selected card and rotation state

### Requirement 11: Combat Visualization

**User Story:** As a player, I want to see combat results clearly, so that I understand what happened during the combat phase.

#### Acceptance Criteria

1. WHEN combat completes, THE Game_State SHALL store combat results in a structured format
2. WHEN combat results are available, THE Game_Loop SHALL invoke Combat_Scene with the results
3. WHEN Combat_Scene displays, THE Combat_Scene SHALL show attacker and defender information
4. WHEN Combat_Scene displays, THE Combat_Scene SHALL show damage dealt by each side
5. WHEN Combat_Scene displays, THE Combat_Scene SHALL show combat events and breakdown
6. WHEN the player views combat results, THE Combat_Scene SHALL allow skipping the animation

### Requirement 12: Error Recovery

**User Story:** As a player, I want the game to handle errors gracefully, so that a single error doesn't crash the entire game.

#### Acceptance Criteria

1. IF a Modal_Scene fails to import, THEN THE Game_Loop SHALL log the error and continue with fallback UI
2. IF a Modal_Scene raises an exception during execution, THEN THE Game_Loop SHALL catch the exception and skip that phase
3. IF an invalid player index is set, THEN THE Hybrid_State SHALL clamp it to a valid range
4. IF rendering fails for a component, THEN THE Game_Loop SHALL log the error and continue rendering other components
5. WHEN an error occurs, THE Game_Loop SHALL display an error message to the player

### Requirement 13: Game Over Handling

**User Story:** As a player, I want clear game over conditions and winner display, so that I know when the game ends and who won.

#### Acceptance Criteria

1. WHEN only one player remains alive, THE Game_Loop SHALL set game over state to true
2. WHEN turn 50 is reached, THE Game_Loop SHALL set game over state to true
3. WHEN game over state is true, THE Game_Loop SHALL determine the winner as the player with highest HP
4. WHEN game over state is true, THE Game_Loop SHALL display the winner's player ID, strategy, and HP
5. WHEN game over state is true, THE Game_Loop SHALL prevent further turn execution

### Requirement 14: Player View Switching

**User Story:** As a player, I want to view different players' boards, so that I can see what my opponents are doing.

#### Acceptance Criteria

1. WHEN the player presses TAB, THE Hybrid_State SHALL cycle to the next player
2. WHEN the player presses a number key 1-8, THE Hybrid_State SHALL switch to that player if valid
3. WHEN the view player changes, THE Board_Renderer SHALL update its strategy to match the new player
4. WHEN the view player changes, THE Game_Loop SHALL render the new player's board and hand
5. WHEN the view player changes, THE Hybrid_State SHALL clear any selected card state

### Requirement 15: Placement Limit Enforcement

**User Story:** As a player, I want placement limits enforced per turn, so that the game follows the rules.

#### Acceptance Criteria

1. WHEN a turn starts, THE Hybrid_State SHALL set placed cards counter to 0
2. WHEN a card is placed, THE Hybrid_State SHALL increment the placed cards counter
3. WHEN the placed cards counter reaches PLACE_PER_TURN, THE Game_Loop SHALL prevent further placements
4. WHEN a player attempts to place beyond the limit, THE Game_Loop SHALL display a message indicating the limit is reached
5. WHEN a new turn starts, THE Hybrid_State SHALL reset the placed cards counter to 0

### Requirement 16: Hover and Tooltip System

**User Story:** As a player, I want to see card details when hovering over them, so that I can understand their abilities.

#### Acceptance Criteria

1. WHEN the mouse hovers over a board card, THE Board_Renderer SHALL highlight that card
2. WHEN the mouse hovers over a board card, THE Board_Renderer SHALL display a tooltip with card details
3. WHEN the mouse hovers over a hand card, THE Game_Loop SHALL display card information
4. WHEN the mouse moves away from a card, THE Board_Renderer SHALL clear the highlight and tooltip
5. WHEN a card is selected for placement, THE Game_Loop SHALL show a preview at the hovered hex

### Requirement 17: Synergy Highlighting

**User Story:** As a player, I want to see which cards contribute to synergies, so that I can plan my strategy.

#### Acceptance Criteria

1. WHEN the mouse hovers over a synergy in the HUD, THE Board_Renderer SHALL highlight all cards of that synergy group
2. WHEN the synergy HUD renders, THE Game_Loop SHALL display active synergy counts
3. WHEN a synergy is active, THE Game_Loop SHALL display it with full opacity
4. WHEN a synergy is inactive, THE Game_Loop SHALL display it with reduced opacity
5. WHEN the mouse moves away from the synergy HUD, THE Board_Renderer SHALL clear synergy highlights

### Requirement 18: Fast Mode Operation

**User Story:** As a player, I want a fast mode to skip shop phases, so that I can test game mechanics quickly.

#### Acceptance Criteria

1. WHEN fast mode is enabled, THE Game_Loop SHALL skip the Shop_Scene
2. WHEN fast mode is enabled, THE Game_Loop SHALL execute turns automatically with a delay
3. WHEN fast mode is enabled, THE Game_Loop SHALL use AI logic for all players including the human player
4. WHEN fast mode is toggled off, THE Game_Loop SHALL return to normal turn-by-turn execution
5. WHEN fast mode is active, THE Game_Loop SHALL display a status message indicating fast mode is on

### Requirement 19: Asset Loading

**User Story:** As a developer, I want assets loaded efficiently at startup, so that runtime performance is optimal.

#### Acceptance Criteria

1. WHEN the game initializes, THE Game_Loop SHALL load the card pool from the data file
2. WHEN the game initializes, THE Game_Loop SHALL preload card images into memory
3. WHEN the game initializes, THE Game_Loop SHALL create Font_Cache with all required font sizes
4. WHEN assets fail to load, THE Game_Loop SHALL log the error and use fallback assets
5. WHEN the game exits, THE Game_Loop SHALL release all loaded assets

### Requirement 20: Passive Ability Logging

**User Story:** As a player, I want to see when passive abilities trigger, so that I understand what effects are active.

#### Acceptance Criteria

1. WHEN a passive ability triggers, THE Game_State SHALL add an entry to the passive log
2. WHEN the passive log renders, THE Game_Loop SHALL display recent passive triggers
3. WHEN a turn starts, THE Game_State SHALL clear the passive log
4. WHEN the passive log is too long, THE Game_Loop SHALL display only the most recent entries
5. WHEN a passive log entry is displayed, THE Game_Loop SHALL show the card name and effect description
