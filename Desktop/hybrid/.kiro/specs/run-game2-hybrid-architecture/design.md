# Design Document: run_game2.py Hybrid Architecture

## Overview

The run_game2.py hybrid architecture combines the proven game loop logic from run_game.py with the visual/UI capabilities of the scene-based system. This design treats scenes as modal UI components rather than loop controllers, keeping the deterministic turn flow in a single main loop while leveraging scene rendering for shop, combat visualization, and placement interfaces.

## Architecture

```mermaid
graph TD
    A[run_game2.py Main Loop] --> B[Game State]
    A --> C[ShopScene Modal]
    A --> D[PlacementScene Modal]
    A --> E[CombatScene Modal]
    A --> F[BoardRenderer]
    
    B --> G[game.step_turn]
    B --> H[AI Logic]
    B --> I[Combat Phase]
    
    C --> J[Market Window]
    C --> K[Card Purchase]
    
    D --> L[Card Placement]
    D --> M[Rotation Control]
    
    E --> N[Combat Visualization]
    E --> O[Results Display]
    
    F --> P[Board Display]
    F --> Q[Hand Panel]
    F --> R[Synergy HUD]
    
    style A fill:#0f2,stroke:#0a0,stroke-width:3px
    style B fill:#08f,stroke:#05a,stroke-width:2px
    style G fill:#f80,stroke:#a50,stroke-width:2px


## Main Algorithm/Workflow

```mermaid
sequenceDiagram
    participant Main as run_game2.py
    participant Shop as ShopScene
    participant Place as PlacementScene
    participant Game as game.step_turn()
    participant Combat as CombatScene
    participant Render as BoardRenderer
    
    Main->>Shop: run_modal(game, screen)
    Shop-->>Main: purchases complete
    
    Main->>Place: run_modal(game, screen)
    Place-->>Main: placement complete
    
    Main->>Game: step_turn()
    Note over Game: AI turns<br/>Income/interest<br/>Passive cleanup
    Game-->>Main: combat results
    
    Main->>Combat: run_modal(results, screen)
    Combat-->>Main: visualization complete
    
    Main->>Render: draw_board(screen)
    Render-->>Main: frame rendered
    
    Note over Main: Loop continues


## Core Interfaces/Types

```python
# Modal Scene Interface
class ModalScene:
    """Base interface for modal scenes that run synchronously."""
    
    @staticmethod
    def run_modal(game: Game, screen: pygame.Surface, **kwargs) -> dict:
        """Run scene as modal dialog, return result when complete.
        
        Args:
            game: Game state object
            screen: Pygame surface for rendering
            **kwargs: Scene-specific parameters
            
        Returns:
            Dictionary with scene results (purchases, placements, etc.)
        """
        pass


# Shop Scene Modal
class ShopSceneModal:
    """Modal shop interface for card purchasing."""
    
    @staticmethod
    def run_modal(game: Game, player: Player, screen: pygame.Surface) -> dict:
        """Open shop, handle purchases, return when player confirms.
        
        Returns:
            {
                'purchased': List[Card],  # Cards bought
                'gold_spent': int,        # Total gold spent
                'refreshes': int          # Number of refreshes
            }
        """
        pass


# Placement Scene Modal
class PlacementSceneModal:
    """Modal placement interface for card positioning."""
    
    @staticmethod
    def run_modal(game: Game, player: Player, screen: pygame.Surface) -> dict:
        """Open placement UI, handle card placement, return when complete.
        
        Returns:
            {
                'placed': List[Tuple[Card, Coord, Rotation]],  # Placed cards
                'locked_coords': Set[Coord]                     # Locked positions
            }
        """
        pass


# Combat Scene Modal
class CombatSceneModal:
    """Modal combat visualization."""
    
    @staticmethod
    def run_modal(combat_results: List[dict], screen: pygame.Surface) -> dict:
        """Display combat results, return when animation complete.
        
        Returns:
            {
                'viewed': bool,      # User viewed results
                'skipped': bool      # User skipped animation
            }
        """
        pass


# Game State
class HybridGameState:
    """Minimal state wrapper for hybrid architecture."""
    
    game: Game                              # Core game engine
    view_player: int                        # Currently viewed player index
    selected_hand_idx: Optional[int]        # Selected card from hand
    pending_rotation: int                   # Rotation before placement (0-5)
    placed_this_turn: int                   # Cards placed this turn
    locked_coords_per_player: Dict[int, Set[Coord]]  # Locked hex coords


## Key Functions with Formal Specifications

### Function 1: main_game_loop()

```python
def main_game_loop(game: Game, screen: pygame.Surface, fonts: dict) -> None:
    """Main hybrid game loop combining run_game.py logic with modal scenes."""
