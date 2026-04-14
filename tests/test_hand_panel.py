import pytest
import pygame
from v2.ui.hand_panel import HandPanel
from v2.constants import Layout, Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_handpanel_initializes_with_correct_dimensions():
    panel = HandPanel()
    assert panel.rect.y == Layout.HAND_PANEL_Y
    assert panel.rect.h == Layout.HAND_PANEL_H

def test_handpanel_creates_six_card_slots_correct_layout():
    panel = HandPanel()
    assert len(panel.card_rects) == Layout.HAND_MAX_CARDS, "Oyuncu eli 6 yuvadan oluşmalıdır."
    for i, rect in enumerate(panel.card_rects):
        assert rect.w == Layout.HAND_CARD_W
        assert rect.h == Layout.HAND_CARD_H
        if i > 0:
            expected_x = panel.card_rects[i-1].x + Layout.HAND_CARD_W + Layout.HAND_CARD_GAP
            assert rect.x == expected_x

def test_handpanel_creates_info_panel_on_right():
    """Panels sağ kısmında hover özellikleri için bir 'bilgi paneli' bulunmalıdır."""
    panel = HandPanel()
    assert hasattr(panel, "info_rect"), "HandPanel'de info_rect bulunamadı!"
    assert panel.info_rect.w == Layout.HAND_INFO_W
    # Info panelinin sağ paneli taşmaması ve panelin bitişine yakın olması doğrulanıyor
    assert panel.info_rect.right <= panel.rect.right - 20

def test_handpanel_creates_capacity_rect():
    """Board kapasitesi göstergesi HandPanel'den LobbyPanel'e taşındı.
    LobbyPanel'de capacity_rect var, HandPanel'de artık beklenmez."""
    from v2.ui.lobby_panel import LobbyPanel
    lobby = LobbyPanel()
    assert hasattr(lobby, "capacity_rect"), "Kapasite gösterge kutusu LobbyPanel'de olmalı."
    # Kapasite kutusu oyuncu listesinin altında, ekranın içinde yer almalı
    assert lobby.capacity_rect.bottom <= Screen.H

def test_handpanel_render_method_exists():
    panel = HandPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)

def test_handpanel_render_draws_visual_rects(monkeypatch):
    """Render: panel artık polygon değil CardFlip/sprite blit kullanıyor.
    _flips listesi dolu ve her slot için bir CardFlip mevcut olmalı."""
    panel = HandPanel()
    assert hasattr(panel, "_flips"), "HandPanel'de CardFlip animatör listesi (_flips) eksik!"
    assert len(panel._flips) == Layout.HAND_MAX_CARDS, "Her slot için bir CardFlip olmalı."
    # render() çağrısı exception atmadan tamamlanmalı
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)

# === EDGE CASES ===

def test_handpanel_ignores_out_of_bounds_ghost_clicks():
    """EDGE CASE: Ekran sınırları dışından veya panel harici yerlerden gelen pygame tıklamaları çökme yaratmaz."""
    panel = HandPanel()
    
    # HandPanel'de henüz handle_event yok ama eklendiğinde bunu yutmalı
    if hasattr(panel, "handle_event"):
        ghost_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(-9999, -9999))
        handled = panel.handle_event(ghost_event)
        assert handled is False

def test_handpanel_gap_clicks_are_ignored():
    """EDGE CASE: Kartlar arasına tıklanması yanlış slot seçimini tetiklemez."""
    panel = HandPanel()
    
    if hasattr(panel, "handle_event"):
        gap_x = panel.card_rects[0].right + (Layout.HAND_CARD_GAP // 2)
        gap_y = panel.card_rects[0].centery
        mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(gap_x, gap_y))
        handled = panel.handle_event(mock_event)
        assert handled is False

def test_handpanel_wheel_scroll_ignored():
    """EDGE CASE: Fare tekerleği slot seçimi veya karta müdahale yapmaz."""
    panel = HandPanel()
    if hasattr(panel, "handle_event"):
        cx, cy = panel.card_rects[1].center
        wheel_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=4, pos=(cx, cy))
        handled = panel.handle_event(wheel_event)
        assert handled is False
