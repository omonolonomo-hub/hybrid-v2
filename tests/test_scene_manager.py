import pygame
import pytest

from v2.core.scene_manager import Scene, SceneManager


# ══════════════════════════════════════════════════════════════════════════════
# MİMARİ NOTU
# Yeni Overlay mimarisinde SceneManager yalnızca LobbyScene <-> ShopScene
# geçişi için kullanılır. Versus / Combat / Endgame artık bağımsız sahneler
# değil; ShopScene'in Phase State Machine'i tarafından yönetilen Overlay
# Pop-up'larıdır (v2/ui/overlays/).
#
# Bu test dosyası SceneManager'ın temel yaşam döngüsünü (Lobby bağlamı)
# doğrular ve VersusScene / CombatScene / EndgameScene kavramlarını
# BİLİNÇLİ OLARAK kapsamaz.
# ══════════════════════════════════════════════════════════════════════════════


class TrackingScene(Scene):
    def __init__(self, name: str):
        self.name = name
        self.enter_count = 0
        self.exit_count = 0
        self.update_calls = []
        self.events = []
        self.draw_count = 0

    def on_enter(self) -> None:
        self.enter_count += 1

    def on_exit(self) -> None:
        self.exit_count += 1

    def handle_event(self, event: pygame.event.Event) -> None:
        self.events.append(event.type)

    def update(self, dt_ms: float) -> None:
        self.update_calls.append(dt_ms)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_count += 1
        surface.fill((20, 30, 40))


class LegacyRenderScene:
    """LobbyScene gibi eski render() imzası kullanan sahneler için fallback testi."""
    def __init__(self):
        self.render_count = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self, dt_ms: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        self.render_count += 1
        surface.fill((60, 70, 80))


@pytest.fixture(autouse=True)
def init_scene_manager():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    SceneManager._instance = None
    yield
    SceneManager._instance = None
    pygame.quit()


def test_set_scene_calls_enter_and_replaces_previous_scene():
    """set_scene() çağrısında önceki sahne exit() alır, yeni sahne enter() alır."""
    manager = SceneManager.get()
    first = TrackingScene("first")
    second = TrackingScene("second")

    manager.set_scene(first)
    manager.set_scene(second)

    assert first.enter_count == 1
    assert first.exit_count == 1
    assert second.enter_count == 1
    assert manager.current_scene_name == "TrackingScene"
    assert manager.is_transitioning is False


def test_transition_blocks_input_until_fade_completes_and_switches_scene():
    """Fade geçişi sırasında input iletilmez; fade bitince yeni sahneye geçilir."""
    manager = SceneManager.get()
    first = TrackingScene("first")
    second = TrackingScene("second")
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

    manager.set_scene(first)
    manager.handle_event(event)
    manager.transition_to(second, fade_ms=100)
    manager.handle_event(event)   # geçiş sırasında — iletilmez
    manager.update(50)
    manager.handle_event(event)   # hâlâ geçişte — iletilmez
    manager.update(60)            # fade tamamlanır
    manager.handle_event(event)   # artık second sahnesine iletilir
    manager.update(100)

    assert first.events == [pygame.KEYDOWN]
    assert first.exit_count == 1
    assert second.enter_count == 1
    assert manager.is_transitioning is False


def test_transition_request_is_ignored_while_another_transition_is_in_progress():
    """Aktif fade varken gelen yeni transition_to() çağrısı yok sayılır."""
    manager = SceneManager.get()
    first = TrackingScene("first")
    second = TrackingScene("second")
    third = TrackingScene("third")

    manager.set_scene(first)
    manager.transition_to(second, fade_ms=100)
    manager.transition_to(third, fade_ms=100)   # bu yok sayılmalı
    manager.update(100)
    manager.update(100)

    assert second.enter_count == 1
    assert third.enter_count == 0
    assert manager.current_scene_name == "TrackingScene"


def test_draw_uses_draw_method_and_applies_overlay_during_transition():
    """Fade sırasında draw() eski sahneyi çizip üstüne yarı saydam overlay ekler."""
    manager = SceneManager.get()
    first = TrackingScene("first")
    second = TrackingScene("second")
    surface = pygame.Surface((160, 90))

    manager.set_scene(first)
    manager.transition_to(second, fade_ms=100)
    manager.update(50)
    manager.draw(surface)

    assert first.draw_count == 1
    assert manager._fade_surface is not None
    assert manager._fade_surface.get_size() == surface.get_size()


def test_draw_falls_back_to_legacy_render_method():
    """draw() metodu olmayan LobbyScene tarzı sahnelerde render() fallback'i çalışır."""
    manager = SceneManager.get()
    legacy = LegacyRenderScene()
    surface = pygame.Surface((120, 80))

    manager.set_scene(legacy)
    manager.draw(surface)

    assert legacy.render_count == 1