```

**Preconditions:**
- `game` is initialized with players and market
- `screen` is valid pygame surface
- `fonts` dictionary contains required font keys

**Postconditions:**
- Game runs until game_over or user quits
- All game state changes are deterministic
- No nested loops (scenes are modal calls)

**Loop Invariants:**
- `game.turn` increments monotonically
- `locked_coords_per_player` cleared at turn end
- AI logic executes identically to run_game.py

### Function 2: step_turn_hybrid()

```python
def step_turn_hybrid(game: Game, state: HybridGameState, 
                     screen: pygame.Surface, fonts: dict) -> None:
    """Execute one complete turn with modal scene integration."""
```

**Preconditions:**
- `game` has at least one alive player
- `state.view_player` is valid player index
- All scenes are importable

**Postconditions:**
- Player completes shop phase (via ShopSceneModal)
- Player completes placement phase (via PlacementSceneModal)
- `game.step_turn()` executes (AI turns, combat, cleanup)
- Combat results displayed (via CombatSceneModal)
- `locked_coords_per_player` cleared for all players

**Loop Invariants:** N/A (single execution per turn)

### Function 3: render_main_screen()

```python
def render_main_screen(screen: pygame.Surface, game: Game, 
                      state: HybridGameState, fonts: dict,
                      renderer: BoardRenderer) -> None:
    """Render main game screen with board, hand, and HUD."""
```

**Preconditions:**
- `screen` is valid pygame surface
- `game.players[state.view_player]` exists
- `renderer` is initialized with correct strategy

**Postconditions:**
- Board rendered with all placed cards
- Hand panel shows current player's hand
- Synergy HUD displays active synergies
- Player info panel shows HP, gold, turn
- Passive log displays recent triggers

**Loop Invariants:** N/A (pure rendering function)

## Algorithmic Pseudocode

### Main Game Loop Algorithm

```pascal
ALGORITHM main_game_loop(game, screen, fonts)
INPUT: game (Game object), screen (pygame.Surface), fonts (dict)
OUTPUT: None (runs until quit)

BEGIN
  ASSERT game is not null
  ASSERT game.players is not empty
  
  // Initialize state
  state ← HybridGameState()
  state.game ← game
  state.view_player ← 0
  state.locked_coords_per_player ← empty dict
  
  renderer ← BoardRenderer(BOARD_ORIGIN, game.players[0].strategy)
  renderer.init_fonts()
  
  game_over ← false
  winner ← null
  clock ← pygame.Clock()
  
  WHILE not game_over DO
    dt ← clock.tick(FPS)
    events ← pygame.event.get()
    
    // Check quit
    FOR each event IN events DO
      IF event.type = QUIT THEN
        game_over ← true
        BREAK
      END IF
    END FOR
    
    IF game_over THEN
      BREAK
    END IF
    
    // Handle input
    handle_input(events, state, game, screen, fonts, renderer)
    
    // Render main screen
    screen.fill(BACKGROUND_COLOR)
    render_main_screen(screen, game, state, fonts, renderer)
    
    pygame.display.flip()
  END WHILE
  
  pygame.quit()
END
```

**Preconditions:**
- pygame initialized
- game built with valid players
- screen created with valid dimensions

**Postconditions:**
- Game loop exits cleanly
- pygame resources released

**Loop Invariants:**
- `state.view_player` always valid index
- `game.turn` never decreases
- `renderer.strategy` matches viewed player

### Turn Step Algorithm

```pascal
ALGORITHM step_turn_hybrid(game, state, screen, fonts)
INPUT: game (Game), state (HybridGameState), screen (Surface), fonts (dict)
OUTPUT: None (modifies game state)

