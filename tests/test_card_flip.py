import pytest
import pygame
from v2.ui.card_flip import CardFlip

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def _make_surfaces():
    back  = pygame.Surface((120, 160), pygame.SRCALPHA)
    front = pygame.Surface((120, 160), pygame.SRCALPHA)
    back.fill((30, 30, 60))
    front.fill((60, 120, 200))
    return back, front

def test_flip_starts_at_back():
    """Yeni oluşturulan CardFlip arka yüzü göstermeli (progress=0)."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    assert flip.flip_progress == 0.0
    assert not flip.is_showing_front

def test_hover_start_sets_target():
    """hover_start() sonrası flip ve hover targetlar 1.0 olmalı."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    flip.hover_start()
    assert flip._flip_target == 1.0
    assert flip._hover_target == 1.0

def test_hover_end_sets_target():
    """hover_end() sonrası flip ve hover targetlar 0.0 olmalı."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    flip.hover_start()
    flip.hover_end()
    assert flip._flip_target == 0.0
    assert flip._hover_target == 0.0

def test_flip_progress_advances_on_update():
    """update() çağrıldıktan sonra flip_progress ilerlemeli."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    flip.hover_start()
    flip.update(dt_ms=200)   # 200ms ilerleme
    assert flip.flip_progress > 0.0

def test_flip_shows_front_after_enough_updates():
    """Yeterli update döngüsü sonrası is_showing_front True olmalı."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    flip.hover_start()
    for _ in range(60):        # 60 frame @ ~16ms ≈ 1 saniye
        flip.update(dt_ms=16)
    assert flip.is_showing_front

def test_flip_renders_without_crash():
    """render() çağrısı exception fırlatmamalı."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(100, 100, 120, 160))
    surface = pygame.Surface((1920, 1080))
    flip.hover_start()
    flip.update(dt_ms=100)
    flip.render(surface)       # Exception yoksa test geçer

def test_flip_snaps_back_to_zero_after_hover_end():
    """Hover bitti, yeterince update sonrası sıfıra dönmeli."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 120, 160))
    flip.hover_start()
    for _ in range(60):
        flip.update(16)
    flip.hover_end()
    for _ in range(60):
        flip.update(16)
    assert not flip.is_showing_front
    assert flip.flip_progress < 0.1
