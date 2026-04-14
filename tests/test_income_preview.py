"""
TDD — IncomePreview
Phase 3 item 15: GDD §13.1 gelir formülü doğrulaması.
"""
import pytest
import pygame
from v2.ui.income_preview import IncomePreview
from v2.constants import Layout


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    from v2.ui import font_cache
    font_cache.clear_cache()
    pygame.quit()


# ── Formül birim testleri (pygame gerektirmez) ─────────────────────────────

def test_base_income_is_always_3():
    t = IncomePreview._compute(gold=0, hp=150, win_streak=0)
    assert t["base"] == 3

def test_interest_zero_below_10_gold():
    t = IncomePreview._compute(gold=9, hp=150, win_streak=0)
    assert t["interest"] == 0

def test_interest_1_at_10_gold():
    t = IncomePreview._compute(gold=10, hp=150, win_streak=0)
    assert t["interest"] == 1

def test_interest_capped_at_5():
    t = IncomePreview._compute(gold=100, hp=150, win_streak=0)
    assert t["interest"] == 5

def test_streak_bonus_zero_for_no_streak():
    t = IncomePreview._compute(gold=0, hp=150, win_streak=0)
    assert t["streak"] == 0

def test_streak_bonus_1_for_streak_3():
    t = IncomePreview._compute(gold=0, hp=150, win_streak=3)
    assert t["streak"] == 1

def test_streak_bonus_2_for_streak_6():
    t = IncomePreview._compute(gold=0, hp=150, win_streak=6)
    assert t["streak"] == 2

def test_negative_streak_gives_zero_bonus():
    t = IncomePreview._compute(gold=0, hp=150, win_streak=-4)
    assert t["streak"] == 0

def test_bailout_zero_above_75hp():
    t = IncomePreview._compute(gold=0, hp=100, win_streak=0)
    assert t["bailout"] == 0

def test_bailout_1_below_75hp():
    t = IncomePreview._compute(gold=0, hp=74, win_streak=0)
    assert t["bailout"] == 1

def test_bailout_3_below_45hp():
    t = IncomePreview._compute(gold=0, hp=44, win_streak=0)
    assert t["bailout"] == 3

def test_total_is_sum_of_all_terms():
    t = IncomePreview._compute(gold=20, hp=74, win_streak=3)
    assert t["total"] == t["base"] + t["interest"] + t["streak"] + t["bailout"]

def test_economist_multiplier_boosts_interest():
    normal    = IncomePreview._compute(gold=30, hp=150, win_streak=0, interest_multiplier=1.0)
    economist = IncomePreview._compute(gold=30, hp=150, win_streak=0, interest_multiplier=1.5)
    assert economist["interest"] >= normal["interest"]

def test_economist_interest_capped_at_8():
    t = IncomePreview._compute(gold=200, hp=150, win_streak=0, interest_multiplier=1.5)
    assert t["interest"] <= 8


# ── Render testi ───────────────────────────────────────────────────────────

def test_income_preview_renders_without_crash():
    """Render çağrısı istisna fırlatmamalı."""
    preview = IncomePreview()
    surface = pygame.Surface((1920, 1080))
    preview.render(surface)   # crash yoksa geçer

def test_income_preview_rect_inside_screen():
    preview = IncomePreview()
    assert preview.rect.x >= Layout.CENTER_ORIGIN_X
    assert preview.rect.y >= Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H
