"""
TDD — FloatingText & FloatingTextManager
Phase 3b item 18: 3-faz animasyon (RISE→HOLD→FADE) + vagon kuyruğu kontratları.
"""
import pytest
import pygame
from v2.ui.widgets import FloatingText, FloatingTextManager
from v2.constants import Timing, Screen


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    from v2.ui import font_cache
    font_cache.clear_cache()
    pygame.quit()


# ══════════════════════════════════════════════════════════════════════════
#  FloatingText — 3-faz birim testleri
# ══════════════════════════════════════════════════════════════════════════

def _make_ft(**kw) -> FloatingText:
    """Kısa yardımcı — varsayılan parametreli FloatingText."""
    return FloatingText("test", 100, 200, (255, 255, 255), **kw)


def test_floatingtext_starts_alive():
    ft = _make_ft()
    assert ft.update(0) is True


def test_floatingtext_dies_after_total_lifetime():
    ft = _make_ft()
    alive = ft.update(ft._total_lifetime + 1)
    assert alive is False


def test_floatingtext_alive_before_total_lifetime():
    ft = _make_ft()
    alive = ft.update(ft._total_lifetime - 1)
    assert alive is True


# ── RISE fazı ─────────────────────────────────────────────────────────────

def test_floatingtext_rises_during_rise_phase():
    ft = _make_ft()
    y_before = ft.y
    ft.update(ft._rise_dur * 0.5)
    assert ft.y < y_before, "RISE fazında y azalmalı (yukarı gitmeli)"


def test_floatingtext_reaches_target_y_after_rise():
    ft = _make_ft()
    ft.update(ft._rise_dur + 1)
    assert abs(ft.y - ft._target_y) < 2, "RISE bittikten sonra target_y'de olmalı"


def test_floatingtext_does_not_overshoot_target():
    ft = _make_ft()
    for _ in range(100):
        ft.update(20)
    assert ft.y >= ft._target_y - 1, "target_y'nin üzerine çıkmamalı"


# ── HOLD fazı ─────────────────────────────────────────────────────────────

def test_floatingtext_stays_at_target_during_hold():
    ft = _make_ft()
    ft.update(ft._rise_dur + 1)          # HOLD'a gir
    y_at_hold = ft.y
    ft.update(ft._hold_ms * 0.5)         # HOLD ortası
    assert abs(ft.y - y_at_hold) < 2, "HOLD fazında y değişmemeli"


def test_floatingtext_full_alpha_during_hold():
    ft = _make_ft()
    ft.update(ft._rise_dur + 1)          # RISE bitti
    assert ft.alpha == 255, "HOLD fazı başında alfa tam olmalı"
    ft.update(ft._hold_ms * 0.5)
    assert ft.alpha == 255, "HOLD ortasında alfa hâlâ tam olmalı"


def test_floatingtext_full_alpha_during_rise():
    ft = _make_ft()
    ft.update(ft._rise_dur * 0.5)
    assert ft.alpha == 255, "RISE fazında alfa tam olmalı"


# ── FADE fazı ─────────────────────────────────────────────────────────────

def test_floatingtext_alpha_starts_decreasing_after_hold():
    ft = _make_ft()
    ft.update(ft._rise_dur + ft._hold_ms + 1)   # FADE'e gir
    assert ft.alpha < 255, "FADE fazında alfa azalmış olmalı"
    assert ft.alpha > 0,   "FADE henüz başlamışsa alfa > 0 olmalı"


def test_floatingtext_alpha_zero_at_end():
    ft = _make_ft()
    ft.update(ft._total_lifetime + 10)
    assert ft.alpha == 0


def test_floatingtext_alpha_monotonically_decreasing_in_fade():
    ft = _make_ft()
    ft.update(ft._rise_dur + ft._hold_ms)   # FADE başına git
    alphas = []
    step = ft._fade_ms / 5
    for _ in range(6):
        ft.update(step)
        alphas.append(ft.alpha)
    for i in range(len(alphas) - 1):
        assert alphas[i] >= alphas[i + 1], f"Alfa monoton azalmalı: {alphas}"


def test_floatingtext_stays_at_target_during_fade():
    ft = _make_ft()
    ft.update(ft._rise_dur + ft._hold_ms + 1)
    y_fade_start = ft.y
    ft.update(ft._fade_ms * 0.5)
    assert abs(ft.y - y_fade_start) < 2, "FADE fazında y değişmemeli"


# ── Render testleri ────────────────────────────────────────────────────────

def test_floatingtext_render_does_not_crash():
    ft = FloatingText("★ +2 STATS", 400, 300, (255, 210, 60), font_size=14)
    surface = pygame.Surface((Screen.W, Screen.H))
    ft.render(surface)


