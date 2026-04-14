# Implementation Plan: Combat Scene 37-Hex Rebuild

## Overview

This plan implements a complete architectural rebuild of the combat scene for a pygame-based autochess game. The implementation follows a strict 4-phase approach: skeleton and geometry first, then UI layout, then assets and rendering, and finally interaction mechanics. Each phase builds incrementally with validation checkpoints to ensure the foundation is solid before proceeding.

The combat scene displays a 37-hex radial grid (radius=3) with unit cards, integrates with existing CoreGameState and HexSystem, and provides a fixed UI layout with strict no-overlap rules. The design prioritizes deterministic geometry, crash-proof rendering, and instant scene transitions while maintaining 60 FPS performance.

## Tasks

### Phase 1: İskelet ve Geometri (Sadece Grid ve Debug)

- [x] 1. Create CombatScene class structure and file organization
  - Create `scenes/combat_scene.py` with CombatScene class extending Scene
  - Define class attributes: hex_size, origin_x, origin_y, grid_area, hex_system
  - Implement lifecycle methods: on_enter(), on_exit(), handle_input(), update(), draw()
  - Add imports for CoreGameState, UIState, HexSystem, SceneManager
  - _Requirements: 1.1, 16.1, 16.2_

- [x] 2. Implement layout calculation system
  - [x] 2.1 Create LayoutCalculator helper class
    - Implement calculate_hex_size() with 15% safety margin
    - Implement calculate_grid_origin() for exact centering
    - Implement verify_no_overlap() with assertion checks
    - _Requirements: 1.3, 1.4, 2.6_
  
  - [x] 2.2 Implement _calculate_board_layout() in CombatScene
    - Define fixed constants: SCREEN_WIDTH=1920, SCREEN_HEIGHT=1080, panel widths
    - Calculate available grid area between UI panels
    - Call LayoutCalculator to compute hex_size and origin
    - Store calculated values in instance variables
    - _Requirements: 1.2, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Initialize HexSystem with calculated parameters
  - In on_enter(), create HexSystem instance with hex_size and origin
  - Generate 37-hex radial grid using HexSystem.radial_grid(radius=3)
  - Store grid reference for coordinate conversions
  - _Requirements: 1.1, 3.5_

- [x] 4. Implement basic hex grid rendering
  - [x] 4.1 Create _draw_hex_grid() method
    - Iterate over all 37 hex coordinates from HexSystem
    - Convert each hex coordinate to pixel position using hex_to_pixel()
    - Draw hex outline using pygame.draw.polygon() with hex corners
    - Use 1px white lines with 50% alpha
    - _Requirements: 1.5, 3.1_
  
  - [x] 4.2 Implement hex corner calculation helper
    - Create _get_hex_corners() method for flat-top orientation
    - Calculate 6 corner positions at angles: 0°, 60°, 120°, 180°, 240°, 300°
    - Return list of (x, y) tuples for polygon drawing
    - _Requirements: 1.5_

- [x] 5. Implement F3 Debug Mode
  - [x] 5.1 Add debug mode toggle and state
    - Add self.debug_mode = False in __init__()
    - Handle F3 key press in handle_input() to toggle debug_mode
    - Log debug mode state changes to console
    - _Requirements: 10.1_
  
  - [x] 5.2 Create _draw_debug_overlay() method
    - Draw crosshairs at each hex center (yellow, 20px cross)
    - Render coordinate labels (q, r) at each hex with black background
    - Display mouse position and detected hex coordinate in top-left panel
    - Show grid origin and hex_size values
    - Draw red rectangle showing grid bounds
    - _Requirements: 10.2, 10.3, 10.4, 10.5_
  
  - [x] 5.3 Implement coordinate consistency validation
    - Create _validate_coordinate_consistency() method
    - For each hex: convert to pixel, then back to hex, verify match
    - Raise AssertionError if any coordinate drift detected
    - Call validation in on_enter() after HexSystem initialization
    - _Requirements: 18.1, 18.2, 18.3_

- [x] 6. Checkpoint - Grid geometry validation
  - Run the game and press F3 to enable debug mode
  - Verify exactly 37 hexes are visible and centered on screen
  - Verify coordinate labels match expected (q, r) values
  - Verify mouse hover correctly identifies hex coordinates
  - Verify grid bounds rectangle does not overlap with panel areas
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: UI ve Layout (The 3-Wing Architecture)

