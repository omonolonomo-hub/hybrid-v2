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

def test_synergyhud_creates_tracking_and_log_rects():
    """SynergyHUD, pasif eşik takibini ve combat log verilerini dikey istiflemelidir."""
    hud = SynergyHud()
    assert hasattr(hud, "passive_tracker_rect"), "SynergyHud passive_tracker_rect uretmiyor!"
    assert hasattr(hud, "combat_log_rect"), "SynergyHud combat_log_rect uretmiyor!"

    # Yukaridan asagiya carpisma olmadan istiflenip istiflenmediklerini kontrol edelim
    assert hud.passive_tracker_rect.y >= hud.groups_rect.bottom
    assert hud.combat_log_rect.y >= hud.passive_tracker_rect.bottom

def test_synergyhud_render_creates_primitives(monkeypatch):
    hud = SynergyHud()
    surface = pygame.Surface((Screen.W, Screen.H))
    drawn_rects = []
    def mock_draw_rect(surf, color, rect, *args, **kwargs):
        drawn_rects.append(rect)
    monkeypatch.setattr(pygame.draw, "rect", mock_draw_rect)
    hud.render(surface)
    assert len(drawn_rects) >= 2, "SynergyHUD background ve GroupBox cizilmelidir."

# ── Phase 3 redesign: yeni kutular ────────────────────────────────────────

def test_synergyhud_has_last_combat_rect():
    hud = SynergyHud()
    assert hasattr(hud, "last_combat_rect"), "SynergyHud last_combat_rect içermeli"
    assert hud.last_combat_rect.y >= hud.score_rect.bottom

def test_synergyhud_has_passive_feed_rect():
    hud = SynergyHud()
    assert hasattr(hud, "passive_feed_rect"), "SynergyHud passive_feed_rect içermeli"
    assert hud.passive_feed_rect.y >= hud.last_combat_rect.bottom

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
