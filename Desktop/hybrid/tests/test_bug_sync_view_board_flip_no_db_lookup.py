"""
Regression test: sync_view/_add_board_flip should not do N DB lookups.

ShopScene._add_board_flip historically called EngineAdapter.get_card_info(card_name)
for every board card. PublicState already includes active_player.board_card_info,
so we should use that cached data and only fallback to EngineAdapter on cache miss.
"""

import pygame
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from v2.core.card_database import CardData
from v2.constants import CameraState
from v2.scenes.shop import ShopScene


def _make_card_data(name: str, rarity: str) -> CardData:
    return CardData(
        name=name,
        category="Science",
        rarity=rarity,
        stats={"atk": 1, "hp": 1},
        passive_type="combat",
        passive_effect="",
        synergy_group="MIND",
    )


class _DummyAssetLoader:
    def get_card_back(self, _name: str) -> pygame.Surface:
        return pygame.Surface((10, 10), pygame.SRCALPHA)

    def get_card_front(self, _name: str) -> pygame.Surface:
        return pygame.Surface((10, 10), pygame.SRCALPHA)

def test_add_board_flip_uses_cached_board_card_info_no_db_call():
    pygame.init()

    coord = (0, 0)
    card_name = "Evolved TestCard"
    cached = _make_card_data(card_name, rarity="E")

    state = SimpleNamespace(
        active_player=SimpleNamespace(
            board_cards={coord: {"name": card_name}},
            board_card_info={coord: cached},
        )
    )

    scene = SimpleNamespace(
        camera=CameraState(),
        _board_flips={},
    )

    with (
        patch("v2.scenes.shop.AssetLoader.get", return_value=_DummyAssetLoader()),
        patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as get_card_info,
    ):
        ShopScene._add_board_flip(scene, coord, state, card_data=cached)

        assert get_card_info.call_count == 0
        assert coord in scene._board_flips
        assert scene._board_flips[coord].evolved is True

