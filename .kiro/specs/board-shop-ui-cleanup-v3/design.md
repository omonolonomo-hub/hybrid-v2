# Design Document: Board and Shop UI Cleanup v3

## Overview

This feature simplifies the board and shop UI for improved readability and professionalism by removing visual clutter and implementing a clean tarot-style design language. The changes span three main areas:

1. **Board Renderer**: Replace glow/aura/medallion effects with thin tarot-style hex frames that vary by rarity geometry
2. **Shop Card Renderer**: Re-proportion layout to display real stats (skipping zeros), use upper-group color coding, and add tarot-style title plates
3. **Shop Screen**: Implement hover compare mode with mini board sidebar showing match/clash analysis

The design maintains backward compatibility with existing game logic while modernizing the visual presentation.

## Architecture

### Component Hierarchy

```
run_game.py (Main Game Loop)
├── BoardRenderer (ui/renderer.py)
│   ├── CyberRenderer.draw_hex_card()
│   ├── CyberRenderer._draw_tarot_frame()
│   └── BoardRenderer.draw()
│
└── ShopScreen (ui/screens/shop_screen.py)
    ├── CyberRenderer.draw_shop_card()
    ├── CyberRenderer.draw_shop_stat_grid()
    ├── ShopScreen._draw_compare_sidebar()
    └── ShopScreen._draw_mini_board()
```

### Data Flow

```
Card Data (card.py)
  ↓
  ├→ Board Rendering Path
  │   ├→ card.rotated_edges() → edge positioning
  │   ├→ card.rarity → frame geometry selection
  │   └→ STAT_TO_GROUP → edge color mapping
  │
  └→ Shop Rendering Path
      ├→ card.stats/edges → real stat extraction
      ├→ STAT_TO_GROUP → color family grouping
      └→ card.name → title plate display

Hover Event (shop_screen.py)
  ↓
  ├→ Extract hovered card upper-groups
  ├→ Compare with board card upper-groups
  ├→ Classify as Match/Clash/Neutral
  └→ Render mini board with highlights
```

## Components and Interfaces

### 1. CyberRenderer (ui/renderer.py)

#### Modified Methods

**`draw_hex_card(surface, card, pos, r, is_hovered, highlighted)`**
- **Purpose**: Render board card with tarot-style hex frame
- **Changes**:
  - Remove: glow effects, aura rings, circle medallions, boxed badges
  - Add: `_draw_tarot_frame()` call for rarity-based geometry
  - Modify: Edge stat positioning to use `card.rotated_edges()` and edge midpoints
  - Modify: Edge stat coloring to use `STAT_TO_GROUP` upper-group mapping

**Signature**:
```python
def draw_hex_card(
    self,
    surface: pygame.Surface,
    card: Card,
    pos: Tuple[int, int],
    r: int = 68,
    is_hovered: bool = False,
    highlighted: bool = False
) -> None
```

**Algorithm**:
1. Extract card rarity and convert to integer level (1-5, E→6)
2. Render hex body fill
3. Call `_draw_tarot_frame()` with rarity level
4. Render card name at center
5. For each edge in `card.rotated_edges()`:
   - Calculate edge midpoint using `_edge_midpoint(corners, i)`
   - Position stat value near midpoint using `_toward_center()`
   - Map stat to upper-group via `STAT_TO_GROUP`
   - Render stat value in upper-group color from `GROUP_COLORS`
   - Skip if value == 0
6. Render passive indicator dot if present

#### New Methods

**`_draw_tarot_frame(surface, cx, cy, r, rarity_col, rarity_level, highlight)`**
- **Purpose**: Draw rarity-specific geometric frame
- **Rarity Geometry Mapping**:
  - **Level 1**: Single thin contour line
  - **Level 2**: Corner tick marks + double contour
  - **Level 3**: Double thin contour (outer + inner)
  - **Level 4**: Double contour + inner diagonal motif lines
  - **Level 5/E**: Corner ornaments + bronze/gold accent ring

