import os

import pytest

from engine_core.board import Board, calculate_group_synergy_bonus
from engine_core.card import Card, get_card_pool
from v2.core.card_database import CardDatabase
from v2.core.synergy_calculator import SynergyCalculator


JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "assets", "data", "cards.json"
)


@pytest.fixture(autouse=True)
def reset_card_db():
    CardDatabase.reset()
    yield
    CardDatabase.reset()


def _board_cards_snapshot(board: Board) -> dict:
    snapshot = {}
    for coord, card in board.grid.items():
        snapshot[coord] = {
            "name": card.name,
            "stats": dict(card.stats),
            "rotation": getattr(card, "rotation", 0),
        }
    return snapshot


def _make_real_card(name: str) -> Card:
    db_card = CardDatabase.get().lookup(name)
    assert db_card is not None, f"Card not found in DB: {name}"
    return Card(
        name=db_card.name,
        category=db_card.category,
        rarity=db_card.rarity,
        stats=dict(db_card.stats),
    )


def test_engine_and_ui_synergy_scores_match_for_same_board_state():
    """
    Single-source contract: engine-side synergy score and UI-side
    SynergyCalculator total score must stay equivalent for the same board.
    """
    CardDatabase.initialize(JSON_PATH)

    pool = get_card_pool()
    assert len(pool) >= 3
    names = [pool[0].name, pool[1].name, pool[2].name]

    board = Board()
    c0 = _make_real_card(names[0])
    c1 = _make_real_card(names[1])
    c2 = _make_real_card(names[2])

    # Build a connected shape to exercise cluster + edge-match scoring.
    board.place((0, 0), c0)
    board.place((0, 1), c1)
    board.place((1, 0), c2)

    c1.rotate(1)
    c2.rotate(2)

    engine_score = calculate_group_synergy_bonus(board)
    calc = SynergyCalculator()
    ui_score = calc.compute(
        _board_cards_snapshot(board), CardDatabase.get()
    ).total

    assert ui_score == engine_score
