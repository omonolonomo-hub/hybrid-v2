# Implementation Plan: Board and Shop UI Cleanup v3

## Overview

This implementation plan converts the design into discrete coding tasks for implementing a clean tarot-style UI for board and shop cards. The changes remove visual clutter (glow, aura, medallions, badges) and replace them with rarity-based geometric frames, real stat displays, and a hover compare mode with mini board sidebar.

## Tasks

- [x] 1. Implement tarot-style hex frame rendering for board cards
  - [x] 1.1 Create `_draw_tarot_frame()` method in CyberRenderer
    - Add method signature: `_draw_tarot_frame(surface, cx, cy, r, rarity_col, rarity_level, highlight)`
    - Implement rarity-level geometry mapping (1-5, E→6)
    - Level 1: Single thin contour line
    - Level 2: Corner tick marks + double contour
    - Level 3: Double thin contour (outer + inner)
    - Level 4: Double contour + inner diagonal motif lines
    - Level 5/E: Corner ornaments + bronze/gold accent ring
    - Use `_hex_corners()` helper for polygon calculation
    - _Requirements: 1.5, 1.6, 1.7_

  - [x] 1.2 Write property test for tarot frame geometry distinctness
    - **Property 1: Rarity Frame Geometry Distinctness**
    - **Validates: Requirements 1.5, 1.6**
    - Generate cards with different rarity values (1-5, E)
    - Render each card and extract frame geometry features
    - Assert that frames for different rarities produce visually distinct patterns
    - Use hypothesis library with minimum 100 iterations

- [x] 2. Remove visual clutter from board card rendering
  - [x] 2.1 Modify `draw_hex_card()` to remove deprecated effects
    - Remove `draw_board_pizzazz()` call (glow effects)
    - Remove aura ring rendering code
    - Remove circle medallion rendering
    - Remove boxed edge badge rendering
    - Add call to `_draw_tarot_frame()` after hex body fill
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Write integration test for visual clutter removal
    - Verify no glow, aura, medallion, or badge rendering occurs
    - Test with cards of all rarity levels
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement edge stat positioning without badges
  - [x] 3.1 Modify edge stat rendering in `draw_hex_card()`
    - Use `card.rotated_edges()` to get rotation-aware edge list
    - For each edge with value > 0:
      - Calculate edge midpoint using `_edge_midpoint(corners, i)`
      - Position stat value near midpoint using `_toward_center()` with `EDGE_LABEL_INSET`
      - Map stat to upper-group via `STAT_TO_GROUP`
      - Render stat value in upper-group color from `GROUP_COLORS`
    - Skip rendering for edges with value == 0
    - Remove any badge or background shape rendering
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 Write property test for edge stat positioning accuracy
    - **Property 2: Edge Stat Positioning Accuracy**
    - **Validates: Requirements 2.1**
    - Generate cards with various edge configurations
    - Render card and extract stat positions
    - Assert each stat is within 15 pixels of its edge midpoint

  - [x] 3.3 Write property test for non-zero edge stat visibility
    - **Property 3: Non-Zero Edge Stat Visibility**
    - **Validates: Requirements 2.4**
    - Generate cards with mixed zero/non-zero edges
    - Render card and extract visible stats
    - Assert all edges with value > 0 are rendered

  - [x] 3.4 Write property test for zero edge stat invisibility
    - **Property 4: Zero Edge Stat Invisibility**
    - **Validates: Requirements 2.5**
    - Generate cards with some zero-value edges
    - Render card and extract visible stats
    - Assert no edges with value == 0 are rendered

- [ ] 4. Checkpoint - Ensure board rendering tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement shop card real stats display
  - [x] 5.1 Modify `draw_shop_stat_grid()` for real stats
    - Extract edge source: `card.edges` or `card.stats.items()`
    - Filter to real_stats: `[(name, val) for name, val in edges if val > 0 and not name.startswith("_")]`
    - Calculate grid layout: 2 columns, rows = ceil(len(real_stats) / 2)
    - For each stat:
      - Map stat_name to upper_group via `STAT_TO_GROUP`
      - Get color from `GROUP_COLORS[upper_group]`
      - Draw cell background with upper-group color border
      - Render stat short name from `STAT_SHORT`
      - Render stat value
    - Return early if no real_stats
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.2 Write property test for shop stat zero filtering
    - **Property 5: Shop Stat Zero Filtering**
    - **Validates: Requirements 3.2**
    - Generate cards with some zero-value stats
    - Render shop card and extract displayed stats
    - Assert no stats with value == 0 appear in grid

  - [x] 5.3 Write property test for shop stat non-zero display
    - **Property 6: Shop Stat Non-Zero Display**
    - **Validates: Requirements 3.3**
    - Generate cards with non-zero stats
    - Render shop card and extract displayed stats
    - Assert all stats with value > 0 are rendered with name and value

  - [ ] 5.4 Write property test for upper-group color consistency
    - **Property 7: Upper-Group Color Consistency**
    - **Validates: Requirements 3.4**
    - Generate cards with multiple stats in same upper-group
    - Render shop card and extract stat colors
    - Assert stats in same upper-group use same color family

