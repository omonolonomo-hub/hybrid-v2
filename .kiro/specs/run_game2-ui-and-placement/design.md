# Design Document: Run Game2 UI and Placement

## Overview

This design addresses critical UI/UX issues in run_game2.py that prevent the game from being playable. The system uses a hybrid architecture with modal scenes for UI, and the modal integration is complete. However, four key areas need implementation:

1. **Hex Grid Sizing**: The current HEX_SIZE (68px) is too small for card assets (140x160px), causing cards to overflow hexagons
2. **Hand Panel Interaction**: Hand cards are displayed but not interactive - no click detection or selection state
3. **Left Panel Rendering**: The left panel area is empty - missing synergy badges and passive buff log
4. **Card Placement System**: No system exists for placing cards from hand onto the board with validation and preview

The solution implements these four systems with proper coordinate conversion using HexSystem's cube rounding algorithm, state management in HybridGameState, and visual feedback for all interactions.

### Key Design Decisions

**HEX_SIZE Calculation**: Card assets are 140x160px. The diagonal of a card at any rotation must fit within the hexagon with 10% padding. For a flat-top hexagon, the inscribed rectangle diagonal is approximately 2 * HEX_SIZE * 0.866. To accommodate a 140x160px card (diagonal ~212px) with 10% padding, HEX_SIZE should be at least 80px. We'll use 85px for comfortable spacing.

**Coordinate Conversion**: All pixel-to-hex conversions MUST use HexSystem.pixel_to_hex with cube rounding algorithm. Simple round(q), round(r) is mathematically incorrect and causes coordinate bugs at hex boundaries.

**State Management**: HybridGameState maintains all placement-related state (selected_hand_idx, pending_rotation, placed_this_turn, locked_coords_per_player). This centralizes state and makes it easy to reset between turns.

**Locked Coordinates**: Cards placed during a turn are locked (cannot be moved) until turn end. This is a strategic constraint that prevents players from repeatedly repositioning cards. Locked coordinates are tracked per-player and cleared when step_turn_hybrid completes.

## Architecture

### Component Structure

```
run_game2.py (Main Game Loop)
├── HybridGameState (State Container)
│   ├── selected_hand_idx: Optional[int]
│   ├── pending_rotation: int (0-5)
│   ├── placed_this_turn: int
│   └── locked_coords_per_player: Dict[int, Set[Tuple[int, int]]]
│
├── Input Handling (handle_input)
│   ├── Hand Card Click Detection (_get_clicked_hand_card)
│   ├── Hex Click Detection (HexSystem.pixel_to_hex)
│   ├── Rotation Controls (R key, right click)
│   └── Placement Execution (place_card_from_hand)
│
├── Rendering (render_main_screen)
│   ├── BoardRendererV3 (Hex Grid + Placement Preview)
│   ├── HUD Renderer (Hand Panel, Synergy HUD, Passive Panel)
│   └── Visual Feedback (Selection, Hover, Locked Indicators)
│
└── Validation (is_valid_placement)
    ├── Empty Hex Check
    ├── Locked Coordinate Check
    └── Placement Limit Check
```

### Data Flow

**Card Selection Flow**:
1. User clicks on hand card
2. `_get_clicked_hand_card` detects click, returns card index
3. `handle_input` updates `state.selected_hand_idx`
4. `render_main_screen` displays selection indicator on hand card

**Card Placement Flow**:
1. User clicks on board with card selected
2. `HexSystem.pixel_to_hex` converts mouse position to hex coordinate
3. `is_valid_placement` validates target hex (empty, not locked, under limit)
4. `place_card_from_hand` executes placement:
   - Apply rotation to card
   - Remove from hand
   - Add to board
   - Add to locked coordinates
   - Increment placed_this_turn
   - Clear selection
5. `render_main_screen` displays updated board

**Placement Preview Flow**:
1. User hovers mouse over board with card selected
2. `BoardRenderer.update_hover` converts mouse position to hex coordinate
3. `render_main_screen` checks if hex is valid for placement
4. `BoardRenderer.draw_placement_preview` renders semi-transparent card at hover position

## Components and Interfaces

### HybridGameState

```python
@dataclass
class HybridGameState:
    """State container for hybrid architecture."""
    game: Game
    view_player: int = 0
    selected_hand_idx: Optional[int] = None  # Index of selected hand card
    pending_rotation: int = 0  # Rotation for next placement (0-5)
    placed_this_turn: int = 0  # Number of cards placed this turn
    locked_coords_per_player: Dict[int, Set[Tuple[int, int]]] = field(default_factory=dict)
    fast_mode: bool = False
```