BEGIN
  ASSERT game.players[state.view_player].alive = true
  
  player ← game.players[state.view_player]
  
  // Phase 1: Shop (modal)
  player.income()
  shop_result ← ShopSceneModal.run_modal(game, player, screen)
  player.apply_interest()  // Apply interest after shop phase
  
  // Phase 2: Placement (modal)
  place_result ← PlacementSceneModal.run_modal(game, player, screen)
  state.locked_coords_per_player[player.pid] ← place_result.locked_coords
  
  // Phase 3: Core game logic (unchanged from run_game.py)
  clear_passive_trigger_log()
  
  // Increment turn
  game.turn ← game.turn + 1
  
  // AI player turns
  FOR each p IN game.players DO
    IF p.pid ≠ state.view_player AND p.alive THEN
      window ← game.market.deal_market_window(p, 5)
      p.income()
      AI.buy_cards(p, window, game.market, game.rng, trigger_passive)
      game.market.return_unsold(p)
      p.apply_interest()
      p.check_evolution(game.market, card_by_name)
      AI.place_cards(p, game.rng)
      p.check_copy_strengthening(game.turn, trigger_passive)
    END IF
  END FOR
  
  // Phase 4: Combat
  game.combat_phase()
  
  // Phase 5: Combat visualization (modal)
  combat_result ← CombatSceneModal.run_modal(game.last_combat_results, screen)
  
  // Phase 6: Cleanup
  FOR each pid IN state.locked_coords_per_player.keys() DO
    state.locked_coords_per_player[pid] ← empty set
  END FOR
  
  // Check game over
  alive ← [p FOR p IN game.players IF p.alive]
  IF length(alive) ≤ 1 OR game.turn ≥ 50 THEN
    winner ← max(game.players, key=lambda p: p.hp)
    display_game_over(screen, winner, fonts)
  END IF
END
```

**Preconditions:**
- Current player is alive
- Market has cards available
- All scenes are functional

**Postconditions:**
- Turn incremented by 1
- All players processed (human + AI)
- Combat executed and visualized
- Locked coords cleared

**Loop Invariants:**
- AI logic matches run_game.py exactly
- No state corruption between phases

### Render Main Screen Algorithm

```pascal
ALGORITHM render_main_screen(screen, game, state, fonts, renderer)
INPUT: screen (Surface), game (Game), state (HybridGameState), fonts (dict), renderer (BoardRenderer)
OUTPUT: None (draws to screen)

BEGIN
  player ← game.players[state.view_player]
  
  // Draw board (from run_game.py)
  renderer.draw(screen, player.board, BOARD_COORDS, 
                locked_coords=state.locked_coords_per_player[player.pid],
                show_tooltip=true)
  
  // Draw hand panel (from run_game.py)
  hand_rects ← _hand_card_rects(length(player.hand))
  draw_hand_panel(screen, player, fonts, state.selected_hand_idx,
                  pygame.mouse.get_pos(), state.pending_rotation)
  
  // Draw synergy HUD (from run_game.py)
  draw_synergy_hud(screen, player, fonts, renderer.highlight_group)
  
  // Draw player info (from run_game.py)
  draw_player_info(screen, player, game.turn, fonts, px=20, py=145)
  
  // Draw player panel (from run_game.py)
  draw_player_panel(screen, game.players, state.view_player,
                    fonts["md"], fonts["sm"], px=W-300, py=20)
  
  // Draw passive log (from run_game.py)
  hand_bottom ← HAND_PANEL_Y + length(player.hand) * (HAND_CARD_H + HAND_CARD_GAP) + 10
  log_max_h ← H - 100 - hand_bottom - 4
  draw_passive_buff_panel(screen, player, fonts["sm"],
                          px=HAND_PANEL_X, py=hand_bottom, max_h=log_max_h)
  
  // Draw cyber-victorian HUD (from run_game.py)
  draw_cyber_victorian_hud(screen, player, game.turn, fonts,
                           fast_mode=false, status_msg="SPACE → next turn")
