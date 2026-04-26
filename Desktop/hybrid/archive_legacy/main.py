"""
Main Entry Point - Scene Manager Architecture

Single game loop with centralized scene management.
No nested loops - all scenes are controlled by SceneManager.
"""

import sys
import pygame

# ========== BACKWARD COMPATIBILITY FLAG ==========
# Toggle between new Scene-based architecture and legacy run_game.py
# 
# USE_SCENE_ARCHITECTURE = True:  Use SceneManager with GameLoopScene (current implementation)
# USE_SCENE_ARCHITECTURE = False: Call run_game.main() directly (legacy path)
#
# This flag allows switching between old and new architecture during migration.
# Once migration is complete and validated, this flag and the legacy path can be removed.
USE_SCENE_ARCHITECTURE = True

# Core systems
from core.scene_manager import SceneManager
from core.core_game_state import CoreGameState
from core.input_state import InputState
from core.animation_system import AnimationSystem
from core.action_system import ActionSystem

# Scenes
from scenes.lobby_scene import LobbyScene
from scenes.shop_scene import ShopScene
from scenes.combat_scene import CombatScene
from scenes.game_loop_scene import GameLoopScene
from scenes.game_over_scene import GameOverScene
from scenes.asset_loader import AssetLoader

# Game engine
from engine_core.game_factory import build_game

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
BACKGROUND_COLOR = (10, 11, 18)