def test_floatingtext_render_dead_does_not_crash():
    ft = _make_ft()
    ft.update(ft._total_lifetime + 100)
    surface = pygame.Surface((Screen.W, Screen.H))
    ft.render(surface)   # alpha==0, erken dönmeli


def test_floatingtext_font_types_do_not_crash():
    surface = pygame.Surface((Screen.W, Screen.H))
    for ftype in ("bold", "mono", "regular"):
        ft = FloatingText("test", 400, 300, (200, 200, 200), font_type=ftype)
        ft.render(surface)


# ── Özel parametreler ─────────────────────────────────────────────────────

def test_floatingtext_custom_max_rise_px():
    ft = FloatingText("x", 100, 300, (255, 255, 255), max_rise_px=50)
    assert ft._target_y == pytest.approx(300 - 50)


def test_floatingtext_custom_rise_speed():
    ft_slow = FloatingText("x", 100, 300, (255, 255, 255), rise_px_s=20)
    ft_fast = FloatingText("x", 100, 300, (255, 255, 255), rise_px_s=200)
    ft_slow.update(200)
    ft_fast.update(200)
    assert ft_fast.y < ft_slow.y, "Hızlı olan daha yüksekte olmalı"


def test_floatingtext_total_lifetime_formula():
    ft = FloatingText("x", 100, 200, (255, 255, 255),
                      max_rise_px=80, rise_px_s=80,
                      hold_ms=650, fade_ms=550)
    # rise_dur = 80/80*1000 = 1000ms
    assert ft._rise_dur    == pytest.approx(1000.0, abs=1)
    assert ft._hold_ms     == pytest.approx(650.0)
    assert ft._fade_ms     == pytest.approx(550.0)
    assert ft._total_lifetime == pytest.approx(2200.0, abs=1)


# ══════════════════════════════════════════════════════════════════════════
#  FloatingTextManager — birim testleri
# ══════════════════════════════════════════════════════════════════════════

def test_manager_starts_empty():
    mgr = FloatingTextManager()
    assert mgr.active_count == 0


def test_manager_spawn_no_key_immediate():
    """coord_key=None → metin hemen aktif olur, kuyruk yok."""
    mgr = FloatingTextManager()
    mgr.spawn("test", 100, 200, (255, 255, 255))
    assert len(mgr._active) == 1
    assert len(mgr._pending) == 0


def test_manager_spawn_with_key_goes_to_queue():
    """coord_key verilirse kuyrukta bekler, henüz aktif değil."""
    mgr = FloatingTextManager()
    mgr.spawn("test", 100, 200, (255, 255, 255), coord_key=("k",))
    assert len(mgr._active) == 0
    assert len(mgr._pending[("k",)]) == 1


def test_manager_first_queued_item_has_zero_delay():
    """Kuyruktaki ilk metin 0 ms gecikmeyle hemen tetiklenmeli."""
    mgr = FloatingTextManager()
    mgr.spawn("A", 100, 200, (255, 255, 255), coord_key=("k",))
    assert mgr._pending[("k",)][0][0] == pytest.approx(0.0)


def test_manager_second_queued_item_has_wagon_delay():
    """İkinci metin WAGON_DELAY_MS kadar gecikmeli başlamalı."""
    mgr = FloatingTextManager()
    key = ("k",)
    mgr.spawn("A", 100, 200, (255, 255, 255), coord_key=key)
    mgr.spawn("B", 100, 200, (255, 255, 255), coord_key=key)
    delays = [item[0] for item in mgr._pending[key]]
    assert delays[0] == pytest.approx(0.0)
    assert delays[1] == pytest.approx(float(FloatingTextManager._WAGON_DELAY_MS))


def test_manager_third_queued_item_double_delay():
    mgr = FloatingTextManager()
    key = ("k",)
    for _ in range(3):
        mgr.spawn("x", 100, 200, (255, 255, 255), coord_key=key)
    delays = [item[0] for item in mgr._pending[key]]
    wd = FloatingTextManager._WAGON_DELAY_MS
    assert delays[0] == pytest.approx(0.0)
    assert delays[1] == pytest.approx(float(wd))
    assert delays[2] == pytest.approx(float(wd * 2))


def test_manager_zero_delay_item_activates_on_first_update():
    """0 ms gecikmeli item ilk update(0)'da aktif olmalı."""
    mgr = FloatingTextManager()
    mgr.spawn("A", 100, 200, (255, 255, 255), coord_key=("k",))
    mgr.update(0)
    assert len(mgr._active) == 1


def test_manager_wagon_activates_sequentially():
    """3 vagon: 0ms, DELAY, 2×DELAY gecikmeli aktivasyon."""
    mgr = FloatingTextManager()
    wd  = FloatingTextManager._WAGON_DELAY_MS
    key = ("k",)
    for _ in range(3):
        mgr.spawn("x", 100, 200, (255, 255, 255), coord_key=key)

    mgr.update(1)               # ilk item aktif (delay=0)
    assert len(mgr._active) == 1

    mgr.update(wd + 1)          # ikinci item aktif
    assert len(mgr._active) == 2

    mgr.update(wd + 1)          # üçüncü item aktif
    assert len(mgr._active) == 3