- [x] 7. Implement void background rendering
  - Create _draw_void_background() method
  - Fill screen with solid dark color or space gradient
  - Call as first layer in draw() method (Z=0)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 8. Implement left panel (Passive Information)
  - [x] 8.1 Create _draw_left_panel() method
    - Draw semi-transparent dark background (300px width, rgba: 20,20,40,200)
    - Draw 2px cyan border glow
    - Position: x=0, y=TOP_MARGIN, height=SCREEN_HEIGHT-TOP_MARGIN-BOTTOM_HUB_HEIGHT
    - _Requirements: 2.1_
  
  - [x] 8.2 Add passive icons placeholder section
    - Draw "Passive Icons" label at y_offset=20
    - Render 5 placeholder squares (64x64) with 10px vertical spacing
    - Use colored squares as placeholders (will be replaced with actual icons later)
    - _Requirements: 2.1_
  
  - [x] 8.3 Add passive description placeholder section
    - Draw "Passive Description" label at y_offset=400
    - Create text area (260x200) with border
    - Render placeholder text: "Hover over passive to see description"
    - _Requirements: 2.1_

- [x] 9. Implement right panel (Player Information)
  - [x] 9.1 Create _draw_right_panel() method
    - Draw semi-transparent dark background (300px width, rgba: 20,20,40,200)
    - Draw 2px magenta border glow
    - Position: x=SCREEN_WIDTH-300, y=TOP_MARGIN, height=SCREEN_HEIGHT-TOP_MARGIN-BOTTOM_HUB_HEIGHT
    - _Requirements: 2.2_
  
  - [x] 9.2 Add player list placeholder section
    - Draw "Players" label at y_offset=20
    - Render 8 placeholder entries (80px height each)
    - Each entry: player name placeholder + HP bar placeholder (250x20)
    - Use colored rectangles for HP bars (green, yellow, red based on percentage)
    - _Requirements: 2.2, 20.3_
  
  - [x] 9.3 Add synergy icons placeholder section
    - Draw "Synergies" label at y_offset=700
    - Create 4x2 grid of placeholder squares (48x48)
    - Use colored squares as placeholders
    - _Requirements: 2.2_

- [x] 10. Implement bottom hub (Strategic Information)
  - [x] 10.1 Create _draw_strategic_bottom_hub() method
    - Draw semi-transparent dark background (150px height, rgba: 20,20,40,220)
    - Draw 2px top border with white glow
    - Position: x=0, y=SCREEN_HEIGHT-150, width=SCREEN_WIDTH, height=150
    - _Requirements: 2.3_
  
  - [x] 10.2 Add economy stats placeholders
    - Gold display at x_offset=50 (icon + "Gold: 50" text)
    - Income display at x_offset=250 (icon + "Income: +5" text)
    - Combo score at x_offset=450 (icon + "Combo: 3x" text)
    - Combat power at x_offset=650 (icon + "Power: 120" text)
    - Use colored circles as icon placeholders
    - _Requirements: 2.3_
  
  - [x] 10.3 Add synergy indicators placeholders
    - Active synergies at x_offset=900 (label + 6 icon placeholders)
    - Potential synergies at x_offset=1400 (label + icon placeholders, semi-transparent)
    - Use colored squares as placeholders
    - _Requirements: 2.3_

- [x] 11. Implement rendering order and overlap testing
  - [x] 11.1 Update draw() method with strict layer order
    - Layer 0: _draw_void_background()
    - Layer 1: _draw_hex_grid()
    - Layer 5: _draw_left_panel(), _draw_right_panel(), _draw_strategic_bottom_hub()
    - Layer 7: _draw_debug_overlay() (if debug_mode)
    - _Requirements: 2.5, 2.6_
  
  - [x] 11.2 Implement layout safety validation
    - Create _validate_layout_safety() method
    - Check screen resolution matches 1920x1080
    - Verify grid bounds do not overlap with any panel
    - Log warnings if issues detected
    - Call validation once per second in update()
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 12. Checkpoint - UI layout validation
  - Run the game and verify all three panels are visible
  - Verify panels have correct colors and borders
  - Verify placeholder content is visible in each panel
  - Verify hex grid does not overlap with any panel
  - Press F3 and verify grid bounds rectangle stays within available area
  - Ensure all tests pass, ask the user if questions arise.

