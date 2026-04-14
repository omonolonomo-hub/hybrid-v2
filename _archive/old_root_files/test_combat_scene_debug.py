"""
Test script for CombatScene debug mode (Task 5)
"""

import pygame
import sys

from core.core_game_state import CoreGameState
from core.input_state import InputState
from scenes.combat_scene import CombatScene
from engine_core.game_factory import build_game

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60


def main():
    """Test CombatScene debug mode."""
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CombatScene Debug Mode Test")
    clock = pygame.time.Clock()
    
    print("=" * 60)
    print("COMBAT SCENE DEBUG MODE TEST")
    print("=" * 60)
    print("Controls:")
    print("  F3 - Toggle debug mode")
    print("  ESC - Quit")
    print("=" * 60)
    print()
    
    # Create a minimal game for testing
    strategies = ["random", "random"]
    game = build_game(strategies)
    core_game_state = CoreGameState(game)
    
    # Create combat scene
    combat_scene = CombatScene(core_game_state)
    combat_scene.on_enter()
    
    print("✓ CombatScene initialized")
    print("✓ Press F3 to toggle debug mode")
    print()
    
    # Game loop
    running = True
    frame_count = 0
    
    while running:
        dt = clock.tick(FPS)
        frame_count += 1
        
        # Capture events
        events = pygame.event.get()
        
        # Check for quit
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
        
        if not running:
            break
        
        # Create input state
        input_state = InputState(events)
        
        # Check for ESC to quit
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            running = False
            break
        
        # Handle input
        combat_scene.handle_input(input_state)
        
        # Update
        combat_scene.update(dt)
        
        # Draw
        screen.fill((5, 8, 15))
        combat_scene.draw(screen)
        
        # Update display
        if frame_count % 60 == 0:
            fps = clock.get_fps()
            pygame.display.set_caption(
                f"CombatScene Debug Mode Test | FPS: {fps:.1f} | "
                f"Debug: {'ON' if combat_scene.debug_mode else 'OFF'}"
            )
        
        pygame.display.flip()
    
    # Cleanup
    print()
    print("=" * 60)
    print("Test complete!")
    print(f"Total frames: {frame_count}")
    print("=" * 60)
    
    combat_scene.on_exit()
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
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
