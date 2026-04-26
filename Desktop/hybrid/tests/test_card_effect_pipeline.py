from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from engine_core.board import Board, combat_phase
from engine_core.damage_calculator import resolve_single_combat
from engine_core.card import Card
from engine_core.effects import Effect, EffectPriority
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.game_state import GameState


def make_card(name: str, category: str = "Test", rarity: str = "1", passive_type: str = "none", **stats) -> Card:
    payload = {
        "Power": 1,
        "Durability": 1,
        "Size": 1,
        "Speed": 1,
        "Meaning": 1,
        "Secret": 1,
    }
    payload.update(stats)
    return Card(name=name, category=category, rarity=rarity, stats=payload, passive_type=passive_type)


def test_stats_snapshot_is_read_only():
    card = make_card("ReadOnly")

    with pytest.raises(TypeError):
        card.stats["Power"] = 99


def test_base_stats_effects_and_meta_are_separated():
    card = Card(
        name="Split",
        category="Test",
        rarity="1",
        stats={
            "Power": 5,
            "Speed": 2,
            "_yggdrasil_bonus": 3,
            "phoenix_used": True,
        },
    )

    assert dict(card.stats) == {"Power": 5, "Speed": 2}
    assert card.get_meta("_yggdrasil_bonus") == 3
    assert card.get_meta("phoenix_used") is True


def test_edges_and_combat_math_follow_resolved_stats():
    buffed = Card(
        name="Buffed",
        category="Test",
        rarity="1",
        stats={
            "Power": 1,
            "Durability": 1,
            "Size": 1,
            "Speed": 1,
            "Gravity": 1,
            "Harmony": 1,
        },
    )
    plain = Card(
        name="Plain",
        category="Test",
        rarity="1",
        stats={
            "Power": 1,
            "Durability": 1,
            "Size": 1,
            "Speed": 1,
            "Gravity": 1,
            "Harmony": 1,
        },
    )

    buffed.add_effect(Effect(source="test", stat_name="Power", delta=2, duration=1, applied_turn=1))

    assert buffed.rotated_edges()[0] == ("Power", 3)
    assert buffed.total_power() == sum(buffed.stats.values())

    a_wins, b_wins = resolve_single_combat(buffed, plain)

    assert a_wins > b_wins


def test_expired_effects_are_removed_cleanly():
    card = make_card("Timed")
    card.add_effect(Effect(source="test", stat_name="Power", delta=2, duration=1, applied_turn=3))

    assert card.stats["Power"] == 3

    card.clear_expired_effects(4)

    assert card.stats["Power"] == 1


def test_effect_priority_is_explicit_and_deterministic():
    debuff_first = make_card("OrderedA", Power=3)
    debuff_first.add_effect(
        Effect(
            source="buff",
            stat_name="Power",
            delta=2,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_BUFF),
        )
    )
    debuff_first.add_effect(
        Effect(
            source="debuff",
            stat_name="Power",
            delta=-5,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_DEBUFF),
        )
    )

    same_priorities_reverse_insert = make_card("OrderedB", Power=3)
    same_priorities_reverse_insert.add_effect(
        Effect(
            source="debuff",
            stat_name="Power",
            delta=-5,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_DEBUFF),
        )
    )
    same_priorities_reverse_insert.add_effect(
        Effect(
            source="buff",
            stat_name="Power",
            delta=2,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_BUFF),
        )
    )

    buff_first = make_card("OrderedC", Power=3)
    buff_first.add_effect(
        Effect(
            source="buff",
            stat_name="Power",
            delta=2,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_DEBUFF),
        )
    )
    buff_first.add_effect(
        Effect(
            source="debuff",
            stat_name="Power",
            delta=-5,
            duration=2,
            applied_turn=1,
            priority=int(EffectPriority.COMBAT_BUFF),
        )
    )

    assert debuff_first.stats["Power"] == 2
    assert same_priorities_reverse_insert.stats["Power"] == 2
    assert buff_first.stats["Power"] == 0


def test_same_stat_effects_stack_additively():
    card = make_card("Stacked", Power=4)
    card.add_effect(Effect(source="one", stat_name="Power", delta=-1, duration=2, applied_turn=1))
    card.add_effect(Effect(source="two", stat_name="Power", delta=-2, duration=2, applied_turn=1))

    assert card.stats["Power"] == 1


def test_unknown_meta_keys_are_rejected_loudly():
    with pytest.raises(KeyError):
        make_card("TypoMeta", _narwhall_buff=1)

    card = make_card("TypoWrite")
    with pytest.raises(KeyError):
        card.set_meta("_narwhall_buff", 1)


def test_unsupported_effect_stacking_policy_is_rejected():
    card = make_card("StackPolicy")

    with pytest.raises(ValueError):
        card.add_effect(
            Effect(
                source="test",
                stat_name="Power",
                delta=1,
                duration=1,
                applied_turn=1,
                stacking="overwrite",
            )
        )