def test_manager_update_removes_dead():
    mgr = FloatingTextManager()
    ft  = FloatingText("x", 100, 200, (255, 255, 255))
    total = ft._total_lifetime
    mgr.spawn("x", 100, 200, (255, 255, 255))
    mgr.update(total + 50)
    assert len(mgr._active) == 0


def test_manager_clear():
    mgr = FloatingTextManager()
    for _ in range(3):
        mgr.spawn("x", 100, 200, (255, 255, 255))
    mgr.clear()
    assert mgr.active_count == 0
    assert len(mgr._pending) == 0


def test_manager_active_count_includes_pending():
    """active_count = aktif + kuyrukta bekleyen."""
    mgr = FloatingTextManager()
    key = ("k",)
    mgr.spawn("A", 100, 200, (255, 255, 255), coord_key=key)  # kuyrukta
    mgr.spawn("B", 100, 200, (255, 255, 255))                 # hemen aktif
    assert mgr.active_count == 2


def test_manager_render_does_not_crash():
    mgr = FloatingTextManager()
    mgr.spawn("★ +2 STATS", 400, 300, (255, 210, 60), font_size=14)
    mgr.spawn("-2G",         300, 200, (210, 70,  55), font_size=13)
    surface = pygame.Surface((Screen.W, Screen.H))
    mgr.render(surface)


def test_manager_render_empty_does_not_crash():
    mgr = FloatingTextManager()
    surface = pygame.Surface((Screen.W, Screen.H))
    mgr.render(surface)


def test_manager_different_keys_independent_queues():
    """Farklı coord_key'ler birbirini etkilemez."""
    mgr = FloatingTextManager()
    mgr.spawn("A", 100, 200, (255, 255, 255), coord_key=("k1",))
    mgr.spawn("B", 100, 200, (255, 255, 255), coord_key=("k2",))
    # Her iki key'in ilk elemanı da 0 ms gecikmeli olmalı
    assert mgr._pending[("k1",)][0][0] == pytest.approx(0.0)
    assert mgr._pending[("k2",)][0][0] == pytest.approx(0.0)


# ══════════════════════════════════════════════════════════════════════════
#  Entegrasyon: gerçek trigger metinleri render edilebilir mi?
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("text,color,size", [
    ("★ +2 STATS",      (255, 210,  60), 15),
    ("★★ +3 STATS",     (255, 160,  30), 16),
    ("◈ +1G",           ( 70, 210, 130), 13),
    ("-2G",             (210,  70,  55), 13),
    ("MIND +3pts ▲",    ( 80, 140, 255), 13),
    ("★ Kopya 2/3",     (255, 210,  60), 14),
    ("★★ Kopya 3/3",    (255, 160,  30), 16),
    ("⬡ YERLEŞTİ",      ( 80, 140, 255), 14),
])
def test_all_trigger_texts_render_without_crash(text, color, size):
    """Tanımlı tüm tetikleyici metinleri crash olmadan render edilebilmeli."""
    mgr     = FloatingTextManager()
    surface = pygame.Surface((Screen.W, Screen.H))
    mgr.spawn(text, 400, 300, color, font_size=size)
    mgr.render(surface)


def test_wagon_visual_sequence_full():
    """
    3 tier milestone birleşik test:
    MIND, CONN, EXST aynı anda tetiklenir —
    vagon gecikmesiyle birer birer aktive olur,
    her biri RISE→HOLD→FADE tamamlar.
    """
    from v2.constants import Colors
    mgr = FloatingTextManager()
    wd  = FloatingTextManager._WAGON_DELAY_MS
    key = ("board_center",)

    mgr.spawn("MIND +3pts ▲",  500, 400, Colors.MIND,       font_size=13, coord_key=key)
    mgr.spawn("CONN +7pts ▲",  500, 400, Colors.CONNECTION, font_size=13, coord_key=key)
    mgr.spawn("EXST +11pts ▲", 500, 400, Colors.EXISTENCE,  font_size=13, coord_key=key)

    # t=0: henüz hiçbiri aktif değil
    assert len(mgr._active) == 0

    mgr.update(1)               # ilk vagon aktif
    assert len(mgr._active) == 1

    mgr.update(wd + 1)          # ikinci vagon
    assert len(mgr._active) == 2

    mgr.update(wd + 1)          # üçüncü vagon
    assert len(mgr._active) == 3

    # Render crash yok
    surface = pygame.Surface((Screen.W, Screen.H))
    mgr.render(surface)