**Responsibilities**:
- Maintain all placement-related state
- Track selection and rotation state
- Track locked coordinates per player
- Provide clean state reset between turns

### BoardRendererV3

```python
class BoardRendererV3:
    def __init__(self, origin, strategy, hex_size=85):
        self.origin = origin
        self.hex_size = hex_size  # Updated from 68 to 85
        self.hex_system = HexSystem(hex_size=hex_size, origin=origin)
        # ... existing fields
    
    def update_hover(self, mouse_pos, board_coords):
        """Update hover state using HexSystem.pixel_to_hex."""
        q, r = self.hex_system.pixel_to_hex(mouse_pos[0], mouse_pos[1])
        self.hovered_coord = (q, r) if (q, r) in board_coords else None
    
    def draw(self, surface, board, board_coords, locked_coords=None, show_tooltip=True):
        """Draw board with locked coordinate indicators."""
        # Draw empty hexes
        # Draw cards
        # Draw locked indicators (orange border) for locked_coords
    
    def draw_placement_preview(self, surface, cx, cy, card, rotation):
        """Draw semi-transparent card preview at target position."""
        # Create preview card with rotation
        # Render with alpha=180
```

**Responsibilities**:
- Calculate HEX_SIZE based on card dimensions (85px for 140x160px cards)
- Use HexSystem for all coordinate conversions
- Render hex grid with proper sizing
- Display locked coordinate indicators
- Render placement preview with rotation

### Input Handling Functions

```python
def _get_clicked_hand_card(mouse_pos: Tuple[int, int], hand_size: int) -> Optional[int]:
    """Detect if mouse click is on a hand card, return index or None."""
    # Calculate hand card rectangles
    # Check if mouse_pos is within any card rect
    # Return card index or None

def _get_clicked_hex(mouse_pos: Tuple[int, int], hex_system: HexSystem, 
                     board_coords: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    """Convert mouse click to hex coordinate if valid."""
    q, r = hex_system.pixel_to_hex(mouse_pos[0], mouse_pos[1])
    return (q, r) if (q, r) in board_coords else None

def is_valid_placement(board: Board, target_coord: Tuple[int, int],
                      locked_coords: Set[Tuple[int, int]],
                      placed_this_turn: int) -> Tuple[bool, str]:
    """Validate placement attempt, return (valid, error_message)."""
    # Check if hex is empty
    # Check if hex is not locked
    # Check if under placement limit
    # Return (True, "") or (False, error_message)

def place_card_from_hand(player: Player, hand_idx: int, target_coord: Tuple[int, int],
                        rotation: int, locked_coords: Set[Tuple[int, int]]) -> bool:
    """Execute card placement from hand to board."""
    # Get card from hand
    # Apply rotation
    # Remove from hand
    # Add to board
    # Add to locked_coords
    # Return True
```

**Responsibilities**:
- Detect hand card clicks with pixel-perfect hit testing
- Convert mouse clicks to hex coordinates using HexSystem
- Validate placement attempts against all rules
- Execute placement with proper state updates

### HUD Rendering Functions

```python
def draw_hand_panel(surface, player, fonts, selected_idx, mouse_pos, current_rotation=0):
    """Draw hand panel with selection and hover states."""
    # Draw hand cards vertically
    # Highlight selected card (cyan border)
    # Show hover effect (lighter background)
    # Display rotation angle for selected card
    # Show tooltip for selected card

def draw_synergy_hud(surface, player, fonts, hovered_group=None):
    """Draw synergy badges at bottom center."""
    # Count active synergies from board
    # Draw badges for EXISTENCE, MIND, CONNECTION
    # Highlight hovered group

def draw_passive_buff_panel(surface, player, font_sm, px, py, max_h):
    """Draw passive buff log below hand panel."""
    # Get last 10 passive buff entries
    # Draw scrollable list
    # Color code by trigger type
```

**Responsibilities**:
- Render hand panel with interactive states
- Display synergy badges with counts
- Show passive buff log
- Provide visual feedback for all interactions

## Data Models

### HybridGameState Fields

