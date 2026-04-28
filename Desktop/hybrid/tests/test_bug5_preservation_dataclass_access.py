"""
Preservation: ActivePlayerViewState / PublicState read access, equality, hashing, serialization.

Baseline must hold after MappingProxyType immutability fix (Task 15).
"""

from __future__ import annotations

import json
from dataclasses import asdict

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


def _make_active_player() -> ActivePlayerViewState:
    return ActivePlayerViewState(
        index=0,
        pid=0,
        display_name="TestPlayer",
        strategy="aggro",
        hp=100,
        gold=10,
        alive=True,
        turns_played=3,
        stats={"bonus": 2, "tier": 1},
        has_catalyst=True,
        has_eclipse=False,
        board_cards={(0, 0): {"hp": 4, "name": "T"}},
        board_rotations={(0, 0): 0},
        adjacency_pairs=(),
        eliminated_coords=(),
        shop=ShopViewState(
            slots=(None, None, None, None, None),
            is_locked=False,
            rarity_probabilities={"1": 0.5},
        ),
        hand=HandViewState(slots=(None,) * 6),
        hud=PlayerHudViewState(
            hp=100,
            gold=10,
            win_streak=1,
            total_pts=5,
            turn=3,
            next_gold=4,
            interest_multiplier=1.25,
        ),
        combat=CombatViewState(last_results=(), logs=(), passive_feed=()),
        synergy=SynergyViewState(groups=(), total=0, passive_feed=()),
        copies_by_name={"Zeus": 1, "Tesla": 2},
        copy_milestones=(),
        prefix_bonus=0,
        shop_card_info={
            0: CardData(
                name="Zeus",
                category="Mythology & Gods",
                rarity="2",
                stats={"atk": 2, "hp": 3},
                passive_type="combat",
                passive_effect="z",
                synergy_group="EXISTENCE",
            )
        },
        hand_card_info={},
        board_card_info={},
    )


def _make_public_state() -> PublicState:
    return PublicState(
        phase="STATE_PREPARATION",
        turn=3,
        view_index=0,
        place_locked=False,
        alive_pids=(0, 1),
        pairings=((0, 1),),
        active_player=_make_active_player(),
        lobby_players=({"name": "A"},),
        endgame_stats=(),
    )


class TestBug5PreservationReadAccess:
    def test_read_stats_board_copies(self):
        ap = _make_active_player()
        assert ap.stats["bonus"] == 2
        assert ap.stats["tier"] == 1
        assert ap.board_cards[(0, 0)]["hp"] == 4
        assert ap.copies_by_name["Zeus"] == 1
        assert ap.copies_by_name["Tesla"] == 2
        assert ap.shop_card_info[0] is not None
        assert ap.shop_card_info[0].name == "Zeus"

    def test_get_card_info_shop_hand_board(self):
        ap = _make_active_player()
        assert ap.get_card_info("shop", 0) is not None
        assert ap.get_card_info("hand", 0) is None
        assert ap.get_card_info("board", (0, 0)) is None


class TestBug5PreservationEquality:
    def test_active_player_equality(self):
        a = _make_active_player()
        b = _make_active_player()
        assert a == b

    def test_public_state_equality(self):
        assert _make_public_state() == _make_public_state()


class TestBug5PreservationHashing:
    def test_active_player_not_hashable_with_mapping_fields(self):
        ap = _make_active_player()
        with pytest.raises(TypeError):
            hash(ap)


class TestBug5PreservationSerialization:
    def test_asdict_roundtrip_structure(self):
        ps = _make_public_state()
        d = asdict(ps)
        assert d["phase"] == "STATE_PREPARATION"
        assert d["turn"] == 3
        assert d["active_player"]["stats"]["bonus"] == 2
        assert d["active_player"]["board_cards"][(0, 0)]["hp"] == 4

    def test_json_after_carddata_converted(self):
        """CardData and tuple keys are not JSON-ready; normalize for smoke encode."""
        ps = _make_public_state()
        d = asdict(ps)
        ap = d["active_player"]
        ap["shop_card_info"] = {str(k): (v.name if v else None) for k, v in ap["shop_card_info"].items()}
        ap["board_cards"] = {str(k): v for k, v in ap["board_cards"].items()}
        ap["board_rotations"] = {str(k): v for k, v in ap["board_rotations"].items()}
        blob = json.dumps(d)
        assert "STATE_PREPARATION" in blob
        assert "bonus" in blob
