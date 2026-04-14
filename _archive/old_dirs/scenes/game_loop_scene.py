"""
GameLoopScene - Central hub for turn orchestration

This scene manages the main game loop, including:
- Turn advancement and orchestration
- Player switching (1-8 keys)
- Fast mode toggle and auto-advance
- Combat results display
- Game over detection
- Transitions to Shop, Combat, and GameOver scenes
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, TYPE_CHECKING

import pygame

from core.scene import Scene
from core.core_game_state import CoreGameState

if TYPE_CHECKING:
    from engine_core.player import Player
    from core.input_state import InputState


@dataclass
class GameLoopUIState:
    """THROWAWAY state specific to GameLoopScene.
    
    This state is created fresh in on_enter() and discarded in on_exit().
    It contains only UI-specific state that does not need to persist across scenes.
    """
    fast_timer: int = 0  # Timer for fast mode auto-advance (milliseconds)
    popup_timer: int = 0  # Timer for combat results popup (milliseconds)
    popup_data: List[dict] = field(default_factory=list)  # Combat results data
    last_breakdown: Optional[dict] = None  # Combat breakdown for current player
    game_over: bool = False  # Game over flag
    winner: Optional['Player'] = None  # Winner player object
    status_msg: str = ""  # Status message to display
    
    # Player panel click detection (T2.3b)
    player_panel_rects: List[pygame.Rect] = field(default_factory=list)  # Rectangles for each player row
    
    # TEMPORARY: Flag to trigger combat after all players prepare (T1.13)
    # TODO: Remove this flag in future refactor - combat triggering should be
    # owned entirely by GameLoopScene without cross-scene signaling
    needs_combat_trigger: bool = False


class GameLoopScene(Scene):
    """Central hub for turn orchestration and game flow control.
    
    Responsibilities:
    - Display current game state (turn, players, HP)
    - Handle player switching (1-8 keys)
    - Handle fast mode toggle (F key)
    - Handle turn advancement (SPACE key)
    - Orchestrate turn flow (income, shop, combat, AI turns)
    - Display combat results popup
    - Detect game over and transition to GameOverScene
    
    Lifecycle:
    - on_enter(): Create fresh GameLoopUIState
    - handle_input(): Process keyboard/mouse input
    - update(): Update timers and game logic
    - draw(): Render UI elements
    - on_exit(): Discard GameLoopUIState
    
    Requirements:
    - Req 2: GameLoopScene is the central hub for turn orchestration
    - Req 3: Turn flow management (income, shop, combat, cleanup)
    - Req 4: Fast mode auto-advance every 600ms
    - Req 5: Player switching (1-8 keys)
    - Req 10: Game over detection and winner tracking
    """
    
    def __init__(self, core_game_state: CoreGameState, **kwargs):
        """Initialize GameLoopScene with shared core game state.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes
            **kwargs: Additional keyword arguments (e.g., strategies from LobbyScene)
        """
        super().__init__(core_game_state)
        
        # Store any additional kwargs for later use
        self.kwargs = kwargs
        
        # UI state will be created in on_enter()
        self.ui_state: Optional[GameLoopUIState] = None
    
    def on_enter(self) -> None:
        """Called when scene becomes active.
        
        Creates fresh GameLoopUIState and initializes scene resources.
        
        Requirements:
        - Create fresh UIState (THROWAWAY)
        - Initialize scene-specific resources
        - T1.13: Set combat trigger flag when returning from CombatScene
        """
        # Create fresh UIState
        self.ui_state = GameLoopUIState()
        
        # ============================================================================
        # TEMPORARY ARCHITECTURAL COMPROMISE (T1.13)
        # ============================================================================
        # The trigger_combat flag passed from CombatScene is a TEMPORARY solution.
        # 
        # CURRENT BEHAVIOR:
        # - CombatScene signals GameLoopScene to trigger combat via kwargs
        # - This creates cross-scene coupling and signaling
        # 
        # FUTURE REFACTOR:
        # - Combat triggering should be owned entirely by GameLoopScene
        # - GameLoopScene should track preparation state internally
        # - Remove trigger_combat flag from CombatScene transition
        # - GameLoopScene determines when all players are ready for combat
        # 
        # WHY THIS IS TEMPORARY:
        # - Violates single responsibility (CombatScene shouldn't know about combat phase)
        # - Creates tight coupling between scenes
        # - Makes scene transitions less declarative
        # ============================================================================
        
        # T1.13: Check if we're returning from CombatScene (human player completed preparation)
        # If trigger_combat flag is set in kwargs, we need to trigger combat phase in update()
        if self.kwargs.get('trigger_combat', False):
            self.ui_state.needs_combat_trigger = True
            print("✓ Combat trigger flag set - will trigger combat in update()")
        
        print("✓ GameLoopScene.on_enter() - Scene initialized")
        print(f"  - Turn: {self.core_game_state.turn}")
        print(f"  - Players: {len(self.core_game_state.game.players)}")
        print(f"  - Current player: {self.core_game_state.current_player.pid}")
    
    def on_exit(self) -> None:
        """Called when scene is deactivated.
        
        Cleans up scene-specific resources and discards UIState.
        
        Requirements:
        - Clean up scene-specific resources
        - Discard UIState (THROWAWAY)
        """
        # Discard THROWAWAY state
        self.ui_state = None
        
        print("✓ GameLoopScene.on_exit() - Resources cleaned up")
    
    def advance_turn(self) -> None:
        """Advance the game turn and orchestrate turn flow.
        
        This method extracts turn advancement logic from run_game.py step_turn().
        
        Responsibilities:
        - Clear passive trigger log
        - Increment turn counter (handled by preparation_phase or after shop)
        - Conditional shop skip for fast mode (T2.6)
        - Trigger combat phase after all players complete preparation
        - Store combat results
        - Clear locked coordinates for all players
        
        Requirements:
        - Req 3: Turn flow management
        - Req 4: Fast mode should bypass shop interaction
        - Req 26: Economy system integration (income)
        - Req 27: Combat phase triggering
        - T1.7: Extract turn orchestration logic from run_game.py
        - T2.6: Conditional shop skip for fast mode
        """
        from engine_core.passive_trigger import clear_passive_trigger_log
        
        # Clear passive trigger log at turn start
        clear_passive_trigger_log()
        print(f"✓ Turn {self.core_game_state.turn} - Passive log cleared")
        
        # ============================================================================
        # T2.6: Conditional Shop Skip for Fast Mode
        # ============================================================================
        # If fast_mode is True:
        #   - Skip shop scene transition
        #   - Call game.preparation_phase() directly (handles all players via AI)
        #   - Trigger combat immediately
        # If fast_mode is False:
        #   - Transition to "shop" scene for human player
        #   - Human player will manually buy cards and place them
        # ============================================================================
        
        if self.core_game_state.fast_mode:
            # Fast mode: Skip shop, process all players via AI, trigger combat
            print("✓ Fast mode enabled - skipping shop scene")
            
            # Call preparation_phase() which handles:
            # - Increment turn counter
            # - Deal market windows for all players
            # - Apply income to all players
            # - AI buys cards for all players
            # - Apply interest to all players
            # - Check evolution for all players
            # - AI places cards for all players
            # - Check copy strengthening for all players
            game = self.core_game_state.game
            game.preparation_phase()
            print(f"✓ Preparation phase complete (all players processed via AI)")
            
            # Trigger combat immediately after preparation
            print("✓ Triggering combat phase")
            game.combat_phase()
            
            # Store combat results for popup display
            if hasattr(game, 'last_combat_results'):
                if self.ui_state:
                    self.ui_state.popup_data = list(game.last_combat_results)
                    self.ui_state.popup_timer = 3000  # 3 seconds
                    
                    # Extract combat breakdown for current player
                    view_player_pid = self.core_game_state.view_player_index
                    for result in self.ui_state.popup_data:
                        if result.get("pid_a") == view_player_pid or result.get("pid_b") == view_player_pid:
                            self.ui_state.last_breakdown = result
                            break
                    
                    print(f"✓ Combat results stored: {len(self.ui_state.popup_data)} battles")
            
            # Clear locked coordinates for all players
            for player in game.players:
                self.core_game_state.clear_locked_coords(player.pid)
            print("✓ Locked coordinates cleared for all players")
            
        else:
            # Normal mode: Apply income to current player, then transition to shop
            current_player = self.core_game_state.current_player
            if current_player.alive:
                current_player.income()
                print(f"✓ Income applied to Player {current_player.pid + 1}: {current_player.gold} gold")
            
            # Transition to shop scene for human player
            # (Turn will be incremented after shop phase completes)
            print("✓ Transitioning to shop scene")
            self.scene_manager.request_transition("shop")
    
    def process_ai_turns(self) -> None:
        """Process AI player turns (economy + placement phase).
        
        This method extracts AI turn loop from run_game.py step_turn() (lines 447-467).
        For each AI player (not current viewed player):
        - Deal market window
        - Apply income
        - Call AI.buy_cards()
        - Return unsold cards to market
        - Apply interest
        - Check evolution (T2.5b)
        - Call AI.place_cards() (T2.5b)
        - Check copy strengthening (T2.5b)
        
        NOTE: This method implements both T2.5a (economy) and T2.5b (placement).
        
        Requirements:
        - Req 12: AI player turns (economy + placement phase)
        - Req 26: Economy system integration (income, interest)
        - T2.5a: Extract AI economy phase from run_game.py
        - T2.5b: Extract AI placement phase from run_game.py
        """
        from engine_core.ai import AI
        from engine_core.passive_trigger import trigger_passive
        
        game = self.core_game_state.game
        view_player_pid = self.core_game_state.view_player_index
        
        print("✓ Processing AI player turns (economy + placement phase)")
        
        # Process each AI player (not the currently viewed player)
        for player in game.players:
            # Skip if player is dead or is the currently viewed player
            if not player.alive or player.pid == view_player_pid:
                continue
            
            print(f"  - Processing AI Player {player.pid + 1} ({player.strategy})")
            
            # ============================================================================
            # ECONOMY PHASE (T2.5a)
            # ============================================================================
            
            # Deal market window (5 cards)
            window_ai = game.market.deal_market_window(player, 5)
            print(f"    • Dealt market window: {len(window_ai)} cards")
            
            # Apply income
            old_gold = player.gold
            player.income()
            print(f"    • Income applied: {old_gold} → {player.gold} gold")
            
            # AI buys cards from market
            old_hand_size = len(player.hand)
            AI.buy_cards(
                player, 
                window_ai, 
                market_obj=game.market,
                rng=game.rng, 
                trigger_passive_fn=trigger_passive
            )
            new_hand_size = len(player.hand)
            cards_bought = new_hand_size - old_hand_size
            print(f"    • AI bought {cards_bought} card(s), hand size: {old_hand_size} → {new_hand_size}")
            
            # Return unsold cards to market
            game.market.return_unsold(player)
            print(f"    • Returned unsold cards to market")
            
            # Apply interest
            old_gold = player.gold
            player.apply_interest()
            interest_earned = player.gold - old_gold
            print(f"    • Interest applied: +{interest_earned} gold (total: {player.gold})")
            
            # ============================================================================
            # PLACEMENT PHASE (T2.5b)
            # ============================================================================
            
            # Check evolution (combine cards into higher tier)
            card_by_name = {c.name: c for c in game.card_pool}
            old_hand_size = len(player.hand)
            player.check_evolution(market=game.market, card_by_name=card_by_name)
            new_hand_size = len(player.hand)
            if new_hand_size != old_hand_size:
                print(f"    • Evolution checked: hand size {old_hand_size} → {new_hand_size}")
            else:
                print(f"    • Evolution checked: no evolutions")
            
            # AI places cards on board
            old_board_size = player.board.alive_count()
            AI.place_cards(player, rng=game.rng)
            new_board_size = player.board.alive_count()
            cards_placed = new_board_size - old_board_size
            print(f"    • AI placed {cards_placed} card(s), board size: {old_board_size} → {new_board_size}")
            
            # Check copy strengthening (strengthen duplicate cards on board)
            player.check_copy_strengthening(
                game.turn, 
                trigger_passive_fn=trigger_passive
            )
            print(f"    • Copy strengthening checked")
        
        print("✓ AI player turns complete (economy + placement)")
    
    def trigger_combat_and_cleanup(self) -> None:
        """Trigger combat phase and perform cleanup after all players complete preparation.
        
        This method is called after all players (human + AI) complete their shop/combat phases.
        
        Responsibilities:
        - Process AI player turns (economy phase) - T2.5a
        - Call game.combat_phase()
        - Store combat results in game.last_combat_results
        - Clear locked coordinates for all players
        - Update popup data for combat results display
        
        Requirements:
        - Req 12: AI player turns (economy phase)
        - Req 27: Combat phase triggering
        - Req 7: Clear locked coordinates after turn end
        - Req 9: Store combat results for popup display
        """
        game = self.core_game_state.game
        
        # Process AI player turns (economy phase only) - T2.5a
        # NOTE: This is Part 1 of AI turn logic. Part 2 (T2.5b) will add placement/evolution.
        self.process_ai_turns()
        
        # Trigger combat phase
        print("✓ Triggering combat phase")
        game.combat_phase()
        
        # Store combat results
        if hasattr(game, 'last_combat_results'):
            if self.ui_state:
                self.ui_state.popup_data = list(game.last_combat_results)
                self.ui_state.popup_timer = 3000  # 3 seconds
                
                # Extract combat breakdown for current player
                view_player_pid = self.core_game_state.view_player_index
                for result in self.ui_state.popup_data:
                    if result.get("pid_a") == view_player_pid or result.get("pid_b") == view_player_pid:
                        self.ui_state.last_breakdown = result
                        break
                
                print(f"✓ Combat results stored: {len(self.ui_state.popup_data)} battles")
        
        # Clear locked coordinates for all players
        for player in game.players:
            self.core_game_state.clear_locked_coords(player.pid)
        print("✓ Locked coordinates cleared for all players")
        
        # Increment turn counter AFTER combat
        game.turn += 1
        print(f"✓ Turn incremented to {game.turn}")
    
    def handle_input(self, input_state: 'InputState') -> None:
        """Process input intents for this scene.
        
        Handles:
        - SPACE: Advance turn (transition to shop)
        - F: Toggle fast mode
        - 1-8: Switch player view
        - ESC: Quit game
        - Mouse click: Click on player panel to switch view
        
        Args:
            input_state: Intent-based input abstraction
        
        Requirements:
        - Req 14: Input handling for SPACE, F, 1-8, ESC
        - T1.10: Transition to "shop" on SPACE key (if not fast_mode)
        - T2.2: Toggle fast mode on F key
        - T2.3a: Player switching via 1-8 keys
        - T2.3b: Player switching via mouse click on player panel
        """
        # Handle mouse click on player panel (T2.3b)
        if input_state.mouse_clicked:  # Left click
            mouse_pos = input_state.mouse_pos
            
            # Check if click is within any player rectangle
            if self.ui_state and self.ui_state.player_panel_rects:
                for player_index, rect in enumerate(self.ui_state.player_panel_rects):
                    if rect.collidepoint(mouse_pos):
                        # Validate that target player exists
                        num_players = len(self.core_game_state.game.players)
                        if 0 <= player_index < num_players:
                            # Set view_player_index directly
                            old_index = self.core_game_state.view_player_index
                            self.core_game_state.view_player_index = player_index
                            
                            # Print debug message showing switch
                            old_player = self.core_game_state.game.players[old_index]
                            new_player = self.core_game_state.game.players[player_index]
                            print(f"✓ Player switch (click): Player {old_index + 1} → Player {player_index + 1} "
                                  f"(PID {old_player.pid} → PID {new_player.pid})")
                        return
        
        # Handle F key - toggle fast mode (T2.2)
        if input_state.is_fast_mode_toggled():
            self.core_game_state.fast_mode = not self.core_game_state.fast_mode
            if self.ui_state:
                self.ui_state.fast_timer = 0  # Reset timer when toggling
            print(f"✓ Fast mode {'enabled' if self.core_game_state.fast_mode else 'disabled'}")
            return
        
        # Handle SPACE key - advance turn (transition to shop)
        if input_state.was_key_pressed_this_frame(pygame.K_SPACE):
            # T1.10: Transition to shop scene (if not fast_mode)
            # In fast mode, turns advance automatically via timer
            if not self.core_game_state.fast_mode:
                print("✓ Advancing turn - calling advance_turn()")
                self.advance_turn()
            return
        
        # Handle ESC key - quit game
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            pygame.quit()
            import sys
            sys.exit(0)
            return
        
        # Handle 1-8 keys - player switching (T2.3a)
        player_switch_request = input_state.get_player_switch_request()
        if player_switch_request != -1:
            # Validate that target player exists
            num_players = len(self.core_game_state.game.players)
            if 0 <= player_switch_request < num_players:
                # Set view_player_index directly (do NOT use switch_player(direction))
                old_index = self.core_game_state.view_player_index
                self.core_game_state.view_player_index = player_switch_request
                
                # Print debug message showing switch
                old_player = self.core_game_state.game.players[old_index]
                new_player = self.core_game_state.game.players[player_switch_request]
                print(f"✓ Player switch: Player {old_index + 1} → Player {player_switch_request + 1} "
                      f"(PID {old_player.pid} → PID {new_player.pid})")
            else:
                print(f"✗ Invalid player switch request: index {player_switch_request} "
                      f"(only {num_players} players exist)")
            return
    
    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        Updates:
        - Combat phase triggering (after all players complete preparation)
        - Fast mode timer (auto-advance turns)
        - Popup timer (combat results fade-out)
        - Game over detection
        
        Args:
            dt: Delta time in milliseconds since last frame
        
        Requirements:
        - Req 27: Combat phase triggering after all players prepare
        - Req 4: Fast mode auto-advance every 600ms
        - Req 25: Popup timer fade-out animation
        - Req 10: Game over detection
        - T1.13: Trigger combat phase and clear locked coords
        - T1.10: Transition to "game_over" when game over detected
        - T2.2: Fast mode timer and auto-advance
        """
        if not self.ui_state:
            return
        
        # ============================================================================
        # TEMPORARY: Combat triggering via cross-scene flag (T1.13)
        # ============================================================================
        # This checks a flag set by CombatScene to trigger combat.
        # FUTURE REFACTOR: GameLoopScene should own combat triggering logic entirely
        # without relying on signals from other scenes.
        # ============================================================================
        if self.ui_state.needs_combat_trigger:
            self.trigger_combat_and_cleanup()
            self.ui_state.needs_combat_trigger = False
            return
        
        # Fast mode timer and auto-advance (T2.2, Req 4, T2.6)
        FAST_DELAY = 600  # milliseconds
        if self.core_game_state.fast_mode and not self.ui_state.game_over:
            self.ui_state.fast_timer += dt
            # Debug: Show timer progress
            if self.ui_state.fast_timer % 100 < dt:  # Print every ~100ms
                print(f"[Fast Mode] Timer: {self.ui_state.fast_timer:.0f}ms / {FAST_DELAY}ms")
            
            if self.ui_state.fast_timer >= FAST_DELAY:
                self.ui_state.fast_timer = 0
                print("✓ Fast mode auto-advance - calling advance_turn()")
                # T2.6: advance_turn() now handles fast mode properly:
                # - Skips shop scene
                # - Calls preparation_phase() for all players
                # - Triggers combat immediately
                self.advance_turn()
        
        # Game over detection (Req 10, T1.10)
        if not self.ui_state.game_over:
            alive_players = self.core_game_state.alive_players
            turn = self.core_game_state.turn
            
            # Check game over conditions
            if len(alive_players) <= 1:
                self.ui_state.game_over = True
                self.ui_state.winner = alive_players[0] if alive_players else None
                print(f"✓ Game over detected - {len(alive_players)} player(s) remaining")
                
                # Transition to game_over scene
                self.scene_manager.request_transition("game_over", winner=self.ui_state.winner)
                return
            
            # Infinite loop guard
            if turn >= 50:
                self.ui_state.game_over = True
                # Find player with max HP as winner
                self.ui_state.winner = max(self.core_game_state.game.players, key=lambda p: p.hp)
                print(f"✓ Game over detected - turn limit reached (turn {turn})")
                
                # Transition to game_over scene
                self.scene_manager.request_transition("game_over", winner=self.ui_state.winner)
                return
        
        # Decrement popup timer (Req 25)
        if self.ui_state.popup_timer > 0:
            self.ui_state.popup_timer = max(0, self.ui_state.popup_timer - dt)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Render scene to screen.
        
        Renders:
        - Turn counter
        - Player list with HP/status
        - Fast mode indicator
        - Combat results popup (T2.4)
        - Combat breakdown (T2.4)
        - Status message
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - Req 11: HUD rendering (turn counter, player list, indicators)
        - Req 9: Combat results popup display
        - Req 25: Popup timer fade-out animation
        - T2.3b: Store player panel rectangles for click detection
        - T2.4: Render combat results popup and breakdown
        """
        from ui.hud_renderer import (
            draw_cyber_victorian_hud, 
            draw_player_panel,
            draw_turn_popup,
            draw_combat_breakdown
        )
        
        # Background
        screen.fill((20, 20, 40))
        
        # Initialize fonts
        def _font(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                return pygame.font.SysFont("consolas", size, bold=bold)
        
        fonts = {
            "title":   _font("bahnschrift", 28, bold=True),
            "lg":      _font("consolas", 24, bold=True),
            "md":      _font("consolas", 16),
            "md_bold": _font("consolas", 16, bold=True),
            "sm":      _font("consolas", 13),
            "sm_bold": _font("consolas", 13, bold=True),
            "xs":      _font("consolas", 12),
            "xs_bold": _font("consolas", 12, bold=True),
            "icon":    _font("segoeuisymbol", 18, bold=True),
        }
        
        # Get current player and game state
        current_player = self.core_game_state.current_player
        game = self.core_game_state.game
        turn = self.core_game_state.turn
        fast_mode = self.core_game_state.fast_mode
        view_player_index = self.core_game_state.view_player_index
        
        # Draw main HUD (top-left corner + bottom bar)
        status_msg = self.ui_state.status_msg if self.ui_state else ""
        draw_cyber_victorian_hud(
            screen, 
            current_player, 
            turn, 
            fonts, 
            fast_mode=fast_mode,
            status_msg=status_msg
        )
        
        # Draw player panel (right side) and capture rectangles for click detection (T2.3b)
        players = game.players
        selected_player_idx = self.core_game_state.view_player_index
        panel_x = screen.get_width() - 300
        panel_y = 20
        player_rects = draw_player_panel(
            screen,
            players,
            selected_player_idx,
            fonts["md_bold"],
            fonts["sm_bold"],
            panel_x,
            panel_y
        )
        
        # Store player rectangles in UIState for click detection (T2.3b)
        if self.ui_state:
            self.ui_state.player_panel_rects = player_rects
        
        # Draw "ADVANCE TURN" prompt in center
        prompt_font = fonts["lg"]
        prompt_text = "Press SPACE to advance turn"
        prompt_surface = prompt_font.render(prompt_text, True, (0, 242, 255))
        prompt_rect = prompt_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        
        # Draw semi-transparent background for prompt
        bg_rect = prompt_rect.inflate(40, 20)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((10, 12, 24, 180))
        screen.blit(bg_surface, bg_rect)
        pygame.draw.rect(screen, (0, 242, 255), bg_rect, 2, border_radius=8)
        
        # Draw prompt text
        screen.blit(prompt_surface, prompt_rect)
        
        # ============================================================================
        # T2.4: Combat Results Popup and Breakdown
        # ============================================================================
        # Render combat results popup when popup_timer > 0
        # Calculate fade alpha based on remaining time
        # Display combat breakdown for current player
        # ============================================================================
        if self.ui_state and self.ui_state.popup_timer > 0:
            POPUP_DURATION = 3000  # milliseconds
            
            # Calculate fade alpha (Req 25)
            # Formula: min(255, int(popup_timer / POPUP_DURATION * 510))
            # This creates a fade-in/fade-out effect:
            # - First half (1500ms): fade in from 0 to 255
            # - Second half (1500ms): fade out from 255 to 0
            fade_alpha = min(255, int(self.ui_state.popup_timer / POPUP_DURATION * 510))
            
            # Draw turn popup with combat results (Req 9)
            if self.ui_state.popup_data:
                draw_turn_popup(
                    screen,
                    self.ui_state.popup_data,
                    view_player_index,
                    players,
                    fonts["lg"],
                    fonts["md"],
                    fonts["sm"],
                    fade_alpha
                )
            
            # Draw combat breakdown for current player (Req 9)
            if self.ui_state.last_breakdown:
                draw_combat_breakdown(
                    screen,
                    self.ui_state.last_breakdown,
                    view_player_index,
                    players,
                    fonts["md"],
                    fonts["sm"]
                )
