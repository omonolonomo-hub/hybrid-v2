import os
import sys
import logging
import ctypes

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Windows import sorunlarını önlemek için proje kök dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from v2.constants import Screen
from v2.core.game_state import GameState
from v2.core.scene_manager import SceneManager
from v2.scenes.menu import MenuScene
from v2.scenes.shop import ShopScene


def _set_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _draw_startup_frame(screen: pygame.Surface) -> None:
    """Draw a cheap first frame immediately so Windows never shows a black gap."""
    width, height = screen.get_size()
    top = (20, 25, 40)
    bottom = (35, 15, 45)

    for y in range(height):
        t = y / max(height - 1, 1)
        color = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(screen, color, (0, y), (width, y))

    stripe_colors = [
        (248, 222, 34),
        (209, 32, 82),
        (35, 114, 39),
        (50, 50, 180),
        (3, 174, 210),
        (244, 91, 38),
    ]
    stripe_w = width / len(stripe_colors)
    for index, color in enumerate(stripe_colors):
        pygame.draw.rect(
            screen,
            color,
            pygame.Rect(round(index * stripe_w), 0, round(stripe_w) + 1, 4),
        )

    font_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    try:
        title_font = pygame.font.Font(os.path.join(font_dir, "Ghore.ttf"), 72)
        label_font = pygame.font.Font(os.path.join(font_dir, "Ghore.ttf"), 18)
    except Exception:
        title_font = pygame.font.Font(None, 72)
        label_font = pygame.font.Font(None, 24)

    title_text = "AUTOCHESS HYBRID"
    title = title_font.render(title_text, True, (255, 255, 255))
    title_rect = title.get_rect(center=(width // 2, int(height * 0.54)))

    glow_layers = [
        ((80, 140, 255), (-8, 0), 90),
        ((80, 140, 255), (8, 0), 70),
        ((60, 200, 100), (5, -2), 82),
        ((220, 60, 60), (-5, 2), 72),
        ((255, 255, 255), (0, 0), 54),
    ]
    for color, offset, alpha in glow_layers:
        glow = title_font.render(title_text, True, color)
        glow.set_alpha(alpha)
        screen.blit(glow, title_rect.move(*offset))

    screen.blit(title, title_rect)

    label = label_font.render("LOADING MENU", True, (80, 140, 255))
    label_rect = label.get_rect(center=(width // 2, title_rect.bottom + 34))
    screen.blit(label, label_rect)
    pygame.display.flip()


def _bring_pygame_window_to_front(hwnd: int | None) -> None:
    if sys.platform != "win32" or not hwnd:
        return

    try:
        user32 = ctypes.windll.user32
        sw_restore = 9
        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_showwindow = 0x0040
        hwnd_top = 0
        user32.ShowWindow(int(hwnd), sw_restore)
        user32.SetWindowPos(
            int(hwnd),
            hwnd_top,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_showwindow,
        )
        user32.SetForegroundWindow(int(hwnd))
    except Exception:
        pass


def _bootstrap(ai_strategies=None) -> GameState:
    """Engine, asset ve veritabanı başlatma — main() öncesinde bir kez çalışır.
    
    Args:
        ai_strategies: List of 7 AI strategy names. If None, uses default strategies.
                      Valid strategies: random, warrior, builder, evolver, economist, balancer, rare_hunter
    """
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
    # Use provided AI strategies or default ones
    if ai_strategies is None:
        ai_strategies = ["random", "warrior", "builder", "evolver", "economist", "balancer", "rare_hunter"]
    
    # Ensure we have exactly 7 AI strategies
    if len(ai_strategies) != 7:
        raise ValueError(f"Expected 7 AI strategies, got {len(ai_strategies)}")
    
    strategies = ["human"] + ai_strategies
    game = build_game(strategies=strategies)
    
    # Motoru UI Köprüsüne (GameState) bağla
    gs = GameState()
    gs.hook_engine(game)
    return gs


def _show_web_menu_before_game() -> bool | None:
    try:
        from v2.ui.web_menu.menu_v3 import show_web_menu_blocking
    except ImportError:
        print("[UYARI] pywebview kurulu degil - fallback: klasik Pygame menusu")
        return None

    try:
        return show_web_menu_blocking()
    except Exception as exc:
        print(f"[UYARI] pywebview menu baslatilamadi - fallback aktif: {exc}")
        return None


def main():
    _set_dpi_awareness()
    os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")

    pygame.init()
    screen = pygame.display.set_mode((Screen.W, Screen.H), pygame.NOFRAME)
    pygame.display.set_caption("AUTOCHESS HYBRID V2")
    _draw_startup_frame(screen)
    clock = pygame.time.Clock()

    # SceneManager'ı başlat — ilk sahne MenuScene
    sm = SceneManager.get()
    web_menu_overlay = None
    web_menu_active = False
    pygame_hwnd = pygame.display.get_wm_info().get("window")
    lobby_initialized = False

    def _ensure_lobby_scene() -> None:
        nonlocal lobby_initialized
        if lobby_initialized:
            return
        from v2.scenes.lobby import LobbyScene

        sm.set_scene(LobbyScene())
        lobby_initialized = True
        sm.update(0)
        sm.draw(screen)
        pygame.display.flip()

    def _on_web_menu_start() -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT,
                {"action": "web_menu_start"},
            )
        )

    def _on_web_menu_ready() -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT,
                {"action": "web_menu_ready"},
            )
        )

    def _on_web_menu_quit() -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT,
                {"action": "web_menu_quit"},
            )
        )

    def _on_web_lobby_open() -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT,
                {"action": "web_lobby_open"},
            )
        )

    def _on_web_start_match(strategies: list[str]) -> None:
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT,
                {
                    "action": "web_start_match",
                    "strategies": strategies,
                },
            )
        )

    try:
        from v2.ui.web_menu.menu_v3 import launch_menu_overlay

        web_menu_overlay = launch_menu_overlay(
            pygame_hwnd,
            _on_web_menu_start,
            on_ready_callback=_on_web_menu_ready,
            on_quit_callback=_on_web_menu_quit,
            on_lobby_callback=_on_web_lobby_open,
            on_match_callback=_on_web_start_match,
        )
        web_menu_active = True
    except ImportError:
        print("[UYARI] pywebview kurulu degil - fallback: klasik Pygame menusu")
        sm.set_scene(MenuScene())
    except Exception as exc:
        print(f"[UYARI] pywebview menu baslatilamadi - fallback aktif: {exc}")
        sm.set_scene(MenuScene())
    print("[SceneManager] Initial scene loaded:", sm.current_scene_name)
    print("Press ESC to exit.")

    running = True
    while running:
        dt_ms = clock.tick(60)          # ms cinsinden delta time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.USEREVENT:
                action = getattr(event, "action", None)
                if action == "web_menu_ready":
                    pass
                elif action == "web_lobby_open":
                    _draw_startup_frame(screen)
                elif action == "web_menu_start":
                    _ensure_lobby_scene()
                    _bring_pygame_window_to_front(pygame_hwnd)
                    sm.update(0)
                    sm.draw(screen)
                    pygame.display.flip()
                    web_menu_active = False
                    if web_menu_overlay is not None:
                        web_menu_overlay.close()
                        web_menu_overlay = None
                    _bring_pygame_window_to_front(pygame_hwnd)
                elif action == "web_start_match":
                    strategies = getattr(event, "strategies", None)
                    if not isinstance(strategies, list):
                        strategies = None
                    gs = _bootstrap(ai_strategies=strategies)
                    from v2.scenes.shop import ShopScene

                    sm.set_scene(ShopScene(gs))
                    sm.update(0)
                    sm.draw(screen)
                    pygame.display.flip()
                    web_menu_active = False
                    if web_menu_overlay is not None:
                        web_menu_overlay.close()
                        web_menu_overlay = None
                    _bring_pygame_window_to_front(pygame_hwnd)
                elif action == "web_menu_quit":
                    running = False
                elif action == "transition_to_lobby":
                    from v2.scenes.lobby import LobbyScene

                    SceneManager.get().transition_to(LobbyScene())
                else:
                    sm.handle_event(event)
            elif web_menu_active:
                continue
            else:
                sm.handle_event(event)  # Geçiş sırasında otomatik olarak bloklanır

        sm.update(dt_ms)
        sm.draw(screen)
        pygame.display.flip()

    if web_menu_overlay is not None:
        web_menu_overlay.close()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
