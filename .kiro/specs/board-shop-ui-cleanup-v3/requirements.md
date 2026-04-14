# Requirements Document

## Introduction

This feature simplifies the board and shop UI for improved readability and professionalism. The board will remove visual clutter (glow, aura, circle-medallion, boxed edge badges) and replace them with a thin tarot-style hex identity frame. The shop card will display real 6 stats with 0-value stats omitted, same upper-group stats shown in the same color family, and a tarot-style title plate at the bottom. A hover compare mode will be added to the shop that works through a mini board sidebar, allowing hovered market cards and matching board cards/edges to be visible simultaneously.

## Glossary

- **Board_Renderer**: The rendering system responsible for drawing hex cards on the game board
- **Shop_Card_Renderer**: The rendering system responsible for drawing cards in the market/shop screen
- **Tarot_Style_Hex_Frame**: A thin, rarity-based geometric frame that replaces previous visual effects (glow, aura, medallion)
- **Edge_Stats**: Numeric values displayed at the midpoint of each hex edge without badges
- **Real_Stats**: The actual 6 stats from a card's data, excluding any stats with 0 values
- **Upper_Group**: The stat category (EXISTENCE, MIND, CONNECTION) that a stat belongs to
- **Hover_Compare_Mode**: A shop feature that displays a mini board sidebar when hovering over market cards
- **Mini_Board_Sidebar**: A compact board view showing which cards match or clash with the hovered market card
- **Match**: When a board card shares at least one upper-group with the hovered market card
- **Clash**: When a board card has active stats but shares no upper-groups with the hovered market card

## Requirements

### Requirement 1: Board Card Tarot-Style Hex Frame

**User Story:** As a player, I want board cards to have a clean tarot-style hex frame based on rarity, so that I can easily identify card rarity without visual clutter.

#### Acceptance Criteria

1. THE Board_Renderer SHALL remove all glow effects from board card rendering
2. THE Board_Renderer SHALL remove all aura effects from board card rendering
3. THE Board_Renderer SHALL remove all circle-medallion effects from board card rendering
4. THE Board_Renderer SHALL remove all boxed edge badges from board card rendering
5. WHEN rendering a board card, THE Board_Renderer SHALL draw a thin hex frame with geometry based on the card's rarity value
6. FOR ALL rarity levels, THE Tarot_Style_Hex_Frame SHALL use a distinct geometric pattern
7. THE Tarot_Style_Hex_Frame SHALL be thin enough to not obscure card content

### Requirement 2: Board Edge Stats Positioning

**User Story:** As a player, I want edge stats positioned near edge midpoints without badges, so that I can quickly read stat values without visual noise.

#### Acceptance Criteria

1. WHEN rendering edge stats, THE Board_Renderer SHALL position each stat value near its corresponding edge midpoint
2. THE Board_Renderer SHALL NOT draw any badge or background shape behind edge stat values
3. THE Board_Renderer SHALL render edge stat values as plain text
4. FOR ALL edge stats with value greater than 0, THE Board_Renderer SHALL display the numeric value
5. FOR ALL edge stats with value equal to 0, THE Board_Renderer SHALL NOT display the stat

### Requirement 3: Shop Card Real Stats Display

**User Story:** As a player, I want shop cards to display only real stats with non-zero values, so that I can focus on meaningful card attributes.

#### Acceptance Criteria

1. WHEN rendering a shop card, THE Shop_Card_Renderer SHALL display exactly 6 stats from the card's data
2. FOR ALL stats with value equal to 0, THE Shop_Card_Renderer SHALL NOT draw the stat
3. FOR ALL stats with value greater than 0, THE Shop_Card_Renderer SHALL draw the stat with its name and value
4. WHEN multiple stats belong to the same Upper_Group, THE Shop_Card_Renderer SHALL render them in the same color family
5. THE Shop_Card_Renderer SHALL use GROUP_COLORS mapping to determine color family for each Upper_Group

### Requirement 4: Shop Card Tarot-Style Title Plate

**User Story:** As a player, I want shop cards to have a professional tarot-style title plate at the bottom, so that card names are clearly presented.

#### Acceptance Criteria

1. WHEN rendering a shop card, THE Shop_Card_Renderer SHALL draw a title plate at the bottom of the card
2. THE title plate SHALL display the card name
3. THE title plate SHALL use a tarot-style visual design
4. THE title plate SHALL be positioned below the stats section
5. THE title plate SHALL maintain consistent styling across all rarity levels