```python
selected_hand_idx: Optional[int]
# - None when no card selected
# - 0-5 when card selected (hand has max 6 cards)
# - Reset to None after placement or ESC key

pending_rotation: int
# - 0-5 representing rotation in 60-degree increments
# - Incremented by R key or right click
# - Applied to card on placement
# - Reset to 0 when card deselected

placed_this_turn: int
# - 0 at turn start
# - Incremented on each placement
# - Checked against PLACE_PER_TURN (currently 1)
# - Reset to 0 at turn end

locked_coords_per_player: Dict[int, Set[Tuple[int, int]]]
# - Maps player ID to set of locked coordinates
# - Coordinates added on placement
# - Cleared at turn end for all players
# - Used to prevent moving cards within same turn
```

### Coordinate Systems

**Screen Coordinates** (px, py):
- Origin at top-left of window
- Used for mouse input and rendering

**Hex Coordinates** (q, r):
- Axial coordinate system
- Origin at center of board (0, 0)
- Converted using HexSystem with cube rounding

**Board Origin**: (800, 470) - center of hex grid in screen space

### Constants

```python
HEX_SIZE = 85  # Updated from 68 to accommodate 140x160px cards
CARD_SIZE = (140, 160)  # Card asset dimensions
BOARD_RADIUS = 3  # 37-hex board
PLACE_PER_TURN = 1  # Maximum placements per turn
BOARD_ORIGIN = (800, 470)  # Center of hex grid
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Hex Size Accommodates Card Assets with Padding

*For any* card dimensions (width, height), the calculated HEX_SIZE SHALL be large enough to contain the card diagonal plus 10% padding margin at any rotation.

**Validates: Requirements 1.1, 1.4, 1.5**

### Property 2: Hand Card Click Detection Accuracy

*For any* mouse position within a hand card rectangle, `_get_clicked_hand_card` SHALL return the correct card index, and for any position outside all card rectangles, it SHALL return None.

**Validates: Requirements 2.1**

### Property 3: Selection State Toggle Idempotence

*For any* card index, clicking the same card twice SHALL return the selection state to its original value (selected → unselected → selected).

**Validates: Requirements 2.2**

### Property 4: Single Selection Invariant

*For any* two different card indices, selecting the second card SHALL deselect the first card, maintaining the invariant that at most one card is selected at any time.

**Validates: Requirements 2.5**

### Property 5: Rotation Display Consistency

*For any* rotation value (0-5), the displayed rotation angle SHALL equal rotation * 60 degrees.

**Validates: Requirements 2.6, 10.3**

### Property 6: Coordinate Conversion Round-Trip

*For any* valid hex coordinate (q, r) in BOARD_COORDS, converting to pixel coordinates and back SHALL return the original coordinate: pixel_to_hex(hex_to_pixel(q, r)) == (q, r).

**Validates: Requirements 4.1, 4.2**

### Property 7: Coordinate Validation Correctness

*For any* hex coordinate (q, r), `is_valid_placement` SHALL return False if the coordinate is not in BOARD_COORDS, and the placement system SHALL ignore such clicks.

**Validates: Requirements 4.3, 4.4**

### Property 8: Empty Hex Validation

*For any* board state and target coordinate, `is_valid_placement` SHALL return False if the target hex is occupied (exists in board.grid).

**Validates: Requirements 5.1**

### Property 9: Locked Coordinate Validation

*For any* set of locked coordinates, `is_valid_placement` SHALL return False if the target coordinate is in the locked set.

**Validates: Requirements 5.2, 8.5**

### Property 10: Placement Limit Enforcement

*For any* placement count, `is_valid_placement` SHALL return False if placed_this_turn >= PLACE_PER_TURN.

**Validates: Requirements 5.3**

### Property 11: Placement State Updates

*For any* valid placement, the following state updates SHALL occur atomically:
- Card removed from player.hand (len(hand) decreases by 1)
- Card added to player.board at target coordinate
- Target coordinate added to locked_coords
- placed_this_turn incremented by 1
- selected_hand_idx set to None

**Validates: Requirements 6.1, 6.3, 6.4, 6.5, 6.6, 6.7**

### Property 12: Rotation Application

*For any* rotation value (0-5) and card placement, the placed card's rotation SHALL equal the pending_rotation value at the time of placement.

**Validates: Requirements 6.2, 10.4**

### Property 13: Rotation Increment with Wraparound

*For any* rotation value (0-5), incrementing rotation SHALL produce (rotation + 1) % 6, ensuring rotation stays in range 0-5.

**Validates: Requirements 10.1, 10.2**

### Property 14: Rotation Reset on Deselection

*For any* rotation value, deselecting a card (setting selected_hand_idx to None) SHALL reset pending_rotation to 0.

**Validates: Requirements 10.5**

### Property 15: Locked Coordinates Accumulation

*For any* sequence of placements within a turn, locked coordinates SHALL accumulate (never decrease) until turn end.

**Validates: Requirements 8.2**

### Property 16: Locked Coordinates Cleanup

*For any* player, after step_turn_hybrid completes, the player's locked coordinate set SHALL be empty.

**Validates: Requirements 8.3**

## Error Handling

### Input Validation Errors

**Invalid Hand Card Click**:
- Condition: Mouse click outside all hand card rectangles
- Handling: Return None, no state change
- User Feedback: No visual feedback (expected behavior)

**Invalid Hex Click**:
- Condition: Mouse click converts to coordinate not in BOARD_COORDS
- Handling: Ignore click, no placement attempt
- User Feedback: No placement preview shown

**Occupied Hex Placement**:
- Condition: Target hex already contains a card
- Handling: Reject placement, display error message
- User Feedback: Status message "Hex occupied"

**Locked Hex Placement**:
- Condition: Target hex is in locked_coords
- Handling: Reject placement, display error message
- User Feedback: Status message "Cannot move card this turn"

**Placement Limit Exceeded**:
- Condition: placed_this_turn >= PLACE_PER_TURN
- Handling: Reject placement, display error message
- User Feedback: Status message "Placement limit reached (1/turn)"

### State Consistency Errors

**No Card Selected**:
- Condition: User clicks hex without selecting a hand card
- Handling: Ignore click, no placement attempt
- User Feedback: No placement preview shown

**Empty Hand**:
- Condition: User tries to select card when hand is empty
- Handling: No selection possible
- User Feedback: "Hand empty" message displayed

### Coordinate Conversion Errors

**Cube Rounding Failure**:
- Condition: Fractional hex coordinates don't satisfy cube constraint
- Handling: HexSystem.cube_round enforces constraint by resetting coordinate with largest error
- User Feedback: None (internal correction)

**Out of Bounds Coordinate**:
- Condition: Converted coordinate outside BOARD_COORDS
- Handling: Validation rejects coordinate
- User Feedback: No placement preview, click ignored

## Testing Strategy

This feature is well-suited for property-based testing because it involves:
- Pure functions (coordinate conversion, validation logic)
- State transitions (selection, placement, rotation)
- Universal properties that should hold across many inputs

### Property-Based Tests

We will use **Hypothesis** (Python's property-based testing library) to implement the correctness properties. Each property test will run a minimum of 100 iterations with randomly generated inputs.

**Test Configuration**:
```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Property: ...
    # Feature: run_game2-ui-and-placement, Property N: ...
    pass