### Phase 3: Varlıklar ve Animasyon (Assets & Rendering)

- [x] 13. Implement AssetManager for card image loading
  - [x] 13.1 Create AssetManager class
    - Add card_images cache dictionary
    - Add placeholder_cache dictionary
    - Implement __init__() to initialize caches
    - _Requirements: 4.4_
  
  - [x] 13.2 Implement load_card_image() method
    - Check cache first, return if found
    - Construct file path: assets/cards/{card_name}_{face}.png
    - Special case for Yggdrasil: check .png then .jpg
    - Try to load image with pygame.image.load()
    - On failure or missing file: create placeholder
    - Cache result and return (NEVER return None)
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 7.1, 7.2_
  
  - [x] 13.3 Implement create_placeholder() method
    - Create pygame.Surface with given dimensions
    - Generate deterministic neon color from card_name hash
    - Draw hex shape with neon border
    - Render card name text in center
    - Cache and return placeholder
    - _Requirements: 4.6, 10.1_
  
  - [x] 13.4 Implement _create_art_placeholder() for missing assets
    - Create neon-styled placeholder with "ART MISSING" label
    - Use hash-based color generation for visual distinction
    - Draw animated glow effect (pulsing borders)
    - Render "ART MISSING" text and card name
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 14. Implement asset pre-loading system
  - [x] 14.1 Create _preload_all_assets() method
    - Collect all unique card names from CoreGameState
    - For each card: load front and back images
    - Validate assets are not None (assert)
    - Log progress for each loaded card
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [x] 14.2 Create _create_corrupted_visual() for data errors
    - Create glitch-style visual with red/black color scheme
    - Draw random red glitch lines (deterministic based on label)
    - Render "CORRUPTED DATA" text
    - _Requirements: 13.2, 13.3, 13.4, 13.5_
  
  - [x] 14.3 Implement _validate_card_data() method
    - Check required attributes exist (name, stats)
    - Validate stat values are integers in range 0-99
    - Return False if validation fails
    - _Requirements: 13.1_
  
  - [x] 14.4 Implement _create_fallback_card() method
    - Create Card object with safe default values
    - Use hex coordinate in name for uniqueness
    - Set all stats to 1, cost to 0
    - _Requirements: 13.3_

- [x] 15. Implement HexCard data structure and building
  - [x] 15.1 Create HexCard dataclass
    - Define fields: hex_coord, card_data, front_image, back_image, position, hex_size, rotation, placement_state, is_rotation_locked, flip_value, flip_value_eased
    - Add default values for flip_value (0.0) and flip_value_eased (0.0)
    - _Requirements: 5.4, 6.1, 6.2_
  
  - [x] 15.2 Implement _build_hex_cards() method
    - Get current player's board from CoreGameState
    - Iterate over board.grid dictionary
    - For each non-None card: call _create_hex_card()
    - Store resulting HexCard objects in self.hex_cards list
    - _Requirements: 16.3_
  
  - [x] 15.3 Implement _create_hex_card() method
    - Validate card data with _validate_card_data()
    - Load front and back images via AssetManager
    - On data corruption: use corrupted visual and fallback card
    - Convert hex coordinate to pixel position
    - Create HexCard object with all required fields
    - Return HexCard (never None)
    - _Requirements: 4.1, 4.2, 4.3, 13.2, 13.3_

- [x] 16. Implement flip animation system
  - [x] 16.1 Create AnimationController class
    - Add reference to UIState
    - Implement __init__() to store ui_state reference
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 16.2 Implement update_flip_animations() method
    - Get hovered_hex from UIState
    - For each hex_card: determine target flip value (1.0 if hovered, 0.0 otherwise)
    - Interpolate current flip_value toward target using flip_speed * dt
    - Apply cosine easing: flip_value_eased = (1 - cos(π * flip_value)) / 2
    - Skip animation if already at target (optimization)
    - _Requirements: 9.2, 9.3, 9.4_
  
  - [x] 16.3 Update CombatScene.update() to call animation controller
    - Create AnimationController instance in on_enter()
    - Call animation_controller.update_flip_animations(dt) in update()
    - _Requirements: 9.2, 9.3_

