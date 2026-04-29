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
    # pygame.init() is handled by session-scoped conftest.py fixture
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    SceneManager._instance = None
    yield
    SceneManager._instance = None
    # Don't call pygame.quit() - let session fixture handle it


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


# ══════════════════════════════════════════════════════════════════════════════
# BUG 3 PRESERVATION TESTS - Scene Lifecycle (Requirements 3.7, 3.8, 3.9)
# These tests capture baseline behavior on UNFIXED code that must be preserved
# after implementing the memory leak fix.
# ══════════════════════════════════════════════════════════════════════════════


def test_preservation_set_scene_calls_on_exit_on_old_scene():
    """
    PRESERVATION TEST (Requirement 3.7)
    WHEN set_scene() transitions to a new scene
    THEN the system SHALL CONTINUE TO call on_exit() on the old scene
    
    This test captures the baseline behavior that must be preserved after fix.
    """
    manager = SceneManager.get()
    old_scene = TrackingScene("old")
    new_scene = TrackingScene("new")
    
    # Set initial scene
    manager.set_scene(old_scene)
    assert old_scene.enter_count == 1
    assert old_scene.exit_count == 0
    
    # Transition to new scene
    manager.set_scene(new_scene)
    
    # Verify old scene's on_exit() was called
    assert old_scene.exit_count == 1, "Old scene's on_exit() must be called"
    assert new_scene.enter_count == 1, "New scene's on_enter() must be called"
    assert manager._current is new_scene, "Current scene must be updated"


def test_preservation_scenes_render_and_update_correctly_after_transition():
    """
    PRESERVATION TEST (Requirement 3.8)
    WHEN scenes are active
    THEN the system SHALL CONTINUE TO render and update correctly
    
    This test verifies that scene rendering and updating work correctly
    after transitions, which must be preserved after the memory leak fix.
    """
    manager = SceneManager.get()
    scene1 = TrackingScene("scene1")
    scene2 = TrackingScene("scene2")
    surface = pygame.Surface((160, 90))
    
    # Set first scene and verify it updates/renders
    manager.set_scene(scene1)
    manager.update(16.0)
    manager.draw(surface)
    
    assert len(scene1.update_calls) == 1
    assert scene1.update_calls[0] == 16.0
    assert scene1.draw_count == 1
    
    # Transition to second scene
    manager.set_scene(scene2)
    
    # Verify second scene updates/renders correctly
    manager.update(32.0)
    manager.draw(surface)
    
    assert len(scene2.update_calls) == 1
    assert scene2.update_calls[0] == 32.0
    assert scene2.draw_count == 1
    
    # Verify first scene is no longer updated/rendered
    assert len(scene1.update_calls) == 1, "Old scene should not receive updates"
    assert scene1.draw_count == 1, "Old scene should not be drawn"


def test_preservation_scene_lifecycle_methods_work_correctly():
    """
    PRESERVATION TEST (Requirement 3.9)
    WHEN scene lifecycle methods (on_enter, on_exit, update, render) are called
    THEN the system SHALL CONTINUE TO function as currently implemented
    
    This test verifies the complete lifecycle flow through multiple transitions.
    """
    manager = SceneManager.get()
    scene_a = TrackingScene("A")
    scene_b = TrackingScene("B")
    scene_c = TrackingScene("C")
    surface = pygame.Surface((100, 100))
    
    # Lifecycle: A enters
    manager.set_scene(scene_a)
    assert scene_a.enter_count == 1
    assert scene_a.exit_count == 0
    
    # A is active - update and draw work
    manager.update(10.0)
    manager.draw(surface)
    assert len(scene_a.update_calls) == 1
    assert scene_a.draw_count == 1
    
    # Lifecycle: A exits, B enters
    manager.set_scene(scene_b)
    assert scene_a.exit_count == 1
    assert scene_b.enter_count == 1
    assert scene_b.exit_count == 0
    
    # B is active - update and draw work
    manager.update(20.0)
    manager.draw(surface)
    assert len(scene_b.update_calls) == 1
    assert scene_b.draw_count == 1
    
    # Lifecycle: B exits, C enters
    manager.set_scene(scene_c)
    assert scene_b.exit_count == 1
    assert scene_c.enter_count == 1
    assert scene_c.exit_count == 0
    
    # C is active - update and draw work
    manager.update(30.0)
    manager.draw(surface)
    assert len(scene_c.update_calls) == 1
    assert scene_c.draw_count == 1
    
    # Verify previous scenes are not updated after transition
    assert len(scene_a.update_calls) == 1
    assert len(scene_b.update_calls) == 1


def test_preservation_first_set_scene_with_no_old_scene_works_correctly():
    """
    PRESERVATION TEST (Requirement 3.9 - Edge Case)
    WHEN first set_scene() call has no old scene
    THEN the system SHALL work correctly (no cleanup needed)
    
    This test verifies that the first scene transition doesn't attempt
    to cleanup a non-existent old scene. This edge case must be preserved.
    """
    manager = SceneManager.get()
    first_scene = TrackingScene("first")
    
    # Verify no current scene exists
    assert manager._current is None
    
    # First set_scene() call should work without errors
    manager.set_scene(first_scene)
    
    # Verify scene was set correctly
    assert manager._current is first_scene
    assert first_scene.enter_count == 1
    assert first_scene.exit_count == 0
    
    # Verify scene is functional
    surface = pygame.Surface((100, 100))
    manager.update(16.0)
    manager.draw(surface)
    
    assert len(first_scene.update_calls) == 1
    assert first_scene.draw_count == 1
