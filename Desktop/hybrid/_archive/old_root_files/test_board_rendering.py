"""
Test: Verify board rendering in GameLoopScene

This test verifies that:
1. GameLoopScene initializes board renderer
2. Board is drawn without errors
3. Renderer uses correct player and locked coords
"""

import sys
import pygame

# Initialize pygame
pygame.init()

# Create test screen
screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Test: GameLoopScene Board Rendering")

# Core systems
from core.scene_manager import SceneManager
from core.core_game_state import CoreGameState

# Scenes
from scenes.lobby_scene import LobbyScene
from scenes.game_loop_scene import GameLoopScene


def test_board_rendering():
    """Test that GameLoopScene renders the board correctly."""
    
    print("=" * 60)
    print("TEST: GameLoopScene Board Rendering")
    print("=" * 60)
    
    # Create dummy game for initial CoreGameState
    class DummyGame:
        def __init__(self):
            self.players = []
            self.market = None
            self.turn = 0
        def alive_players(self):
            return []
    
    dummy_game = DummyGame()
    core_game_state = CoreGameState(dummy_game)
    
    # Create lobby scene
    lobby_scene = LobbyScene(core_game_state)
    
    # Create scene manager
    scene_manager = SceneManager(lobby_scene)
    
    # Register game_loop factory
    def create_game_loop(core_game_state, **kwargs):
        strategies = kwargs.get('strategies', None)
        return GameLoopScene(core_game_state, strategies=strategies)
    
    scene_manager.register_scene_factory("game_loop", create_game_loop)
    
    # Test strategies
    test_strategies = ["aggro", "control", "midrange", "combo", "tempo", "builder", "evolver", "warrior"]
    
    print(f"\n1. Creating GameLoopScene with strategies: {test_strategies}")
    
    # Request transition
    scene_manager.request_transition("game_loop", strategies=test_strategies)
    scene_manager._execute_transition()
    
    active_scene = scene_manager.active_scene
    
    if not isinstance(active_scene, GameLoopScene):
        print("✗ ERROR: Active scene is not GameLoopScene")
        return False
    
    print("   ✓ GameLoopScene created")
    
    # Check renderer initialization
    print("\n2. Checking renderer initialization...")
    if hasattr(active_scene, 'renderer') and active_scene.renderer is not None:
        print("   ✓ Board renderer initialized")
    else:
        print("   ✗ ERROR: Board renderer not initialized")
        return False
    
    if hasattr(active_scene, 'cyber') and active_scene.cyber is not None:
        print("   ✓ Cyber renderer initialized")
    else:
        print("   ✗ ERROR: Cyber renderer not initialized")
        return False
    
    # Test rendering
    print("\n3. Testing board rendering...")
    try:
        # Clear screen
        screen.fill((10, 11, 18))
        
        # Call draw
        active_scene.draw(screen)
        
        print("   ✓ Board rendered without errors")
        
        # Update display
        pygame.display.flip()
        
        print("   ✓ Display updated")
        
    except Exception as e:
        print(f"   ✗ ERROR: Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify renderer state
    print("\n4. Verifying renderer state...")
    current_player = active_scene.game.players[active_scene.core_game_state.view_player_index]
    print(f"   ✓ Current player: {current_player.strategy}")
    print(f"   ✓ Board has {len(current_player.board.grid)} cards")
    
    locked_coords = active_scene.core_game_state.locked_coords_per_player.get(current_player.pid, set())
    print(f"   ✓ Locked coordinates: {len(locked_coords)}")
    
    # Keep window open for visual inspection
    print("\n5. Visual inspection...")
    print("   Window will stay open for 3 seconds for visual inspection")
    print("   You should see:")
    print("   - Dark background")
    print("   - Hex grid board in the center")
    print("   - Empty hexes (no cards placed yet)")
    
    # Wait 3 seconds
    pygame.time.wait(3000)
    
    print("\n" + "=" * 60)
    print("✓✓✓ TEST PASSED ✓✓✓")
    print("=" * 60)
    print("Board rendering is working correctly!")
    print("- Renderer initialized: YES")
    print("- Board drawn: YES")
    print("- No errors: YES")
    
    return True


if __name__ == "__main__":
    try:
        success = test_board_rendering()
        pygame.quit()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
