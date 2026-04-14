"""
main.py  —  Hybrid v2.1
========================
Tek giriş noktası. Scene geçişleri buradan yönetilir.

Başlatma:
    python main.py
"""

import sys
import os
import pygame
import pygame_gui

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.game_state import GameState

WINDOW_W   = 1280
WINDOW_H   = 800
WINDOW_TITLE = "Hybrid — 37-Hex Strateji"
TARGET_FPS   = 60

# Sahne adı → sınıf adının alt kısmı (scene switcher için)
SCENE_NAMES = {
    "lobby":     "lobbyscreen",
    "shop":      "shopscreen",
    "combat":    "combatscreen",
    "game_over": "gameoverscreen",
}


def make_manager(screen: pygame.Surface) -> pygame_gui.UIManager:
    theme_path = os.path.join(os.path.dirname(__file__), "theme.json")
    if os.path.exists(theme_path):
        return pygame_gui.UIManager((WINDOW_W, WINDOW_H), theme_path)
    return pygame_gui.UIManager((WINDOW_W, WINDOW_H))


def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    manager = make_manager(screen)
    state   = GameState()
    state.setup()
    state.current_screen = "lobby"

    current_scene = None
    current_scene_name = ""

    def load_scene(name: str):
        nonlocal current_scene, current_scene_name
        if current_scene is not None:
            current_scene.destroy()
            manager.clear_and_reset()

        print(f"[Scene] → {name}")

        if name == "lobby":
            from screens.lobby import LobbyScreen
            current_scene = LobbyScreen(state, manager)
        elif name == "shop":
            from screens.shop import ShopScreen
            current_scene = ShopScreen(state, manager)
        elif name == "combat":
            from screens.combat import CombatScreen
            current_scene = CombatScreen(state, manager)
        elif name == "game_over":
            from screens.game_over import GameOverScreen
            current_scene = GameOverScreen(state, manager)
        else:
            print(f"[Uyarı] Bilinmeyen sahne: {name}")
            return

        current_scene_name = name

    def restart():
        nonlocal state
        state = GameState()
        state.setup()
        state.current_screen = "lobby"
        load_scene("lobby")

    load_scene("lobby")

    running = True
    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break

            manager.process_events(event)

            if current_scene:
                result = current_scene.handle_event(event)
                if result == "quit":
                    running = False
                elif result == "restart":
                    restart()
                elif result is not None and result != current_scene_name:
                    load_scene(result)

        # Otomatik geçiş: state değişmişse sahneyi güncelle
        if current_scene and state.current_screen != current_scene_name:
            load_scene(state.current_screen)

        manager.update(dt)
        if current_scene:
            current_scene.update(dt)

        if current_scene:
            current_scene.draw(screen)
        manager.draw_ui(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    run()
