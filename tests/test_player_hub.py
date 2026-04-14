import pytest
import pygame
from v2.ui.player_hub import PlayerHub
from v2.constants import Layout, Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_playerhub_initializes_with_correct_dimensions():
    hub = PlayerHub()
    # Left sidebar top placement
    assert hub.rect.x == 0
    assert hub.rect.y == 0
    assert hub.rect.w == Layout.SIDEBAR_LEFT_W
    assert hub.rect.h == Layout.PLAYER_HUB_H

def test_playerhub_creates_vital_status_rects():
    """PlayerHub, can, altın ve diğer verileri gösterecek bloklara sahip olmalıdır."""
    hub = PlayerHub()
    # HP Bar check
    assert hasattr(hub, "hp_rect")
    assert hub.hp_rect.w <= Layout.SIDEBAR_LEFT_W - 20
    # Gold Indicator check
    assert hasattr(hub, "gold_rect")

def test_playerhub_render_creates_primitives(monkeypatch):
    hub = PlayerHub()
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn_rects = []
    def mock_draw_rect(surf, color, rect, *args, **kwargs):
        drawn_rects.append(rect)
    monkeypatch.setattr(pygame.draw, "rect", mock_draw_rect)

    hub.render(surface)
    assert len(drawn_rects) >= 3, "Hub arka planı, HP bar ve Gold bar çizilmelidir."


# ── Phase 3 redesign: yeni alanlar ────────────────────────────────────────

def test_playerhub_has_streak_rect():
    hub = PlayerHub()
    assert hasattr(hub, "streak_rect"), "PlayerHub streak_rect alanına sahip olmalı"

def test_playerhub_has_pts_rect():
    hub = PlayerHub()
    assert hasattr(hub, "pts_rect"), "PlayerHub pts_rect (toplam puan kutusu) içermeli"

def test_playerhub_has_board_rect():
    hub = PlayerHub()
    assert hasattr(hub, "board_rect"), "PlayerHub board_rect (board kapasite) içermeli"

def test_playerhub_has_income_rect():
    hub = PlayerHub()
    assert hasattr(hub, "income_rect"), "PlayerHub income_rect (gelir ipucu) içermeli"

def test_playerhub_sync_does_not_crash_without_engine():
    """Engine bağlı olmadan sync() çağrısı istisna fırlatmamalı."""
    from v2.core.game_state import GameState
    GameState._instance = None
    hub = PlayerHub()
    hub.sync()   # engine yok → try/except içinde sessizce geçmeli

def test_playerhub_render_does_not_crash(monkeypatch):
    """render() tam yüzey üzerinde çağrıldığında hata fırlatmamalı."""
    hub = PlayerHub()
    surface = pygame.Surface((Screen.W, Screen.H))
    hub.render(surface)   # crash yoksa geçer

def test_playerhub_all_subrects_within_bounds():
    """Tüm iç rect'ler sidebar sınırları içinde kalmalı."""
    hub = PlayerHub()
    for rect_name in ("hp_rect", "gold_rect", "streak_rect", "pts_rect", "board_rect", "income_rect"):
        r = getattr(hub, rect_name)
        assert r.right  <= hub.rect.right  + 2, f"{rect_name} sağ sınır aştı"
        assert r.bottom <= hub.rect.bottom + 2, f"{rect_name} alt sınır aştı"
        assert r.x >= hub.rect.x,               f"{rect_name} sol sınır aştı"
