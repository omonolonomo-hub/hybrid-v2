# Requirements Document

## Introduction

This document specifies the requirements for the Combat Scene 37-Hex Rebuild feature. The combat scene is a pygame-based tactical visualization layer that displays a 37-hex radial grid with unit cards, integrates with existing CoreGameState and HexSystem, and provides a fixed UI layout for observing board state, unit placements, synergies, and combat outcomes.

## Glossary

- **CombatScene**: The scene class responsible for rendering the 37-hex grid and managing combat visualization
- **HexSystem**: Existing system providing coordinate conversion and geometry utilities for hexagonal grids
- **CoreGameState**: Source of truth for game state including players, boards, units, and economy
- **UIState**: State container for animation and interaction data
- **AssetManager**: Component responsible for loading and caching card images with fallback support
- **PlacementController**: Component managing card placement and rotation mechanics
- **HexCard**: Data structure representing a card placed on a hex with rendering information
- **Axial_Coordinates**: Coordinate system using (q, r) pairs to identify hexes
- **Rotation_Lock**: Mechanism preventing rotation changes after card placement

## Requirements

### Requirement 1: 37-Hex Radial Grid Rendering

**User Story:** As a player, I want to see a 37-hex radial grid centered on screen, so that I can view the tactical board layout.

#### Acceptance Criteria

1. THE CombatScene SHALL render exactly 37 hexes in a radial pattern with radius 3
2. THE grid SHALL be centered in the available screen area between UI panels
3. WHEN the scene is entered, THE CombatScene SHALL calculate hex_size to fit the grid within available space with 15% safety margin
4. THE grid origin SHALL be positioned at the exact center of the available area
5. THE hexes SHALL use flat-top orientation with axial (q, r) coordinates

### Requirement 2: Fixed UI Layout

**User Story:** As a player, I want a fixed UI layout with panels and a bottom hub, so that I can view game information without overlap with the hex grid.

#### Acceptance Criteria

1. THE CombatScene SHALL render a left panel of 300px width for passive information
2. THE CombatScene SHALL render a right panel of 300px width for player information
3. THE CombatScene SHALL render a bottom hub of 150px height for economy and stats
4. THE CombatScene SHALL maintain a top margin of 50px
5. THE hex grid SHALL NOT overlap with any UI panel
6. WHEN layout is calculated, THE CombatScene SHALL assert no overlap between grid bounds and panel boundaries

### Requirement 3: Coordinate Conversion

**User Story:** As a developer, I want accurate coordinate conversion between pixel and hex coordinates, so that mouse interactions work correctly.

#### Acceptance Criteria

1. WHEN converting hex coordinates to pixels, THE HexSystem SHALL apply the grid origin offset
2. WHEN converting pixels to hex coordinates, THE HexSystem SHALL remove the grid origin offset
3. THE HexSystem SHALL use axial rounding with cube coordinate method for pixel-to-hex conversion
4. FOR ALL hexes in the grid, converting to pixels and back to hex SHALL return the original hex coordinate
5. THE HexSystem SHALL serve as the single source of truth for all coordinate conversions

### Requirement 4: Card Asset Loading

**User Story:** As a player, I want to see card artwork when available, so that I can visually identify units.

#### Acceptance Criteria

1. WHEN loading Yggdrasil card assets, THE AssetManager SHALL check for Yggdrasil_front.png and Yggdrasil_back.png
2. WHEN a card asset file is not found, THE AssetManager SHALL create a neon hex placeholder with the card name
3. WHEN a card asset fails to load, THE AssetManager SHALL create a neon hex placeholder with the card name
4. THE AssetManager SHALL cache all loaded images to prevent redundant file I/O
5. THE AssetManager SHALL NEVER return None from asset loading functions
6. WHEN creating placeholders, THE AssetManager SHALL use deterministic colors based on card name hash

### Requirement 5: Card Placement Mechanics

**User Story:** As a player, I want to place cards on the hex grid with rotation control, so that I can position units strategically.

#### Acceptance Criteria

1. WHEN a card is selected from hand, THE CombatScene SHALL enter placement mode
2. WHEN in placement mode, THE CombatScene SHALL display a ghost preview of the card at the nearest valid hex
3. WHEN the user right-clicks during placement, THE PlacementController SHALL rotate the preview card by 60 degrees clockwise
4. WHEN the user left-clicks on a valid hex during placement, THE PlacementController SHALL place the card and lock its rotation
5. WHEN the user presses ESC during placement, THE CombatScene SHALL cancel placement and return to normal mode
6. WHEN a card is placed, THE card rotation SHALL be permanently locked and stored in card data

