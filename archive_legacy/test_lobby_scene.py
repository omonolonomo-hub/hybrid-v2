"""Test script for LobbyScene refactoring."""

import pygame
import sys

# Initialize pygame first (CRITICAL for font initialization)
pygame.init()

from core.core_game_state import CoreGameState
from core.scene_manager import SceneManager
from core.input_state import InputState
from scenes.lobby_scene import LobbyScene
from engine_core.game import Game


def test_lobby_scene():
    """Test LobbyScene in isolation."""
    print("Testing LobbyScene...")
    
    # Create display
    screen = pygame.display.set_mode((1600, 960))
    pygame.display.set_caption("LobbyScene Test")
    clock = pygame.time.Clock()
    
    # Create minimal game state
    # For now, we'll create a dummy game object
    # In real usage, this would be built with build_game()
    class DummyGame:
        def __init__(self):
            self.players = []
            self.market = None
    
    game = DummyGame()
    core_game_state = CoreGameState(game)
    
    # Create scene manager with lobby scene
    lobby_scene = LobbyScene(core_game_state)
    scene_manager = SceneManager(lobby_scene)
    
    print("✓ LobbyScene created successfully")
    print("✓ SceneManager initialized")
    print("\nControls:")
    print("  - Use < > arrows to change strategies")
    print("  - Click 'REMIX LOBBY' to randomize")
    print("  - Press ENTER or click 'INITIALIZE' to continue")
    print("  - Press ESC to exit")
    
    running = True
    while running:
        # Capture delta time
        dt = clock.tick(60)
        
        # Capture events
        events = pygame.event.get()
        
        # Create input state
        input_state = InputState(events)
        
        # Check for quit
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Update scene manager
        scene_manager.update(dt, input_state)
        
        # Check if transition was requested (would normally go to shop)
        if scene_manager._transition_requested is not None:
            print("\n✓ Transition requested to shop scene!")
            print(f"  Selected strategies: {lobby_scene.ui_state.strategies}")
            running = False
        
        # Draw
        screen.fill((10, 11, 18))
        scene_manager.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    try:
        test_lobby_scene()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
