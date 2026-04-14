"""
Manual test for GameOverScene

Run this script to visually test the GameOverScene:
- Winner display
- Final stats
- Restart button (R key or click)
- Quit button (ESC key or click)
- Hover effects
"""

import pygame
import sys
from unittest.mock import Mock

from scenes.game_over_scene import GameOverScene
from core.core_game_state import CoreGameState
from core.input_state import InputState


def create_mock_game():
    """Create a mock game with players."""
    game = Mock()
    game.turn = 25
    
    # Create mock players
    players = []
    for i in range(4):
        player = Mock()
        player.pid = i
        player.hp = 100 - i * 30  # P0: 100, P1: 70, P2: 40, P3: 10
        player.strategy = ["warrior", "builder", "evolver", "economist"][i]
        player.alive = player.hp > 0
        player.total_pts = 150 + i * 50
        player.win_streak = 3 - i
        player.stats = {
            'wins': 10 - i * 2,
            'losses': i * 2,
            'win_streak_max': 5 - i,
            'gold_earned': 500 + i * 100,
            'damage_dealt': 800 + i * 200,
        }
        players.append(player)
    
    game.players = players
    return game


def main():
    """Run manual test."""
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("GameOverScene Manual Test")
    clock = pygame.time.Clock()
    
    # Create game and core state
    game = create_mock_game()
    core_game_state = CoreGameState(game)
    
    # Create GameOverScene with winner (P0)
    winner = game.players[0]
    scene = GameOverScene(core_game_state, winner=winner)
    
    # Mock scene_manager
    scene.scene_manager = Mock()
    
    # Enter scene
    scene.on_enter()
    
    print("=" * 60)
    print("GameOverScene Manual Test")
    print("=" * 60)
    print("Controls:")
    print("  R key or click RESTART button - transitions to lobby")
    print("  ESC key or click QUIT button - exits game")
    print("  Hover over buttons to see effects")
    print()
    print("Winner: P1 (warrior)")
    print("HP: 100")
    print("=" * 60)
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(60)
        
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # Create input state
        input_state = InputState(events)
        
        # Handle input
        scene.handle_input(input_state)
        
        # Check if restart was requested
        if scene.scene_manager.request_transition.called:
            print("\n✓ Restart requested! Transition to lobby would occur here.")
            print("  In actual game, this would return to LobbyScene.")
            running = False
        
        # Update scene
        scene.update(dt)
        
        # Draw scene
        screen.fill((10, 11, 18))
        scene.draw(screen)
        
        # Display
        pygame.display.flip()
    
    # Cleanup
    scene.on_exit()
    pygame.quit()
    print("\n✓ Manual test complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        pygame.quit()
        sys.exit(0)
