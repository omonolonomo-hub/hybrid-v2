import pytest
import pygame
from v2.ui.overlays.versus_overlay import VersusOverlay
from v2.constants import Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    pygame.quit()

def test_versusoverlay_renders_matched_opponents_behaviorally(monkeypatch):
    """VersusOverlay render edildiğinde ekrana sahte eşleşme isimlerini bastığını doğrular."""
    overlay = VersusOverlay(player_name="P1 (Builder)", opp_name="P5 (Economy)", duration_ms=2000)
    surface = pygame.Surface((Screen.W, Screen.H))
    
    drawn_texts = []
    
    # Mock font_cache
    from v2.ui import font_cache
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text))
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    # Render it
    overlay.render(surface)
    
    joined_text = " ".join(drawn_texts)
    
    # Beklenen isimlerin ekrana (font_cache'e) gitmiş olması lâzım
    assert "P1 (Builder)" in joined_text
    assert "P5 (Economy)" in joined_text
    assert "VS" in joined_text.upper()

def test_versusoverlay_timeout_finishes_overlay():
    """VersusOverlay belirtilen süre sonunda is_finished bayrağını kaldırır."""
    overlay = VersusOverlay("A", "B", duration_ms=100)
    assert not overlay.is_finished
    
    # Zaman geçişi simülasyonu
    overlay.update(50)
    assert not overlay.is_finished
    
    overlay.update(51)
    assert overlay.is_finished
