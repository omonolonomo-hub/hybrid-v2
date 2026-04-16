import pytest
import pygame
from v2.ui.overlays.endgame_overlay import EndgameOverlay
from v2.constants import Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    pygame.quit()

def test_endgameoverlay_renders_scoreboard_behaviorally(monkeypatch):
    """EndgameOverlay'in skor tablosu verilerini ekrana (font_cache'e) yazdığını doğrular."""
    
    mock_stats = [
        {"name": "Hero", "strategy": "Aggro", "hp": 50, "total_pts": 1200, "rank": 1},
        {"name": "Rival", "strategy": "Economy", "hp": 0, "total_pts": 850, "rank": 2}
    ]
    
    overlay = EndgameOverlay(player_stats=mock_stats)
    surface = pygame.Surface((Screen.W, Screen.H))
    
    drawn_texts = []
    
    from v2.ui import font_cache
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text))
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    overlay.render(surface)
    
    joined_text = " ".join(drawn_texts)
    
    assert "Hero" in joined_text
    assert "Aggro" in joined_text
    assert "1200" in joined_text
    assert "WINS" in joined_text or "KAZANDI" in joined_text

def test_endgameoverlay_handles_restart_click():
    """EndgameOverlay üzerindeki Restart butonunun tıklamayı yakaladığını doğrular."""
    overlay = EndgameOverlay(player_stats=[])
    
    # Butonun ortasına mock click atalım
    mock_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=overlay.restart_rect.center)
    handled = overlay.handle_event(mock_event)
    
    assert handled is True
    assert overlay.restart_clicked is True
