"""
ShopSceneModal - Modal wrapper for ShopScene

Converts ShopScene into a synchronous modal dialog for use in run_game2.py hybrid architecture.
The modal runs its own internal loop and returns control when the shop phase is complete.

CRITICAL: This wrapper acts as a bridge between run_game2.py (which uses Game) and 
ShopScene (which uses CoreGameState). The bridge is created INSIDE the wrapper, 
not exposed to run_game2.py.
"""

from types import SimpleNamespace
from typing import Dict, Any
import pygame

from scenes.shop_scene import ShopScene
from core.core_game_state import CoreGameState
from core.input_state import InputState
from engine_core.game import Game
from engine_core.player import Player


class ShopSceneModal:
    """Modal wrapper for ShopScene that runs synchronously."""
    
    @staticmethod
    def run_modal(game: Game,
                  player: Player,
                  screen: pygame.Surface,
                  asset_loader: 'AssetLoader',
                  fonts: dict = None) -> Dict[str, Any]:
        """Run shop scene as modal dialog, return when player confirms.
        
        This method creates a CoreGameState bridge internally, instantiates ShopScene,
        runs an internal event loop until the player presses the "Done" button (or ENTER/ESC),
        then calls on_exit() to apply interest and returns the results.
        
        Args:
            game: Game instance (NOT CoreGameState - bridge created internally)
            player: Current player who is shopping
            screen: Pygame surface for rendering
            asset_loader: AssetLoader for card asset management (REQUIRED)
            fonts: Optional font dictionary
            
        Returns:
            Dictionary with shop results:
            {
                'purchased': List[str],  # Card names bought
                'gold_spent': int,       # Total gold spent
                'completed': bool        # True if shop phase completed normally
            }
        """
        # Track purchases before shop opens
        initial_gold = player.gold
        initial_hand_size = len(player.hand)
        initial_copies = dict(player.copies)
        
        # ============================================================================
        # BRIDGE: Game → CoreGameState (internal, not exposed to caller)
        # ============================================================================
        core_game_state = CoreGameState(game)
        core_game_state.view_player_index = player.pid
        
        # Create ShopScene instance
        scene = ShopScene(
            core_game_state=core_game_state,
            action_system=None,  # No action system needed for modal
            animation_system=None,  # No animation system needed for modal
            asset_loader=asset_loader,
            renderer=None,  # Scene will create its own renderer
            fonts=fonts
        )
        
        # Mock SceneManager to prevent scene transitions
        # The scene will call scene_manager.request_transition("combat") when done
        # We intercept this and set a flag to exit the modal loop
        modal_done = {'value': False}
        
        def mock_request_transition(target_scene: str):
            """Mock transition request - just sets done flag."""
            modal_done['value'] = True
        
        scene.scene_manager = SimpleNamespace(request_transition=mock_request_transition)
        
        # Call on_enter() to initialize scene state
        scene.on_enter()
        
        # Internal modal loop
        clock = pygame.time.Clock()
        
        while not modal_done['value']:
            dt = clock.tick(60)  # 60 FPS
            
            # Get events
            events = pygame.event.get()
            
            # Check for quit event
            for event in events:
                if event.type == pygame.QUIT:
                    modal_done['value'] = True
                    break
            
            if modal_done['value']:
                break
            
            # Create InputState from events (wrapper handles this, not run_game2.py)
            input_state = InputState(events)
            
            # Handle input
            scene.handle_input(input_state)
            
            # Update scene
            scene.update(dt)
            
            # Clear screen first (prevent background bleed-through)
            screen.fill((0, 0, 0))
            
            # Draw scene
            scene.draw(screen)
            
            # Flip display
            pygame.display.flip()
        
        # Call on_exit() to apply interest (lifecycle requirement)
        # CRITICAL: Interest is applied HERE, not in step_turn_hybrid()
        scene.on_exit()
        
        # Calculate what was purchased
        purchased_cards = []
        for card_name, count in player.copies.items():
            initial_count = initial_copies.get(card_name, 0)
            if count > initial_count:
                # Add card name for each copy purchased
                purchased_cards.extend([card_name] * (count - initial_count))
        
        gold_spent = initial_gold - player.gold
        
        # Return results
        return {
            'purchased': purchased_cards,
            'gold_spent': gold_spent,
            'completed': True
        }