END
```

**Preconditions:**
- `player` exists and is valid
- `renderer` initialized with player's strategy
- All rendering functions available

**Postconditions:**
- Screen contains complete game view
- All UI elements visible
- No rendering artifacts

**Loop Invariants:** N/A (pure rendering)

## Example Usage

```python
# Example 1: Initialize and run hybrid game loop
import pygame
from engine_core.game_factory import build_game
from scenes.shop_scene import ShopSceneModal
from scenes.placement_scene import PlacementSceneModal
from scenes.combat_scene import CombatSceneModal
from ui.board_renderer_v3 import BoardRendererV3

pygame.init()
screen = pygame.display.set_mode((1600, 960))
fonts = initialize_fonts()

# Build game (same as run_game.py)
strategies = ["aggressive", "defensive", "balanced", "economic"]
game = build_game(strategies)

# Run hybrid loop
main_game_loop(game, screen, fonts)

# Example 2: Execute one turn with modal scenes
state = HybridGameState()
state.game = game
state.view_player = 0

# This replaces the entire scene manager transition chain
step_turn_hybrid(game, state, screen, fonts)

# Example 3: Render main screen (called every frame)
renderer = BoardRendererV3(BOARD_ORIGIN, game.players[0].strategy)
render_main_screen(screen, game, state, fonts, renderer)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: AI Logic Equivalence

*For any* game state, AI player decisions in run_game2.py SHALL produce identical results to run_game.py when given the same random seed.

**Validates: Requirements 1.3, 9.2**

### Property 2: Combat Calculation Equivalence

*For any* board configuration, combat damage calculations SHALL produce identical results to run_game.py.

**Validates: Requirements 1.4, 9.3**

### Property 3: Passive Ability Equivalence

*For any* game state with passive abilities, ability effects SHALL be applied identically to run_game.py with consistent trigger ordering.

**Validates: Requirements 1.5, 9.4**

### Property 4: Modal Scene State Isolation

*For any* game state and modal scene execution, the game state SHALL remain unchanged until the scene returns and the main loop applies the returned results.

**Validates: Requirements 3.4**

### Property 5: Board Rendering Completeness

*For any* board state, all placed cards SHALL appear in the rendered output.

**Validates: Requirements 4.1**

### Property 6: Hand Rendering Completeness

*For any* hand state, all cards in the player's hand SHALL appear in the rendered hand panel.

**Validates: Requirements 4.2**

### Property 7: Synergy Display Accuracy

*For any* board state, the synergy HUD SHALL display counts that accurately reflect the active synergies on the board.

**Validates: Requirements 4.3**

### Property 8: Card Selection State Management

*For any* hand state and valid card index, clicking that card SHALL toggle the selected state correctly.

**Validates: Requirements 5.1, 8.9**

### Property 9: Rotation Increment Correctness

*For any* rotation value in range [0, 5], pressing R or right-clicking SHALL increment the rotation to (rotation + 1) mod 6.

**Validates: Requirements 5.3, 8.6, 8.11**

### Property 10: Card Placement Correctness

*For any* valid empty hex coordinate and selected card, clicking the hex SHALL place the card at that coordinate with the current rotation value.

**Validates: Requirements 5.4, 8.10**

### Property 11: Coordinate Locking on Placement

*For any* card placement, the placed coordinate SHALL be added to the locked coordinates set immediately after placement.

**Validates: Requirements 5.5**

### Property 12: Locked Coordinates Cleanup

*For any* game state with locked coordinates, all locked coordinate sets SHALL be empty after turn end.

**Validates: Requirements 5.7, 10.1**

### Property 13: Turn Execution Determinism

*For any* initial game state and input sequence, executing a turn SHALL produce the same final state when repeated with the same inputs and random seed.

**Validates: Requirements 9.1**

### Property 14: Turn Counter Monotonicity

*For any* turn execution, the turn counter SHALL increment by exactly 1.

**Validates: Requirements 9.5**

### Property 15: Turn End State Cleanup

*For any* turn end, the hybrid state SHALL reset selected_hand_idx to None, pending_rotation to 0, and placed_this_turn to 0.

**Validates: Requirements 10.2, 10.3, 10.4**

### Property 16: View Switch State Cleanup

*For any* view player change, the hybrid state SHALL clear selected card index and pending rotation.

**Validates: Requirements 10.5, 14.5**

### Property 17: Combat Results Structure