def main():
    """Main entry point with backward compatibility support.
    
    Supports two execution paths:
    1. Scene-based architecture (USE_SCENE_ARCHITECTURE = True)
    2. Legacy run_game.py (USE_SCENE_ARCHITECTURE = False)
    """
    
    # ========== BACKWARD COMPATIBILITY ROUTING ==========
    if not USE_SCENE_ARCHITECTURE:
        # Legacy path: Use original run_game.py implementation
        print("=" * 60)
        print("RUNNING LEGACY MODE (run_game.py)")
        print("=" * 60)
        import run_game
        run_game.main()
        return
    
    # ========== NEW SCENE-BASED ARCHITECTURE ==========
    print("=" * 60)
    print("RUNNING SCENE-BASED ARCHITECTURE")
    print("=" * 60)
    
    # ========== System Initialization ==========
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Autochess Hybrid - Scene Manager Architecture")
    clock = pygame.time.Clock()
    
    print("=" * 60)
    print("AUTOCHESS HYBRID - Scene Manager Architecture")
    print("=" * 60)
    print(f"Screen: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"Target FPS: {FPS}")
    print()
    
    # ========== Core Initialization ==========
    print("Initializing core systems...")
    
    # Create AssetLoaders (separate instances for shop and combat)
    # Shop needs larger cards (200x230), combat uses smaller cards (140x160)
    from scenes.asset_loader import SHOP_CARD_SIZE, CARD_SIZE
    
    shop_asset_loader = AssetLoader(
        cards_dir="assets/cards",
        target_size=SHOP_CARD_SIZE  # 200x230 for shop
    )
    
    combat_asset_loader = AssetLoader(
        cards_dir="assets/cards",
        target_size=CARD_SIZE  # 140x160 for combat/board
    )
    print("✓ AssetLoader initialized")
    
    # Initialize animation and action systems
    animation_system = AnimationSystem()
    action_system = ActionSystem()
    print("✓ AnimationSystem initialized")
    print("✓ ActionSystem initialized")
    
    # Build game engine (will be configured in lobby)
    # For now, create a placeholder - lobby will rebuild with selected strategies
    game = None  # Will be built after lobby
    
    # Create core game state (SAVEABLE)
    # Note: We'll create this after lobby selects strategies
    core_game_state = None
    
    # Create initial scene (Lobby)
    print("Creating LobbyScene...")
    # Lobby doesn't need a game yet - it just selects strategies
    # We'll pass a dummy CoreGameState for now
    class DummyGame:
        def __init__(self):
            self.players = []
            self.market = None
            self.turn = 0
        def alive_players(self):
            return []
    
    dummy_game = DummyGame()
    core_game_state = CoreGameState(dummy_game)
    
    lobby_scene = LobbyScene(core_game_state)
    
    # Create scene manager
    print("Creating SceneManager...")
    scene_manager = SceneManager(lobby_scene)
    
    # Register scene factories
    def create_lobby(core_game_state, **kwargs):
        return LobbyScene(core_game_state)
    
    def create_game_loop(core_game_state, **kwargs):
        """T1.4 & T1.10: Create GameLoopScene with strategies from lobby.
        
        BREAKING CHANGE: Moved build_game() call from ShopScene factory to here.
        This establishes the correct flow: Lobby → GameLoop → Shop → Combat → GameLoop
        
        GameLoopScene now builds the game and initializes CoreGameState.
        
        T1.13: Passes trigger_combat flag from CombatScene to GameLoopScene.
        NOTE: This is a TEMPORARY architectural compromise. Future refactor should
        remove cross-scene signaling and have GameLoopScene own combat triggering.
        """
        strategies = kwargs.get('strategies', None)
        print(f"[main.py] create_game_loop called with kwargs: {kwargs}")
        
        # Build game with selected strategies (moved from create_shop)
        if strategies:
            print(f"\nBuilding game with strategies: {strategies}")
            game = build_game(strategies)
            core_game_state.game = game
            print(f"✓ Game built with {len(game.players)} players")
        
        # Pass all kwargs to GameLoopScene (including trigger_combat flag from T1.13)
        return GameLoopScene(core_game_state, **kwargs)
    
    def create_shop(core_game_state, **kwargs):
        """Create ShopScene with already-initialized CoreGameState.
        
        BREAKING CHANGE: No longer builds game - expects CoreGameState already initialized.
        GameLoopScene factory now handles game building.
        """
        # Open market window for current player
        player = core_game_state.current_player
        if hasattr(core_game_state.game, 'market'):
            core_game_state.game.market.deal_market_window(player, n=5)
            print(f"✓ Market window dealt for player {player.pid}")
        
        return ShopScene(core_game_state, 
                        action_system=action_system, 
                        animation_system=animation_system,
                        asset_loader=shop_asset_loader)  # Use shop-specific loader
    
    def create_combat(core_game_state, **kwargs):
        # Create CombatScene with action and animation systems
        from scenes.combat_scene import CombatScene
        return CombatScene(core_game_state, 
                          action_system=action_system,
                          animation_system=animation_system,
                          asset_loader=combat_asset_loader)  # Use combat-specific loader
    
    scene_manager.register_scene_factory("lobby", create_lobby)
    scene_manager.register_scene_factory("game_loop", create_game_loop)
    scene_manager.register_scene_factory("shop", create_shop)
    scene_manager.register_scene_factory("combat", create_combat)
    
    def create_game_over_scene(core_game_state, **kwargs):
        """Create GameOverScene with winner information.
        
        Args:
            core_game_state: Shared game state
            **kwargs: Additional arguments (winner, etc.)
        
        Returns:
            GameOverScene instance
        """
        return GameOverScene(core_game_state, **kwargs)
    
    scene_manager.register_scene_factory("game_over", create_game_over_scene)
    
    print("✓ Initialization complete!")
    print()
    print("Controls:")
    print("  - Lobby: Select strategies, press ENTER to start")
    print("  - Shop: Buy cards (1-5), SPACE to refresh, ENTER for battle")
    print("  - ESC to quit")
    print()
    
    # ========== Single Game Loop ==========
    running = True
    frame_count = 0
    
    while running:
        # Capture delta time (in milliseconds)
        dt = clock.tick(FPS)
        frame_count += 1
        
        # Capture input events ONCE per frame
        events = pygame.event.get()
        
        # Check for quit event
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
        
        if not running:
            break
        
        # Create input state (translates events to intents)
        input_state = InputState(events)
        
        # Update animation system
        animation_system.update(dt)
        
        # Update scene manager (handles input, updates scene, processes transitions)
        scene_manager.update(dt, input_state)
        
        # Render
        screen.fill(BACKGROUND_COLOR)
        scene_manager.draw(screen)
        animation_system.draw(screen)
        
        # Display FPS counter (optional)
        if frame_count % 60 == 0:  # Update every second
            fps = clock.get_fps()
            pygame.display.set_caption(
                f"Autochess Hybrid - Scene Manager Architecture | FPS: {fps:.1f}"
            )
        
        pygame.display.flip()
    
    # ========== Cleanup ==========
    print()
    print("=" * 60)
    print("Shutting down...")
    print(f"Total frames rendered: {frame_count}")
    print("=" * 60)
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        pygame.quit()
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
