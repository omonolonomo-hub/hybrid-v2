import pytest
import pygame
from v2.ui.timer_bar import TimerBar
from v2.constants import Layout

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_timerbar_dimensions_and_position():
    """TimerBar, ShopPanel'in hemen altinda ve merkez canvas uzerinde yer almalidir."""
    timer = TimerBar()
    assert timer.rect.x == Layout.CENTER_ORIGIN_X
    assert timer.rect.y == Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H
    assert timer.rect.w == Layout.CENTER_W
    assert timer.rect.h > 0

def test_timerbar_render_creates_primitives(monkeypatch):
    """Eriyen bar arkaplanini ve iskeletini cizmelidir."""
    timer = TimerBar()
    surface = pygame.Surface((1920, 1080))
    drawn_rects = []
    
    def mock_draw_rect(surf, color, rect, *args, **kwargs):
        drawn_rects.append(rect)
        
    monkeypatch.setattr(pygame.draw, "rect", mock_draw_rect)
    timer.render(surface, ratio=0.5)
    
    # En az 1 arkaplan, 1 dolgu olmak uzere 2 primitive bekliyoruz
    assert len(drawn_rects) >= 2
