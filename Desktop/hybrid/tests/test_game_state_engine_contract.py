import random

import pytest

from engine_core.board import combat_phase
from engine_core.card import get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.game_state import GameState


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


def build_seeded_game(strategies=None, seed=123):
    if strategies is None:
        strategies = ["random", "builder", "economist", "warrior"]

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


def normalize_pairs(pairs):
    return tuple(sorted(tuple(sorted(pair)) for pair in pairs))


@pytest.fixture
def real_game_state():
    state = GameState()
    game = build_seeded_game()
    state.hook_engine(game)
    yield state, game


def test_real_engine_accessors_expose_turn_alive_players_and_stats(real_game_state):
    state, game = real_game_state

    assert state.get_public_state().turn == 0
    assert list(state.get_public_state().alive_pids) == [0, 1, 2, 3]
    assert dict(state.get_public_state().active_player.stats) == dict(game.players[0].stats)


def test_real_engine_accessors_track_turn_progression_interest_and_board_flags(real_game_state):
    state, game = real_game_state

    game.preparation_phase()

    assert state.get_public_state().turn == 1
    assert state.get_public_state().active_player.turns_played == 1
    state.view_index = 2
    assert state.get_public_state().active_player.hud.interest_multiplier == pytest.approx(1.5)
    state.view_index = 0
    assert isinstance(state.get_public_state().active_player.has_catalyst, bool)
    assert isinstance(state.get_public_state().active_player.has_eclipse, bool)


def test_get_current_pairings_returns_distinct_pid_pairs_for_alive_players(real_game_state):
    state, game = real_game_state
    state.commit_human_turn()  # preparation_phase + freeze_pairings birlikte

    pairings = list(state.get_public_state().pairings)

    assert pairings
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in pairings)
    flat = [pid for pair in pairings for pid in pair]
    assert len(flat) == len(set(flat))
    assert set(flat).issubset(set(state.get_public_state().alive_pids))


def test_get_last_combat_results_proxies_engine_snapshot_with_expected_shape(real_game_state):
    state, game = real_game_state
    state.commit_human_turn()  # preparation_phase + freeze_pairings birlikte
    game.combat_phase()

    results = list(state.get_public_state().active_player.combat.last_results)

    assert results == game.last_combat_results
    assert len(results) == len(list(state.get_public_state().pairings))
    for result in results:
        assert set(result.keys()) == EXPECTED_COMBAT_RESULT_KEYS
        assert result["winner_pid"] in {-1, result["pid_a"], result["pid_b"]}
        assert result["dmg"] >= 0
        assert result["hp_after_a"] <= result["hp_before_a"]
        assert result["hp_after_b"] <= result["hp_before_b"]
        if result["winner_pid"] == -1:
            assert result["dmg"] == 0


def test_passive_buff_log_and_copy_milestone_accessors_are_shape_stable(real_game_state):
    state, game = real_game_state
    game.preparation_phase()
    game.combat_phase()

    log_entries = list(state.get_public_state().active_player.combat.passive_feed)
    milestones = list(state.get_public_state().active_player.copy_milestones)

    assert isinstance(log_entries, list)
    assert isinstance(milestones, list)
    for entry in log_entries:
        assert isinstance(entry, dict)
        assert {"turn", "card", "passive", "trigger", "delta"}.issubset(entry.keys())
    for milestone in milestones:
        assert isinstance(milestone, dict)
        assert {"card", "trigger", "count", "turn"}.issubset(milestone.keys())


def test_pairing_snapshot_is_stable_within_same_turn(real_game_state):
    """Eşleşmeler aynı tur içinde değişmemeli (freeze garantisi)."""
    state, game = real_game_state
    state.commit_human_turn()

    seen_pairings = {normalize_pairs(list(state.get_public_state().pairings)) for _ in range(8)}

    assert len(seen_pairings) == 1


def test_identity_bridge_exposes_display_name_and_strategy(real_game_state):
    """GameState, motor’un oyuncu kimliğini (pid → display name + strategy) UI’a sunabilmeli."""
    state, game = real_game_state

    assert state.get_public_state().active_player.strategy == game.players[0].strategy
    assert state.get_public_state().active_player.display_name == "P0"


def test_prefix_bonus_bridge_returns_non_negative_int(real_game_state):
    """get_prefix_bonus() her zaman negatif olmayan bir int döndmeli."""
    state, _ = real_game_state

    value = state.get_public_state().active_player.prefix_bonus

    assert isinstance(value, int)
    assert value >= 0


def test_board_mutation_outside_game_state_invalidates_public_state_cache(real_game_state):
    state, game = real_game_state
    first_state = state.get_public_state()
    assert first_state is state.get_public_state()

    # Mutate board directly (outside GameState APIs) and verify cache is invalidated
    player0 = game.players[0]
    if not player0.hand:
        pytest.skip("fixture should start with cards in hand")
    card = player0.hand[0]
    if card is None:
        pytest.skip("fixture first hand slot should contain a card")
    player0.hand[0] = None
    player0.board.place((0, 0), card)

    second_state = state.get_public_state()
    assert second_state is not first_state
    assert (0, 0) in second_state.active_player.board_cards
