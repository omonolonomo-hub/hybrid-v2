from engine_core.card import Card
from engine_core.player import Player


def _make_card(name: str = "Unit", rarity: str = "1") -> Card:
    return Card(
        name=name,
        category="Science",
        rarity=rarity,
        stats={
            "Meaning": 1,
            "Secret": 1,
            "Intelligence": 1,
            "Trace": 1,
            "Power": 1,
            "Gravity": 1,
        },
    )


def test_cards_bought_counter_uses_single_source_on_buy_and_reset():
    p = Player(pid=0, strategy="random")
    p.gold = 10

    p.buy_card(_make_card("A", "1"))
    p.buy_card(_make_card("B", "1"))

    assert p.cards_bought_this_turn == 2
    assert p.stats["cards_bought_this_turn"] == 2

    p.reset_turn_state()
    assert p.cards_bought_this_turn == 0
    assert p.stats["cards_bought_this_turn"] == 0


def test_cards_bought_property_setter_keeps_stats_in_sync():
    p = Player(pid=1, strategy="random")
    p.cards_bought_this_turn = 3

    assert p.cards_bought_this_turn == 3
    assert p.stats["cards_bought_this_turn"] == 3