```

**Property Test 1: Hex Size Calculation**
- Generator: Random card dimensions (width: 50-300, height: 50-300)
- Property: HEX_SIZE >= card_diagonal * 1.1 / (2 * 0.866)
- Tag: Feature: run_game2-ui-and-placement, Property 1: Hex size accommodates card assets with padding

**Property Test 2: Hand Click Detection**
- Generator: Random mouse positions, random hand sizes (0-6)
- Property: Click inside rect returns index, click outside returns None
- Tag: Feature: run_game2-ui-and-placement, Property 2: Hand card click detection accuracy

**Property Test 3: Selection Toggle**
- Generator: Random card index (0-5), random initial selection state
- Property: Clicking twice returns to original state
- Tag: Feature: run_game2-ui-and-placement, Property 3: Selection state toggle idempotence

**Property Test 4: Single Selection**
- Generator: Two different card indices (0-5)
- Property: Selecting second deselects first
- Tag: Feature: run_game2-ui-and-placement, Property 4: Single selection invariant

**Property Test 5: Rotation Display**
- Generator: Random rotation (0-5)
- Property: Displayed angle == rotation * 60
- Tag: Feature: run_game2-ui-and-placement, Property 5: Rotation display consistency

**Property Test 6: Coordinate Round-Trip**
- Generator: Random valid hex coordinates from BOARD_COORDS
- Property: pixel_to_hex(hex_to_pixel(q, r)) == (q, r)
- Tag: Feature: run_game2-ui-and-placement, Property 6: Coordinate conversion round-trip

**Property Test 7: Coordinate Validation**
- Generator: Random hex coordinates (including invalid ones)
- Property: Invalid coordinates rejected
- Tag: Feature: run_game2-ui-and-placement, Property 7: Coordinate validation correctness

**Property Test 8: Empty Hex Validation**
- Generator: Random board states, random target coordinates
- Property: Occupied hexes rejected
- Tag: Feature: run_game2-ui-and-placement, Property 8: Empty hex validation

**Property Test 9: Locked Coordinate Validation**
- Generator: Random locked coordinate sets, random target coordinates
- Property: Locked coordinates rejected
- Tag: Feature: run_game2-ui-and-placement, Property 9: Locked coordinate validation

**Property Test 10: Placement Limit**
- Generator: Random placement counts (0-5)
- Property: Placements rejected when limit reached
- Tag: Feature: run_game2-ui-and-placement, Property 10: Placement limit enforcement

**Property Test 11: Placement State Updates**
- Generator: Random valid placements
- Property: All state updates occur atomically
- Tag: Feature: run_game2-ui-and-placement, Property 11: Placement state updates

**Property Test 12: Rotation Application**
- Generator: Random rotation (0-5), random placements
- Property: Placed card rotation matches pending_rotation
- Tag: Feature: run_game2-ui-and-placement, Property 12: Rotation application

**Property Test 13: Rotation Wraparound**
- Generator: Random rotation (0-5)
- Property: (rotation + 1) % 6 stays in range
- Tag: Feature: run_game2-ui-and-placement, Property 13: Rotation increment with wraparound

**Property Test 14: Rotation Reset**
- Generator: Random rotation (0-5)
- Property: Deselection resets rotation to 0
- Tag: Feature: run_game2-ui-and-placement, Property 14: Rotation reset on deselection

**Property Test 15: Locked Coordinates Accumulation**
- Generator: Random placement sequences
- Property: Locked set never decreases within turn
- Tag: Feature: run_game2-ui-and-placement, Property 15: Locked coordinates accumulation

**Property Test 16: Locked Coordinates Cleanup**
- Generator: Random board states with locked coordinates
- Property: All locked sets empty after turn end
- Tag: Feature: run_game2-ui-and-placement, Property 16: Locked coordinates cleanup

### Unit Tests

Unit tests will cover specific examples and edge cases:

**Hand Panel Tests**:
- Empty hand display
- Full hand (6 cards) display
- Selection indicator rendering
- Hover effect rendering
- Rotation angle display

**Synergy HUD Tests**:
- No synergies (all counts 0)
- Single synergy active
- Multiple synergies active
- Hover highlighting

**Passive Buff Panel Tests**:
- Empty log
- Single entry
- Multiple entries (scrolling)
- Color coding by trigger type

**Placement Preview Tests**:
- Preview shown for valid hex
- No preview for invalid hex
- Preview rotation matches pending_rotation
- Preview alpha is 180

**Locked Indicator Tests**:
- Locked hex displays orange border
- Unlocked hex has no indicator
- Multiple locked hexes

### Integration Tests

Integration tests will verify component interactions:

**Hand to Board Placement Flow**:
1. Select card from hand
2. Click valid hex
3. Verify card moved from hand to board
4. Verify locked coordinate added
5. Verify selection cleared

**Rotation Flow**:
1. Select card
2. Press R key 3 times
3. Verify rotation is 3
4. Place card
5. Verify placed card has rotation 3

**Placement Limit Flow**:
1. Place 1 card (limit is 1)
2. Attempt to place another card
3. Verify rejection with error message

**Turn End Cleanup**:
1. Place card (adds to locked_coords)
2. Call step_turn_hybrid
3. Verify locked_coords cleared
4. Verify placed_this_turn reset to 0

### Visual Regression Tests

Visual tests will verify rendering correctness:
- Hand panel with selection and hover states
- Board with locked coordinate indicators
- Placement preview with rotation
- Synergy HUD with active synergies
- Passive buff panel with entries

## Implementation Notes

### HEX_SIZE Calculation

The current HEX_SIZE of 68px is too small for 140x160px card assets. The calculation:

```python
# Card dimensions
card_w, card_h = 140, 160
card_diagonal = math.sqrt(card_w**2 + card_h**2)  # ~212px