**Signature**:
```python
def _draw_tarot_frame(
    self,
    surface: pygame.Surface,
    cx: int,
    cy: int,
    r: int,
    rarity_col: Tuple[int, int, int],
    rarity_level: int,
    highlight: bool = False
) -> None
```

**Algorithm**:
1. Calculate hex corners using `_hex_corners(cx, cy, r)`
2. Select border width: 3 if highlighted, else 2
3. **If rarity_level >= 3**:
   - Draw outer polygon with rarity_col
   - Draw inner polygon (r-5) with darkened rarity_col
4. **Else**:
   - Draw single polygon with border width based on rarity_level
5. **If rarity_level == 2**:
   - Draw corner ticks at 18% of edge length from each corner
6. **If rarity_level >= 4**:
   - Calculate edge midpoints
   - Draw 3 diagonal lines connecting opposite midpoints
7. **If rarity_level >= 5**:
   - Draw corner node circles with gold color
   - Draw inner gold accent ring at r-8
8. **Else**:
   - Draw corner node circles with rarity_col

**`draw_shop_card(surface, card, rect, hovered, bought, affordable, cost, alpha)`**
- **Purpose**: Render shop card with new proportioned layout
- **Layout Sections** (top to bottom):
  1. Category ribbon (22px height)
  2. Cameo/sigil (92px height)
  3. Real stats grid (92px height)
  4. Passive preview (56px height)
  5. Tarot title plate (30px height)

**Signature**:
```python
def draw_shop_card(
    self,
    surface: pygame.Surface,
    card: Card,
    rect: pygame.Rect,
    hovered: bool = False,
    bought: bool = False,
    affordable: bool = True,
    cost: int = 0,
    alpha: int = 255
) -> None
```

**Algorithm**:
1. Create layer surface with rect dimensions
2. Extract card rarity and convert to level
3. Draw background with hover/bought state colors
4. Draw rarity geometry border (same logic as board frame)
5. Draw category ribbon at top
6. Draw cameo section with category icon
7. Call `draw_shop_stat_grid()` for stats section
8. Draw passive preview section
9. Draw tarot title plate:
   - Background with rarity border
   - Rarity accent strip at top
   - Card name (truncated if needed)
   - Cost medallion on right
10. Blit layer to surface at rect position

**`draw_shop_stat_grid(surface, card, rect)`**
- **Purpose**: Render real stats (non-zero only) with upper-group color coding
- **Changes**:
  - Use `card.edges` or `card.stats.items()` as source
  - Filter out stats with value <= 0
  - Filter out internal stats (starting with "_")
  - Group stats by upper-group via `STAT_TO_GROUP`
  - Apply same color to stats in same upper-group

**Signature**:
```python
def draw_shop_stat_grid(
    self,
    surface: pygame.Surface,
    card: Card,
    rect: pygame.Rect
) -> None
```

**Algorithm**:
1. Extract edge source: `card.edges` or `card.stats.items()`
2. Filter to real_stats: `[(name, val) for name, val in edges if val > 0 and not name.startswith("_")]`
3. Calculate grid layout: 2 columns, rows = ceil(len(real_stats) / 2)
4. For each stat in real_stats:
   - Calculate cell position (col, row)
   - Map stat_name to upper_group via `STAT_TO_GROUP`
   - Get color from `GROUP_COLORS[upper_group]`
   - Draw cell background
   - Render stat short name (from `STAT_SHORT`)
   - Render stat value
5. Return early if no real_stats

### 2. ShopScreen (ui/screens/shop_screen.py)

#### Modified Methods

**`_draw_compare_sidebar()`**
- **Purpose**: Replace synergy sidebar with mini board during hover
- **Behavior**:
  - If no hovered market card: call `_draw_synergy_sidebar()` (existing)
  - If market card hovered: render mini board with match/clash analysis