*For any* combat execution, the combat results SHALL contain a dictionary with keys: attacker, defender, attacker_damage, defender_damage, events, and breakdown.

**Validates: Requirements 11.1**

### Property 18: Player Index Clamping

*For any* player index value, the view_player SHALL be clamped to the valid range [0, num_players - 1].

**Validates: Requirements 12.3**

### Property 19: Winner Determination Correctness

*For any* game over state, the winner SHALL be the player with the highest HP value.

**Validates: Requirements 13.3**

### Property 20: Player View Cycling

*For any* current view_player value, pressing TAB SHALL cycle to (view_player + 1) mod num_players.

**Validates: Requirements 14.1**

### Property 21: Renderer Strategy Synchronization

*For any* view player change, the Board_Renderer's strategy SHALL match the new view player's strategy.

**Validates: Requirements 14.3**

### Property 22: Placement Counter Increment

*For any* card placement, the placed_this_turn counter SHALL increment by exactly 1.

**Validates: Requirements 15.2**

### Property 23: Placement Limit Enforcement

*For any* game state where placed_this_turn equals PLACE_PER_TURN, further placement attempts SHALL be rejected.

**Validates: Requirements 15.3**

### Property 24: Synergy Highlight Correctness

*For any* board state and synergy group, hovering over that synergy in the HUD SHALL highlight all cards belonging to that synergy group.

**Validates: Requirements 17.1**

### Property 25: Passive Log Entry Creation

*For any* passive ability trigger, an entry SHALL be added to the passive log.

**Validates: Requirements 20.1**

### Property 26: Passive Log Cleanup

*For any* turn start, the passive log SHALL be cleared to empty.

**Validates: Requirements 20.3**

## Error Handling

### Error Scenario 1: Scene Import Failure
**Condition:** ShopSceneModal, PlacementSceneModal, or CombatSceneModal fails to import
**Response:** Fallback to text-based input (similar to original run_game.py before UI)
**Recovery:** Log error, continue with minimal UI

### Error Scenario 2: Invalid Player Index
**Condition:** `state.view_player` references non-existent player
**Response:** Clamp to valid range `[0, len(game.players)-1]`
**Recovery:** Reset to player 0, log warning

### Error Scenario 3: Scene Modal Crash
**Condition:** Modal scene raises exception during execution
**Response:** Catch exception, log traceback, skip scene phase
**Recovery:** Continue to next phase with default values (empty purchases, no placements)

## Testing Strategy

### Unit Testing Approach

Test individual functions in isolation:
- `step_turn_hybrid()`: Mock game state, verify turn flow
- `render_main_screen()`: Mock pygame surface, verify draw calls
- Modal scene interfaces: Test return value structure

**Key Test Cases:**
1. Turn flow matches run_game.py exactly
2. Locked coords cleared at turn end
3. AI logic produces identical results
4. Rendering functions called in correct order

### Property-Based Testing Approach

**Property Test Library**: Hypothesis (Python)

**Properties to Test:**
1. **Determinism**: Same input → same output across runs
2. **Turn Monotonicity**: `game.turn` never decreases
3. **State Validity**: Game state always valid after turn
4. **Rendering Idempotence**: Multiple render calls produce same output

**Example Property Test:**
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=7))
def test_view_player_always_valid(player_idx):
    """View player index always clamped to valid range."""
    state = HybridGameState()
    state.view_player = player_idx
    game = build_game(["strat1", "strat2"])
    
    # Clamp logic
    state.view_player = max(0, min(state.view_player, len(game.players) - 1))
    
    assert 0 <= state.view_player < len(game.players)