### Requirement 5: Shop Market Layout Re-Proportioning

**User Story:** As a player, I want the shop market layout to accommodate the new card design, so that cards are properly displayed.

#### Acceptance Criteria

1. THE Shop_Screen SHALL adjust card dimensions to accommodate the new stat display format
2. THE Shop_Screen SHALL adjust card spacing to maintain visual balance
3. WHEN displaying market cards, THE Shop_Screen SHALL ensure all card elements are visible
4. THE Shop_Screen SHALL maintain the existing number of cards displayed per row

### Requirement 6: Hover Compare Mode Activation

**User Story:** As a player, I want to see a mini board sidebar when hovering over market cards, so that I can compare potential purchases with my current board.

#### Acceptance Criteria

1. WHEN the mouse cursor hovers over a market card, THE Shop_Screen SHALL display the Mini_Board_Sidebar
2. WHEN the mouse cursor is not hovering over any market card, THE Shop_Screen SHALL hide the Mini_Board_Sidebar
3. THE Mini_Board_Sidebar SHALL replace the existing synergy sidebar during hover
4. WHEN hover ends, THE Shop_Screen SHALL restore the original synergy sidebar

### Requirement 7: Mini Board Sidebar Match and Clash Display

**User Story:** As a player, I want to see which board cards match or clash with a hovered market card, so that I can make informed purchasing decisions.

#### Acceptance Criteria

1. WHEN a market card is hovered, THE Mini_Board_Sidebar SHALL display all cards currently on the player's board
2. FOR ALL board cards that Match the hovered card, THE Mini_Board_Sidebar SHALL highlight them with a match indicator
3. FOR ALL board cards that Clash with the hovered card, THE Mini_Board_Sidebar SHALL highlight them with a clash indicator
4. THE Mini_Board_Sidebar SHALL determine Match by comparing Upper_Group values between hovered and board cards
5. WHEN a board card shares at least one Upper_Group with the hovered card, THE Mini_Board_Sidebar SHALL classify it as Match
6. WHEN a board card has active stats but shares no Upper_Groups with the hovered card, THE Mini_Board_Sidebar SHALL classify it as Clash
7. THE Mini_Board_Sidebar SHALL use distinct visual indicators for Match and Clash states

### Requirement 8: Mini Board Sidebar Edge Highlighting

**User Story:** As a player, I want to see which edges on board cards match or clash with the hovered market card, so that I can understand synergy at the edge level.

#### Acceptance Criteria

1. FOR ALL edges on board cards in the Mini_Board_Sidebar, THE Shop_Screen SHALL determine if the edge Upper_Group matches the hovered card
2. WHEN an edge's Upper_Group matches any Upper_Group on the hovered card, THE Mini_Board_Sidebar SHALL highlight the edge with match color
3. WHEN an edge has a non-zero value but its Upper_Group does not match the hovered card, THE Mini_Board_Sidebar SHALL highlight the edge with clash color
4. THE Mini_Board_Sidebar SHALL use the Upper_Group's color for matching edges
5. THE Mini_Board_Sidebar SHALL use a muted red color for clashing edges

### Requirement 9: Main Board Render Order Preservation

**User Story:** As a developer, I want the main board render order to remain unchanged, so that existing gameplay is not disrupted.

#### Acceptance Criteria

1. THE Board_Renderer SHALL maintain the existing render order for board elements
2. THE Board_Renderer SHALL preserve hex-frame alignment with existing coordinate system
3. WHEN rendering the board, THE Board_Renderer SHALL use the same BOARD_COORDS structure
4. THE Board_Renderer SHALL maintain compatibility with existing board interaction logic

### Requirement 10: Shop Card Renderer Re-Proportioning

**User Story:** As a developer, I want the shop card renderer to be re-proportioned for the new layout, so that all elements fit properly.

#### Acceptance Criteria

1. THE Shop_Card_Renderer SHALL allocate vertical space for category ribbon, cameo, stats grid, passive preview, and title plate
2. THE Shop_Card_Renderer SHALL ensure the stats grid has sufficient height to display up to 6 stats
3. THE Shop_Card_Renderer SHALL ensure the title plate has sufficient height for card name display
4. THE Shop_Card_Renderer SHALL maintain proper spacing between all card sections
5. WHEN a card has fewer than 6 non-zero stats, THE Shop_Card_Renderer SHALL adjust layout to avoid empty space

