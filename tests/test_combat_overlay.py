import pytest
import pygame
from v2.ui.overlays.combat_overlay import CombatOverlay
from v2.constants import Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    pygame.quit()

def test_combatoverlay_renders_log_stream_behaviorally(monkeypatch):
    """CombatOverlay'in motor loglarını terminal benzeri streaming ile ekrana bastığını doğrular."""
    
    mock_log_lines = [
        "A: Kill= 0 Combo= 0 Synergy= 24 TOPLAM= 25",
        "B: Kill= 0 Combo= 3 Synergy= 24 TOPLAM= 27",
        "SONUÇ: P2 (economist) kazandı -> P1 -1 HP"
    ]
    
    overlay = CombatOverlay(combat_logs=mock_log_lines, line_delay_ms=0)
    surface = pygame.Surface((Screen.W, Screen.H))
    
    drawn_texts = []
    
    from v2.ui import font_cache
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text))
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    # Force lines to show by skipping delay
    overlay.update(1000)
    overlay.render(surface)
    
    joined_text = " ".join(drawn_texts)
    
    # Ekrana basılı logları doğrula
    assert "kazandı -> P1 -1 HP" in joined_text
    assert "Synergy= 24" in joined_text

def test_combatoverlay_streams_lines_based_on_time():
    """CombatOverlay logları anında değil, dt (time) gecikmesi ile yazar."""
    mock_log_lines = ["Line 1", "Line 2", "Line 3"]
    overlay = CombatOverlay(combat_logs=mock_log_lines, line_delay_ms=100)
    
    assert len(overlay.visible_lines) == 0
    overlay.update(50)
    assert len(overlay.visible_lines) == 0 # Daha 100 ms olmadı
    
    overlay.update(60) # total 110ms
    assert len(overlay.visible_lines) == 1
    
    overlay.update(250) # total 360ms
    assert len(overlay.visible_lines) == 3 # Hepsi görünür

    assert overlay.is_finished == False # Henüz post-combat delay bitmedi
    overlay.update(2500) # Post-combat beklemesi aşıldı
    assert overlay.is_finished == True
