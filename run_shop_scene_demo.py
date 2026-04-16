"""
ShopScene full feature demo: FloatingText, evolved cards, audio all integrated.
MockGame provides endless play without real engine dependency.
Run: python run_shop_scene_demo.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pygame
from v2.core.game_state import GameState
from v2.mock.engine_mock import MockGame
from v2.scenes.shop import ShopScene
from v2.constants import Screen, Timing


def main():
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode(
        (Screen.W, Screen.H), 
        pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("ShopScene Demo: FloatingText + Evolved Cards + Audio")
    clock = pygame.time.Clock()
    
    # Initialize GameState with MockGame
    mock_game = MockGame()
    gs = GameState.get()
    gs.hook_engine(mock_game)
    
    # Create and enter ShopScene
    shop_scene = ShopScene()
    
    running = True
    while running:
        dt_ms = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            shop_scene.handle_event(event)
        
        shop_scene.update(dt_ms)
        
        screen.fill((16, 20, 30))
        shop_scene.render(screen)
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()
