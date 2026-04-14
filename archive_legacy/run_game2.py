"""
================================================================
  Autochess Hybrid - run_game2.py (Hybrid Architecture)
  Oyunu başlat:  python run_game2.py
================================================================
  Hybrid architecture combining run_game.py's proven game loop
  with scene-based UI components as modal dialogs.
  
  Kontroller:
    SPACE      → tur ilerlet (shop → AI → combat)
    S          → Shop modal aç
    F          → hızlı mod
    1-8        → oyuncular arası geçiş
    TAB        → sonraki oyuncu
    R          → yeni oyun | seçili kart varken: döndür
    ESC        → seçimi iptal et / çıkış
================================================================
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional
import pygame

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool
from engine_core.player import Player
from engine_core.game import Game
from engine_core.board import combat_phase, BOARD_COORDS
from engine_core.constants import STRATEGIES, PLACE_PER_TURN
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log
from ui.board_renderer_v3 import BoardRendererV3 as BoardRenderer
from ui.renderer_v3 import CyberRendererV3 as CyberRenderer
from ui.renderer import COLOR_BG
from ui.hud_renderer import (
    draw_hand_panel,
    draw_synergy_hud,
    draw_player_info,
    draw_player_panel,
    draw_passive_buff_panel,
    draw_cyber_victorian_hud,
    get_hovered_synergy_group,
)

# ── Window constants ──────────────────────────────────────────
W, H = 1600, 960
FPS = 60
TITLE = "Autochess Hybrid // Neon Circuit (v2)"
BOARD_ORIGIN = (800, H // 2 - 10)


# ── HybridGameState ───────────────────────────────────────────
@dataclass
class HybridGameState:
    """Minimal state wrapper for hybrid architecture."""
    game: Game
    view_player: int = 0
    selected_hand_idx: Optional[int] = None
    pending_rotation: int = 0
    placed_this_turn: int = 0
    locked_coords_per_player: Dict[int, Set[Tuple[int, int]]] = field(default_factory=dict)
    fast_mode: bool = False


# ── build_game ────────────────────────────────────────────────
def build_game(strategies: list = None) -> Game:
    """Build game instance with players and market."""
    import random
    rng = random.Random()
    pool = get_card_pool()
    if strategies is None:
        strategies = STRATEGIES[:]
        rng.shuffle(strategies)
    players = [Player(pid=i, strategy=strategies[i]) for i in range(len(strategies))]
    game = Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=pool,
    )
    return game


# ── Font initialization ───────────────────────────────────────
def initialize_fonts() -> dict:
    """Initialize pygame fonts once and cache."""
    def _font(name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            return pygame.font.SysFont("consolas", size, bold=bold)

    return {
        "title": _font("bahnschrift", 28, bold=True),
        "lg": _font("consolas", 24, bold=True),
        "md": _font("consolas", 16),
        "md_bold": _font("consolas", 16, bold=True),
        "sm": _font("consolas", 13),
        "sm_bold": _font("consolas", 13, bold=True),
        "xs": _font("consolas", 12),
        "xs_bold": _font("consolas", 12, bold=True),
        "icon": _font("segoeuisymbol", 18, bold=True),
    }


# ── Input handling ────────────────────────────────────────────
def handle_input(events: list, state: HybridGameState, game: Game,
                 renderer: BoardRenderer, screen: pygame.Surface, fonts: dict,
                 asset_loader: 'AssetLoader') -> None:
    """Handle keyboard and mouse input, updating HybridGameState and triggering game logic.
    
    Args:
        events: List of pygame events
        state: HybridGameState to update
        game: Game instance
        renderer: BoardRenderer instance (for strategy updates)
        screen: pygame Surface for modal scenes
        fonts: Dictionary of fonts for modal scenes
        asset_loader: AssetLoader for modal scenes
    """
    player = game.players[state.view_player]
    
    for event in events:
        if event.type == pygame.KEYDOWN:
            # SPACE: Execute turn (step_turn_hybrid)
            if event.key == pygame.K_SPACE:
                step_turn_hybrid(game, state, screen, fonts, asset_loader)
            
            # S: Open shop modal
            elif event.key == pygame.K_s:
                # TODO: Integrate with ShopSceneModal when CoreGameState bridge is ready
                # For now, just apply income and interest
                if player.alive:
                    player.income()
                    player.apply_interest()
            
            # R: Rotate card (if card selected)
            elif event.key == pygame.K_r:
                if state.selected_hand_idx is not None:
                    # Rotate selected card
                    state.pending_rotation = (state.pending_rotation + 1) % 6
            
            # TAB: Cycle to next player
            elif event.key == pygame.K_TAB:
                state.view_player = (state.view_player + 1) % len(game.players)
                renderer.strategy = game.players[state.view_player].strategy
                # Clear selection when switching players
                state.selected_hand_idx = None
                state.pending_rotation = 0
            
            # 1-8: Switch to specific player
            elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                              pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(game.players):
                    state.view_player = idx
                    renderer.strategy = game.players[state.view_player].strategy
                    # Clear selection when switching players
                    state.selected_hand_idx = None
                    state.pending_rotation = 0
            
            # ESC: Deselect card (if card is selected)
            elif event.key == pygame.K_ESCAPE:
                if state.selected_hand_idx is not None:
                    state.selected_hand_idx = None
                    state.pending_rotation = 0
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Left click: Card selection from hand
            if event.button == 1:  # Left click
                clicked_idx = _get_clicked_hand_card(mouse_pos, len(player.hand))
                if clicked_idx is not None:
                    # Toggle selection
                    if state.selected_hand_idx == clicked_idx:
                        state.selected_hand_idx = None
                        state.pending_rotation = 0
                    else:
                        state.selected_hand_idx = clicked_idx
                        state.pending_rotation = 0
            
            # Right click: Rotate selected card
            elif event.button == 3:  # Right click
                if state.selected_hand_idx is not None:
                    state.pending_rotation = (state.pending_rotation + 1) % 6


def _get_clicked_hand_card(mouse_pos: Tuple[int, int], hand_size: int) -> Optional[int]:
    """Check if mouse position is over a hand card, return card index or None.
    
    Args:
        mouse_pos: (x, y) mouse position
        hand_size: Number of cards in hand
        
    Returns:
        Card index if clicked, None otherwise
    """
    HAND_PANEL_X = 20
    HAND_PANEL_Y = 430
    HAND_CARD_W = 220
    HAND_CARD_H = 70
    HAND_CARD_GAP = 6
    
    mx, my = mouse_pos
    
    for i in range(hand_size):
        card_x = HAND_PANEL_X
        card_y = HAND_PANEL_Y + i * (HAND_CARD_H + HAND_CARD_GAP)
        
        if (card_x <= mx <= card_x + HAND_CARD_W and
            card_y <= my <= card_y + HAND_CARD_H):
            return i
    
    return None


# ── Turn execution ────────────────────────────────────────────
def step_turn_hybrid(game: Game, state: HybridGameState, 
                     screen: pygame.Surface, fonts: dict,
                     asset_loader: 'AssetLoader') -> None:
    """Execute one complete turn with modal scene integration.
    
    This function implements the hybrid turn flow:
    1. Shop phase (modal) for human player
    2. Increment turn counter
    3. AI player turns (income, buy, interest, evolution, place, strengthen)
    4. Combat phase
    5. Combat visualization (modal)
    6. Cleanup (clear locked coordinates)
    
    Args:
        game: Game instance
        state: HybridGameState instance
        screen: pygame Surface for rendering
        fonts: Dictionary of fonts
        asset_loader: AssetLoader for modal scenes
    """
    # Reset turn state
    state.selected_hand_idx = None
    state.pending_rotation = 0
    state.placed_this_turn = 0
    
    # Check game over before turn
    alive = [p for p in game.players if p.alive]
    if len(alive) <= 1 or game.turn >= 50:
        return  # Game over, don't execute turn
    
    # Phase 1: Clear passive log and human player shop phase
    clear_passive_trigger_log()
    
    player = game.players[state.view_player]
    if player.alive:
        # Give income to human player
        player.income()
        
        # Open shop modal
        from scenes.shop_scene_modal import ShopSceneModal
        shop_result = ShopSceneModal.run_modal(
            game=game,
            player=player,
            screen=screen,
            asset_loader=asset_loader,
            fonts=fonts
        )
        
        # CRITICAL: Interest is applied in ShopScene.on_exit()
        # DO NOT call player.apply_interest() here - it would be duplicate!
        
        # Check copy strengthening after shop
        player.check_copy_strengthening(
            game.turn + 1, trigger_passive_fn=trigger_passive
        )
    
    # Phase 2: Increment turn counter
    game.turn += 1
    
    # Phase 3: AI player turns
    from engine_core.ai import AI
    
    for p in game.players:
        # Skip human player and dead players
        if not p.alive or p.pid == state.view_player:
            continue
        
        # Deal market window for AI player
        window_ai = game.market.deal_market_window(p, 5)
        
        # Income
        p.income()
        
        # Buy cards
        AI.buy_cards(
            p, 
            window_ai, 
            market_obj=game.market,
            rng=game.rng, 
            trigger_passive_fn=trigger_passive
        )
        
        # Return unsold cards
        game.market.return_unsold(p)
        
        # Apply interest
        p.apply_interest()
        
        # Check evolution
        card_by_name = {c.name: c for c in game.card_pool}
        p.check_evolution(market=game.market, card_by_name=card_by_name)
        
        # Place cards on board
        AI.place_cards(p, rng=game.rng)
        
        # Check copy strengthening
        p.check_copy_strengthening(
            game.turn, trigger_passive_fn=trigger_passive
        )
    
    # Phase 4: Combat phase
    game.combat_phase()
    
    # Phase 5: Combat visualization modal
    from scenes.combat_scene_modal import CombatSceneModal
    combat_result = CombatSceneModal.run_modal(
        game=game,
        screen=screen,
        asset_loader=asset_loader,
        last_combat_results=game.last_combat_results
    )
    
    # Phase 6: Cleanup - clear locked coordinates for all players
    for pid in state.locked_coords_per_player:
        state.locked_coords_per_player[pid] = set()


# ── Game over display ────────────────────────────────────────
def display_game_over(screen: pygame.Surface, game: Game, fonts: dict) -> None:
    """Display game over screen with winner information.
    
    Args:
        screen: pygame Surface to draw on
        game: Game instance
        fonts: Dictionary of fonts
    """
    # Determine winner (player with highest HP)
    winner = max(game.players, key=lambda p: p.hp)
    
    # Semi-transparent overlay
    overlay = pygame.Surface((W, H))
    overlay.set_alpha(200)
    overlay.fill((10, 10, 20))
    screen.blit(overlay, (0, 0))
    
    # Game over title
    title_text = fonts["title"].render("GAME OVER", True, (255, 50, 50))
    title_rect = title_text.get_rect(center=(W // 2, H // 2 - 120))
    screen.blit(title_text, title_rect)
    
    # Winner info
    winner_text = fonts["lg"].render(f"Winner: Player {winner.pid + 1}", True, (100, 255, 100))
    winner_rect = winner_text.get_rect(center=(W // 2, H // 2 - 50))
    screen.blit(winner_text, winner_rect)
    
    # Strategy info
    strategy_text = fonts["md"].render(f"Strategy: {winner.strategy}", True, (200, 200, 255))
    strategy_rect = strategy_text.get_rect(center=(W // 2, H // 2))
    screen.blit(strategy_text, strategy_rect)
    
    # HP info
    hp_text = fonts["md"].render(f"HP: {winner.hp}", True, (255, 200, 100))
    hp_rect = hp_text.get_rect(center=(W // 2, H // 2 + 50))
    screen.blit(hp_text, hp_rect)
    
    # Turn info
    turn_text = fonts["sm"].render(f"Turn: {game.turn}", True, (180, 180, 180))
    turn_rect = turn_text.get_rect(center=(W // 2, H // 2 + 100))
    screen.blit(turn_text, turn_rect)
    
    # Restart instruction
    restart_text = fonts["md_bold"].render("Press R to restart", True, (255, 255, 100))
    restart_rect = restart_text.get_rect(center=(W // 2, H // 2 + 160))
    screen.blit(restart_text, restart_rect)


# ── Render main screen ────────────────────────────────────────
def render_main_screen(screen: pygame.Surface, game: Game, 
                      state: HybridGameState, fonts: dict,
                      renderer: BoardRenderer) -> None:
    """Render main game screen with board, hand, and HUD.
    
    Args:
        screen: pygame Surface to draw on
        game: Game instance
        state: HybridGameState instance
        fonts: Dictionary of fonts
        renderer: BoardRenderer instance
    """
    player = game.players[state.view_player]
    mouse_pos = pygame.mouse.get_pos()
    
    # Update renderer's highlight group based on hovered synergy
    renderer.highlight_group = get_hovered_synergy_group(screen, mouse_pos)
    
    # Draw board with locked coordinates
    locked_set = state.locked_coords_per_player.get(player.pid, set())
    renderer.draw(
        screen,
        player.board,
        BOARD_COORDS,
        locked_coords=locked_set,
        show_tooltip=False,
    )
    
    # Draw hand panel
    draw_hand_panel(screen, player, fonts, state.selected_hand_idx,
                    mouse_pos, current_rotation=state.pending_rotation)
    
    # Draw synergy HUD
    draw_synergy_hud(screen, player, fonts, renderer.highlight_group)
    
    # Draw player info panel (left side)
    draw_player_info(screen, player, game.turn, fonts["md"], fonts["sm"], px=20, py=145)
    
    # Draw player panel (right side - all players)
    draw_player_panel(screen, game.players, state.view_player,
                      fonts["md"], fonts["sm"], px=W - 300, py=20)
    
    # Draw passive buff panel (below hand panel)
    HAND_PANEL_Y = 430
    HAND_CARD_H = 70
    HAND_CARD_GAP = 6
    HAND_PANEL_X = 20
    hand_bottom = HAND_PANEL_Y + len(player.hand) * (HAND_CARD_H + HAND_CARD_GAP) + 10
    log_max_h = H - 100 - hand_bottom - 4
    draw_passive_buff_panel(screen, player, fonts["sm"],
                            px=HAND_PANEL_X, py=hand_bottom, max_h=log_max_h)
    
    # Draw cyber-victorian HUD
    draw_cyber_victorian_hud(screen, player, game.turn, fonts,
                             fast_mode=state.fast_mode, 
                             status_msg="SPACE → next turn")


# ── Main game loop ────────────────────────────────────────────
def main_game_loop(game: Game, screen: pygame.Surface, fonts: dict, 
                   asset_loader: 'AssetLoader') -> None:
    """Main hybrid game loop combining run_game.py logic with modal scenes."""
    clock = pygame.time.Clock()
    
    # Initialize state
    state = HybridGameState(
        game=game,
        view_player=0,
        locked_coords_per_player={p.pid: set() for p in game.players}
    )
    
    # Initialize renderer
    renderer = BoardRenderer(BOARD_ORIGIN, game.players[0].strategy)
    renderer.init_fonts()
    
    # Initialize cyber renderer
    cyber = CyberRenderer(fonts)
    
    game_over = False
    running = True
    while running:
        dt = clock.tick(FPS)
        
        # Check game over conditions
        alive = [p for p in game.players if p.alive]
        if len(alive) <= 1 or game.turn >= 50:
            game_over = True
        
        # Event handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and state.selected_hand_idx is None:
                    running = False
                # R key restarts game when game is over
                elif event.key == pygame.K_r and game_over:
                    # Restart game
                    new_game = build_game()
                    game.players = new_game.players
                    game.market = new_game.market
                    game.turn = new_game.turn
                    game.rng = new_game.rng
                    game.card_pool = new_game.card_pool
                    game.last_combat_results = []
                    state.view_player = 0
                    state.selected_hand_idx = None
                    state.pending_rotation = 0
                    state.placed_this_turn = 0
                    state.locked_coords_per_player = {p.pid: set() for p in new_game.players}
                    renderer.strategy = new_game.players[0].strategy
                    game_over = False
        
        # Handle input only if game is not over
        if not game_over:
            handle_input(events, state, game, renderer, screen, fonts, asset_loader)
        
        # Render
        screen.fill(COLOR_BG)
        cyber.draw_vfx_base(screen)
        
        # Render main screen
        render_main_screen(screen, game, state, fonts, renderer)
        
        # Display game over screen if game is over
        if game_over:
            display_game_over(screen, game, fonts)
        
        pygame.display.flip()
    
    pygame.quit()


# ── Entry point ───────────────────────────────────────────────
def main():
    """Entry point for run_game2.py"""
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    
    # Initialize fonts once
    fonts = initialize_fonts()
    
    # Initialize AssetLoader (REQUIRED for modal scenes)
    from scenes.asset_loader import AssetLoader
    asset_loader = AssetLoader("assets/cards")
    
    # Build game
    game = build_game()
    
    # Run main loop
    main_game_loop(game, screen, fonts, asset_loader)
    
    sys.exit()


if __name__ == "__main__":
    main()
