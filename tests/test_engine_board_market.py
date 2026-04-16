import random
from types import SimpleNamespace

from engine_core.board import Board, calculate_damage, find_combos, resolve_single_combat
from engine_core.card import Card, get_card_pool
from engine_core.market import Market, _rarity_weight


def make_card(name: str, *, group: str = "MIND", rarity: str = "1", value: int = 2) -> Card:
    if group == "MIND":
        stats = {
            "Meaning": value,
            "Secret": value,
            "Intelligence": value,
            "Trace": value,
            "Power": 0,
            "Size": 0,
        }
    elif group == "EXISTENCE":
        stats = {
            "Power": value,
            "Durability": value,
            "Size": value,
            "Speed": value,
            "Meaning": 0,
            "Secret": 0,
        }
    else:
        stats = {
            "Gravity": value,
            "Harmony": value,
            "Spread": value,
            "Prestige": value,
            "Power": 0,
            "Meaning": 0,
        }
    return Card(name=name, category="Test", rarity=rarity, stats=stats)


def test_rarity_weight_curve_matches_expected_turn_steps():
    assert _rarity_weight("3", 1) == 0.3
    assert _rarity_weight("3", 9) == 1.0
    assert _rarity_weight("4", 1) == 0.0
    assert _rarity_weight("4", 5) == 0.2
    assert _rarity_weight("5", 7) == 0.0
    assert _rarity_weight("5", 18) == 1.0


def test_deal_market_window_respects_early_game_rarity_gates_and_updates_roll_stats():
    market = Market(get_card_pool(), rng=random.Random(0))
    player = SimpleNamespace(pid=7, turns_played=1, stats={"market_rolls": 0}, _window_bought=[])

    window = market.deal_market_window(player, n=5)

    assert len(window) == 5
    assert all(card.rarity in {"1", "2", "3"} for card in window)
    assert player.stats["market_rolls"] == 1
    assert market._player_windows[player.pid] == window
    assert all(market.pool_copies[card.name] == 2 for card in window)


def test_return_unsold_restores_only_cards_not_marked_as_bought():
    pool = [
        make_card("A", group="MIND"),
        make_card("B", group="EXISTENCE"),
        make_card("C", group="CONNECTION"),
    ]
    market = Market(pool, rng=random.Random(0))
    player = SimpleNamespace(pid=3, turns_played=1, stats={"market_rolls": 0}, _window_bought=[])

    window = market.deal_market_window(player, n=3)
    bought_clone = window[0].clone()

    market.return_unsold(player, bought=[bought_clone])

    assert market.pool_copies[window[0].name] == 2
    assert market.pool_copies[window[1].name] == 3
    assert market.pool_copies[window[2].name] == 3
    assert player.pid not in market._player_windows


def test_board_place_and_remove_keep_coord_index_in_sync():
    board = Board()
    first = make_card("First")
    second = make_card("Second")

    board.place((0, 0), first)
    assert board.coord_index[first.uid] == (0, 0)

    board.place((0, 0), second)
    assert first.uid not in board.coord_index
    assert board.coord_index[second.uid] == (0, 0)

    board.remove((0, 0))
    assert second.uid not in board.coord_index
    assert board.grid == {}


def test_find_combos_counts_each_unique_neighbor_pair_once():
    board = Board()
    board.place((0, 0), make_card("Center", group="MIND"))
    board.place((1, 0), make_card("Right", group="MIND"))
    board.place((0, 1), make_card("Bottom", group="MIND"))

    combo_points, combat_bonus = find_combos(board)

    assert combo_points == 3
    assert combat_bonus[(0, 0)][2] == 1
    assert combat_bonus[(0, 0)][3] == 1
    assert combat_bonus[(1, 0)][4] == 1
    assert combat_bonus[(1, 0)][5] == 1
    assert combat_bonus[(0, 1)][0] == 1
    assert combat_bonus[(0, 1)][1] == 1


def test_resolve_single_combat_distributes_prefix_bonus_evenly_across_edges():
    card_a = make_card("Buffed", group="EXISTENCE", value=1)
    card_b = make_card("Plain", group="EXISTENCE", value=1)
    card_a.stats["_prefix_bonus"] = 6

    a_wins, b_wins = resolve_single_combat(card_a, card_b)

    assert (a_wins, b_wins) == (6, 0)


def test_calculate_damage_applies_early_cap_and_late_full_value():
    empty_board = Board()

    early_damage = calculate_damage(40, 0, empty_board, turn=1)
    late_damage = calculate_damage(40, 0, empty_board, turn=16)

    assert early_damage == 15
    assert late_damage == 40
    assert early_damage < late_damage
