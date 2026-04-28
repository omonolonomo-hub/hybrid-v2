import os
import random

import pytest

from engine_core.board import combat_phase, calculate_group_synergy_bonus
from engine_core.card import Card, get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.card_database import CardDatabase
from v2.core.game_state import GameState
from v2.core.synergy_calculator import SynergyCalculator


JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "assets", "data", "cards.json"
)


def _build_seeded_game(strategies=None, seed=321):
    if strategies is None:
        strategies = ["random", "builder", "economist", "warrior"]
    rng = random.Random(seed)
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    return Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )


def _board_snapshot(board) -> dict:
    out = {}
    for coord, card in board.grid.items():
        out[coord] = {
            "name": card.name,
            "stats": dict(card.stats),
            "rotation": getattr(card, "rotation", 0),
        }
    return out


def _make_real_card(name: str) -> Card:
    db_card = CardDatabase.get().lookup(name)
    assert db_card is not None, f"Card not found in DB: {name}"
    return Card(
        name=db_card.name,
        category=db_card.category,
        rarity=db_card.rarity,
        stats=dict(db_card.stats),
    )


@pytest.fixture(autouse=True)
def _reset_singletons():
    CardDatabase.reset()
    yield
    CardDatabase.reset()


def test_c1_direct_board_remove_invalidation_updates_public_state():
    state = GameState()
    game = _build_seeded_game()
    state.hook_engine(game)

    p0 = game.players[0]
    card = p0.hand[0]
    assert card is not None
    p0.hand[0] = None
    p0.board.place((0, 0), card)
    assert (0, 0) in state.get_public_state().active_player.board_cards

    p0.board.remove((0, 0))
    refreshed = state.get_public_state()
    assert (0, 0) not in refreshed.active_player.board_cards


@pytest.mark.parametrize(
    "coords,rotations",
    [
        ([(0, 0), (0, 1)], [0, 0]),
        ([(0, 0), (1, 0), (0, 1)], [1, 2, 0]),
        ([(0, 0), (1, 0), (0, 1), (-1, 1)], [0, 3, 1, 2]),
    ],
)
def test_c2_engine_ui_synergy_parity_on_multiple_layouts(coords, rotations):
    CardDatabase.initialize(JSON_PATH)
    pool = get_card_pool()
    assert len(pool) >= len(coords)
    chosen = [pool[i].name for i in range(len(coords))]

    from engine_core.board import Board

    board = Board()
    for idx, coord in enumerate(coords):
        card = _make_real_card(chosen[idx])
        card.rotate(rotations[idx])
        board.place(coord, card)

    engine_score = calculate_group_synergy_bonus(board)
    calc = SynergyCalculator()
    ui_score = calc.compute(_board_snapshot(board), CardDatabase.get()).total

    assert ui_score == engine_score


def test_c4_legacy_assignment_and_income_reset_keep_single_source_sync():
    CardDatabase.initialize(JSON_PATH)
    p = Player(pid=0, strategy="random")
    p.gold = 10
    p.cards_bought_this_turn = 7
    assert "cards_bought_this_turn" not in p.stats

    p.buy_card(get_card_pool()[0])
    assert p.cards_bought_this_turn == 8
    assert "cards_bought_this_turn" not in p.stats

    p.income()
    assert p.cards_bought_this_turn == 0
    assert "cards_bought_this_turn" not in p.stats