- [x] 17. Implement card rendering with flip animation
  - [x] 17.1 Create HexCardRenderer class
    - Add references to HexSystem and AssetManager
    - Implement __init__() to store references
    - _Requirements: 9.5, 9.6_
  
  - [x] 17.2 Implement render_card() method
    - Determine which image to show based on flip_value (< 0.5: back, >= 0.5: front)
    - Calculate horizontal scale factor for flip effect
    - Scale image width (horizontal flip)
    - Skip rendering if scaled width < 2 pixels (optimization)
    - Blit scaled image centered at card position
    - _Requirements: 9.5, 9.6, 17.1_
  
  - [x] 17.3 Implement render_hex_border() method
    - Get hex corners using _get_hex_corners()
    - Draw polygon outline with specified color
    - Use pygame.draw.polygon() with width parameter
    - _Requirements: 1.5_
  
  - [x] 17.4 Create _draw_hex_cards() method in CombatScene
    - Iterate over self.hex_cards list
    - For each hex_card: call hex_card_renderer.render_card()
    - Pass screen, hex_card, and flip_value_eased
    - Call in draw() method at Layer 2
    - _Requirements: 9.5, 9.6_

- [x] 18. Implement hover interaction
  - [x] 18.1 Update handle_input() to detect hovered hex
    - Get mouse position from input_state
    - Convert pixel to hex using hex_system.pixel_to_hex()
    - Check if hex is in grid
    - Update ui_state.hovered_hex
    - _Requirements: 9.1_
  
  - [x] 18.2 Implement hover highlight rendering
    - In _draw_hex_cards(), check if hex is hovered
    - If hovered: draw cyan glow border (2px, 80% alpha)
    - Use hex_card_renderer.render_hex_border()
    - Render at Layer 4 (after cards, before UI panels)
    - _Requirements: 9.1_

- [x] 19. Integrate with scene lifecycle
  - [x] 19.1 Update on_enter() to initialize all components
    - Call _calculate_board_layout()
    - Create HexSystem instance
    - Call _validate_coordinate_consistency()
    - Call _preload_all_assets()
    - Call _build_hex_cards()
    - Create AnimationController
    - Reset UIState for combat scene
    - _Requirements: 11.1, 11.2, 16.1, 16.2, 16.3_
  
  - [x] 19.2 Implement _load_player_strategies() method
    - Read strategy names from CoreGameState.game.players
    - Use fallback "Player {id}" if strategy_name not set
    - Store in self.player_strategies dictionary
    - _Requirements: 20.1, 20.2, 20.5_
  
  - [x] 19.3 Update on_exit() to clean up resources
    - Clear hex_cards list
    - Clear UIState references
    - Log scene exit
    - _Requirements: 16.4_

- [x] 20. Checkpoint - Asset loading and rendering
  - Run the game and verify cards are visible on the hex grid
  - Verify Yggdrasil card loads correctly (if present)
  - Verify missing assets show "ART MISSING" placeholder
  - Hover over cards and verify flip animation works smoothly
  - Verify flip animation completes in ~0.3 seconds
  - Verify no crashes occur with missing or corrupted assets
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: Etkileşim (Input State Machine & Placement)

- [x] 21. Implement input state machine
  - [x] 21.1 Create InputMode enum
    - Define states: NORMAL, PLACING, CARD_DETAIL, PAUSED
    - _Requirements: 15.1_
  
  - [x] 21.2 Add input mode management to CombatScene
    - Add self.input_mode = InputMode.NORMAL
    - Add self.input_stack = [] for nested modes
    - Implement push_input_mode() to push new mode onto stack
    - Implement pop_input_mode() to return to previous mode
    - _Requirements: 15.5_
  
  - [x] 21.3 Implement input routing by mode
    - Update handle_input() to route based on input_mode
    - Create _handle_input_normal() for NORMAL mode
    - Create _handle_input_placing() for PLACING mode
    - Create _handle_input_card_detail() for CARD_DETAIL mode
    - Create _handle_input_paused() for PAUSED mode
    - _Requirements: 15.6_

