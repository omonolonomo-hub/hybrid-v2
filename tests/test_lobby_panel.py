import pytest
import pygame
from v2.ui.lobby_panel import LobbyPanel
from v2.constants import Layout, Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_lobbypanel_initializes_with_correct_dimensions():
    """LobbyPanel (Right HUD) ekranın en sağına bitişik şekilde tam boy oturmalıdır."""
    panel = LobbyPanel()
    assert panel.rect.x == Layout.SIDEBAR_RIGHT_X
    assert panel.rect.y == 0
    assert panel.rect.w == Layout.SIDEBAR_RIGHT_W
    assert panel.rect.h == Screen.H

def test_lobbypanel_creates_player_rows():
    """LobbyPanel, rakiplerin sağlıklarını sergileyecek sıralı kutucuklar (rows) barındırmalıdır."""
    panel = LobbyPanel(player_count=4)
    assert hasattr(panel, "player_rects")
    assert len(panel.player_rects) == 4
    
    # Kutularin ust uste binmediginden ve panel disina cikmadigindan emin olalim
    for i, p_rect in enumerate(panel.player_rects):
        assert p_rect.x >= panel.rect.x
        assert p_rect.right <= panel.rect.right
        
        if i > 0:
            prev_rect = panel.player_rects[i-1]
            assert p_rect.y >= prev_rect.bottom

def test_lobbypanel_render_creates_primitives(monkeypatch):
    panel = LobbyPanel(player_count=2)
    surface = pygame.Surface((Screen.W, Screen.H))
    
    drawn_rects = []
    def mock_draw_rect(surf, color, rect, *args, **kwargs):
        drawn_rects.append(rect)
    monkeypatch.setattr(pygame.draw, "rect", mock_draw_rect)
    
    panel.render(surface)
    # Lobi backgroundu kaldırıldı. Üstte yüzen (1 title bar) + (player_count row) çizilmeli. 1 title + 2 rows = 3 ana kutu. + ic barlar vs.
    assert len(drawn_rects) >= 3, "LobbyPanel rowları ve yüzen barı çizmelidir."