**Signature**:
```python
def _draw_compare_sidebar(self) -> None
```

**Algorithm**:
1. Check `self._hovered_market_card`
2. If None: call `_draw_synergy_sidebar()` and return
3. Extract hovered card upper-groups:
   ```python
   hovered_groups = set()
   for stat_name, value in hovered.stats.items():
       if value > 0 and not stat_name.startswith("_"):
           group = STAT_TO_GROUP.get(stat_name)
           if group:
               hovered_groups.add(group)
   ```
4. Draw sidebar panel background
5. Draw header: "COMPARE_MODE"
6. Draw hovered card name
7. Draw hovered card upper-groups list
8. Draw legend: "■ MATCH" (green), "■ CLASH" (red)
9. Call `_draw_mini_board(x, y, hovered_groups)`

#### New Methods

**`_draw_mini_board(start_x, start_y, hovered_groups)`**
- **Purpose**: Render compact board view with match/clash highlights
- **Layout**: Grid of mini hexes (20px radius), max width constrained by sidebar

**Signature**:
```python
def _draw_mini_board(
    self,
    start_x: int,
    start_y: int,
    hovered_groups: set
) -> None
```

**Algorithm**:
1. Get board cards: `board_cards = list(self.player.board.grid.values())`
2. If empty: render "Board empty." message and return
3. Calculate grid layout:
   - `cols = max(1, MAX_W // (MINI_R * 2 + 8))`
   - `row_h = MINI_R * 2 + 12`
4. For each card in board_cards:
   - Calculate position: `col = idx % cols`, `row = idx // cols`
   - Calculate center: `cx = start_x + col * spacing + MINI_R`, `cy = start_y + row * row_h + MINI_R`
   - Extract card upper-groups (same logic as hovered card)
   - Determine match: `is_match = bool(card_groups & hovered_groups)`
   - Draw hex polygon with dominant group fill color
   - Draw border: green if match, muted gray if not
   - For each edge in `card.rotated_edges()`:
     - Get edge upper-group via `STAT_TO_GROUP`
     - If edge_group in hovered_groups: draw edge with GROUP_COLORS[edge_group]
     - Else if edge value > 0: draw edge with muted red (180, 60, 60)
   - Render card name (truncated to 8 chars)

**Match/Clash Classification Logic**:
```python
def classify_board_card(board_card, hovered_groups):
    card_groups = extract_upper_groups(board_card)
    
    if not card_groups:
        return "NEUTRAL"  # No active stats
    
    if card_groups & hovered_groups:
        return "MATCH"  # Shared upper-group
    
    return "CLASH"  # Active stats but no shared groups
```

### 3. BoardRenderer (ui/renderer.py)

#### Modified Methods

**`draw(surface, board, board_coords, locked_coords, show_tooltip)`**
- **Purpose**: Main board rendering loop
- **Changes**: None (maintains existing render order and coordinate system)
- **Preservation**:
  - Uses existing `BOARD_COORDS` structure
  - Maintains `hex_to_pixel()` and `pixel_to_hex()` coordinate transforms
  - Preserves synergy line rendering
  - Preserves tooltip rendering

## Data Models

### Card (engine_core/card.py)

**Existing Structure** (no changes):
```python
@dataclass
class Card:
    name: str
    category: str
    rarity: str  # "1", "2", "3", "4", "5", "E"
    stats: Dict[str, int]  # 6 stats: name -> value
    passive_type: str
    edges: List[Tuple[str, int]]  # [(stat_name, value), ...]
    rotation: int  # 0-5 (steps of 60°)
    
    def rotated_edges(self) -> List[Tuple[str, int]]:
        """Return edges shifted by rotation"""
        # edges[i] faces direction (i + rotation) % 6
```

### Constants (engine_core/constants.py)

