import pytest
import pygame
from v2.ui.synergy_hud import SynergyHud
from v2.constants import Layout, Screen

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_synergyhud_initializes_with_correct_dimensions():
    hud = SynergyHud()
    assert hud.rect.x == 0
    assert hud.rect.y == Layout.SYNERGY_HUD_Y
    assert hud.rect.w == Layout.SIDEBAR_LEFT_W
    assert hud.rect.h == Screen.H - Layout.SYNERGY_HUD_Y

def test_synergyhud_creates_group_badge_container():
    hud = SynergyHud()
    assert hasattr(hud, "groups_rect")
    assert hud.groups_rect.x >= hud.rect.x
    assert hud.groups_rect.w <= hud.rect.w

def test_synergyhud_render_displays_passive_log_and_combat_stats(monkeypatch):
    """SynergyHUD render edildiğinde Synergy grupları ve Combat Özetleri gibi verilerin davranıssal olarak ekrana (font_cache ile) basıldıgını dogrular."""
    hud = SynergyHud()
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn_texts = []
    from v2.ui import font_cache
    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text).upper())
    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    # Force some fake state to ensure text paths trigger
    hud._last_state = {
        "groups": {"A": 1},
        "score_rows": [("kill", 10), ("combo", 5), ("syn", 20)],
        "score_total": 35,
        "results": {"win": True},
        "feed": ["A triggered"],
    }

    hud.render(surface)

    joined_text = " ".join(drawn_texts)
    
    assert "COMBAT SUMMARY" in joined_text or "COMBAT" in joined_text or "SAVAŞ" in joined_text
    assert "PASSIVES" in joined_text or "PASSIVE" in joined_text or "PASİF" in joined_text or "PASIF" in joined_text
    assert "TOTAL" in joined_text or "TOPLAM" in joined_text

def test_synergyhud_score_rect_height_fits_content():
    """score_rect TOPLAM satırını içinde barındıracak kadar yüksek olmalı (>=110)."""
    hud = SynergyHud()
    assert hud.score_rect.h >= 110, f"score_rect.h={hud.score_rect.h} TOPLAM için yetersiz"

def test_synergyhud_boxes_do_not_overflow_sidebar():
    """Tüm kutular sol sidebar sınırları içinde kalmalı."""
    hud = SynergyHud()
    for name, r in [
        ("groups_rect",       hud.groups_rect),
        ("score_rect",        hud.score_rect),
        ("last_combat_rect",  hud.last_combat_rect),
        ("passive_feed_rect", hud.passive_feed_rect),
    ]:
        assert r.right  <= hud.rect.right  + 2, f"{name} sağ sınır aştı"
        assert r.bottom <= hud.rect.bottom + 2, f"{name} alt sınır aştı"

def test_synergyhud_stacking_order():
    """Kutular yukarıdan aşağıya sırayla istiflenmiş olmalı."""
    hud = SynergyHud()
    assert hud.groups_rect.top      <  hud.score_rect.top
    assert hud.score_rect.top       <  hud.last_combat_rect.top
    assert hud.last_combat_rect.top <  hud.passive_feed_rect.top

def test_synergyhud_render_full_does_not_crash():
    """render() tam bir Surface üzerinde istisna fırlatmamalı."""
    hud = SynergyHud()
    surface = pygame.Surface((Screen.W, Screen.H))
    hud.render(surface)   # crash yoksa geçer

def test_synergyhud_score_row_colors_defined():
    """_SCORE_ROWS tablosu 3 bileşen içermeli ve doğru anahtarlara sahip olmalı."""
    hud = SynergyHud()
    assert hasattr(hud, "_SCORE_ROWS"), "_SCORE_ROWS class değişkeni tanımlı olmalı"
    keys = {row[0] for row in hud._SCORE_ROWS}
    assert keys == {"kill", "combo", "syn"}, f"Beklenen anahtarlar: kill,combo,syn — Bulunan: {keys}"
