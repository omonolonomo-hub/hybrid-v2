"""
Bug 5: frozen ActivePlayerViewState — immutability exploration tests.

Expected behavior after fix (Tasks 13 / 15): mutating dict-backed fields raises TypeError.

These tests use pytest.raises(TypeError). On unfixed code mutations succeed → tests fail.
"""

from __future__ import annotations

import pytest

from v2.core.card_database import CardData
from v2.core.public_state import (
    ActivePlayerViewState,
    CombatViewState,
    HandViewState,
    PlayerHudViewState,
    PublicState,
    ShopViewState,
    SynergyViewState,
)


def _minimal_active_player(
    *,
    stats: dict | None = None,
    board_cards: dict | None = None,
    copies_by_name: dict | None = None,
    shop_card_info: dict | None = None,
    hand_card_info: dict | None = None,
    board_card_info: dict | None = None,
) -> ActivePlayerViewState:
    return ActivePlayerViewState(
        index=0,
        pid=0,
        display_name="P0",
        strategy="test",
        hp=10,
        gold=5,
        alive=True,
        turns_played=1,
        stats=dict(stats or {"bonus": 0}),
        has_catalyst=False,
        has_eclipse=False,
        board_cards=dict(board_cards or {}),
        board_rotations={},
        adjacency_pairs=(),
        eliminated_coords=(),
        shop=ShopViewState(
            slots=(None,) * 5,
            is_locked=False,
            rarity_probabilities={},
        ),
        hand=HandViewState(slots=(None,) * 6),
        hud=PlayerHudViewState(
            hp=10,
            gold=5,
            win_streak=0,
            total_pts=0,
            turn=1,
            next_gold=3,
            interest_multiplier=1.0,
        ),
        combat=CombatViewState(last_results=(), logs=(), passive_feed=()),
        synergy=SynergyViewState(groups=(), total=0, passive_feed=()),
        copies_by_name=dict(copies_by_name or {}),
        copy_milestones=(),
        prefix_bonus=0,
        shop_card_info=dict(shop_card_info or {}),
        hand_card_info=dict(hand_card_info or {}),
        board_card_info=dict(board_card_info or {}),
    )


def _minimal_public_state(active: ActivePlayerViewState) -> PublicState:
    return PublicState(
        phase="STATE_PREPARATION",
        turn=1,
        view_index=0,
        place_locked=False,
        alive_pids=(0,),
        pairings=(),
        active_player=active,
        lobby_players=(),
        endgame_stats=(),
    )


class TestBug5FrozenDataclassImmutability:
    def test_stats_assignment_raises_type_error(self):
        """Task 13.1: stats['bonus'] = 99 must not succeed silently."""
        ap = _minimal_active_player()
        with pytest.raises(TypeError):
            ap.stats["bonus"] = 99  # type: ignore[index]

    def test_board_cards_nested_assignment_raises_type_error(self):
        """Task 13.2: nested board dict mutation must not succeed."""
        coord = (0, 0)
        ap = _minimal_active_player(
            board_cards={coord: {"hp": 5, "name": "X"}},
        )
        with pytest.raises(TypeError):
            ap.board_cards[coord]["hp"] = 999  # type: ignore[index]

    def test_mutation_blocked_after_construction(self):
        """Task 13.3: in-place mutation must raise (no silent cache bypass via dict tweak)."""
        ap = _minimal_active_player(stats={"tmp": 1})
        with pytest.raises(TypeError):
            ap.stats["tmp"] = 2  # type: ignore[index]

    def test_serialization_path_does_not_allow_silent_stats_tweak(self):
        """Task 13.4: illicit mutation must raise before any snapshot semantics apply."""
        ps = _minimal_public_state(_minimal_active_player(stats={"k": 1}))
        with pytest.raises(TypeError):
            ps.active_player.stats["k"] = 2  # type: ignore[index]


class TestBug5FrozenDataclassCardInfo:
    """Cover mapping fields listed in Task 15 (shop/hand/board card info)."""

    def test_shop_card_info_row_assignment_raises(self):
        cd = CardData(
            name="C",
            category="Science",
            rarity="1",
            stats={"atk": 1, "hp": 1},
            passive_type="combat",
            passive_effect="x",
            synergy_group="MIND",
        )
        ap = _minimal_active_player(shop_card_info={0: cd})
        with pytest.raises(TypeError):
            ap.shop_card_info[1] = cd  # type: ignore[index]

    def test_hand_card_info_assignment_raises(self):
        ap = _minimal_active_player(hand_card_info={0: None})
        with pytest.raises(TypeError):
            ap.hand_card_info[0] = None  # type: ignore[index]

    def test_copies_by_name_assignment_raises(self):
        ap = _minimal_active_player(copies_by_name={"CardA": 2})
        with pytest.raises(TypeError):
            ap.copies_by_name["CardA"] = 99  # type: ignore[index]