**Existing Mappings** (used, not modified):
```python
STAT_TO_GROUP: Dict[str, str] = {
    "Power": "EXISTENCE",
    "Durability": "EXISTENCE",
    "Size": "EXISTENCE",
    "Speed": "EXISTENCE",
    "Meaning": "MIND",
    "Secret": "MIND",
    "Intelligence": "MIND",
    "Trace": "MIND",
    "Gravity": "CONNECTION",
    "Harmony": "CONNECTION",
    "Spread": "CONNECTION",
    "Prestige": "CONNECTION",
}

GROUP_COLORS: Dict[str, Tuple[int, int, int]] = {
    "EXISTENCE": (255, 60, 50),
    "MIND": (50, 130, 255),
    "CONNECTION": (40, 230, 130),
}
```

### Renderer Constants (ui/renderer.py)

**Modified**:
```python
# Remove (no longer used):
# - FIXED_SHOP_STATS (replaced by card.edges)

# Keep (still used):
STAT_SHORT: Dict[str, str] = {
    "Power": "PW",
    "Durability": "DU",
    # ... (all 12 stats)
}

HEX_SIZE = 68  # Board hex radius
EDGE_LABEL_INSET = 12  # Distance from edge midpoint toward center
```

### Shop Screen State (ui/screens/shop_screen.py)

