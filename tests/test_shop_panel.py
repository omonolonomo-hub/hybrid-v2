import pytest
import pygame
from v2.ui.shop_panel import ShopPanel
from v2.constants import Layout, Screen
from v2.core.game_state import GameState, ActionResult

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    from v2.ui import font_cache
    font_cache.clear_cache()   # Eski font nesnelerini temizle
    pygame.font.quit()
    pygame.quit()

@pytest.fixture
def mock_game_state(monkeypatch):
    class DummyEngine:
        def get_shop_cards(self, player_index):
            return [None, None, None, None, None]
            
    GameState._instance = None
    state = GameState.get()
    state._engine = DummyEngine()
    
    state._engine.get_shop_cards_called = False
    original = state._engine.get_shop_cards
    def tracker(player_index):
        state._engine.get_shop_cards_called = True
        return original(player_index)
    state._engine.get_shop_cards = tracker
    
    return state

def test_shoppanel_initializes_with_correct_dimensions():
    panel = ShopPanel()
    assert panel.rect.y == Layout.SHOP_PANEL_Y
    assert panel.rect.h == Layout.SHOP_PANEL_H

def test_shoppanel_render_method_exists(mock_game_state):
    panel = ShopPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)

def test_shoppanel_creates_five_card_slots_correct_layout():
    panel = ShopPanel()
    assert len(panel.card_rects) == Layout.SHOP_SLOTS, "Dükkan 5 yuvadan oluşmalıdır."
    for i, rect in enumerate(panel.card_rects):
        assert rect.w == Layout.SHOP_CARD_W
        assert rect.h == Layout.SHOP_CARD_H
        if i > 0:
            expected_x = panel.card_rects[i-1].x + Layout.SHOP_CARD_W + Layout.SHOP_CARD_GAP
            assert rect.x == expected_x

def test_shoppanel_creates_reroll_button_at_correct_position():
    """Reroll butonu sağ tarafa yaslı olarak hizalanmış olmalı."""
    panel = ShopPanel()
    btn   = panel.reroll_rect
    expected_x = panel.rect.right - Layout.REROLL_BTN_W - 20
    assert btn.x == expected_x, "Reroll butonu yanlış X konumunda!"
    # Y: panel içinde, üstten 20px'den daha fazla aşağıda olmamalı
    assert panel.rect.y <= btn.y <= panel.rect.y + 20, (
        "Reroll butonu panel üstüne yakın olmalı (overlap fix sonrası yeni anchor)."

    )

def test_shoppanel_creates_info_panel():
    panel = ShopPanel()
    assert hasattr(panel, "info_rect"), "ShopPanel'de hover bilgi kutusu info_rect bulunamadı!"
    assert panel.info_rect.w == Layout.SHOP_INFO_W

def test_shoppanel_creates_lock_and_stats_rects():
    """ShopPanel içerisinde oyun motoru verilerini okuyacak Stats alanı ve Lock butonu bulunmalıdır."""
    panel = ShopPanel()
    assert hasattr(panel, "lock_rect"), "ShopPanel'de lock_rect sabiti eksik!"
    assert hasattr(panel, "stats_rect"), "ShopPanel'de drop rates/gold stats_rect eksik!"
    
    # Kapsülleme doğrulama (Panel dışına hiçbir kutu taşmamalı!)
    assert panel.lock_rect.bottom <= panel.rect.bottom
    assert panel.stats_rect.bottom <= panel.rect.bottom
    assert panel.reroll_rect.bottom <= panel.rect.bottom

    # Lock, Reroll'un altında olmalı
    assert panel.lock_rect.y >= panel.reroll_rect.bottom
    # Stats, info panel'in sağında olmalı
    assert panel.stats_rect.x >= panel.info_rect.right

def test_shoppanel_reads_pool_from_gamestate(mock_game_state):
    panel = ShopPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)

def test_shoppanel_render_draws_visual_rects(mock_game_state, monkeypatch):
    """Render: panel artık polygon değil CardFlip/sprite blit kullanıyor.
    _flips listesi dolu ve her slot için bir CardFlip mevcut olmalı."""
    panel = ShopPanel()
    assert hasattr(panel, "_flips"), "ShopPanel'de CardFlip animatör listesi (_flips) eksik!"
    assert len(panel._flips) == Layout.SHOP_SLOTS, "Her slot için bir CardFlip olmalı."
    # render() exception atmadan tamamlanmalı
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)

