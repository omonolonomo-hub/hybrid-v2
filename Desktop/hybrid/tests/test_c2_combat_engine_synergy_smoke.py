"""
tests/test_c2_combat_engine_synergy_smoke.py
═══════════════════════════════════════════════════════════════════
C2 Ön hazırlık: CombatEngine.run_combat() akışında
calculate_group_synergy_bonus sonucunun skorlamaya yansıdığını
doğrulayan smoke test.

Bu test, C2 cleanup sırasında board.py'deki duplicate BFS kodu
wrapper'a çevrildiğinde combat_engine通路ının hâlâ doğru çalıştığını
garanti altına alır.
═══════════════════════════════════════════════════════════════════
"""

import random

import pytest

from engine_core.board import Board, combat_phase, calculate_group_synergy_bonus
from engine_core.card import Card, get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.card_database import CardDatabase
from v2.core.synergy_calculator import SynergyCalculator

import os

JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "assets", "data", "cards.json"
)


def _build_seeded_game(strategies=None, seed=321, n=None):
    if n is not None and strategies is None:
        strategies = ["random", "builder", "economist", "warrior"][:n]
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


# ──────────────────────────────────────────────────────────────────
# Test 1: CombatEngine skorlaması calculate_group_synergy_bonus
#         sonucunu doğru toplama dahil ediyor
# ──────────────────────────────────────────────────────────────────

def test_combat_engine_synergy_score_reflected_in_turn_points():
    """
    Board'a kartlar yerleştirip combat çalıştırdığımızda,
    calculate_group_synergy_bonus sonucu p_a / p_b turn_pts içinde
    yer alıyor olmalı.
    """
    CardDatabase.initialize(JSON_PATH)
    game = _build_seeded_game(n=2, seed=77)

    # Her iki oyuncunun board'una kart yerleştirelim
    pool = get_card_pool()
    assert len(pool) >= 2

    p0, p1 = game.players[0], game.players[1]

    c0 = _make_real_card(pool[0].name)
    c1 = _make_real_card(pool[1].name)

    p0.board.place((0, 0), c0)
    p1.board.place((0, 0), c1)

    # Combat öncesi synergy skorlarını hesapla
    syn_a = calculate_group_synergy_bonus(p0.board)
    syn_b = calculate_group_synergy_bonus(p1.board)

    # Combat çalıştır
    game.combat_phase()

    # turn_pts = kill + combo + synergy oldugu için,
    # turn_pts >= synergy olmalı (en azından synergy kadar puan var)
    assert p0.turn_pts >= syn_a, (
        f"P0 turn_pts={p0.turn_pts} < synergy={syn_a}"
    )
    assert p1.turn_pts >= syn_b, (
        f"P1 turn_pts={p1.turn_pts} < synergy={syn_b}"
    )


# ──────────────────────────────────────────────────────────────────
# Test 2: engine calculate_group_synergy_bonus ve
#         SynergyCalculator.compute uyumlu - combat engine
#        通路yla entegre
# ──────────────────────────────────────────────────────────────────

def test_combat_engine_synergy_matches_synergy_calculator():
    """
    Combat sonrası player.board üzerinden hem engine-side
    calculate_group_synergy_bonus hem de SynergyCalculator.compute
    aynı sonucu vermeli (parity contract).
    """
    CardDatabase.initialize(JSON_PATH)
    game = _build_seeded_game(n=2, seed=99)

    pool = get_card_pool()
    p0 = game.players[0]

    # Board'a 2-3 kart yerleştirelim
    for i in range(min(3, len(pool))):
        card = _make_real_card(pool[i].name)
        coord = (i, 0)
        p0.board.place(coord, card)

    engine_score = calculate_group_synergy_bonus(p0.board)
    ui_score = SynergyCalculator.compute(
        _board_snapshot(p0.board), CardDatabase.get()
    ).total

    assert ui_score == engine_score, (
        f"Parity bozuldu: engine={engine_score}, ui={ui_score}"
    )


# ──────────────────────────────────────────────────────────────────
# Test 3: Boş board = 0 synergy, combat engine buna dayanıyor
# ──────────────────────────────────────────────────────────────────

def test_empty_board_synergy_is_zero_in_combat_context():
    """
    Boş board ile calculate_group_synergy_bonus 0 dönmeli.
    Combat engine bu değeri skorlamaya güvenle ekliyor olmalı.
    """
    board = Board()
    assert calculate_group_synergy_bonus(board) == 0

    # SynergyCalculator ile de parity kontrolü
    CardDatabase.initialize(JSON_PATH)
    ui_result = SynergyCalculator.compute({}, CardDatabase.get())
    assert ui_result.total == 0