- [x] 22. Implement ESC key handling for each mode
  - [x] 22.1 Handle ESC in NORMAL mode
    - Push PAUSED mode onto stack
    - Open pause menu (placeholder)
    - _Requirements: 15.2_
  
  - [x] 22.2 Handle ESC in PLACING mode
    - Call _cancel_placement() to clean up
    - Pop input mode to return to NORMAL
    - _Requirements: 15.3_
  
  - [x] 22.3 Handle ESC in CARD_DETAIL mode
    - Close card detail view
    - Pop input mode to return to previous mode
    - _Requirements: 15.4_
  
  - [x] 22.4 Handle ESC in PAUSED mode
    - Close pause menu
    - Pop input mode to return to previous mode
    - _Requirements: 15.2_

- [x] 23. Implement PlacementController
  - [x] 23.1 Create PlacementController class
    - Add references to CoreGameState, UIState, HexSystem
    - Add fields: selected_card, preview_hex, preview_rotation
    - Implement __init__() to store references
    - _Requirements: 5.1, 5.2_
  
  - [x] 23.2 Implement handle_card_selection() method
    - Store selected card reference
    - Set preview_rotation to 0
    - Update UIState.is_placing to True
    - _Requirements: 5.1_
  
  - [x] 23.3 Implement is_valid_placement() method
    - Check if hex is in grid
    - Check if hex is empty (not in board.grid)
    - Check if hex is within player's board area
    - Return True if all checks pass
    - _Requirements: 5.2, 7.1_
  
  - [x] 23.4 Implement handle_right_click() method
    - Increment preview_rotation by 60 degrees
    - Apply modulo 360 to wrap around
    - Update UIState.preview_rotation
    - _Requirements: 5.3_
  
  - [x] 23.5 Implement handle_left_click() method
    - Validate placement with is_valid_placement()
    - Get current player's board from CoreGameState
    - Add card to board.grid at hex_coord
    - Create HexCard with locked rotation
    - Add HexCard to UIState.hex_cards
    - Return True if successful
    - _Requirements: 5.4, 6.1_

- [x] 24. Implement placement preview rendering
  - [x] 24.1 Create _render_placement_preview() method
    - Check if UIState.is_placing is True
    - Get mouse position and convert to nearest hex
    - Check if hex is valid for placement
    - If invalid: draw red border and return
    - If valid: draw cyan border
    - _Requirements: 19.1, 19.2_
  
  - [x] 24.2 Render ghost card at preview hex
    - Get card front image
    - Apply preview_rotation using pygame.transform.rotate()
    - Set alpha to 120 (47% transparency)
    - Blit at hex center position (snapped to grid)
    - _Requirements: 19.3, 19.4_
  
  - [x] 24.3 Implement _draw_hex_border_highlight() helper
    - Get hex corners using _get_hex_corners()
    - Draw polygon with specified color and 3px width
    - No particles, no glow effects, just clean line
    - _Requirements: 19.1, 19.2_
  
  - [x] 24.4 Implement _draw_invalid_hex_border() helper
    - Call _draw_hex_border_highlight() with red color
    - _Requirements: 19.2_

- [x] 25. Implement rotation mechanics
  - [x] 25.1 Update _handle_input_placing() for right-click
    - Detect right-click from input_state
    - Call placement_controller.handle_right_click()
    - _Requirements: 5.3_
  
  - [x] 25.2 Implement rotation lock on placement
    - In handle_left_click(): set card.rotation to preview_rotation
    - Set card.is_rotation_locked to True
    - Store rotation in HexCard object
    - _Requirements: 5.4, 6.1, 6.2_
  
  - [x] 25.3 Implement can_rotate_card() helper
    - Check if hex_card.is_rotation_locked is False
    - Return True only if rotation is not locked
    - _Requirements: 6.2_

