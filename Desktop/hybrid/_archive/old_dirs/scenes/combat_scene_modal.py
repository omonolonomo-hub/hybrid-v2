"""
CombatSceneModal - Modal wrapper for CombatScene

Converts CombatScene into a synchronous modal dialog for use in run_game2.py hybrid architecture.
The modal runs its own internal loop and returns control when the player exits (SPACE/ESC).

CRITICAL: This wrapper acts as a bridge between run_game2.py (which uses Game) and 
CombatScene (which uses CoreGameState). The bridge is created INSIDE the wrapper, 
not exposed to run_game2.py.
"""

from types import SimpleNamespace
from typing import Dict, Any
import pygame

from scenes.combat_scene import CombatScene
from core.core_game_state import CoreGameState
from core.input_state import InputState
from engine_core.game import Game


class CombatSceneModal:
    """Modal wrapper for CombatScene that runs synchronously."""
    
    @staticmethod
    def run_modal(game: Game,
                  screen: pygame.Surface,
                  asset_loader: 'AssetLoader',
                  last_combat_results: list = None) -> Dict[str, Any]:
        """Run combat scene as modal dialog, return when player exits.
        
        This method creates a CoreGameState bridge internally, instantiates CombatScene,
        renders it to a temporary 1920x1080 surface, scales it down to 1600x960, and runs
        an internal event loop until the player presses SPACE or ESC to exit.
        
        Args:
            game: Game instance (NOT CoreGameState - bridge created internally)
            screen: Pygame surface for rendering (1600x960)
            asset_loader: AssetLoader for card asset management (REQUIRED)
            last_combat_results: Optional combat results data (currently unused by scene)
            
        Returns:
            Dictionary with combat visualization results:
            {
                'viewed': bool,      # True if player viewed the scene
                'skipped': bool      # True if player pressed ESC to skip
            }
        """
        # Create temporary surface for CombatScene at native resolution (1920x1080)
        combat_surface = pygame.Surface((1920, 1080))
        
        # ============================================================================
        # BRIDGE: Game → CoreGameState (internal, not exposed to caller)
        # ============================================================================
        core_game_state = CoreGameState(game)
        
        # Create CombatScene instance
        scene = CombatScene(
            core_game_state=core_game_state,
            action_system=None,  # No action system needed for modal
            animation_system=None,  # No animation system needed for modal
            asset_loader=asset_loader
        )
        
        # Mock SceneManager to prevent scene transitions
        # The scene might call scene_manager.request_transition() for navigation
        # We intercept this and ignore it (combat is view-only in this context)
        def mock_request_transition(target_scene: str):
            """Mock transition request - no-op for modal."""
            pass
        
        scene.scene_manager = SimpleNamespace(request_transition=mock_request_transition)
        
        # Call on_enter() to initialize scene state
        scene.on_enter()
        
        # Track whether player viewed or skipped
        viewed = True
        skipped = False
        
        # Internal modal loop
        clock = pygame.time.Clock()
        modal_done = False
        
        while not modal_done:
            dt = clock.tick(60)  # 60 FPS
            
            # Get events
            events = pygame.event.get()
            
            # Check for quit event or exit keys
            for event in events:
                if event.type == pygame.QUIT:
                    modal_done = True
                    skipped = True
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # SPACE exits normally (viewed)
                        modal_done = True
                        break
                    elif event.key == pygame.K_ESCAPE:
                        # ESC exits early (skipped)
                        modal_done = True
                        skipped = True
                        break
            
            if modal_done:
                break
            
            # Create InputState from events (wrapper handles this, not run_game2.py)
            input_state = InputState(events)
            
            # Handle input
            scene.handle_input(input_state)
            
            # Update scene
            scene.update(dt)
            
            # Clear main screen first (prevent background bleed-through)
            screen.fill((0, 0, 0))
            
            # Draw scene to temporary surface at native resolution (1920x1080)
            scene.draw(combat_surface)
            
            # Scale down from 1920x1080 to 1600x960 and blit to main screen
            scaled_surface = pygame.transform.scale(combat_surface, (1600, 960))
            screen.blit(scaled_surface, (0, 0))
            
            # Flip display
            pygame.display.flip()
        
        # Call on_exit() to clean up resources
        scene.on_exit()
        
        # Return results
        return {
            'viewed': viewed,
            'skipped': skipped
        }