**New State Variables**:
```python
class ShopScreen:
    def __init__(self, ...):
        # ... existing state ...
        self._hovered_market_card: Optional[Card] = None  # NEW
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Rarity Frame Geometry Distinctness

*For any* two cards with different rarity values, the tarot-style hex frame SHALL produce visually distinct geometric patterns.

**Validates: Requirements 1.5, 1.6**

### Property 2: Edge Stat Positioning Accuracy

*For any* card with non-zero edge stats, each stat value SHALL be positioned within a threshold distance (15 pixels) of its corresponding edge midpoint.

**Validates: Requirements 2.1**

### Property 3: Non-Zero Edge Stat Visibility

*For any* card, all edges with value > 0 SHALL be rendered with visible stat values.

**Validates: Requirements 2.4**

### Property 4: Zero Edge Stat Invisibility

*For any* card, all edges with value == 0 SHALL NOT be rendered.

**Validates: Requirements 2.5**

### Property 5: Shop Stat Zero Filtering

*For any* card in the shop, stats with value == 0 SHALL NOT appear in the rendered stat grid.

**Validates: Requirements 3.2**

### Property 6: Shop Stat Non-Zero Display

*For any* card in the shop, stats with value > 0 SHALL be rendered with both name and value visible.

**Validates: Requirements 3.3**

### Property 7: Upper-Group Color Consistency

*For any* card with multiple stats in the same upper-group, those stats SHALL be rendered in the same color family.

**Validates: Requirements 3.4**

### Property 8: Title Plate Name Display

*For any* card in the shop, the title plate SHALL contain the card's name.

**Validates: Requirements 4.2**

### Property 9: Title Plate Rarity Consistency

*For any* two cards with different rarities, the title plate styling (excluding rarity-specific accents) SHALL be consistent.

**Validates: Requirements 4.5**

### Property 10: Shop Card Element Visibility

*For any* set of market cards, all card elements (ribbon, cameo, stats, passive, title plate) SHALL fit within the card bounds without clipping.

**Validates: Requirements 5.3**

### Property 11: Hover Sidebar Activation

*For any* mouse hover event over a market card, the Mini_Board_Sidebar SHALL be displayed.

**Validates: Requirements 6.1**

### Property 12: Hover Sidebar Deactivation

*For any* mouse position not over a market card, the Mini_Board_Sidebar SHALL be hidden.

**Validates: Requirements 6.2**

### Property 13: Sidebar Mutual Exclusivity

*For any* UI state, the synergy sidebar and mini board sidebar SHALL NOT be visible simultaneously.

**Validates: Requirements 6.3**

### Property 14: Synergy Sidebar Restoration

*For any* hover-end event, the synergy sidebar SHALL be restored to visible state.

**Validates: Requirements 6.4**

### Property 15: Mini Board Completeness

*For any* hover event, all cards in `player.board.grid` SHALL be displayed in the Mini_Board_Sidebar.

**Validates: Requirements 7.1**

### Property 16: Match Highlight Correctness

*For any* board card that shares at least one upper-group with the hovered market card, the Mini_Board_Sidebar SHALL highlight it with a match indicator.

**Validates: Requirements 7.2, 7.5**

### Property 17: Clash Highlight Correctness

*For any* board card with active stats (value > 0) that shares no upper-groups with the hovered market card, the Mini_Board_Sidebar SHALL highlight it with a clash indicator.

**Validates: Requirements 7.3, 7.6**

### Property 18: Edge Match Determination

*For any* edge on a board card in the Mini_Board_Sidebar, the upper-group matching logic SHALL correctly determine if the edge matches the hovered card.

**Validates: Requirements 8.1**

### Property 19: Edge Match Highlight

*For any* edge whose upper-group matches any upper-group on the hovered card, the Mini_Board_Sidebar SHALL highlight the edge with the upper-group's color.

**Validates: Requirements 8.2**

### Property 20: Edge Clash Highlight

*For any* edge with non-zero value whose upper-group does not match the hovered card, the Mini_Board_Sidebar SHALL highlight the edge with muted red color.

**Validates: Requirements 8.3**

### Property 21: Shop Layout Adaptation

*For any* card with fewer than 6 non-zero stats, the shop card renderer SHALL adjust the stats grid layout to avoid large empty spaces.

**Validates: Requirements 10.5**

## Error Handling

### Rendering Errors

**Missing Card Data**:
- **Scenario**: Card object missing `rarity`, `edges`, or `stats` attributes
- **Handling**: Use default values (rarity="1", edges=[], stats={})
- **Location**: `CyberRenderer.draw_hex_card()`, `CyberRenderer.draw_shop_card()`

**Invalid Rarity Values**:
- **Scenario**: Card rarity is not in ["1", "2", "3", "4", "5", "E"]
- **Handling**: Use `_safe_rarity_int()` to convert to integer, default to 1 if invalid
- **Location**: `CyberRenderer._draw_tarot_frame()`

**Empty Board**:
- **Scenario**: `player.board.grid` is empty during hover compare
- **Handling**: Display "Board empty." message in mini board sidebar
- **Location**: `ShopScreen._draw_mini_board()`

### State Errors

**Hover State Desync**:
- **Scenario**: `_hovered_market_card` not cleared when mouse leaves shop area
- **Handling**: Explicitly set to `None` in mouse motion handler when not over any card
- **Location**: `ShopScreen._handle_events()`

**Missing Upper-Group Mapping**:
- **Scenario**: Stat name not found in `STAT_TO_GROUP`
- **Handling**: Default to "EXISTENCE" group
- **Location**: All upper-group extraction logic

## Testing Strategy

### Unit Tests

**Board Renderer Tests**:
- Test tarot frame geometry for each rarity level (1-5, E)
- Test edge stat positioning calculations
- Test zero-value edge filtering
- Test edge color mapping via STAT_TO_GROUP
- Test rotation-aware edge rendering via `card.rotated_edges()`

**Shop Renderer Tests**:
- Test stat grid filtering (zero values removed)
- Test upper-group color consistency
- Test title plate rendering with various card names
- Test layout proportions (ribbon, cameo, stats, passive, title)
- Test rarity geometry border rendering

**Shop Screen Tests**:
- Test hover state transitions (hover on/off)
- Test sidebar mutual exclusivity
- Test match/clash classification logic
- Test upper-group extraction from cards
- Test mini board grid layout calculations

### Property-Based Tests

**Library**: Use `pytest` with `hypothesis` for Python property-based testing

**Configuration**: Minimum 100 iterations per property test

**Test Tag Format**: `# Feature: board-shop-ui-cleanup-v3, Property {number}: {property_text}`