# Hex inscribed rectangle diagonal (flat-top hex)
# diagonal = 2 * HEX_SIZE * sqrt(3) / 2 = HEX_SIZE * sqrt(3)
# With 10% padding: diagonal = card_diagonal * 1.1

HEX_SIZE = (card_diagonal * 1.1) / math.sqrt(3)  # ~134px

# However, cards are rendered smaller than hex to show edges
# Practical HEX_SIZE for comfortable display: 85px
```

We'll use HEX_SIZE = 85px, which provides:
- Enough space for 140x160px cards
- Visible hex edges for edge stat display
- Comfortable spacing between hexes

### Cube Rounding Algorithm

The HexSystem.cube_round algorithm is critical for accurate coordinate conversion:

```python
def cube_round(self, frac_q: float, frac_r: float) -> Tuple[int, int]:
    # Calculate third coordinate (cube constraint: q + r + s = 0)
    frac_s = -frac_q - frac_r
    
    # Round all three
    q, r, s = round(frac_q), round(frac_r), round(frac_s)
    
    # Find largest rounding error
    q_diff = abs(q - frac_q)
    r_diff = abs(r - frac_r)
    s_diff = abs(s - frac_s)
    
    # Reset coordinate with largest error to satisfy constraint
    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    
    return (q, r)
