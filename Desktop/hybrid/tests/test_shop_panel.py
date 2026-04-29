import pygame
import pytest

from v2.constants import Layout, Screen
from v2.core.public_state import ShopViewState
from v2.ui.shop_panel import ShopPanel, ShopPanelAction


@pytest.fixture(autouse=True)
def init_pygame():
    # pygame.init() is handled by session-scoped conftest.py fixture
    pygame.font.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    from v2.ui import font_cache
    font_cache.clear_cache()
    # Don't call pygame.font.quit() or pygame.quit() - let session fixture handle it


def test_shoppanel_initializes_with_correct_dimensions():
    panel = ShopPanel()
    assert panel.rect.y == Layout.SHOP_PANEL_Y
    assert panel.rect.h == Layout.SHOP_PANEL_H


def test_shoppanel_render_method_exists():
    panel = ShopPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)


def test_shoppanel_render_produces_interactive_regions(monkeypatch):
    panel = ShopPanel()
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn_texts = []
    from v2.ui import font_cache

    def mock_render_text(surf, text, font, color, pos, *args, **kwargs):
        drawn_texts.append(str(text).upper())

    monkeypatch.setattr(font_cache, "render_text", mock_render_text)

    panel.render(surface)

    joined_text = " ".join(drawn_texts)

    assert "REROLL" in joined_text
    assert "LOCK" in joined_text or "LOCKED" in joined_text or "\U0001f512" in joined_text
    assert "TIER" in joined_text or "LEVEL" in joined_text or "DROP:" in joined_text
    assert len(panel.card_rects) == 5


def test_shoppanel_render_is_state_free():
    panel = ShopPanel()
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)
    assert panel._card_names == [None] * Layout.SHOP_SLOTS


def test_shoppanel_render_draws_visual_rects():
    panel = ShopPanel()
    assert hasattr(panel, "_flips")
    assert len(panel._flips) == Layout.SHOP_SLOTS
    surface = pygame.Surface((Screen.W, Screen.H))
    panel.render(surface)


def test_shoppanel_parses_reroll_click_to_intent():
    panel = ShopPanel()
    cx, cy = panel.reroll_rect.center
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))

    action = panel.handle_event(event)

    assert action == ShopPanelAction("reroll")


def test_shoppanel_ready_intent_only_exists_in_preparation():
    panel = ShopPanel()
    cx, cy = panel.ready_rect.center
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))

    assert panel.handle_event(event) == ShopPanelAction("ready")

    panel.sync(ShopViewState(slots=[None] * Layout.SHOP_SLOTS, is_locked=False, rarity_probabilities={"1": 100.0}), gold=10, phase="STATE_COMBAT")
    assert panel.handle_event(event) is None


def test_shoppanel_parses_lock_click_to_intent():
    panel = ShopPanel()
    cx, cy = panel.lock_rect.center
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))

    action = panel.handle_event(event)

    assert action == ShopPanelAction("lock")


def test_shoppanel_parses_card_slot_click_to_buy_intent():
    panel = ShopPanel()
    panel.assign_shop(["Atlas", None, "Mona Lisa", None, None])
    cx, cy = panel.card_rects[2].center
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy))

    action = panel.handle_event(event)

    assert action == ShopPanelAction("buy", slot_index=2, card_name="Mona Lisa")


def test_shoppanel_ignores_clicks_in_empty_gaps():
    panel = ShopPanel()
    gap_x = panel.card_rects[0].right + (Layout.SHOP_CARD_GAP // 2)
    gap_y = panel.card_rects[0].centery
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(gap_x, gap_y))

    assert panel.handle_event(event) is None


def test_shoppanel_ignores_right_click_and_scroll():
    panel = ShopPanel()
    cx, cy = panel.card_rects[1].center

    right_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(cx, cy))
    scroll_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=4, pos=(cx, cy))

    assert panel.handle_event(right_click) is None
    assert panel.handle_event(scroll_click) is None


def test_shoppanel_out_of_bounds_rendering_safety():
    panel = ShopPanel()
    ghost_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(-9999, -9999))
    assert panel.handle_event(ghost_event) is None
