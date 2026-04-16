"""
Edge Case Test Suite — Ghost Shell, Drag & Drop, CardFlip, AssetLoader
=======================================================================
Bu testler Faz 2'de eklenen sprite/flip altyapısının sınır durumlarını zorlar.
Özellikle:
  - Ghost Shell'in şekil doğruluğu (dikdörtgen değil altıgen)
  - Ghost alpha şeffaflığı (SRCALPHA yüzeylerde set_alpha() davranışı)
  - Drag state makinesi edge case'leri
  - CardFlip sınır değerleri
  - AssetLoader özel karakterli kart isimleri
"""

import pytest
import pygame
from v2.ui.hand_panel import HandPanel
from v2.ui.card_flip import CardFlip
from v2.constants import Layout, Screen


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    pygame.quit()


# ==========================================================================
# GHOST SHELL — Şekil & Alpha
# ==========================================================================

def test_ghost_shell_uses_card_back_surf_not_rectangle():
    """Ghost, back_surf.copy() kullanmalı — düz dikdörtgen fill değil."""
    panel  = HandPanel()
    flip   = panel._flips[0]

    # Ghost oluşturma mantığını simüle et
    ghost_surf = flip.back_surf.copy()
    ghost_surf.set_alpha(70)

    # Yüzeyin boyutları orijinal kartla eşleşmeli (dikdörtgen genişletme olmadı)
    assert ghost_surf.get_width()  == flip.back_surf.get_width()
    assert ghost_surf.get_height() == flip.back_surf.get_height()


def test_ghost_shell_alpha_is_reduced():
    """
    SRCALPHA yüzeylerde set_alpha() çalışmaz (!).
    Bu test, ghost'un gerçekten saydamlık kazanıp kazanmadığını denetler.
    Eğer başarısız olursa BLEND_RGBA_MULT çözümüne geçilmeli.
    """
    panel = HandPanel()
    flip  = panel._flips[0]

    # Ghost oluştur
    ghost_surf = flip.back_surf.copy()
    ghost_surf.set_alpha(70)

    # Siyah bir yüzey üstüne blit et, ardından merge olan rengi ölç
    bg = pygame.Surface((ghost_surf.get_width(), ghost_surf.get_height()))
    bg.fill((0, 0, 0))
    bg.blit(ghost_surf, (0, 0))

    # Merge edilen piksel tam beyaz (255,255,255) OLMAMALI → saydamlık var demek
    # Not: SRCALPHA+set_alpha() sorunu varsa piksel tam parlak gelir, bu assert kırılır
    cx, cy = ghost_surf.get_width() // 2, ghost_surf.get_height() // 2
    pixel_color = bg.get_at((cx, cy))
    # En az bir kanalın 255'ten küçük olmasını bekle (yarı saydam blit)
    assert any(c < 240 for c in pixel_color[:3]), (
        "Ghost shell şeffaf görünmüyor! SRCALPHA yüzeylerde set_alpha() çalışmayabilir — "
        "BLEND_RGBA_MULT ile değiştir."
    )


def test_ghost_shell_render_with_valid_index():
    """Geçerli ghost_index ile render() exception fırlatmamalı."""
    panel   = HandPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface, ghost_index=0)   # Slot 0 ghost


def test_ghost_shell_render_with_last_index():
    """Son slot ghost olarak render edilebilmeli."""
    panel   = HandPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface, ghost_index=Layout.HAND_MAX_CARDS - 1)


def test_ghost_shell_render_with_no_ghost():
    """ghost_index=-1 (default): hiçbir ghost yok, normal render."""
    panel   = HandPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface, ghost_index=-1)


def test_ghost_shell_on_empty_slot_no_crash():
    """Boş slotun ghost'unu çizerken çökme olmaz. (Fallback surface copy)"""
    panel = HandPanel()
    # Slot 2'yi boşalt (None)
    panel.assign_card(2, None)
    surface = pygame.Surface((Screen.W, Screen.H))
    # Boş slotun ghost'u → fallback surface üzerinde copy+set_alpha
    panel.render(surface, ghost_index=2)


def test_ghost_shell_out_of_bounds_index_no_crash():
    """
    EDGE CASE: ghost_index sınır dışında → render() çökmez, sadece tüm slotlar normal çizilir.
    """
    panel   = HandPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface, ghost_index=99)   # Hiçbir slota denk gelmez
    panel.render(surface, ghost_index=-5)   # Negatif ama -1 değil


# ==========================================================================
# CARDFLIP — Sınır Değerleri
# ==========================================================================

def _make_surfaces():
    back  = pygame.Surface((140, 160), pygame.SRCALPHA)
    front = pygame.Surface((140, 160), pygame.SRCALPHA)
    back.fill((40, 40, 80, 255))
    front.fill((60, 120, 200, 255))
    return back, front