```

This ensures the cube constraint (q + r + s = 0) is always satisfied, preventing coordinate drift.

### State Reset Points

State must be reset at specific points to prevent bugs:

**Turn Start** (in step_turn_hybrid):
- selected_hand_idx = None
- pending_rotation = 0
- placed_this_turn = 0

**Turn End** (in step_turn_hybrid):
- Clear all locked_coords_per_player sets

**Player Switch** (in handle_input):
- selected_hand_idx = None
- pending_rotation = 0

**Card Placement** (in place_card_from_hand):
- selected_hand_idx = None
- pending_rotation = 0

**ESC Key** (in handle_input):
- selected_hand_idx = None
- pending_rotation = 0

### Performance Considerations

**Hand Click Detection**: O(n) where n is hand size (max 6), negligible cost

**Hex Click Detection**: O(1) coordinate conversion + O(1) set lookup in BOARD_COORDS

**Placement Validation**: O(1) checks (dict lookup, set lookup, counter comparison)

**Placement Preview**: Rendered every frame when card selected and mouse over board, uses cached card rendering

**Locked Coordinate Tracking**: O(1) set operations (add, lookup, clear)

All operations are O(1) or O(n) with small n, so performance is not a concern.

## Dependencies

### External Libraries
- pygame: Rendering and input handling
- hypothesis: Property-based testing

### Internal Modules
- core.hex_system: HexSystem for coordinate conversion
- engine_core.board: Board class and BOARD_COORDS
- engine_core.constants: PLACE_PER_TURN, BOARD_RADIUS
- ui.board_renderer_v3: BoardRendererV3 for hex grid rendering
- ui.hud_renderer: Hand panel, synergy HUD, passive panel rendering
- scenes.asset_loader: Card asset loading (CARD_SIZE constant)

### Module Modifications

**ui/board_renderer_v3.py**:
- Update HEX_SIZE from 68 to 85
- Add locked_coords parameter to draw()
- Implement draw_placement_preview()
- Add locked indicator rendering (orange border)

**ui/hud_renderer.py**:
- Update draw_hand_panel() to show selection and hover states
- Add current_rotation parameter to draw_hand_panel()
- Ensure draw_synergy_hud() and draw_passive_buff_panel() are called

**run_game2.py**:
- Implement _get_clicked_hand_card()
- Implement _get_clicked_hex()
- Implement is_valid_placement()
- Implement place_card_from_hand()
- Update handle_input() to handle hand clicks and hex clicks
- Update render_main_screen() to pass locked_coords to BoardRenderer
- Update render_main_screen() to render placement preview
- Update step_turn_hybrid() to clear locked coordinates

## Migration Path

This feature builds on the existing hybrid architecture and requires no breaking changes:

1. **Phase 1: Hex Grid Sizing**
   - Update HEX_SIZE in renderer_v3.py
   - Update BoardRendererV3 to use new size
   - Test rendering with new size

2. **Phase 2: Hand Panel Interaction**
   - Implement _get_clicked_hand_card()
   - Update handle_input() to detect hand clicks
   - Update draw_hand_panel() to show selection/hover states
   - Test hand card selection

3. **Phase 3: Left Panel Rendering**
   - Verify draw_synergy_hud() is called in render_main_screen()
   - Verify draw_passive_buff_panel() is called in render_main_screen()
   - Test synergy and passive rendering

4. **Phase 4: Card Placement System**
   - Implement _get_clicked_hex()
   - Implement is_valid_placement()
   - Implement place_card_from_hand()
   - Update handle_input() to handle hex clicks
   - Update BoardRenderer to show locked indicators
   - Implement placement preview
   - Test complete placement flow

5. **Phase 5: Testing**
   - Implement property-based tests
   - Implement unit tests
   - Implement integration tests
   - Run full test suite

Each phase can be developed and tested independently, allowing for incremental progress.