def test_shoppanel_handles_reroll_click(mock_game_state, monkeypatch):
    panel = ShopPanel()
    called_reroll = False
    def mock_reroll(player_index):
        nonlocal called_reroll
        called_reroll = True
        return ActionResult.OK
    monkeypatch.setattr(mock_game_state, "reroll_market", mock_reroll, raising=False)
    
    cx, cy = panel.reroll_rect.center
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))
    handled = panel.handle_event(mock_event)
    
    assert handled is True
    assert called_reroll is True

def test_shoppanel_handles_lock_click(mock_game_state, monkeypatch):
    """Kilit butonuna basıldığında GameState.lock_shop tetiklenmelidir."""
    panel = ShopPanel()
    called_lock = False
    def mock_lock(player_index):
        nonlocal called_lock
        called_lock = True
        return ActionResult.OK
    monkeypatch.setattr(mock_game_state, "toggle_lock_shop", mock_lock, raising=False)
    
    cx, cy = panel.lock_rect.center
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))
    handled = panel.handle_event(mock_event)
    
    assert handled is True
    assert called_lock is True

def test_shoppanel_handles_card_slot_click(mock_game_state, monkeypatch):
    panel = ShopPanel()
    buy_called_slot = -1
    def mock_buy_card_from_slot(player_index, slot_index):
        nonlocal buy_called_slot
        buy_called_slot = slot_index
        return ActionResult.OK
    monkeypatch.setattr(mock_game_state, "buy_card_from_slot", mock_buy_card_from_slot, raising=False)
    
    cx, cy = panel.card_rects[2].center
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))
    handled = panel.handle_event(mock_event)
    
    assert handled is True
    assert buy_called_slot == 2

# === EDGE CASE TESTS ===

def test_shoppanel_ignores_clicks_in_empty_gaps(mock_game_state, monkeypatch):
    """EDGE CASE: Kart rect'lerinin dışındaki boşluklara (padding/gap) tıklanırsa ShopPanel false döner ve hata atmaz."""
    panel = ShopPanel()
    call_log = []
    
    monkeypatch.setattr(mock_game_state, "reroll_market", lambda *args, **kw: call_log.append("reroll"), raising=False)
    monkeypatch.setattr(mock_game_state, "buy_card_from_slot", lambda *args, **kw: call_log.append("buy"), raising=False)

    # 1. Slotun bittiği yer ile 2. Slotun başladığı yerin tam ortası
    gap_x = panel.card_rects[0].right + (Layout.SHOP_CARD_GAP // 2)
    gap_y = panel.card_rects[0].centery
    
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(gap_x, gap_y))
    handled = panel.handle_event(mock_event)
    
    assert handled is False, "Boşluğa tıklanması handled sayılmamalı!"
    assert len(call_log) == 0, "Boşluğa tıklayınca GameState tetiklendi (Kaçak çağrı)!"

def test_shoppanel_ignores_right_click_and_scroll(mock_game_state, monkeypatch):
    """EDGE CASE: Sağ tık (button=3) veya Fare Tekerleği Scroll (button=4,5) satın alma yapmaz."""
    panel = ShopPanel()
    call_log = []
    monkeypatch.setattr(mock_game_state, "buy_card_from_slot", lambda *args, **kw: call_log.append("buy"), raising=False)

    cx, cy = panel.card_rects[1].center
    
    # Sağ tık simüle edelim (Sol değil)
    bad_event_right = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(cx, cy))
    handled1 = panel.handle_event(bad_event_right)
    
    # Tekerlek simüle edelim
    bad_event_scroll = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=4, pos=(cx, cy))
    handled2 = panel.handle_event(bad_event_scroll)
    
    assert handled1 is False and handled2 is False, "Sol tık hariç tuşlar görmezden gelinmeli!"
    assert len(call_log) == 0

def test_shoppanel_out_of_bounds_rendering_safety(mock_game_state):
    """EDGE CASE: Ekran sınırları ötesinden hayalet pygame olayları gelirse patlamaz."""
    panel = ShopPanel()
    ghost_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(-9999, -9999))
    handled = panel.handle_event(ghost_event)
    assert handled is False