### Requirement 6: Rotation Lock Mechanism

**User Story:** As a player, I want card rotations to be locked after placement, so that unit orientations remain stable during gameplay.

#### Acceptance Criteria

1. WHEN a card is placed on the board, THE system SHALL set is_rotation_locked to True
2. WHEN a card has is_rotation_locked set to True, THE system SHALL prevent any rotation changes
3. WHEN rendering a placed card, THE system SHALL use the locked rotation value
4. THE rotation value SHALL be stored in the card data and persist across scene transitions

### Requirement 7: Snap-to-Grid Placement

**User Story:** As a player, I want cards to snap to hex centers during placement, so that positioning is precise and consistent.

#### Acceptance Criteria

1. WHEN in placement mode, THE CombatScene SHALL convert mouse position to the nearest hex coordinate
2. WHEN displaying the placement preview, THE CombatScene SHALL render the ghost card at the hex center position
3. WHEN a card is placed, THE card SHALL be positioned at the exact hex center
4. THE system SHALL NOT support free-form card positioning outside of hex centers

### Requirement 8: Edge Stats Rendering

**User Story:** As a player, I want to see unit stats at hex edges, so that I can evaluate tactical positioning.

#### Acceptance Criteria

1. WHEN rendering a placed card, THE CombatScene SHALL render stat values at each of the six hex edges
2. THE edge stat positions SHALL be rotated based on the card's locked rotation
3. THE edge stat text SHALL always be rendered upright for readability
4. WHEN a card is rotated, THE stat-to-edge mapping SHALL shift accordingly

### Requirement 9: Hover Interaction and Flip Animation

**User Story:** As a player, I want cards to flip when I hover over them, so that I can inspect unit details.

#### Acceptance Criteria

1. WHEN the mouse hovers over a hex with a card, THE CombatScene SHALL update the hovered_hex in UIState
2. WHEN a hex is hovered, THE AnimationController SHALL interpolate flip_value toward 1.0
3. WHEN a hex is not hovered, THE AnimationController SHALL interpolate flip_value toward 0.0
4. THE flip animation SHALL complete in 0.3 seconds using cosine easing
5. WHEN flip_value is less than 0.5, THE system SHALL render the card back image
6. WHEN flip_value is greater than or equal to 0.5, THE system SHALL render the card front image

### Requirement 10: Visual Debug Mode

**User Story:** As a developer, I want a visual debug mode, so that I can verify coordinate system accuracy.

#### Acceptance Criteria

1. WHEN the user presses F3, THE CombatScene SHALL toggle debug mode
2. WHEN debug mode is active, THE CombatScene SHALL render crosshairs at each hex center
3. WHEN debug mode is active, THE CombatScene SHALL render coordinate labels for each hex
4. WHEN debug mode is active, THE CombatScene SHALL display mouse position and detected hex coordinate
5. WHEN debug mode is active, THE CombatScene SHALL render a red rectangle showing grid bounds

### Requirement 11: Asset Loading Pre-load

**User Story:** As a developer, I want all assets pre-loaded during scene entry, so that rendering never encounters missing assets.

#### Acceptance Criteria

1. WHEN CombatScene.on_enter is called, THE scene SHALL pre-load all card assets before building hex cards
2. THE pre-load process SHALL load both front and back images for each unique card
3. WHEN pre-loading completes, THE scene SHALL validate that no assets are None
4. IF an asset fails to load during pre-load, THE AssetManager SHALL create a placeholder
5. THE scene SHALL NOT proceed to rendering until all assets are loaded or have placeholders

### Requirement 12: Error Handling for Missing Assets

**User Story:** As a player, I want the game to continue gracefully when assets are missing, so that I don't experience crashes.

#### Acceptance Criteria

1. WHEN a card asset file is not found, THE AssetManager SHALL log a warning and create an "ART MISSING" placeholder
2. WHEN a card asset fails to load due to corruption, THE AssetManager SHALL log a warning and create an "ART MISSING" placeholder
3. THE "ART MISSING" placeholder SHALL display the card name and use a neon hex visual style
4. THE system SHALL NEVER crash due to missing or corrupted asset files

### Requirement 13: Error Handling for Corrupted Card Data

**User Story:** As a developer, I want the system to handle corrupted card data gracefully, so that invalid data doesn't crash the game.

#### Acceptance Criteria

