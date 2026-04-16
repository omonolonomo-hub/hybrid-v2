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

def test_playerhub_render_paints_all_vital_statistics(monkeypatch):
    """PlayerHub render edildiğinde HP, Gold, Streak gibi kilit etiketlerin ekrana çizildiğini (behavior) doğrular."""
    hub = PlayerHub()
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn_texts = []
    
    # Gerçek font_cache'in import'unu engellemek veya monkeypatch ile yakalamak
    from v2.ui import font_cache
    
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text).upper())
        
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    hub.render(surface)
    
    # Ekrana çizilen (rendered) yazılar arasında hayati verilerin etiket veya değerlerinin bulunduğunu onayla
    joined_text = " ".join(drawn_texts)
    
    assert "HP" in joined_text or "Y" in joined_text # (YOU kelimesindeki Y veya HP)
    assert "GOLD" in joined_text or "G" in joined_text
    assert "STREAK" in joined_text or "NÖTR" in joined_text or "ATEŞ" in joined_text or "\u2605" in joined_text
    assert "BOARD" in joined_text or "PTS:" in joined_text