- [x] 26. Implement edge stats rendering
  - [x] 26.1 Create _render_edge_stats() method
    - Get card rotation from hex_card
    - Define base edge positions (N, NE, SE, S, SW, NW)
    - Call _get_rotated_edge_stats() to map stats to edges
    - For each edge: calculate rotated position
    - Render stat text at position (always upright)
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 26.2 Implement _get_rotated_edge_stats() method
    - Get base stats array from card data
    - Calculate rotation offset (rotation // 60) % 6
    - Rotate stats array by offset
    - Map rotated stats to edge names
    - Return dictionary of edge_name -> stat_value
    - _Requirements: 8.2, 8.4_
  
  - [x] 26.3 Implement _render_stat_text() method
    - Render stat value as text
    - Draw background circle for contrast
    - Draw white border around circle
    - Center text on position (always upright, rotation=0)
    - _Requirements: 8.3_
  
  - [x] 26.4 Implement _rotate_point() helper
    - Apply rotation matrix to point coordinates
    - Convert rotation angle to radians
    - Return rotated (x, y) tuple
    - _Requirements: 8.2_

- [x] 27. Implement placement mode transitions
  - [x] 27.1 Implement _start_placement() method
    - Set placement_controller.selected_card
    - Set preview_rotation to 0
    - Set UIState.is_placing to True
    - Push PLACING input mode
    - _Requirements: 5.1_
  
  - [x] 27.2 Implement _cancel_placement() method
    - Clear placement_controller.selected_card
    - Clear preview_hex and preview_rotation
    - Set UIState.is_placing to False
    - Log cancellation message
    - _Requirements: 15.3_
  
  - [x] 27.3 Update _handle_input_normal() for card selection
    - Detect left-click on hand area
    - Call _get_card_at_hand_position() to find clicked card
    - If card found: call _start_placement()
    - _Requirements: 5.1_

- [x] 28. Implement snap-to-grid placement
  - [x] 28.1 Update _render_placement_preview() for snap-to-grid
    - Convert mouse position to nearest hex coordinate
    - Get hex center pixel position
    - Render ghost card at hex center (not at mouse cursor)
    - _Requirements: 7.2, 7.3_
  
  - [x] 28.2 Update handle_left_click_placement() for snap-to-grid
    - Convert mouse position to hex coordinate
    - Validate hex is in grid and valid for placement
    - Place card at hex center position
    - _Requirements: 7.3, 7.4_

- [x] 29. Implement scene transition data integrity
  - [x] 29.1 Validate CoreGameState in on_enter()
    - Assert CoreGameState is not None
    - Assert game is not None
    - Assert players list has at least one player
    - Log validation success
    - _Requirements: 16.2, 16.3_
  
  - [x] 29.2 Ensure CoreGameState passed by reference
    - Verify SceneManager passes same instance
    - No serialization or copying
    - Store reference in self.core_game_state
    - _Requirements: 16.1, 16.4_

- [x] 30. Implement performance optimizations
  - [x] 30.1 Add dirty flag optimization to flip animations
    - Skip animation update if flip_value already at target
    - Use threshold of 0.01 for "close enough"
    - _Requirements: 17.2_
  
  - [x] 30.2 Optimize rendering with early exits
    - Skip rendering if scaled width < 2 pixels
    - Skip rendering if card is off-screen
    - _Requirements: 17.3_
  
  - [x] 30.3 Implement layout validation throttling
    - Run layout safety check once per second (every 60 frames)
    - Use frame counter to throttle validation
    - _Requirements: 14.1_

- [x] 31. Final checkpoint - Complete integration test
  - Run the game and verify complete combat scene functionality
  - Test card selection from hand (placeholder)
  - Test placement mode: select card, see ghost preview
  - Test rotation: right-click to rotate ghost card by 60°
  - Test placement: left-click to place card, verify rotation locked
  - Test ESC cancellation: press ESC during placement, verify return to normal
  - Test hover: hover over placed cards, verify flip animation
  - Test edge stats: verify stats appear at correct edges and rotate with card
  - Test debug mode: press F3, verify all debug info visible
  - Verify 60 FPS performance maintained
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each phase builds on the previous phase - do not skip ahead
- Debug mode (F3) should be implemented early and used throughout development
- All asset loading must have fallback placeholders to prevent crashes
- Coordinate consistency validation is critical - run after any geometry changes
- Input state machine prevents state confusion - always use push/pop for mode transitions
- Rotation lock is permanent after placement - no exceptions
- Edge stats are always rendered upright regardless of card rotation
- Performance target is 60 FPS - use optimizations to stay within 16.67ms frame budget
