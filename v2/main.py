import os
import sys

# Windows import sorunlarını önlemek için proje kök dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from v2.constants import Screen
from v2.core.game_state import GameState
from v2.core.scene_manager import SceneManager
from v2.scenes.shop import ShopScene


def _bootstrap() -> None:
    """Engine, asset ve veritabanı başlatma — main() öncesinde bir kez çalışır."""
    from v2.assets.loader import AssetLoader
    from v2.core.card_database import CardDatabase
    from engine_core.game_factory import build_game

    v2_base = os.path.dirname(__file__)
    
    # Önce UI Database ve Assetleri yüklenir
    AssetLoader.initialize(os.path.join(v2_base, "assets"))
    CardDatabase.initialize(
        os.path.join(v2_base, "..", "assets", "data", "cards.json")
    )

    # Motoru İnşa Et (Human ve 7 AI stratejisi)
    strategies = ["human", "random", "warrior", "builder",
                  "defender", "economist", "synergist", "aggressive"]
    game = build_game(strategies=strategies)
    
    # Motoru UI Köprüsüne (GameState) bağla
    GameState.get().hook_engine(game)


def main():
    pygame.init()
    screen = pygame.display.set_mode((Screen.W, Screen.H))
    pygame.display.set_caption("AUTOCHESS HYBRID V2")
    clock = pygame.time.Clock()

    _bootstrap()

    # SceneManager'ı başlat — ilk sahne ShopScene (LobbyScene hazır olana kadar)
    sm = SceneManager.get()
    sm.set_scene(ShopScene())

    print("[SceneManager] İlk sahne yüklendi:", sm.current_scene_name)
    print("Pencereyi kapatmak için X tuşuna basın.")

    running = True
    while running:
        dt_ms = clock.tick(60)          # ms cinsinden delta time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                sm.handle_event(event)  # Geçiş sırasında otomatik olarak bloklanır

        sm.update(dt_ms)
        sm.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