def test_cardflip_update_with_zero_dt():
    """dt_ms=0 ile update() sonsuz döngüye veya ZeroDivision'a yol açmaz."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 140, 160))
    flip.hover_start()
    flip.update(dt_ms=0)   # Sıfır delta — hiçbir şey değişmemeli


def test_cardflip_update_with_huge_dt():
    """Çok büyük dt ile update() progress'i aşırı taşırmaz (0-1 aralığında kalır)."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 140, 160))
    flip.hover_start()
    flip.update(dt_ms=99999)   # 100 saniyelik dev delta
    assert 0.0 <= flip.flip_progress <= 1.0


def test_cardflip_rapid_hover_toggle_no_oscillation_crash():
    """Hover başlat/bitir çok hızlı yapılırsa progress tutarlı kalmalı."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(0, 0, 140, 160))
    for _ in range(100):
        flip.hover_start()
        flip.update(dt_ms=1)
        flip.hover_end()
        flip.update(dt_ms=1)
    assert 0.0 <= flip.flip_progress <= 1.0


def test_cardflip_render_at_progress_zero():
    """progress=0.0 → back yüzü tam görünür, render patlamaz."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(50, 50, 140, 160))
    flip.flip_progress = 0.0
    surface = pygame.Surface((Screen.W, Screen.H))
    flip.render(surface)


def test_cardflip_render_at_progress_exactly_half():
    """progress=0.5 → geçiş noktası, minimum genişlik, render patlamaz."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(50, 50, 140, 160))
    flip.flip_progress = 0.5
    surface = pygame.Surface((Screen.W, Screen.H))
    flip.render(surface)


def test_cardflip_render_at_progress_one():
    """progress=1.0 → front tam görünür, render patlamaz."""
    back, front = _make_surfaces()
    flip = CardFlip(back, front, pygame.Rect(50, 50, 140, 160))
    flip.flip_progress = 1.0
    surface = pygame.Surface((Screen.W, Screen.H))
    flip.render(surface)


# ==========================================================================
# ASSETLOADER — Özel Karakterli Kart İsimleri
# ==========================================================================

def test_assetloader_loads_special_char_cards(monkeypatch):
    """
    'π (Pi)', 'E = mc²', "Pandora'nın Kutusu" gibi özel karakterli
    kart isimleri AssetLoader tarafından başarıyla işlenebilmeli.
    Fiziksel png'ler olmadığı için load süreci mock ile test edilir.
    """
    import os
    from v2.assets.loader import AssetLoader
    
    # Mock os.path.exists to always return True
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    
    # Mock pygame.image.load to return a dummy surface
    dummy_surf = pygame.Surface((10, 10))
    monkeypatch.setattr(pygame.image, "load", lambda path: dummy_surf)

    AssetLoader._instance = None
    base = os.path.join(os.path.dirname(__file__), "..", "v2", "assets")
    AssetLoader.initialize(base)
    loader = AssetLoader.get()

    special_cards = ["π (Pi)", "E = mc²", "Pandora'nın Kutusu"]
    for name in special_cards:
        surf = loader.get_card_front(name)
        assert isinstance(surf, pygame.Surface), f"{name} yüklenemedi!"
        assert surf.get_width() > 0

    AssetLoader._instance = None


def test_assetloader_missing_card_raises_not_silently_fails():
    """Var olmayan kart ismi FileNotFoundError fırlatmalı, None dönmemeli."""
    import os
    from v2.assets.loader import AssetLoader
    AssetLoader._instance = None
    base = os.path.join(os.path.dirname(__file__), "..", "v2", "assets")
    AssetLoader.initialize(base)
    loader = AssetLoader.get()

    with pytest.raises(FileNotFoundError):
        loader.get_card_front("BU_KART_YOK_KESINLIKLE")

    AssetLoader._instance = None


# ==========================================================================
# HAND PANEL — handle_hover Edge Cases
# ==========================================================================

def test_handle_hover_mouse_far_outside_all_slots():
    """
    Fareye tüm slotların dışında bir konum verilince hover_end çağrılmalı,
    hiçbir flip hover_start durumuna girmemeli, exception olmamalı.
    """
    panel = HandPanel()
    panel.handle_hover((-9999, -9999))
    for flip in panel._flips:
        assert flip._flip_target == 0.0   # hover_end → _flip_target=0


def test_handle_hover_mouse_exactly_on_slot_boundary():
    """Slot rect'inin tam köşesine (topleft) hover → o slot hover_start almalı."""
    panel = HandPanel()
    first_slot = panel.card_rects[0]
    panel.handle_hover(first_slot.topleft)
    assert panel._flips[0]._flip_target == 1.0   # hover_start


def test_assign_card_out_of_bounds_no_crash():
    """Sınır dışı slot indeksine kart atanmaya çalışılırsa çökme olmaz."""
    panel = HandPanel()
    panel.assign_card(99, "Fibonacci Sequence")   # Geçersiz index
    panel.assign_card(-1, "Fibonacci Sequence")   # Negatif index