```

### Integration Testing Approach

Test full turn execution with real game engine:
1. Build game with 4 players
2. Execute `step_turn_hybrid()` for 10 turns
3. Verify game state matches run_game.py after same inputs
4. Compare combat results, HP changes, gold totals

## Performance Considerations

- **Font Caching**: Initialize fonts once, reuse across frames (avoid run_game.py's per-frame recreation)
- **Asset Loading**: Preload card images at startup, cache in memory
- **Rendering Optimization**: Only redraw changed UI elements (dirty rectangles)
- **Modal Scene Overhead**: Minimal - scenes are function calls, not separate processes

## Security Considerations

- **Input Validation**: Validate all user inputs (card selection, hex coordinates)
- **State Integrity**: Prevent invalid game states (negative gold, invalid placements)
- **Determinism**: Ensure no non-deterministic behavior (fixed RNG seed for testing)

## Dependencies

- **pygame**: Graphics and input handling
- **engine_core**: Game logic (Game, Player, Card, Board, Market, AI)
- **ui**: Rendering utilities (BoardRenderer, CyberRenderer, HUD functions)
- **scenes**: Modal scene implementations (ShopSceneModal, PlacementSceneModal, CombatSceneModal)
- **core**: Minimal state wrappers (HybridGameState)

## Implementation Notes

### Scene Modal Conversion

Existing scenes (ShopScene, CombatScene) use SceneManager signals (`self.manager.go_to(...)`). Converting to modal pattern requires:

**Option 1: Wrapper Approach**
```python
class ShopSceneModal:
    @staticmethod
    def run_modal(game, player, screen):
        # Create temporary scene without manager
        scene = ShopScene(game, player)
        scene.manager = None  # Disable manager
        
        # Run internal loop until done
        done = False
        while not done:
            events = pygame.event.get()
            scene.handle_input(events)
            scene.update(dt)
            scene.draw(screen)
            pygame.display.flip()
            
            # Check exit condition (e.g., SPACE pressed)
            if scene.should_exit:
                done = True
        
        return scene.get_results()
```

**Option 2: Subclass Approach**
```python
class ShopSceneModal(ShopScene):
    def __init__(self, game, player):
        super().__init__(game, player)
        self.manager = None  # No manager needed
        self.modal_done = False
    
    def handle_confirm(self):
        # Override to set flag instead of manager.go_to()
        self.modal_done = True
    
    @staticmethod
    def run_modal(game, player, screen):
        scene = ShopSceneModal(game, player)
        # ... run loop until scene.modal_done
```

### Combat Results Format

Verify `game.last_combat_results` structure matches CombatScene expectations:
```python
# Expected format from game.combat_phase()
last_combat_results = [
    {
        'attacker': Player,
        'defender': Player,
        'attacker_damage': int,
        'defender_damage': int,
        'events': List[str],  # Combat log
        'breakdown': dict     # Detailed analysis
    },
    # ... one per combat pair
]
```

If CombatScene currently receives results via signals, extract the data structure and pass directly to `CombatSceneModal.run_modal()`.

### Renderer Strategy Updates

Add to `handle_input()` function:
```python
def handle_input(events, state, game, screen, fonts, renderer):
    """Handle keyboard/mouse input for main game screen."""
    for event in events:
        if event.type == pygame.KEYDOWN:
            # Switch viewed player
            if event.key == pygame.K_TAB:
                state.view_player = (state.view_player + 1) % len(game.players)
                renderer.strategy = game.players[state.view_player].strategy
            
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(game.players):
                    state.view_player = idx
                    renderer.strategy = game.players[state.view_player].strategy
            
            # Trigger turn step
            elif event.key == pygame.K_SPACE:
                step_turn_hybrid(game, state, screen, fonts)
            
            # Reset game
            elif event.key == pygame.K_r and state.selected_hand_idx is None:
                # Return to lobby (implementation specific)
                pass
            
            # Direct shop access
            elif event.key == pygame.K_s:
                player = game.players[state.view_player]
                ShopSceneModal.run_modal(game, player, screen)
        
        # Handle mouse input for card selection, placement, etc.
        # ... (copy from run_game.py)
```

### Recommended Implementation Order

1. **render_main_screen()** - Copy rendering code from run_game.py, verify visual output matches
2. **handle_input()** - Implement input handling without modal scenes first
3. **step_turn_hybrid() skeleton** - AI and combat disabled, just view_player flow
4. **ShopSceneModal wrapper** - Most complex conversion, test thoroughly
5. **PlacementSceneModal wrapper** - Similar to shop, but simpler
6. **Combat integration** - Enable `game.combat_phase()`, verify results format
7. **CombatSceneModal wrapper** - Visual-only, should be straightforward
8. **Full integration test** - Run complete turn cycle, compare with run_game.py
