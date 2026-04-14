# Implementation Plan: Run Game2 UI and Placement

## Overview

This plan implements four critical systems to make run_game2.py playable: hex grid sizing for card assets, hand panel interaction with click detection and selection, left panel rendering for synergies and passives, and a complete card placement system with validation and preview. The implementation follows the migration path from the design document, building incrementally from rendering to interaction to placement logic.

## Tasks

- [ ] 1. Update hex grid sizing for card assets
  - [x] 1.1 Update HEX_SIZE constant in BoardRendererV3
    - Change HEX_SIZE from 68 to 85 in ui/board_renderer_v3.py
    - Update HexSystem initialization to use new size
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.2 Write property test for hex size calculation
    - **Property 1: Hex size accommodates card assets with padding**
    - **Validates: Requirements 1.1, 1.4, 1.5**

  - [x] 1.3 Test rendering with updated hex size
    - Run run_game2.py and verify cards fit properly in hexagons
    - Verify hex edges are visible for edge stat display
    - _Requirements: 1.3, 1.4_

- [ ] 2. Implement hand panel interaction
  - [x] 2.1 Add selection state fields to HybridGameState
    - Add selected_hand_idx: Optional[int] field
    - Add pending_rotation: int field (0-5)
    - Initialize both to None and 0 in __init__
    - _Requirements: 2.1, 2.2, 10.1_

  - [x] 2.2 Implement _get_clicked_hand_card function
    - Create function in run_game2.py to detect hand card clicks
    - Calculate hand card rectangles based on hand size
    - Return card index if click is within rect, None otherwise
    - _Requirements: 2.1_

  - [ ]* 2.3 Write property tests for hand click detection
    - **Property 2: Hand card click detection accuracy**
    - **Validates: Requirements 2.1**

  - [x] 2.4 Update handle_input to detect hand card clicks
    - Call _get_clicked_hand_card on left mouse button down
    - Toggle selection state (select if unselected, deselect if selected)
    - Move selection to new card if different card clicked
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ]* 2.5 Write property tests for selection state
    - **Property 3: Selection state toggle idempotence**
    - **Property 4: Single selection invariant**
    - **Validates: Requirements 2.2, 2.5**

  - [x] 2.6 Update draw_hand_panel to show selection and hover states
    - Add selected_idx parameter to draw_hand_panel
    - Draw cyan border for selected card
    - Draw lighter background for hovered card
    - Display rotation angle for selected card
    - Show tooltip "→hex / R:rotate / RClick:rotate" for selected card
    - _Requirements: 2.3, 2.4, 2.6, 9.1, 9.2_

  - [x] 2.7 Implement rotation controls
    - Handle R key press to increment pending_rotation
    - Handle right mouse button click to increment pending_rotation
    - Apply modulo 6 to keep rotation in range 0-5
    - _Requirements: 10.1, 10.2_

  - [ ]* 2.8 Write property tests for rotation
    - **Property 5: Rotation display consistency**
    - **Property 13: Rotation increment with wraparound**
    - **Property 14: Rotation reset on deselection**
    - **Validates: Requirements 2.6, 10.1, 10.2, 10.3, 10.5**

- [ ] 3. Checkpoint - Verify hand panel interaction
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement left panel rendering
  - [ ] 4.1 Add synergy HUD rendering to render_main_screen
    - Call draw_synergy_hud in render_main_screen
    - Position at bottom center of screen
    - Pass player and fonts
    - _Requirements: 3.1, 3.3, 3.5_

  - [ ] 4.2 Add passive buff panel rendering to render_main_screen
    - Call draw_passive_buff_panel in render_main_screen
    - Position below hand panel with appropriate spacing
    - Pass player, font, and dimensions
    - _Requirements: 3.2, 3.4, 3.6_

  - [ ] 4.3 Test left panel rendering
    - Run run_game2.py with active synergies
    - Verify synergy badges display with correct counts
    - Verify passive buff log displays entries
    - _Requirements: 3.3, 3.4_

- [ ] 5. Implement hex click detection and coordinate conversion
  - [ ] 5.1 Implement _get_clicked_hex function
    - Create function in run_game2.py to convert mouse clicks to hex coordinates
    - Use HexSystem.pixel_to_hex with cube rounding
    - Validate coordinate is in BOARD_COORDS
    - Return (q, r) if valid, None otherwise
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.2 Write property tests for coordinate conversion
    - **Property 6: Coordinate conversion round-trip**
    - **Property 7: Coordinate validation correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [ ] 5.3 Update BoardRendererV3.update_hover to use HexSystem
    - Implement update_hover method to convert mouse position to hex
    - Set hovered_coord if coordinate is in board_coords
    - _Requirements: 4.1, 4.2, 7.4_

  - [ ] 5.4 Update handle_input to track hover state
    - Call board_renderer.update_hover on mouse motion
    - Pass mouse position and BOARD_COORDS
    - _Requirements: 9.3_