**Example Property Test**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: board-shop-ui-cleanup-v3, Property 3: Non-Zero Edge Stat Visibility
@given(card=st.builds(Card, ...))
def test_nonzero_edges_visible(card):
    """For any card, all edges with value > 0 SHALL be rendered."""
    surface = pygame.Surface((800, 600))
    renderer = CyberRenderer()
    
    # Render card
    renderer.draw_hex_card(surface, card, (400, 300))
    
    # Extract rendered stat positions
    rendered_stats = extract_rendered_stats(surface)
    
    # Verify all non-zero edges are present
    for stat_name, value in card.rotated_edges():
        if value > 0:
            assert stat_name in rendered_stats, \
                f"Edge {stat_name} with value {value} not rendered"
```

**Property Test Coverage**:
- Properties 1-21 (all correctness properties)
- Focus on universal quantification ("for any card", "for any edge")
- Use card generators with varying rarities, stats, rotations
- Use board state generators with varying card counts and compositions

### Integration Tests

**Board Interaction Tests**:
- Verify existing board placement logic still works
- Verify coordinate system compatibility (hex_to_pixel, pixel_to_hex)
- Verify synergy line rendering with new edge coloring
- Verify tooltip rendering with new frame geometry

**Shop Interaction Tests**:
- Verify card purchase flow with new layout
- Verify hover compare mode activation/deactivation
- Verify mini board updates when board changes
- Verify sidebar restoration after hover ends

### Visual Regression Tests

**Snapshot Tests**:
- Capture reference images for each rarity level (board cards)
- Capture reference images for shop cards (all rarities)
- Capture reference images for mini board sidebar (match/clash states)
- Compare against references on each build

**Manual Visual Inspection**:
- Verify tarot frame "thinness" (Requirement 1.7)
- Verify title plate "tarot-style" aesthetic (Requirement 4.3)
- Verify overall visual balance and readability

## Implementation Notes

### Removal Checklist

**From `CyberRenderer.draw_hex_card()`**:
- ❌ Remove `draw_board_pizzazz()` call (glow effects)
- ❌ Remove aura ring rendering code
- ❌ Remove circle medallion rendering
- ❌ Remove boxed edge badge rendering

**From `CyberRenderer.draw_shop_card()`**:
- ❌ Remove `FIXED_SHOP_STATS` usage
- ✅ Replace with `card.edges` or `card.stats.items()`

### Addition Checklist

**To `CyberRenderer`**:
- ✅ Add `_draw_tarot_frame()` method
- ✅ Modify `draw_hex_card()` to use tarot frames
- ✅ Modify `draw_shop_card()` to use real stats
- ✅ Modify `draw_shop_stat_grid()` to filter zeros and color by upper-group

**To `ShopScreen`**:
- ✅ Add `_hovered_market_card` state variable
- ✅ Add `_draw_compare_sidebar()` method
- ✅ Add `_draw_mini_board()` method
- ✅ Modify mouse motion handler to track hovered card

### Performance Considerations

**Rendering Optimization**:
- Mini board hex rendering: Use simple polygons (no complex effects)
- Stat filtering: Cache filtered stat lists per card
- Upper-group extraction: Cache per card to avoid repeated lookups

**Memory**:
- Mini board sidebar: Render directly to screen (no intermediate surfaces)
- Tarot frames: Use polygon primitives (no texture caching needed)

### Backward Compatibility

**Preserved Interfaces**:
- `BoardRenderer.draw()` signature unchanged
- `CyberRenderer.draw_hex_card()` signature unchanged (only implementation changes)
- `ShopScreen.__init__()` signature unchanged
- `hex_to_pixel()` and `pixel_to_hex()` functions unchanged
- `BOARD_COORDS` structure unchanged

**Migration Path**:
- No data migration needed (card structure unchanged)
- No save file changes (rendering only)
- Existing game logic unaffected (combat, economy, AI)

---

**Design Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Implementation