1. WHEN creating a HexCard, THE system SHALL validate card data integrity
2. IF card data is missing required attributes, THE system SHALL create a "CORRUPTED DATA" visual placeholder
3. IF card data has invalid stat values, THE system SHALL create a fallback card with default values
4. THE system SHALL log warnings for corrupted data but SHALL NOT remove cards from the board
5. THE system SHALL NEVER crash due to corrupted card data

### Requirement 14: Layout Safety Validation

**User Story:** As a developer, I want layout safety checks, so that resolution changes are detected and logged.

#### Acceptance Criteria

1. WHEN the update loop runs, THE CombatScene SHALL validate layout safety once per second
2. IF the screen resolution has changed from 1920x1080, THE system SHALL log a warning
3. IF the grid bounds overlap with UI panels, THE system SHALL log a warning
4. THE system SHALL NOT recalculate layout dynamically in response to resolution changes
5. THE system SHALL continue rendering with the original layout even if resolution changes

### Requirement 15: Input State Machine

**User Story:** As a player, I want consistent input behavior across different interaction modes, so that controls are predictable.

#### Acceptance Criteria

1. THE CombatScene SHALL maintain an input mode state with values: NORMAL, PLACING, CARD_DETAIL, PAUSED
2. WHEN in NORMAL mode and ESC is pressed, THE system SHALL enter PAUSED mode
3. WHEN in PLACING mode and ESC is pressed, THE system SHALL cancel placement and return to NORMAL mode
4. WHEN in CARD_DETAIL mode and ESC is pressed, THE system SHALL close the detail view and return to the previous mode
5. THE input state machine SHALL use a stack to support nested modes
6. THE system SHALL route input handling based on the current input mode

### Requirement 16: Scene Transition Data Integrity

**User Story:** As a developer, I want zero data loss during scene transitions, so that game state remains consistent.

#### Acceptance Criteria

1. WHEN transitioning from ShopScene to CombatScene, THE SceneManager SHALL pass the same CoreGameState instance by reference
2. WHEN CombatScene.on_enter is called, THE scene SHALL validate that CoreGameState is not None
3. WHEN CombatScene.on_enter is called, THE scene SHALL validate that the game has at least one player
4. THE scene transition SHALL NOT serialize or deserialize game state
5. THE CoreGameState SHALL serve as the single source of truth across all scenes

### Requirement 17: Performance Target

**User Story:** As a player, I want smooth 60 FPS performance, so that the game feels responsive.

#### Acceptance Criteria

1. THE CombatScene SHALL maintain 60 frames per second during normal operation
2. THE total frame rendering time SHALL NOT exceed 16.67 milliseconds
3. THE pixel_to_hex conversion SHALL complete in less than 1 millisecond
4. THE flip animation update for all 37 hexes SHALL complete in less than 2 milliseconds
5. THE rendering of all hex cards SHALL complete in less than 12 milliseconds

### Requirement 18: Coordinate Consistency Validation

**User Story:** As a developer, I want automated coordinate consistency checks, so that coordinate drift is detected early.

#### Acceptance Criteria

1. WHEN CombatScene.on_enter is called, THE scene SHALL run a coordinate consistency check
2. FOR ALL 37 hexes, THE check SHALL verify that hex_to_pixel followed by pixel_to_hex returns the original coordinate
3. IF any coordinate drift is detected, THE system SHALL raise an AssertionError with details
4. IF the consistency check passes, THE system SHALL log a success message

### Requirement 19: Placement Preview Visual Feedback

**User Story:** As a player, I want clear visual feedback during card placement, so that I know where the card will be placed.

#### Acceptance Criteria

1. WHEN in placement mode with a valid hex, THE system SHALL render a bright cyan border around the hex
2. WHEN in placement mode with an invalid hex, THE system SHALL render a bright red border around the hex
3. WHEN in placement mode, THE system SHALL render a semi-transparent ghost card at the preview hex with alpha value 120
4. THE ghost card SHALL be rendered with the current preview rotation
5. THE system SHALL NOT render particle effects, glow effects, or animation trails during placement

### Requirement 20: Player Strategy Display

**User Story:** As a player, I want to see player names and strategies in the right panel, so that I can identify opponents.

#### Acceptance Criteria

1. WHEN CombatScene.on_enter is called, THE scene SHALL load player strategy names from CoreGameState
2. THE right panel SHALL display a list of all players with their strategy names
3. THE right panel SHALL display HP bars for each player with color coding: green (>66%), yellow (33-66%), red (<33%)
4. THE current player SHALL be highlighted with a gold border
5. IF a player has no strategy name set, THE system SHALL use "Player {id}" as a fallback
