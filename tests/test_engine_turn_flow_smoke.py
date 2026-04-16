import random

import pytest

from engine_core.board import combat_phase
from engine_core.card import get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.game_state import GameState


def build_seeded_game(seed=123, strategies=None):
    if strategies is None:
        strategies = ["random", "warrior", "builder", "economist"]

    rng = random.Random(seed)
    players = [Player(pid=i, strategy=strategy) for i, strategy in enumerate(strategies)]
    return Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )


def test_eliminated_players_drop_out_of_alive_filter_and_cleanup_state():
    game = build_seeded_game(seed=123)
    doomed = game.players[0]

    doomed.hp = 1
    game.players[1].hp = 200
    game.players[2].hp = 200
    game.players[3].hp = 200

    game.preparation_phase()
    game.combat_phase()
    game.preparation_phase()
    game.combat_phase()

    assert doomed.alive is False
    assert doomed.hp == 0
    assert doomed.pid not in [player.pid for player in game.alive_players()]
    assert doomed.board.grid == {}
    assert doomed.hand == []
    assert doomed.copies == {}
    assert doomed.board.has_catalyst is False


def test_alive_player_filter_changes_pair_count_on_following_turn_after_elimination():
    game = build_seeded_game(seed=123)

    game.players[0].hp = 1
    game.players[1].hp = 200
    game.players[2].hp = 200
    game.players[3].hp = 200

    game.preparation_phase()
    game.combat_phase()
    game.preparation_phase()
    game.combat_phase()

    alive_after_elimination = [player.pid for player in game.alive_players()]
    assert len(alive_after_elimination) == 3

    game.preparation_phase()
    game.combat_phase()

    assert len(game.last_combat_results) == len(game.alive_players()) // 2
    for result in game.last_combat_results:
        assert result["pid_a"] in alive_after_elimination
        assert result["pid_b"] in alive_after_elimination


def test_game_run_reaches_single_winner_with_low_hp_fixture():
    game = build_seeded_game(seed=123)

    game.players[0].hp = 1
    game.players[1].hp = 1
    game.players[2].hp = 1
    game.players[3].hp = 2

    winner = game.run()
    alive_players = game.alive_players()

    assert game.turn <= 50
    assert len(alive_players) == 1
    assert winner is alive_players[0]
    assert winner.alive is True
    assert winner.hp > 0
    assert all((not player.alive) == (player.hp == 0) for player in game.players)


@pytest.mark.xfail(reason="Phase 4 endgame bridge does not expose elimination order yet.")
def test_game_state_exposes_stable_elimination_order():
    GameState._instance = None
    state = GameState.get()
    game = build_seeded_game(seed=123)
    state.hook_engine(game)

    game.players[0].hp = 1
    game.players[1].hp = 1
    game.players[2].hp = 1
    game.players[3].hp = 2

    game.run()

    elimination_order = state.get_elimination_order()

    assert isinstance(elimination_order, list)
    assert len(elimination_order) == 3
    assert elimination_order[-1] != game.alive_players()[0].pid
