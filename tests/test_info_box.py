import pygame
import pytest

from v2.core.card_database import CardData
from v2.ui import font_cache
from v2.ui.info_box import InfoBox, _stat_color, _wrap_text


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    yield
    font_cache.clear_cache()
    pygame.font.quit()
    pygame.quit()


def make_card(*, synergy_group: str = "MIND") -> CardData:
    return CardData(
        name="Info Test",
        category="Science",
        rarity="3",
        stats={
            "Meaning": 8,
            "Secret": 6,
            "Intelligence": 4,
            "Trace": 2,
            "Power": 1,
            "Size": 0,
        },
        passive_type="combat",
        passive_effect="Gain bonus combat points when this card wins a clash.",
        synergy_group=synergy_group,
    )


def test_wrap_text_splits_long_text_to_fit_max_width():
    font = font_cache.regular(12)
    lines = _wrap_text(
        "This sentence should wrap into multiple lines inside the info box.",
        font,
        120,
    )

    assert len(lines) >= 2
    assert all(font.size(line)[0] <= 120 for line in lines)


def test_infobox_placeholder_render_changes_surface_pixels():
    box = InfoBox(pygame.Rect(20, 20, 280, 180))
    surface = pygame.Surface((400, 260))
    surface.fill((255, 0, 255))

    box.set_card(None)
    box.render(surface)

    assert surface.get_at((box.rect.centerx, box.rect.centery))[:3] != (255, 0, 255)


def test_infobox_card_render_differs_from_placeholder_output():
    box = InfoBox(pygame.Rect(20, 20, 280, 180))
    placeholder_surface = pygame.Surface((400, 260))
    card_surface = pygame.Surface((400, 260))
    placeholder_surface.fill((0, 0, 0))
    card_surface.fill((0, 0, 0))

    box.set_card(None)
    box.render(placeholder_surface)
    box.set_card(make_card())
    box.render(card_surface)

    assert pygame.image.tobytes(placeholder_surface, "RGBA") != pygame.image.tobytes(card_surface, "RGBA")


def test_infobox_render_handles_independent_card_without_synergy_group():
    box = InfoBox(pygame.Rect(20, 20, 280, 180))
    surface = pygame.Surface((400, 260))

    box.set_card(make_card(synergy_group=""))
    box.render(surface)


def test_stat_color_varies_by_group_and_value_threshold():
    assert _stat_color("Meaning", 8) != _stat_color("Meaning", 4)
    assert _stat_color("Meaning", 6) != _stat_color("Power", 6)
    assert _stat_color("Spread", 8) != _stat_color("Power", 8)
