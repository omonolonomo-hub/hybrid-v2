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

def test_lobbypanel_render_draws_dynamic_player_list_based_on_payload(monkeypatch):
    """LobbyPanel render edildiğinde, verilen payload'daki (engine verisi) kişi sayısı kadar satırın ekrana isimlerle basıldığını doğrular."""
    panel = LobbyPanel(player_count=8)  # Max capacity
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn_texts = []
    from v2.ui import font_cache
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text))
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    # Senaryo 1: 3 Kişilik lobi Payload'u
    mock_payload_3 = [
        {"name": "Hero", "hp": 100, "max_hp": 150, "gold": 10, "rank": 1},
        {"name": "Rival", "hp": 80, "max_hp": 150, "gold": 5, "rank": 2},
        {"name": "Bot", "hp": 0, "max_hp": 150, "gold": 0, "rank": 3},
    ]

    panel.render(surface, players=mock_payload_3)

    joined_text = " ".join(drawn_texts)
    
    # Ekrana basılan isimlerin 3'ünün de render komutuna gitmiş olması lazım
    assert "Hero" in joined_text
    assert "Rival" in joined_text
    assert "Bot" in joined_text
    
    # Senaryo 2: Layout doğrulaması, payload değiştikçe card rectleri dinamik çalışıyor olmalı
    assert len(panel.player_rects) >= 3

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

@pytest.mark.xfail(reason="Phase 4 Task D: LobbyPanel elimination overlay is not implemented yet.")
def test_lobbypanel_renders_eliminated_players_differently():
    # Covers: "LobbyPanel satırı grayscale + ELIMINATED görünümüne geçer"
    pass
