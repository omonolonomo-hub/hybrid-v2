# Requirements Document

## Introduction

This document specifies requirements for fixing critical UI/UX issues in run_game2.py that prevent the game from being playable. The system uses a hybrid architecture with modal scenes (ShopScene, CombatScene) for UI, and the modal integration is complete. However, the hex grid is too small for card assets, hand panel cards are not interactive, the left panel is empty, and there is no card placement system.

The requirements focus on four main areas: hex grid sizing based on card asset dimensions, hand panel interaction with click detection and selection state, left panel rendering for synergy and passive displays, and a complete card placement system with hex click detection, validation, preview, and locked coordinate tracking.

## Glossary

- **Run_Game2**: The main game loop file (run_game2.py) using hybrid architecture
- **Hex_Grid**: The hexagonal board grid rendered by BoardRendererV3
- **Hand_Panel**: The vertical card list displayed on the left side showing player's hand
- **Left_Panel**: The top-left UI area for synergy badges and passive buff log
- **Card_Asset**: PNG image files for card front/back faces (140x160px default)
- **HEX_SIZE**: The radius of hexagons in pixels (currently 68px)
- **BoardRenderer**: The BoardRendererV3 class responsible for hex grid rendering
- **HUD_Renderer**: The module containing UI rendering functions (hud_renderer.py)
- **Placement_System**: The logic for placing cards from hand onto the hex grid
- **Locked_Coordinates**: Hex coordinates where cards were placed this turn (cannot be moved)
- **Selection_State**: Visual indication that a hand card is selected for placement
- **Placement_Preview**: Visual feedback showing where a card will be placed
- **HexSystem**: Core coordinate conversion system using cube rounding
- **PLACE_PER_TURN**: Maximum number of cards that can be placed per turn (constant)

## Requirements

### Requirement 1: Hex Grid Sizing

**User Story:** As a player, I want the hex grid to be sized appropriately for card assets, so that cards fit properly in hexagons and are readable.

#### Acceptance Criteria

1. THE BoardRenderer SHALL calculate HEX_SIZE based on Card_Asset dimensions (140x160px)
2. WHEN Card_Asset dimensions are (140, 160), THE BoardRenderer SHALL set HEX_SIZE to at least 80 pixels
3. THE BoardRenderer SHALL ensure hexagons are large enough to display card content without clipping
4. WHEN the board is rendered, THE Hex_Grid SHALL accommodate card assets with 10% padding margin
5. THE HEX_SIZE calculation SHALL maintain aspect ratio compatibility with card assets

### Requirement 2: Hand Panel Interaction

**User Story:** As a player, I want to click on cards in my hand panel, so that I can select them for placement on the board.

#### Acceptance Criteria

1. WHEN the player clicks on a hand card, THE Hand_Panel SHALL detect the click and identify the card index
2. WHEN a hand card is clicked, THE Selection_State SHALL toggle for that card (select if unselected, deselect if selected)
3. WHILE a hand card is selected, THE Hand_Panel SHALL display a visual highlight (cyan border, background change)
4. WHEN the mouse hovers over a hand card, THE Hand_Panel SHALL display a hover effect (lighter background)
5. WHEN a different hand card is clicked, THE Selection_State SHALL move to the new card (only one card selected at a time)
6. THE Hand_Panel SHALL display the current rotation angle for the selected card

### Requirement 3: Left Panel Rendering

**User Story:** As a player, I want to see synergy badges and passive buff log in the left panel, so that I can track active synergies and passive effects.

#### Acceptance Criteria

1. THE render_main_screen function SHALL call draw_synergy_hud to display synergy badges
2. THE render_main_screen function SHALL call draw_passive_buff_panel to display passive buff log
3. WHEN synergies are active, THE Left_Panel SHALL display synergy badges with group counts (EXISTENCE, MIND, CONNECTION)
4. WHEN passive buffs are triggered, THE Left_Panel SHALL display the passive buff log with card name, trigger type, and delta
5. THE Left_Panel SHALL position synergy HUD at bottom center of screen
6. THE Left_Panel SHALL position passive buff panel below the hand panel with appropriate spacing