- [x] 6. Implement shop card tarot-style title plate
  - [x] 6.1 Add title plate rendering to `draw_shop_card()`
    - Calculate title plate rect at bottom of card (30px height)
    - Draw background with rarity border
    - Draw rarity accent strip at top (3px height)
    - Render card name (truncated if needed using `_truncate_to_width()`)
    - Position cost medallion on right side
    - Use consistent styling across all rarity levels
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 6.2 Write property test for title plate name display
    - **Property 8: Title Plate Name Display**
    - **Validates: Requirements 4.2**
    - Generate cards with various names
    - Render shop card and extract title plate content
    - Assert card name appears in title plate

  - [x] 6.3 Write property test for title plate rarity consistency
    - **Property 9: Title Plate Rarity Consistency**
    - **Validates: Requirements 4.5**
    - Generate cards with different rarities
    - Render shop cards and extract title plate styling
    - Assert consistent styling (excluding rarity-specific accents)

- [x] 7. Re-proportion shop card layout
  - [x] 7.1 Update `draw_shop_card()` layout sections
    - Define section heights: ribbon (22px), cameo (92px), stats (92px), passive (56px), title plate (30px)
    - Adjust vertical positioning for each section
    - Ensure all elements fit within card bounds (CARD_H = 360px)
    - Maintain proper spacing between sections
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 10.1, 10.2, 10.3, 10.4_

  - [x] 7.2 Write property test for shop card element visibility
    - **Property 10: Shop Card Element Visibility**
    - **Validates: Requirements 5.3**
    - Generate various shop cards
    - Render cards and verify all elements within bounds
    - Assert no clipping occurs for ribbon, cameo, stats, passive, title plate

  - [x] 7.3 Write property test for shop layout adaptation
    - **Property 21: Shop Layout Adaptation**
    - **Validates: Requirements 10.5**
    - Generate cards with fewer than 6 non-zero stats
    - Render shop cards and measure layout
    - Assert stats grid adjusts to avoid large empty spaces

- [ ] 8. Checkpoint - Ensure shop rendering tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement hover compare mode activation
  - [x] 9.1 Add hover state tracking to ShopScreen
    - Add `_hovered_market_card` state variable (initialized to None)
    - Update mouse motion handler to track hovered market card
    - Set `_hovered_market_card` when mouse over market card
    - Clear `_hovered_market_card` when mouse not over any card
    - _Requirements: 6.1, 6.2_

  - [x] 9.2 Create `_draw_compare_sidebar()` method
    - Check `self._hovered_market_card`
    - If None: call `_draw_synergy_sidebar()` and return
    - If not None: render mini board sidebar
    - Extract hovered card upper-groups using `STAT_TO_GROUP`
    - Draw sidebar panel background
    - Draw header: "COMPARE_MODE"
    - Draw hovered card name
    - Draw hovered card upper-groups list
    - Draw legend: "■ MATCH" (green), "■ CLASH" (red)
    - Call `_draw_mini_board(x, y, hovered_groups)`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 9.3 Write property test for hover sidebar activation
    - **Property 11: Hover Sidebar Activation**
    - **Validates: Requirements 6.1**
    - Simulate mouse hover over market card
    - Assert Mini_Board_Sidebar is displayed

  - [x] 9.4 Write property test for hover sidebar deactivation
    - **Property 12: Hover Sidebar Deactivation**
    - **Validates: Requirements 6.2**
    - Simulate mouse position not over any market card
    - Assert Mini_Board_Sidebar is hidden

  - [x] 9.5 Write property test for sidebar mutual exclusivity
    - **Property 13: Sidebar Mutual Exclusivity**
    - **Validates: Requirements 6.3**
    - Test both hover and non-hover states
    - Assert synergy sidebar and mini board sidebar never visible simultaneously

  - [x] 9.6 Write property test for synergy sidebar restoration
    - **Property 14: Synergy Sidebar Restoration**
    - **Validates: Requirements 6.4**
    - Simulate hover-end event
    - Assert synergy sidebar is restored to visible state