def test_clone_drops_transient_effects_and_meta():
    card = make_card("CloneBase")
    card.add_effect(Effect(source="test", stat_name="Power", delta=4, duration=1, applied_turn=1))
    card.set_meta("_combat_bonus", 2)

    cloned = card.clone()

    assert cloned.stats["Power"] == card.get_base_stat("Power")
    assert cloned.get_meta("_combat_bonus") is None


def test_board_snapshot_and_elimination_share_same_resolved_truth():
    gs = GameState()
    player = Player(pid=0, strategy="human")
    card = make_card("Snapshot")
    card.add_effect(Effect(source="test", stat_name="Power", delta=1, duration=1, applied_turn=1))
    player.board.place((0, 0), card)
    engine = SimpleNamespace(players=[player], turn=1, last_combat_results=[], market=None, signals=MagicMock())
    gs.hook_engine(engine)

    snapshot = gs.get_board_cards(0)

    assert snapshot[(0, 0)]["stats"]["Power"] == 2
    assert card.is_eliminated() is False

    for stat_name in list(card.get_base_stats().keys()):
        card.set_base_stat(stat_name, 0)
    card.clear_expired_effects(2)

    assert card.is_eliminated() is True


def test_permanent_growth_passive_uses_base_stats_and_meta():
    card = make_card("Narwhal", passive_type="combat")

    trigger_passive(card, "combat_win", None, None, {"turn": 1}, verbose=False)

    assert card.get_base_stat("Power") == 2
    assert card.stats["Power"] == 2
    assert card.get_meta("_narwhal_buff") == 1
    assert card.get_meta("_narwhal_last_turn") == 1


def test_temporary_debuff_passive_uses_effect_layer():
    owner = Player(pid=0, strategy="human")
    opponent = Player(pid=1, strategy="random")
    medusa = make_card("Medusa", passive_type="synergy_field")
    target = make_card("Target", Speed=3)
    owner.board.place((0, 0), medusa)
    opponent.board.place((0, 0), target)

    trigger_passive(medusa, "pre_combat", owner, opponent, {"turn": 1}, verbose=False)

    assert target.get_base_stat("Speed") == 3
    assert target.stats["Speed"] == 2

    target.clear_expired_effects(2)

    assert target.stats["Speed"] == 3


def test_same_passive_instances_stack_to_expected_temporary_effect():
    owner = Player(pid=0, strategy="human")
    opponent = Player(pid=1, strategy="random")
    medusa_a = make_card("Medusa", passive_type="synergy_field")
    medusa_b = make_card("Medusa", passive_type="synergy_field")
    target = make_card("Target", Speed=3)
    owner.board.place((0, 0), medusa_a)
    owner.board.place((1, 0), medusa_b)
    opponent.board.place((0, 0), target)

    trigger_passive(medusa_a, "pre_combat", owner, opponent, {"turn": 1}, verbose=False)
    trigger_passive(medusa_b, "pre_combat", owner, opponent, {"turn": 1}, verbose=False)

    assert target.stats["Speed"] == 1

    target.clear_expired_effects(2)

    assert target.stats["Speed"] == 3


def test_revive_passive_restores_base_stats_and_meta_flags():
    card = make_card("Phoenix", passive_type="survival")
    for stat_name in list(card.get_base_stats().keys()):
        card.set_base_stat(stat_name, 0)

    trigger_passive(card, "card_killed", None, None, {"turn": 1}, verbose=False)

    assert all(value == 1 for value in card.stats.values())
    assert card.get_meta("phoenix_used") is True
    assert card.get_meta("revived_this_combat") is True


def test_start_turn_clears_expired_effects_and_combat_meta():
    player = Player(pid=0, strategy="human")
    card = make_card("Transient")
    card.add_effect(Effect(source="test", stat_name="Power", delta=2, duration=1, applied_turn=0))
    card.set_meta("phoenix_used", True)
    card.set_meta("revived_this_combat", True)
    player.board.place((0, 0), card)

    game = Game(
        [player],
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=[],
    )

    game.start_turn()

    assert card.stats["Power"] == 1
    assert card.get_meta("phoenix_used") is None
    assert card.get_meta("revived_this_combat") is None


def test_combat_phase_defensively_clears_stale_effects_before_resolution():
    player_a = Player(pid=0, strategy="human")
    player_b = Player(pid=1, strategy="random")
    stale = make_card("Stale")
    fresh = make_card("Fresh")
    stale.add_effect(Effect(source="stale", stat_name="Power", delta=2, duration=1, applied_turn=1))
    player_a.board.place((0, 0), stale)
    player_b.board.place((0, 0), fresh)

    game = Game(
        [player_a, player_b],
        verbose=False,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=[],
    )
    game.turn = 2

    game.combat_phase(pairs=[(player_a, player_b)])

    assert stale.stats["Power"] == 1
    assert game.last_combat_results[0]["winner_pid"] == -1