### Requirement 4: Hex Click Detection

**User Story:** As a player, I want to click on hexagons on the board, so that I can place selected cards at specific coordinates.

#### Acceptance Criteria

1. WHEN the player clicks on the board area, THE Placement_System SHALL convert mouse position to hex coordinates using HexSystem
2. THE Placement_System SHALL use HexSystem.pixel_to_hex with cube rounding for accurate coordinate conversion
3. WHEN a hex coordinate is calculated, THE Placement_System SHALL validate that the coordinate is within BOARD_COORDS
4. IF the clicked coordinate is not in BOARD_COORDS, THEN THE Placement_System SHALL ignore the click
5. THE Placement_System SHALL return the hex coordinate (q, r) for valid board clicks

### Requirement 5: Placement Validation

**User Story:** As a player, I want the game to validate my card placements, so that I cannot place cards in invalid locations or exceed placement limits.

#### Acceptance Criteria

1. WHEN a placement is attempted, THE Placement_System SHALL check that the target hex is empty (not in board.grid)
2. WHEN a placement is attempted, THE Placement_System SHALL check that the target hex is not in Locked_Coordinates
3. WHEN a placement is attempted, THE Placement_System SHALL check that placed_this_turn is less than PLACE_PER_TURN
4. IF any validation check fails, THEN THE Placement_System SHALL reject the placement and display an error message
5. WHEN a placement is valid, THE Placement_System SHALL return True and allow the placement to proceed

### Requirement 6: Card Placement Execution

**User Story:** As a player, I want to place selected cards from my hand onto the board, so that I can build my board composition.

#### Acceptance Criteria

1. WHEN a valid hex is clicked with a card selected, THE Placement_System SHALL place the card at the target coordinate
2. WHEN a card is placed, THE Placement_System SHALL apply the current rotation (pending_rotation) to the card
3. WHEN a card is placed, THE Placement_System SHALL remove the card from player.hand
4. WHEN a card is placed, THE Placement_System SHALL add the card to player.board at the target coordinate
5. WHEN a card is placed, THE Placement_System SHALL add the target coordinate to Locked_Coordinates
6. WHEN a card is placed, THE Placement_System SHALL increment placed_this_turn counter
7. WHEN a card is placed, THE Placement_System SHALL clear the selection state (selected_hand_idx = None)

### Requirement 7: Placement Preview

**User Story:** As a player, I want to see a preview of where my selected card will be placed, so that I can make informed placement decisions.

#### Acceptance Criteria

1. WHILE a hand card is selected and the mouse hovers over a valid hex, THE BoardRenderer SHALL display a placement preview
2. THE Placement_Preview SHALL show the card with current rotation at the target hex coordinate
3. THE Placement_Preview SHALL use semi-transparent rendering (alpha 180) to distinguish from placed cards
4. WHEN the mouse moves to an invalid hex, THE Placement_Preview SHALL not be displayed
5. THE Placement_Preview SHALL update in real-time as the mouse moves across the board

### Requirement 8: Locked Coordinates Tracking

**User Story:** As a player, I want cards placed this turn to be locked, so that I cannot move them until the next turn.

#### Acceptance Criteria

1. THE HybridGameState SHALL maintain locked_coords_per_player dictionary mapping player ID to set of locked coordinates
2. WHEN a card is placed, THE Placement_System SHALL add the coordinate to locked_coords_per_player for the current player
3. WHEN the turn ends (step_turn_hybrid completes), THE Placement_System SHALL clear all locked coordinates for all players
4. WHILE a coordinate is locked, THE BoardRenderer SHALL display a locked indicator (orange border) on that hex
5. WHEN a placement is attempted on a locked coordinate, THE Placement_System SHALL reject the placement

### Requirement 9: Visual Feedback

**User Story:** As a player, I want clear visual feedback for my interactions, so that I understand the current state and available actions.

#### Acceptance Criteria