- [ ] 6. Implement placement validation
  - [ ] 6.1 Add placement tracking fields to HybridGameState
    - Add placed_this_turn: int field
    - Add locked_coords_per_player: Dict[int, Set[Tuple[int, int]]] field
    - Initialize to 0 and empty dict in __init__
    - _Requirements: 5.3, 8.1, 8.2_

  - [ ] 6.2 Implement is_valid_placement function
    - Create function in run_game2.py to validate placement attempts
    - Check if target hex is empty (not in board.grid)
    - Check if target hex is not in locked_coords
    - Check if placed_this_turn < PLACE_PER_TURN
    - Return (True, "") or (False, error_message)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 6.3 Write property tests for placement validation
    - **Property 8: Empty hex validation**
    - **Property 9: Locked coordinate validation**
    - **Property 10: Placement limit enforcement**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ] 7. Implement card placement execution
  - [ ] 7.1 Implement place_card_from_hand function
    - Create function in run_game2.py to execute card placement
    - Get card from player.hand at hand_idx
    - Apply rotation to card
    - Remove card from hand
    - Add card to board at target coordinate
    - Add target coordinate to locked_coords
    - Increment placed_this_turn
    - Clear selection state (selected_hand_idx = None, pending_rotation = 0)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 7.2 Write property tests for placement execution
    - **Property 11: Placement state updates**
    - **Property 12: Rotation application**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 10.4**

  - [ ] 7.3 Update handle_input to handle hex clicks for placement
    - Call _get_clicked_hex on left mouse button down when card selected
    - Call is_valid_placement to validate target hex
    - Call place_card_from_hand if valid
    - Display error message if invalid
    - _Requirements: 5.4, 6.1, 6.7, 9.5_

- [ ] 8. Checkpoint - Verify placement execution
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement placement preview
  - [ ] 9.1 Implement draw_placement_preview in BoardRendererV3
    - Create method to render semi-transparent card at target position
    - Use alpha=180 for preview rendering
    - Apply current rotation to preview card
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 9.2 Update render_main_screen to show placement preview
    - Check if card is selected and mouse is over valid hex
    - Call board_renderer.draw_placement_preview with selected card and rotation
    - _Requirements: 7.1, 7.4, 7.5_

  - [ ] 9.3 Test placement preview
    - Run run_game2.py and select a hand card
    - Move mouse over board and verify preview appears
    - Rotate card and verify preview updates
    - Move to invalid hex and verify preview disappears
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Implement locked coordinate tracking and display
  - [ ] 10.1 Update BoardRendererV3.draw to show locked indicators
    - Add locked_coords parameter to draw method
    - Draw orange border for hexes in locked_coords
    - _Requirements: 8.4, 9.4_

  - [ ] 10.2 Update render_main_screen to pass locked coordinates
    - Get locked_coords for current player from state.locked_coords_per_player
    - Pass to board_renderer.draw
    - _Requirements: 8.1, 8.4_

  - [ ] 10.3 Update step_turn_hybrid to clear locked coordinates
    - Clear all locked_coords_per_player sets at turn end
    - Reset placed_this_turn to 0 at turn start
    - _Requirements: 8.3, 8.1_

  - [ ]* 10.4 Write property tests for locked coordinate tracking
    - **Property 15: Locked coordinates accumulation**
    - **Property 16: Locked coordinates cleanup**
    - **Validates: Requirements 8.2, 8.3**

  - [ ] 10.5 Test locked coordinate system
    - Run run_game2.py and place a card
    - Verify orange border appears on placed hex
    - Attempt to place another card on same hex
    - Verify rejection with error message
    - End turn and verify locked indicator disappears
    - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Implement state reset logic
  - [ ] 11.1 Add state reset on turn start
    - Reset selected_hand_idx to None in step_turn_hybrid
    - Reset pending_rotation to 0 in step_turn_hybrid
    - Reset placed_this_turn to 0 in step_turn_hybrid
    - _Requirements: 2.2, 10.5_

  - [ ] 11.2 Add state reset on player switch
    - Reset selected_hand_idx to None when view_player changes
    - Reset pending_rotation to 0 when view_player changes
    - _Requirements: 2.2, 10.5_

  - [ ] 11.3 Add state reset on ESC key
    - Handle ESC key press to clear selection
    - Reset selected_hand_idx to None
    - Reset pending_rotation to 0
    - _Requirements: 2.2, 10.5_

- [ ] 12. Final integration and testing
  - [ ] 12.1 Run complete placement flow test
    - Select card from hand
    - Rotate card 3 times
    - Click valid hex
    - Verify card placed with correct rotation
    - Verify locked indicator appears
    - Verify selection cleared
    - _Requirements: 2.1, 2.2, 6.1, 6.2, 6.7, 8.2, 8.4, 10.4_

  - [ ] 12.2 Test placement limit enforcement
    - Place 1 card (PLACE_PER_TURN = 1)
    - Attempt to place another card
    - Verify rejection with error message "Placement limit reached (1/turn)"
    - _Requirements: 5.3, 5.4, 9.5_

  - [ ] 12.3 Test visual feedback for all interactions
    - Verify hand card selection indicator (cyan border)
    - Verify hand card hover effect (lighter background)
    - Verify hex hover highlight (cyan border)
    - Verify locked coordinate indicator (orange border)
    - Verify placement preview with rotation
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 12.4 Run full property-based test suite
    - Execute all 16 property tests with Hypothesis
    - Verify all properties pass with 100+ examples
    - Fix any failures discovered by property tests

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties using Hypothesis
- The implementation follows the migration path: sizing → interaction → rendering → placement
- HEX_SIZE update from 68 to 85 is critical for card asset display
- All coordinate conversions must use HexSystem.pixel_to_hex with cube rounding
- Locked coordinates prevent card movement within the same turn (strategic constraint)
- PLACE_PER_TURN is currently 1, limiting placements per turn
