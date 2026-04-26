import pygame
import pytest

from v2.constants import Layout, Screen
from v2.core.public_state import EffectViewState, PassiveFeedEntryViewState, SynergyGroupViewState, SynergyViewState
from v2.ui.synergy_hud import SynergyHud


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def _sample_view_model() -> SynergyViewState:
    return SynergyViewState(
        groups=[
            SynergyGroupViewState(
                key="MIND",
                label="MIND",
                short_label="MIND",
                color=(100, 220, 255),
                count=3,
                bonus=11,
                next_tier_count=4,
                next_tier_bonus=16,
            ),
            SynergyGroupViewState(
                key="CONNECTION",
                label="CONNECTION",
                short_label="CONN",
                color=(255, 180, 80),
                count=2,
                bonus=5,
                next_tier_count=3,
                next_tier_bonus=9,
            ),
        ],
        total=16,
        passive_feed=[
            PassiveFeedEntryViewState(
                trigger="card_buy",
                card="Atlas",
                delta=2,
                res=0,
                color=(100, 180, 255),
                icon_key="SHOP",
            )
        ],
        active_effects=[
            EffectViewState(label="MIND 3/4", value="+16", color=(100, 220, 255), icon_key="BOLT")
        ],
    )


def test_synergyhud_initializes_panel_regions():
    hud = SynergyHud()
    assert hud.rect.x == 0
    assert hud.rect.y == Layout.SYNERGY_HUD_Y
    assert hud.rect.w == Layout.SIDEBAR_LEFT_W
    assert hasattr(hud, "groups_rect")
    assert hasattr(hud, "effects_rect")
    assert hasattr(hud, "passive_feed_rect")


def test_synergyhud_accepts_view_model_without_engine_state():
    hud = SynergyHud()
    vm = _sample_view_model()

    hud.set_view_model(vm)
    hud.update(16)

    assert hud.view_model == vm


def test_synergyhud_render_uses_view_model_text(monkeypatch):
    hud = SynergyHud()
    hud.set_view_model(_sample_view_model())
    surface = pygame.Surface((Screen.W, Screen.H))

    drawn = []
    from v2.ui import font_cache

    def capture_text(surf, text, font, color, pos, *args, **kwargs):
        drawn.append(str(text).upper())

    monkeypatch.setattr(font_cache, "render_text", capture_text)

    hud.render(surface)

    joined = " ".join(drawn)
    assert "SYNERGY" in joined
    assert "TOTAL 16" in joined
    assert "PASSIVES" in joined
    assert "MIND" in joined
    assert "ATLAS" in joined


def test_synergyhud_update_can_replace_view_model():
    hud = SynergyHud()
    first = _sample_view_model()
    second = SynergyViewState(groups=[], total=0, passive_feed=[], active_effects=[])

    hud.update(16, first)
    hud.update(16, second)

    assert hud.view_model == second


def test_synergyhud_render_full_does_not_crash():
    hud = SynergyHud()
    hud.set_view_model(_sample_view_model())
    surface = pygame.Surface((Screen.W, Screen.H))
    hud.render(surface)