- [x] 10. Implement mini board sidebar with match/clash analysis
  - [x] 10.1 Create `_draw_mini_board()` method
    - Get board cards: `board_cards = list(self.player.board.grid.values())`
    - If empty: render "Board empty." message and return
    - Calculate grid layout: `cols = max(1, MAX_W // (MINI_R * 2 + 8))`, `row_h = MINI_R * 2 + 12`
    - For each card in board_cards:
      - Calculate position: `col = idx % cols`, `row = idx // cols`
      - Calculate center: `cx = start_x + col * spacing + MINI_R`, `cy = start_y + row * row_h + MINI_R`
      - Extract card upper-groups (filter stats with value > 0, map via `STAT_TO_GROUP`)
      - Determine match: `is_match = bool(card_groups & hovered_groups)`
      - Draw hex polygon with dominant group fill color
      - Draw border: green if match, muted gray if not
      - Render card name (truncated to 8 chars)
    - _Requirements: 7.1, 7.4_

  - [x] 10.2 Add edge highlighting to `_draw_mini_board()`
    - For each edge in `card.rotated_edges()`:
      - Get edge upper-group via `STAT_TO_GROUP`
      - If edge_group in hovered_groups: draw edge with `GROUP_COLORS[edge_group]`
      - Else if edge value > 0: draw edge with muted red (180, 60, 60)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 10.3 Write property test for mini board completeness
    - **Property 15: Mini Board Completeness**
    - **Validates: Requirements 7.1**
    - Create player with various board configurations
    - Simulate hover event
    - Assert all cards in player.board.grid are displayed in mini board

  - [x] 10.4 Write property test for match highlight correctness
    - **Property 16: Match Highlight Correctness**
    - **Validates: Requirements 7.2, 7.5**
    - Generate board cards with shared upper-groups
    - Simulate hover with market card
    - Assert cards with shared upper-groups are highlighted with match indicator

  - [x] 10.5 Write property test for clash highlight correctness
    - **Property 17: Clash Highlight Correctness**
    - **Validates: Requirements 7.3, 7.6**
    - Generate board cards with no shared upper-groups but active stats
    - Simulate hover with market card
    - Assert cards are highlighted with clash indicator

  - [x] 10.6 Write property test for edge match determination
    - **Property 18: Edge Match Determination**
    - **Validates: Requirements 8.1**
    - Generate board cards with various edge configurations
    - Simulate hover with market card
    - Assert edge matching logic correctly determines matches

  - [x] 10.7 Write property test for edge match highlight
    - **Property 19: Edge Match Highlight**
    - **Validates: Requirements 8.2**
    - Generate board cards with matching edge upper-groups
    - Simulate hover with market card
    - Assert matching edges are highlighted with upper-group color

  - [x] 10.8 Write property test for edge clash highlight
    - **Property 20: Edge Clash Highlight**
    - **Validates: Requirements 8.3**
    - Generate board cards with non-matching edge upper-groups
    - Simulate hover with market card
    - Assert non-matching edges with non-zero values are highlighted with muted red

- [ ] 11. Checkpoint - Ensure hover compare mode tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Integration and compatibility verification
  - [x] 12.1 Verify run_game.py compatibility
    - Test board rendering with new tarot frames
    - Test shop screen with new card layout
    - Test hover compare mode activation/deactivation
    - Verify existing game loop and controls work unchanged
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 12.2 Write integration test for board interaction
    - Test existing board placement logic
    - Test coordinate system compatibility (hex_to_pixel, pixel_to_hex)
    - Test synergy line rendering with new edge coloring
    - Test tooltip rendering with new frame geometry

  - [x] 12.3 Write integration test for shop interaction
    - Test card purchase flow with new layout
    - Test hover compare mode activation/deactivation
    - Test mini board updates when board changes
    - Test sidebar restoration after hover ends

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (21 properties total)
- Integration tests validate compatibility with existing game logic
- All code examples use Python as the implementation language