1. WHEN a hand card is selected, THE Hand_Panel SHALL display selection indicator (cyan border, "→hex / R:rotate / RClick:rotate" tooltip)
2. WHEN the mouse hovers over a hand card, THE Hand_Panel SHALL display hover effect (lighter background, cyan border)
3. WHEN a hex is hovered, THE BoardRenderer SHALL highlight the hex (cyan border)
4. WHEN a coordinate is locked, THE BoardRenderer SHALL display locked indicator (orange border)
5. WHEN a placement is invalid, THE Placement_System SHALL display error message in status area

### Requirement 10: Rotation Controls

**User Story:** As a player, I want to rotate selected cards before placement, so that I can orient cards strategically.

#### Acceptance Criteria

1. WHEN a hand card is selected and R key is pressed, THE Placement_System SHALL increment pending_rotation by 1 (modulo 6)
2. WHEN a hand card is selected and right mouse button is clicked, THE Placement_System SHALL increment pending_rotation by 1 (modulo 6)
3. THE Hand_Panel SHALL display the current rotation angle in degrees (rotation * 60)
4. WHEN a card is placed, THE Placement_System SHALL apply pending_rotation to the card before placement
5. WHEN a card is deselected, THE Placement_System SHALL reset pending_rotation to 0

## Parser and Serializer Requirements

This feature does not require parsers or serializers. All data structures use Python native types and pygame coordinate systems.

## Round-Trip Properties

This feature does not require round-trip properties as there is no serialization/deserialization.

## Acceptance Criteria Testing Strategy

### Property-Based Tests

1. **Hex Coordinate Conversion Invariant** (Requirement 4)
   - Property: For all valid screen coordinates within board area, pixel_to_hex(hex_to_pixel(q, r)) == (q, r)
   - Tests that coordinate conversion is consistent and uses cube rounding correctly

2. **Placement Validation Consistency** (Requirement 5)
   - Property: For all board states, is_valid_placement returns False for occupied hexes, locked hexes, and when placement limit is reached
   - Tests that validation rules are consistently applied

3. **Locked Coordinates Preservation** (Requirement 8)
   - Property: For all placements within a turn, locked coordinates accumulate and are only cleared at turn end
   - Tests that locked coordinate tracking is correct across multiple placements

### Integration Tests

1. **Hand Panel Click Detection** (Requirement 2)
   - Test: Click on each hand card position and verify correct card index is returned
   - Use 2-3 representative hand sizes (1 card, 3 cards, 6 cards)

2. **Left Panel Rendering** (Requirement 3)
   - Test: Verify synergy HUD and passive panel are rendered when render_main_screen is called
   - Use 1-2 representative board states (with synergies, with passive buffs)

3. **Card Placement Flow** (Requirements 6, 7)
   - Test: Select card, click valid hex, verify card is placed with correct rotation
   - Use 2-3 representative scenarios (first placement, multiple placements, placement limit reached)

4. **Visual Feedback** (Requirement 9)
   - Test: Verify selection indicators, hover effects, and locked indicators are displayed
   - Use 1-2 representative UI states (card selected, hex hovered, coordinate locked)

### Edge Cases

1. **Hex Grid Boundary** (Requirement 4)
   - Test: Click outside board area and verify click is ignored
   - Test: Click on edge hexes and verify correct coordinate conversion

2. **Placement Limit** (Requirement 5)
   - Test: Attempt to place more than PLACE_PER_TURN cards and verify rejection
   - Test: Verify error message is displayed

3. **Rotation Wraparound** (Requirement 10)
   - Test: Rotate card 6 times and verify rotation returns to 0
   - Test: Verify rotation is applied correctly to placed card

## Notes

- HEX_SIZE is currently 68px in renderer_v3.py, which is too small for 140x160px card assets
- Card assets are loaded at 140x160px by AssetLoader (CARD_SIZE constant)
- The hex grid should be sized to accommodate card assets with comfortable padding
- HexSystem uses cube rounding for accurate coordinate conversion (critical for placement)
- PLACE_PER_TURN constant defines maximum placements per turn (currently 3)
- Locked coordinates prevent card movement within the same turn (strategic constraint)
