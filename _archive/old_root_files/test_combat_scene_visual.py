"""
Visual test for CombatScene - Run this to see the combat scene in action.
Press F3 to toggle debug mode.
Press ESC to exit.
"""

import pygame
import sys
from core.core_game_state import CoreGameState
from scenes.combat_scene import CombatScene
from engine_core.game import Game
from engine_core.player import Player
from engine_core.board import Board
from engine_core.card import Card


def create_test_game():
    """Create a test game with some cards on the board."""
    # Create player
    player = Player(pid=0, strategy="test_strategy")
    player.hp = 100
    player.gold = 50
    
    # Create board with some test cards
    board = Board()
    
    # Add some test cards to the board
    test_cards = [
        ("Athena", (0, 0)),
        ("Yggdrasil", (1, 0)),
        ("TestCard", (0, 1)),
    ]
    
    for card_name, hex_coord in test_cards:
        card = Card(
            name=card_name,
            category="test",
            rarity="common",
            stats={"N": 5, "NE": 4, "SE": 3, "S": 2, "SW": 1, "NW": 6}
        )
        board.grid[hex_coord] = card
    
    player.board = board
    
    # Create game with player
    game = Game(players=[player])
    game.current_player_id = 0
    game.turn = 1
    
    return game


def main():
    """Run visual test of CombatScene."""
    print("=" * 60)
    print("Combat Scene Visual Test")
    print("=" * 60)
    print("Controls:")
    print("  F3  - Toggle debug mode")
    print("  ESC - Exit")
    print("=" * 60)
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("Combat Scene Test")
    clock = pygame.time.Clock()
    
    # Create game state
    game = create_test_game()
    core_game_state = CoreGameState(game)
    
    # Create combat scene
    scene = CombatScene(core_game_state)
    scene.on_enter()
    
    print("\n✓ Combat scene initialized successfully")
    print(f"✓ Hex cards created: {len(scene.hex_cards)}")
    print(f"✓ Hex grid size: {len(scene.hex_grid)}")
    print(f"✓ Hex size: {scene.hex_size:.2f}")
    print(f"✓ Grid origin: ({scene.origin_x:.2f}, {scene.origin_y:.2f})")
    print("\nScene is running... (press ESC to exit)\n")
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Create input state
        events = pygame.event.get()
        
        # Check for quit or ESC
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        
        # Create InputState from events
        from core.input_state import InputState
        input_state = InputState(events)
        
        # Update scene
        scene.handle_input(input_state)
        scene.update(dt)
        
        # Draw scene
        scene.draw(screen)
        
        # Update display
        pygame.display.flip()
    
    # Cleanup
    scene.on_exit()
    pygame.quit()
    print("\n✓ Test completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
