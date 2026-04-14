"""
Visual test for Task 1.3: Verify HEX_SIZE=85 accommodates cards properly

This test verifies:
- Cards fit properly in hexagons with HEX_SIZE=85
- Hex edges are visible for edge stat display
- Card content is not clipped
"""

import sys
import os
import pygame
import math

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool
from ui.board_renderer_v3 import BoardRendererV3, HEX_SIZE
from ui.renderer_v3 import CyberRendererV3
from engine_core.board import Board

def main():
    """Run visual test for hex size rendering."""
    print("=" * 60)
    print("Task 1.3: Hex Size Rendering Test")
    print("=" * 60)
    print(f"HEX_SIZE: {HEX_SIZE}")
    print()
    
    pygame.init()
    
    # Create window
    width, height = 1200, 800
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Task 1.3: Hex Size Rendering Test")
    
    # Create renderer
    origin = (width // 2, height // 2)
    renderer = BoardRendererV3(origin=origin)
    renderer.init_fonts()
    
    # Get some test cards
    pool = get_card_pool()
    test_cards = pool[:3] if len(pool) >= 3 else pool
    
    # Create test board with cards at different positions
    board = Board()
    test_positions = [(0, 0), (1, 0), (-1, 1)]
    for i, card in enumerate(test_cards):
        if i < len(test_positions):
            q, r = test_positions[i]
            board.grid[(q, r)] = card
    
    # Valid board coordinates (just the test positions)
    board_coords = test_positions
    
    # Main loop
    clock = pygame.time.Clock()
    running = True
    
    print("Visual Test Instructions:")
    print("- Verify cards fit properly in hexagons")
    print("- Verify hex edges are visible around cards")
    print("- Verify card content (stats, text) is not clipped")
    print("- Press ESC to exit")
    print()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen
        screen.fill((15, 16, 24))
        
        # Draw title
        font_title = pygame.font.SysFont("segoeui", 24, bold=True)
        title = font_title.render(f"Task 1.3: Hex Size Test (HEX_SIZE={HEX_SIZE})", True, (255, 255, 255))
        screen.blit(title, (width // 2 - title.get_width() // 2, 20))
        
        # Draw instructions
        font_sm = pygame.font.SysFont("consolas", 14)
        instructions = [
            "Verify:",
            "1. Cards fit properly in hexagons",
            "2. Hex edges are visible for edge stat display",
            "3. Card content is not clipped",
            "",
            "Press ESC to exit"
        ]
        y = 60
        for line in instructions:
            text = font_sm.render(line, True, (180, 180, 200))
            screen.blit(text, (20, y))
            y += 20
        
        # Draw board
        renderer.draw(screen, board, board_coords)
        
        # Draw hex size info
        info_text = f"HEX_SIZE: {HEX_SIZE}px | Card dimensions: 140x160px"
        info_surf = font_sm.render(info_text, True, (100, 200, 255))
        screen.blit(info_surf, (width // 2 - info_surf.get_width() // 2, height - 40))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("\n✓ Visual test completed")
    print("If cards fit properly and hex edges are visible, Task 1.3 is complete.")

if __name__ == "__main__":
    main()
