import random

from engine_core.board import calculate_damage, combat_phase
from engine_core.card import get_card_pool
from engine_core.constants import KILL_PTS
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player


EXPECTED_COMBAT_RESULT_KEYS = {
    "pid_a",
    "pid_b",
    "pts_a",
    "pts_b",
    "kill_a",
    "kill_b",
    "combo_a",
    "combo_b",
    "synergy_a",
    "synergy_b",
    "draws",
    "winner_pid",
    "dmg",
    "hp_before_a",
    "hp_before_b",
    "hp_after_a",
    "hp_after_b",
}


def build_seeded_game(seed=123, strategies=None):
    if strategies is None:
        strategies = [
            "random",
            "warrior",
            "builder",
            "economist",
            "adaptive",
            "aggressive",
        ]

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


def advance_one_turn(game):
    game.preparation_phase()
    expected_pair_count = len(game.alive_players()) // 2
    game.combat_phase()
    return expected_pair_count, game.last_combat_results


def test_combat_results_reset_each_turn_and_match_current_pair_count():
    game = build_seeded_game(seed=123)

    pair_count_turn_1, results_turn_1 = advance_one_turn(game)
    first_results_object = game.last_combat_results
    pair_count_turn_2, results_turn_2 = advance_one_turn(game)
    second_results_object = game.last_combat_results

    assert len(results_turn_1) == pair_count_turn_1
    assert len(results_turn_2) == pair_count_turn_2
    assert first_results_object is not second_results_object


def test_combat_result_snapshot_has_expected_shape_and_score_decomposition():
    game = build_seeded_game(seed=777)

    for _ in range(4):
        _, results = advance_one_turn(game)

    assert results
    for result in results:
        assert set(result.keys()) == EXPECTED_COMBAT_RESULT_KEYS
        assert result["pts_a"] == result["kill_a"] + result["combo_a"] + result["synergy_a"]
        assert result["pts_b"] == result["kill_b"] + result["combo_b"] + result["synergy_b"]
        assert result["winner_pid"] in {-1, result["pid_a"], result["pid_b"]}
        assert result["draws"] >= 0


def test_combat_damage_and_hp_snapshots_follow_winner_state():
    game = build_seeded_game(seed=777)

    for _ in range(4):
        _, results = advance_one_turn(game)

    for result in results:
        if result["winner_pid"] == -1:
            assert result["dmg"] == 0
            assert result["hp_after_a"] == result["hp_before_a"]
            assert result["hp_after_b"] == result["hp_before_b"]
            continue

        if result["winner_pid"] == result["pid_a"]:
            winner_pts = result["pts_a"]
            loser_pts = result["pts_b"]
            winner_board = game.players[result["pid_a"]].board
            assert result["hp_after_a"] == result["hp_before_a"]
            assert result["hp_after_b"] == result["hp_before_b"] - result["dmg"]
        else:
            winner_pts = result["pts_b"]
            loser_pts = result["pts_a"]
            winner_board = game.players[result["pid_b"]].board
            assert result["hp_after_b"] == result["hp_before_b"]
            assert result["hp_after_a"] == result["hp_before_a"] - result["dmg"]

        assert result["dmg"] == calculate_damage(winner_pts, loser_pts, winner_board, turn=game.turn)


def test_kill_buckets_can_include_non_kill_combat_points():
    game = build_seeded_game(seed=22)

    for _ in range(2):
        _, results = advance_one_turn(game)

    mixed_bucket_result = next(
        (
            result
            for result in results
            if any(value > 0 and value % KILL_PTS != 0 for value in (result["kill_a"], result["kill_b"]))
        ),
        None,
    )

    assert mixed_bucket_result is not None
    assert mixed_bucket_result["pts_a"] == (
        mixed_bucket_result["kill_a"] + mixed_bucket_result["combo_a"] + mixed_bucket_result["synergy_a"]
    )
    assert mixed_bucket_result["pts_b"] == (
        mixed_bucket_result["kill_b"] + mixed_bucket_result["combo_b"] + mixed_bucket_result["synergy_b"]
    )
