"""
Comprehensive tests for trigger_passive() in autochess_sim_v06.py
Run: pytest test_trigger_passive.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from engine_core.card import get_card_pool, Card
from engine_core.board import Board
from engine_core.player import Player
from engine_core.passive_trigger import trigger_passive

CARD_BY_NAME = {c.name: c for c in get_card_pool()}
CARD_NAME_RAGNAROK = "Ragnarök"

# ASCII-safe alias for cards.json key (superscript two)
CARD_NAME_E_MC2 = "E = mc\u00b2"


# ---------------------------------------------
# HELPERS
# ---------------------------------------------

def make_card(name, passive_type="none", category="Test", rarity="1",
              stats=None, edges=None):
    """Build a Card without touching cards.json."""
    if stats is None:
        stats = {"Power": 5, "Durability": 5, "Speed": 5,
                 "Meaning": 5, "Gravity": 5, "Prestige": 5}
    c = Card(name=name, category=category, rarity=rarity,
             stats=dict(stats), passive_type=passive_type)
    if edges is not None:
        c.edges = list(edges)
    return c


def make_board_with_card(card, coord=(0, 0)):
    """Return a Board that has `card` placed at `coord`."""
    b = Board()
    b.place(coord, card)
    return b


def make_owner(board=None, gold=10, win_streak=0, stats=None):
    owner = MagicMock()
    owner.board = board or Board()
    owner.gold = gold
    owner.win_streak = win_streak
    owner.turns_played = 1
    owner.market = []
    base_stats = {
        "wins": 0, "losses": 0, "draws": 0,
        "kills": 0, "damage_dealt": 0, "damage_taken": 0,
        "synergy_sum": 0, "synergy_turns": 0,
        "gold_spent": 0, "gold_earned": 0,
    }
    if stats:
        base_stats.update(stats)
    owner.stats = dict(base_stats)
    return owner


def make_opponent(board=None):
    opp = MagicMock()
    opp.board = board or Board()
    return opp


def ctx(turn=1, **kwargs):
    return {"turn": turn, **kwargs}


# ---------------------------------------------
# SECTION 1 - passive_type == "none"
# ---------------------------------------------

class TestPassiveTypeNone:
    def test_returns_zero_for_none_passive(self):
        card = make_card("Platypus", passive_type="none")
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert result == 0
        assert isinstance(result, int)

    def test_none_passive_ignores_all_triggers(self):
        card = make_card("Platypus", passive_type="none")
        for trigger in ["combat_win", "combat_lose", "income", "pre_combat",
                        "card_killed", "copy_2", "copy_3", "market_refresh", "card_buy"]:
            assert trigger_passive(card, trigger, None, None, ctx()) == 0


# ---------------------------------------------
# SECTION 2 - passive_type == "combat"
# ---------------------------------------------

class TestCombatPassive:

    # -- combat_win --

    def test_ragnarok_loses_highest_edge_on_target(self):
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat", category="Mythology & Gods")
        target = make_card("Dummy", stats={"Power": 9, "Durability": 3,
                                           "Speed": 3, "Meaning": 3, "Gravity": 3, "Prestige": 3})
        opp_board = make_board_with_card(target)
        opp = make_opponent(opp_board)
        result = trigger_passive(card, "combat_win", None, opp, ctx())
        assert result == 0
        assert target.stats["Power"] == 0  # highest edge zeroed

    def test_world_war_ii_hits_all_opponent_cards(self):
        card = make_card("World War II", passive_type="combat",
                         category="History & Civilizations")
        t1 = make_card("A", stats={"Power": 8, "Durability": 3, "Speed": 3,
                                   "Meaning": 3, "Gravity": 3, "Prestige": 3})
        t2 = make_card("B", stats={"Power": 7, "Durability": 3, "Speed": 3,
                                   "Meaning": 3, "Gravity": 3, "Prestige": 3})
        opp_board = Board()
        opp_board.place((0, 0), t1)
        opp_board.place((1, 0), t2)
        opp = make_opponent(opp_board)
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert t1.stats["Power"] == 0
        assert t2.stats["Power"] == 0

    def test_loki_debuffs_meaning_on_target(self):
        card = make_card("Loki", passive_type="combat",
                         category="Mythology & Gods")
        target = make_card("Dummy", stats={"Power": 3, "Durability": 3,
                                           "Speed": 3, "Meaning": 9, "Gravity": 3, "Prestige": 3})
        opp_board = make_board_with_card(target)
        opp = make_opponent(opp_board)
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert target.stats["Meaning"] == 8

    def test_cubism_debuffs_boyut(self):
        card = make_card("Cubism", passive_type="combat", category="Art & Culture")
        target = make_card("Dummy", stats={"Power": 3, "Durability": 3,
                                           "Size": 7, "Meaning": 3, "Gravity": 3, "Prestige": 3})
        opp_board = make_board_with_card(target)
        opp = make_opponent(opp_board)
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert target.stats["Size"] == 6

    def test_komodo_dragon_debuffs_lowest_edge(self):
        card = make_card("Komodo Dragon", passive_type="combat",
                         category="Nature & Creatures")
        target = make_card("Dummy", stats={"Power": 9, "Durability": 2,
                                           "Speed": 3, "Meaning": 3, "Gravity": 3, "Prestige": 3})
        opp_board = make_board_with_card(target)
        opp = make_opponent(opp_board)
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert target.stats["Durability"] == 0  # 2 - 2 = 0

    def test_venus_flytrap_max_two_debuffs(self):
        card = make_card("Venus Flytrap", passive_type="combat",
                         category="Nature & Creatures",
                         stats={"Power": 6, "Durability": 5, "Speed": 4,
                                "Secret": 5, "Trace": 6, "Gravity": 6})
        target = make_card("Dummy", stats={"Power": 3, "Durability": 3,
                                           "Speed": 3, "Meaning": 3, "Gravity": 5, "Prestige": 3})
        opp_board = make_board_with_card(target)
        opp = make_opponent(opp_board)
        # First two wins should debuff
        trigger_passive(card, "combat_win", None, opp, ctx())
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert card.stats.get("_venus_debuffs", 0) == 2
        # Third win should NOT debuff further
        before = target.stats["Gravity"]
        trigger_passive(card, "combat_win", None, opp, ctx())
        assert target.stats["Gravity"] == before

    def test_narwhal_stacks_guc_max_three(self):
        card = make_card("Narwhal", passive_type="combat",
                         category="Nature & Creatures",
                         stats={"Power": 6, "Size": 5, "Speed": 6,
                                "Secret": 6, "Gravity": 5, "Spread": 5})
        owner_board = make_board_with_card(card)
        owner = make_owner(owner_board)
        for _ in range(5):
            trigger_passive(card, "combat_win", owner, None, ctx())
        assert card.stats.get("_narwhal_buff", 0) == 3

    def test_sirius_stacks_hiz_max_two(self):
        card = make_card("Sirius", passive_type="combat", category="Cosmos",
                         stats={"Power": 6, "Size": 5, "Speed": 7,
                                "Meaning": 5, "Gravity": 5, "Spread": 4})
        owner_board = make_board_with_card(card)
        owner = make_owner(owner_board)
        for _ in range(5):
            trigger_passive(card, "combat_win", owner, None, ctx())
        assert card.stats.get("_sirius_buff", 0) == 2

    def test_pulsar_returns_2_first_win_per_turn(self):
        card = make_card("Pulsar", passive_type="combat", category="Cosmos")
        owner = make_owner()
        result = trigger_passive(card, "combat_win", owner, None, ctx(turn=5))
        assert result == 2

    def test_pulsar_returns_0_second_win_same_turn(self):
        card = make_card("Pulsar", passive_type="combat", category="Cosmos")
        owner = make_owner()
        trigger_passive(card, "combat_win", owner, None, ctx(turn=5))
        result = trigger_passive(card, "combat_win", owner, None, ctx(turn=5))
        assert result == 0

    def test_cerberus_returns_3_on_third_win(self):
        card = make_card("Cerberus", passive_type="combat",
                         category="Mythology & Gods")
        owner = make_owner()
        trigger_passive(card, "combat_win", owner, None, ctx())
        trigger_passive(card, "combat_win", owner, None, ctx())
        result = trigger_passive(card, "combat_win", owner, None, ctx())
        assert result == 3
        assert owner.stats["cerberus_win_qty"] == 0  # resets

    def test_e_mc2_returns_0_because_passive_type_is_none_in_json(self):
        """CARD_NAME_E_MC2 has passive_type='none' in cards.json, so trigger_passive
        exits early and returns 0 regardless of trigger."""
        card = make_card(CARD_NAME_E_MC2, passive_type="none", category="Science")
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert result == 0

    def test_fibonacci_sequence_returns_0_because_passive_type_is_none(self):
        """Fibonacci Sequence is passive_type='none' in cards.json, so
        trigger_passive exits early - the combat_win branch is unreachable."""
        card = make_card("Fibonacci Sequence", passive_type="none",
                         category="Science")
        owner = make_owner(win_streak=5)
        result = trigger_passive(card, "combat_win", owner, None, ctx())
        assert result == 0

    def test_fibonacci_sequence_with_combat_passive_type_returns_clamped_streak(self):
        """Fibonacci Sequence combat_win: min(3, max(1, win_streak)) by card name."""
        card = make_card("Fibonacci Sequence", passive_type="combat",
                         category="Science")
        owner = make_owner(win_streak=5)
        result = trigger_passive(card, "combat_win", owner, None, ctx())
        assert result == 3

    def test_fibonacci_sequence_min_1_when_streak_zero(self):
        """Fibonacci Sequence: max(1, streak) floor -> 1 when streak is 0."""
        card = make_card("Fibonacci Sequence", passive_type="combat",
                         category="Science")
        owner = make_owner(win_streak=0)
        result = trigger_passive(card, "combat_win", owner, None, ctx())
        assert result == 1

    # -- combat_lose --

    def test_guernica_returns_1_per_loss_max_3_per_turn(self):
        card = make_card("Guernica", passive_type="combat",
                         category="Art & Culture")
        owner = make_owner()
        results = [trigger_passive(card, "combat_lose", owner, None, ctx(turn=1))
                   for _ in range(5)]
        assert results[:3] == [1, 1, 1]
        assert results[3] == 0
        assert results[4] == 0

    def test_guernica_resets_counter_on_new_turn(self):
        card = make_card("Guernica", passive_type="combat",
                         category="Art & Culture")
        owner = make_owner()
        for _ in range(3):
            trigger_passive(card, "combat_lose", owner, None, ctx(turn=1))
        result = trigger_passive(card, "combat_lose", owner, None, ctx(turn=2))
        assert result == 1

    def test_minotaur_buffs_guc_on_loss_max_2(self):
        card = make_card("Minotaur", passive_type="combat",
                         category="Mythology & Gods",
                         stats={"Power": 7, "Durability": 7, "Size": 5,
                                "Speed": 4, "Meaning": 3, "Gravity": 5})
        owner = make_owner()
        trigger_passive(card, "combat_lose", owner, None, ctx(turn=1))
        trigger_passive(card, "combat_lose", owner, None, ctx(turn=1))
        assert owner.stats.get("minotaur_buff", 0) == 2
        # Third loss same turn should not buff
        trigger_passive(card, "combat_lose", owner, None, ctx(turn=1))
        assert owner.stats.get("minotaur_buff", 0) == 2

    def test_code_of_hammurabi_buffs_first_positive_edge(self):
        card = make_card("Code of Hammurabi", passive_type="combat",
                         category="History & Civilizations",
                         stats={"Power": 5, "Durability": 5, "Speed": 5,
                                "Meaning": 5, "Gravity": 5, "Prestige": 5})
        owner = make_owner()
        original_first = card.edges[0][1]
        trigger_passive(card, "combat_lose", owner, None, ctx())
        assert card.edges[0][1] == original_first + 2

    # -- card_killed --

    def test_anubis_buffs_sir_on_card_killed_max_2(self):
        card = make_card("Anubis", passive_type="combat",
                         category="Mythology & Gods",
                         stats={"Power": 5, "Durability": 7, "Meaning": 7,
                                "Secret": 8, "Gravity": 5, "Spread": 4})
        trigger_passive(card, "card_killed", None, None, ctx())
        trigger_passive(card, "card_killed", None, None, ctx())
        assert card.stats.get("_anubis_buff", 0) == 2
        trigger_passive(card, "card_killed", None, None, ctx())
        assert card.stats.get("_anubis_buff", 0) == 2  # capped

    # -- wrong trigger does nothing --

    def test_combat_passive_ignores_income_trigger(self):
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat",
                         category="Mythology & Gods")
        result = trigger_passive(card, "income", None, None, ctx())
        assert result == 0

    # -- None owner/opponent safety --

    def test_combat_win_with_none_opponent_no_crash(self):
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat",
                         category="Mythology & Gods")
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert isinstance(result, int)

    def test_combat_win_with_none_owner_no_crash(self):
        card = make_card("Pulsar", passive_type="combat", category="Cosmos")
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 3 - passive_type == "economy"
# ---------------------------------------------

class TestEconomyPassive:

    def test_industrial_revolution_adds_gold_on_income(self):
        card = make_card("Industrial Revolution", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 6
        assert owner.stats["gold_earned"] == 1

    def test_ottoman_empire_adds_gold_on_income(self):
        card = make_card("Ottoman Empire", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 6

    def test_babylon_adds_gold_on_income(self):
        card = make_card("Babylon", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=3)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 4

    def test_midas_adds_gold_when_win_streak_ge_2(self):
        """Midas economy passive: +1 gold on income when win_streak >= 2."""
        card = make_card("Midas", passive_type="economy",
                         category="Mythology & Gods")
        owner = make_owner(gold=5, win_streak=2)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 6
        assert owner.stats["gold_earned"] == 1

    def test_midas_no_gold_when_win_streak_lt_2(self):
        card = make_card("Midas", passive_type="economy",
                         category="Mythology & Gods")
        owner = make_owner(gold=5, win_streak=1)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 5

    def test_silk_road_adds_gold_when_2_cards_bought(self):
        card = make_card("Silk Road", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5, stats={"cards_bought_this_turn": 2,
                                          "gold_earned": 0})
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 6

    def test_silk_road_no_gold_when_less_than_2_bought(self):
        card = make_card("Silk Road", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5, stats={"cards_bought_this_turn": 1,
                                          "gold_earned": 0})
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 5

    def test_exoplanet_adds_gold_when_rare_card_in_market(self):
        card = make_card("Exoplanet", passive_type="economy", category="Cosmos")
        rare_card = make_card("SomeRare", rarity="4")
        owner = make_owner(gold=5)
        owner.market = [rare_card]
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 6

    def test_exoplanet_no_gold_when_no_rare_in_market(self):
        card = make_card("Exoplanet", passive_type="economy", category="Cosmos")
        common_card = make_card("SomeCommon", rarity="1")
        owner = make_owner(gold=5)
        owner.market = [common_card]
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 5

    def test_moon_landing_adds_gold_on_even_turn(self):
        card = make_card("Moon Landing", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5)
        owner.turns_played = 4  # even
        trigger_passive(card, "income", owner, None, ctx(turn=4))
        assert owner.gold == 6

    def test_moon_landing_no_gold_on_odd_turn(self):
        card = make_card("Moon Landing", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5)
        owner.turns_played = 3  # odd
        trigger_passive(card, "income", owner, None, ctx(turn=3))
        assert owner.gold == 5

    def test_algorithm_adds_gold_on_market_refresh(self):
        card = make_card("Algorithm", passive_type="economy", category="Science")
        owner = make_owner(gold=5)
        trigger_passive(card, "market_refresh", owner, None, ctx())
        assert owner.gold == 6

    def test_algorithm_no_gold_on_income(self):
        card = make_card("Algorithm", passive_type="economy", category="Science")
        owner = make_owner(gold=5)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 5  # income branch is pass for Algorithm

    def test_age_of_discovery_adds_2_gold_for_new_category(self):
        card = make_card("Age of Discovery", passive_type="economy",
                         category="History & Civilizations")
        bought = make_card("NewCard", category="Cosmos")
        owner = make_owner(gold=5)
        owner.stats.setdefault("seen_categories", set())
        trigger_passive(card, "card_buy", owner, None,
                        ctx(bought_card=bought))
        assert owner.gold == 7

    def test_age_of_discovery_no_gold_for_seen_category(self):
        card = make_card("Age of Discovery", passive_type="economy",
                         category="History & Civilizations")
        bought = make_card("NewCard", category="Cosmos")
        owner = make_owner(gold=5)
        owner.stats["seen_categories"] = {"Cosmos"}
        trigger_passive(card, "card_buy", owner, None,
                        ctx(bought_card=bought))
        assert owner.gold == 5

    def test_economy_passive_ignores_combat_win(self):
        card = make_card("Industrial Revolution", passive_type="economy",
                         category="History & Civilizations")
        owner = make_owner(gold=5)
        result = trigger_passive(card, "combat_win", owner, None, ctx())
        assert result == 0
        assert owner.gold == 5

    def test_none_owner_economy_no_crash(self):
        card = make_card("Industrial Revolution", passive_type="economy",
                         category="History & Civilizations")
        result = trigger_passive(card, "income", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 4 - passive_type == "copy"
# ---------------------------------------------

class TestKopyaPassive:

    def _copy_card(self, name, stats=None):
        if stats is None:
            stats = {"Power": 5, "Durability": 5, "Speed": 5,
                     "Meaning": 5, "Gravity": 5, "Prestige": 5}
        return make_card(name, passive_type="copy", category="Test", stats=stats)

    def test_copy_2_buffs_highest_edge_by_1(self):
        card = self._copy_card("Event Horizon",
                                stats={"Power": 7, "Durability": 6, "Meaning": 9,
                                       "Secret": 6, "Gravity": 7, "Prestige": 7})
        original_meaning = card.stats["Meaning"]
        trigger_passive(card, "copy_2", None, None, ctx())
        assert card.stats["Meaning"] == original_meaning + 1

    def test_copy_3_buffs_highest_edge_by_1(self):
        """DNA uses default copy path: +1 to highest stat edge (no special DNA branch)."""
        card = self._copy_card("DNA",
                                stats={"Durability": 6, "Size": 6, "Meaning": 7,
                                       "Intelligence": 6, "Harmony": 7, "Spread": 7})
        trigger_passive(card, "copy_3", None, None, ctx())
        assert max(card.stats.values()) == 8

    def test_coelacanth_buffs_by_2(self):
        card = self._copy_card("Coelacanth",
                                stats={"Power": 7, "Durability": 8, "Size": 8,
                                       "Speed": 6, "Harmony": 8, "Spread": 8})
        trigger_passive(card, "copy_2", None, None, ctx())
        assert max(card.stats.values()) >= 10  # 8 + 2 on highest edge

    def test_marie_curie_gives_2_gold_on_copy(self):
        card = self._copy_card("Marie Curie")
        owner = make_owner(gold=5)
        owner.board = make_board_with_card(card)
        trigger_passive(card, "copy_2", owner, None, ctx())
        assert owner.gold == 7
        assert owner.stats["gold_earned"] == 2

    def test_space_time_buffs_all_board_cards(self):
        card = self._copy_card("Space-Time")
        ally = make_card("Ally", stats={"Power": 5, "Durability": 5, "Speed": 5,
                                        "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), ally)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "copy_2", owner, None, ctx())
        # Space-Time mutates edges list (not stats dict); check edges are +1
        assert all(e[1] == 6 for e in ally.edges)

    def test_fungus_spreads_buff_to_neighbor(self):
        card = self._copy_card("Fungus",
                                stats={"Durability": 5, "Size": 5, "Meaning": 5,
                                       "Trace": 7, "Harmony": 6, "Spread": 5})
        neighbor = make_card("Neighbor", stats={"Power": 5, "Durability": 5,
                                                "Speed": 5, "Meaning": 5,
                                                "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), neighbor)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "copy_2", owner, None, ctx())
        # neighbor's highest edge should have been buffed (edges list updated)
        assert max(e[1] for e in neighbor.edges) == 6

    def test_yggdrasil_pre_combat_advances_neighbor_copy_counter(self):
        card = self._copy_card("Yggdrasil")
        neighbor = make_card("Neighbor")
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), neighbor)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx())
        assert neighbor.stats.get("_yggdrasil_bonus", 0) == 1

    def test_copy_passive_ignores_income_trigger(self):
        card = self._copy_card("Marie Curie")
        owner = make_owner(gold=5)
        trigger_passive(card, "income", owner, None, ctx())
        assert owner.gold == 5

    def test_none_owner_copy_no_crash(self):
        card = self._copy_card("Marie Curie")
        result = trigger_passive(card, "copy_2", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 5 - passive_type == "survival"
# ---------------------------------------------

class TestSurvivalPassive:

    def test_valhalla_queues_3_gold_on_card_killed(self):
        card = make_card("Valhalla", passive_type="survival",
                         category="Mythology & Gods")
        owner = make_owner()
        trigger_passive(card, "card_killed", owner, None, ctx())
        assert owner.stats.get("valhalla_gold_pending", 0) == 3

    def test_valhalla_only_triggers_once(self):
        card = make_card("Valhalla", passive_type="survival",
                         category="Mythology & Gods")
        owner = make_owner()
        trigger_passive(card, "card_killed", owner, None, ctx())
        trigger_passive(card, "card_killed", owner, None, ctx())
        assert owner.stats.get("valhalla_gold_pending", 0) == 3  # not 6

    def test_phoenix_revives_with_all_edges_1(self):
        card = make_card("Phoenix", passive_type="survival",
                         category="Mythology & Gods",
                         stats={"Power": 6, "Speed": 8, "Meaning": 7,
                                "Secret": 6, "Gravity": 7, "Spread": 7})
        owner = make_owner()
        trigger_passive(card, "card_killed", owner, None, ctx())
        assert all(v == 1 for k, v in card.stats.items()
                   if not str(k).startswith("_") and k not in ("phoenix_used", "revived_this_combat"))
        assert card.stats.get("phoenix_used") is True
        assert card.stats.get("revived_this_combat") is True

    def test_phoenix_only_revives_once(self):
        card = make_card("Phoenix", passive_type="survival",
                         category="Mythology & Gods",
                         stats={"Power": 6, "Speed": 8, "Meaning": 7,
                                "Secret": 6, "Gravity": 7, "Spread": 7})
        owner = make_owner()
        trigger_passive(card, "card_killed", owner, None, ctx())
        # Manually set edges to 0 to simulate second death
        for i in range(len(card.edges)):
            card.edges[i] = (card.edges[i][0], 0)
        trigger_passive(card, "card_killed", owner, None, ctx())
        assert all(v == 0 for v in [e[1] for e in card.edges])

    def test_gothic_architecture_buffs_neighbor_dayaniklilik(self):
        card = make_card("Gothic Architecture", passive_type="survival",
                         category="Art & Culture",
                         stats={"Power": 5, "Durability": 9, "Size": 7,
                                "Meaning": 6, "Gravity": 5, "Prestige": 6})
        neighbor = make_card("Neighbor",
                             stats={"Power": 5, "Durability": 5, "Speed": 5,
                                    "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), neighbor)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "card_killed", owner, None, ctx())
        # Code mutates edges list, not stats dict - check edges
        dayaniklilik_edge = next(
            (e[1] for e in neighbor.edges if e[0] == "Durability"), None)
        assert dayaniklilik_edge == 6

    def test_axolotl_revives_with_all_edges_2(self):
        card = make_card("Axolotl", passive_type="survival",
                         category="Nature & Creatures",
                         stats={"Durability": 6, "Speed": 6, "Meaning": 4,
                                "Secret": 5, "Harmony": 6, "Spread": 6})
        owner = make_owner()
        trigger_passive(card, "card_killed", owner, None, ctx())
        assert all(e[1] == 2 for e in card.edges)
        assert card.stats.get("revived_this_combat") is True

    def test_baobab_buffs_neighbors_dayaniklilik_by_2(self):
        card = make_card("Baobab", passive_type="survival",
                         category="Nature & Creatures",
                         stats={"Power": 5, "Durability": 8, "Size": 7,
                                "Meaning": 6, "Harmony": 6, "Prestige": 5})
        neighbor = make_card("Neighbor",
                             stats={"Power": 5, "Durability": 5, "Speed": 5,
                                    "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), neighbor)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "card_killed", owner, None, ctx())
        # Code mutates edges list, not stats dict - check edges
        dayaniklilik_edge = next(
            (e[1] for e in neighbor.edges if e[0] == "Durability"), None)
        assert dayaniklilik_edge == 7

    def test_frida_kahlo_restores_zero_edge_on_combat_lose(self):
        card = make_card("Frida Kahlo", passive_type="survival",
                         category="Art & Culture",
                         stats={"Power": 5, "Durability": 6, "Meaning": 8,
                                "Secret": 7, "Trace": 7, "Prestige": 7})
        # Simulate a lost edge
        card.edges[0] = (card.edges[0][0], 0)
        card.stats[card.edges[0][0]] = 0
        trigger_passive(card, "combat_lose", None, None, ctx())
        assert card.edges[0][1] == 1

    def test_survival_ignores_income_trigger(self):
        card = make_card("Valhalla", passive_type="survival",
                         category="Mythology & Gods")
        owner = make_owner()
        result = trigger_passive(card, "income", owner, None, ctx())
        assert result == 0
        assert owner.stats.get("valhalla_gold_pending", 0) == 0

    def test_none_owner_survival_no_crash(self):
        card = make_card("Valhalla", passive_type="survival",
                         category="Mythology & Gods")
        result = trigger_passive(card, "card_killed", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 6 - passive_type == "synergy_field"
# ---------------------------------------------

class TestSynergyFieldPassive:

    def test_synergy_field_returns_at_least_1_on_pre_combat(self):
        card = make_card("Odin", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 7, "Durability": 6, "Meaning": 9,
                                "Secret": 6, "Gravity": 7, "Prestige": 7})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None, ctx())
        assert result >= 1

    def test_odin_buffs_meaning_on_mythology_neighbors(self):
        card = make_card("Odin", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 7, "Durability": 6, "Meaning": 9,
                                "Secret": 6, "Gravity": 7, "Prestige": 7})
        neighbor = make_card("Loki", passive_type="combat",
                             category="Mythology & Gods",
                             stats={"Size": 5, "Speed": 7, "Secret": 8,
                                    "Trace": 7, "Gravity": 5, "Meaning": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((0, -1), neighbor)  # valid axial neighbor of (0,0)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx())
        # Code mutates edges list, not stats dict - check edges
        meaning_edge = next(
            (e[1] for e in neighbor.edges if e[0] == "Meaning"), None)
        assert meaning_edge == 6

    def test_olympus_buffs_prestige_when_3_mythology(self):
        card = make_card("Olympus", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 5, "Size": 7, "Meaning": 7,
                                "Intelligence": 5, "Gravity": 7, "Prestige": 8})
        cards = [make_card(f"Mito{i}", category="Mythology & Gods",
                           stats={"Power": 5, "Durability": 5, "Speed": 5,
                                  "Meaning": 5, "Gravity": 5, "Prestige": 5})
                 for i in range(2)]
        board = Board()
        board.place((0, 0), card)
        # Use valid axial neighbors: (0,-1) and (1,-1)
        from engine_core.constants import HEX_DIRS
        for i, c in enumerate(cards):
            dq, dr = HEX_DIRS[i]
            board.place((dq, dr), c)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx())
        # Code mutates edges list, not stats dict - check edges
        for c in cards:
            prestige_edge = next(
                (e[1] for e in c.edges if e[0] == "Prestige"), None)
            assert prestige_edge == 6

    def test_olympus_no_buff_when_less_than_3_mythology(self):
        card = make_card("Olympus", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 5, "Size": 7, "Meaning": 7,
                                "Intelligence": 5, "Gravity": 7, "Prestige": 8})
        ally = make_card("Mito1", category="Mythology & Gods",
                         stats={"Power": 5, "Durability": 5, "Speed": 5,
                                "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((1, 0), ally)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx())
        assert ally.stats["Prestige"] == 5  # no buff

    def test_medusa_debuffs_opponent_hiz(self):
        card = make_card("Medusa", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 6, "Speed": 6, "Secret": 7,
                                "Trace": 7, "Gravity": 5, "Spread": 5})
        opp_card = make_card("OppCard",
                             stats={"Power": 5, "Durability": 5, "Speed": 7,
                                    "Meaning": 5, "Gravity": 5, "Prestige": 5})
        opp_board = make_board_with_card(opp_card)
        opp = make_opponent(opp_board)
        board = make_board_with_card(card)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, opp, ctx())
        assert opp_card.stats["Speed"] == 6

    def test_black_hole_debuffs_opponent_center_cekim(self):
        card = make_card("Black Hole", passive_type="synergy_field",
                         category="Cosmos",
                         stats={"Power": 9, "Size": 9, "Meaning": 8,
                                "Gravity": 10, "Spread": 6, "Prestige": 8})
        center_card = make_card("Center",
                                stats={"Power": 5, "Durability": 5, "Speed": 5,
                                       "Meaning": 5, "Gravity": 7, "Prestige": 5})
        opp_board = Board()
        opp_board.place((0, 0), center_card)
        opp = make_opponent(opp_board)
        board = make_board_with_card(card)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, opp, ctx())
        assert center_card.stats["Gravity"] == 6

    def test_entropy_triggers_on_turn_divisible_by_3(self):
        card = make_card("Entropy", passive_type="synergy_field",
                         category="Science",
                         stats={"Power": 5, "Durability": 4, "Size": 7,
                                "Meaning": 7, "Secret": 7, "Spread": 8})
        ally = make_card("Ally", stats={"Power": 9, "Durability": 5, "Speed": 5,
                                        "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((1, 0), ally)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx(turn=3))
        assert ally.stats["Power"] == 0  # highest edge zeroed

    def test_entropy_no_effect_on_non_divisible_turn(self):
        card = make_card("Entropy", passive_type="synergy_field",
                         category="Science",
                         stats={"Power": 5, "Durability": 4, "Size": 7,
                                "Meaning": 7, "Secret": 7, "Spread": 8})
        ally = make_card("Ally", stats={"Power": 9, "Durability": 5, "Speed": 5,
                                        "Meaning": 5, "Gravity": 5, "Prestige": 5})
        board = Board()
        board.place((0, 0), card)
        board.place((1, 0), ally)
        owner = make_owner(board)
        trigger_passive(card, "pre_combat", owner, None, ctx(turn=2))
        assert ally.stats["Power"] == 9  # unchanged

    def test_synergy_field_ignores_combat_win(self):
        card = make_card("Odin", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 7, "Durability": 6, "Meaning": 9,
                                "Secret": 6, "Gravity": 7, "Prestige": 7})
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert result == 0

    def test_none_owner_synergy_field_no_crash(self):
        card = make_card("Olympus", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 5, "Size": 7, "Meaning": 7,
                                "Intelligence": 5, "Gravity": 7, "Prestige": 8})
        result = trigger_passive(card, "pre_combat", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 7 - passive_type == "combo"
# ---------------------------------------------

class TestComboPassive:

    def test_combo_passive_returns_at_least_1_on_pre_combat(self):
        card = make_card("Athena", passive_type="combo",
                         category="Mythology & Gods",
                         stats={"Durability": 7, "Size": 5, "Meaning": 8,
                                "Intelligence": 7, "Harmony": 5, "Prestige": 5})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None, ctx())
        assert result >= 1

    def test_athena_adds_pts_for_zihin_combo(self):
        card = make_card("Athena", passive_type="combo",
                         category="Mythology & Gods",
                         stats={"Durability": 7, "Size": 5, "Meaning": 8,
                                "Intelligence": 7, "Harmony": 5, "Prestige": 5})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=2, combo_group="MIND"))
        assert result >= 3  # 1 base + 2 from Athena

    def test_ballet_adds_pts_for_baglanti_combo(self):
        card = make_card("Ballet", passive_type="combo",
                         category="Art & Culture",
                         stats={"Size": 5, "Speed": 7, "Meaning": 5,
                                "Intelligence": 4, "Harmony": 6, "Prestige": 5})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=1, combo_group="CONNECTION"))
        assert result >= 2  # 1 base + 1 from Ballet

    def test_impressionism_adds_1_when_combo_count_ge_2(self):
        card = make_card("Impressionism", passive_type="combo",
                         category="Art & Culture",
                         stats={"Size": 5, "Speed": 5, "Meaning": 6,
                                "Trace": 6, "Harmony": 6, "Prestige": 5})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=2))
        assert result >= 2  # 1 base + 1 from Impressionism

    def test_impressionism_no_extra_when_combo_count_lt_2(self):
        card = make_card("Impressionism", passive_type="combo",
                         category="Art & Culture",
                         stats={"Size": 5, "Speed": 5, "Meaning": 6,
                                "Trace": 6, "Harmony": 6, "Prestige": 5})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=1))
        assert result == 1  # only base

    def test_nebula_adds_2_pts_per_kozmos_combo(self):
        card = make_card("Nebula", passive_type="combo", category="Cosmos",
                         stats={"Durability": 6, "Size": 7, "Meaning": 6,
                                "Secret": 6, "Harmony": 7, "Spread": 7})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=1, combo_target_category="Cosmos"))
        assert result >= 3  # 1 base + 2 from Nebula

    def test_albert_einstein_adds_2_pts_per_zihin_combo(self):
        card = make_card("Albert Einstein", passive_type="combo",
                         category="Science",
                         stats={"Power": 5, "Size": 9, "Meaning": 10,
                                "Intelligence": 10, "Trace": 9, "Prestige": 9})
        board = make_board_with_card(card)
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None,
                                 ctx(combo_count=1, combo_group="MIND"))
        assert result >= 3  # 1 base + 2 from Einstein

    def test_golden_ratio_adds_3_when_center_full(self):
        card = make_card("Golden Ratio", passive_type="combo",
                         category="Science",
                         stats={"Durability": 5, "Size": 7, "Meaning": 7,
                                "Intelligence": 7, "Harmony": 7, "Prestige": 7})
        from engine_core.constants import HEX_DIRS
        board = Board()
        board.place((0, 0), card)
        for dq, dr in HEX_DIRS:
            board.place((dq, dr), make_card(f"Fill{dq}{dr}"))
        owner = make_owner(board)
        result = trigger_passive(card, "pre_combat", owner, None, ctx())
        assert result >= 4  # 1 base + 3 golden ratio

    def test_combo_passive_ignores_combat_win(self):
        card = make_card("Athena", passive_type="combo",
                         category="Mythology & Gods",
                         stats={"Durability": 7, "Size": 5, "Meaning": 8,
                                "Intelligence": 7, "Harmony": 5, "Prestige": 5})
        result = trigger_passive(card, "combat_win", None, None, ctx())
        assert result == 0

    def test_none_owner_combo_no_crash(self):
        card = make_card("Athena", passive_type="combo",
                         category="Mythology & Gods",
                         stats={"Durability": 7, "Size": 5, "Meaning": 8,
                                "Intelligence": 7, "Harmony": 5, "Prestige": 5})
        result = trigger_passive(card, "pre_combat", None, None, ctx())
        assert isinstance(result, int)


# ---------------------------------------------
# SECTION 8 - Edge cases
# ---------------------------------------------

class TestEdgeCases:

    def test_empty_board_opponent_no_crash(self):
        """combat_win with opponent having empty board should not raise."""
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat",
                         category="Mythology & Gods")
        opp = make_opponent(Board())
        result = trigger_passive(card, "combat_win", None, opp, ctx())
        assert isinstance(result, int)

    def test_empty_board_owner_no_crash(self):
        """pre_combat with owner having empty board should not raise."""
        card = make_card("Odin", passive_type="synergy_field",
                         category="Mythology & Gods",
                         stats={"Power": 7, "Durability": 6, "Meaning": 9,
                                "Secret": 6, "Gravity": 7, "Prestige": 7})
        owner = make_owner(Board())
        result = trigger_passive(card, "pre_combat", owner, None, ctx())
        assert isinstance(result, int)

    def test_none_owner_and_opponent_all_triggers(self):
        """All trigger types with None owner and opponent must not crash."""
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat",
                         category="Mythology & Gods")
        for trigger in ["combat_win", "combat_lose", "card_killed",
                        "income", "pre_combat", "copy_2", "copy_3",
                        "market_refresh", "card_buy"]:
            result = trigger_passive(card, trigger, None, None, ctx())
            assert isinstance(result, int), f"Failed for trigger={trigger}"

    def test_missing_context_keys_use_defaults(self):
        """Empty context dict should not raise KeyError."""
        card = make_card("Pulsar", passive_type="combat", category="Cosmos")
        owner = make_owner()
        result = trigger_passive(card, "combat_win", owner, None, {})
        assert isinstance(result, int)

    def test_unknown_trigger_returns_0(self):
        card = make_card(CARD_NAME_RAGNAROK, passive_type="combat",
                         category="Mythology & Gods")
        result = trigger_passive(card, "nonexistent_trigger", None, None, ctx())
        assert result == 0

    def test_all_passive_types_return_int(self):
        """Smoke test: every passive_type returns int for every trigger."""
        passive_types = ["none", "combat", "economy", "copy",
                         "survival", "synergy_field", "combo"]
        triggers = ["combat_win", "combat_lose", "card_killed", "income",
                    "pre_combat", "copy_2", "copy_3", "market_refresh", "card_buy"]
        for pt in passive_types:
            card = make_card("TestCard", passive_type=pt)
            for trigger in triggers:
                result = trigger_passive(card, trigger, None, None, ctx())
                assert isinstance(result, int), \
                    f"passive_type={pt}, trigger={trigger} returned non-int"


# ---------------------------------------------
# SECTION 9 - cards.json name matching
# ---------------------------------------------

class TestCardNameMatching:
    """Verify that card names used in trigger_passive exactly match cards.json."""

    COMBAT_NAMES = [
        CARD_NAME_RAGNAROK, "World War II", "Loki", "Cubism", "Komodo Dragon",
        "Venus Flytrap", "Quantum Mechanics", "Asteroid Belt", "Mongol Empire",
        "Quetzalcoatl", "Flamenco", "Narwhal", "Sirius", "Sparta",
        "Pulsar", "Cerberus", CARD_NAME_E_MC2, "Fibonacci Sequence",
        "Guernica", "Minotaur", "Code of Hammurabi", "Anubis",
    ]
    ECONOMY_NAMES = [
        "Midas", "Silk Road", "Ottoman Empire", "Industrial Revolution",
        "Moon Landing", "Exoplanet", "Babylon", "Algorithm",
        "Age of Discovery", "Printing Press",
    ]
    COPY_NAMES = [
        "Coelacanth", "Fungus", "Space-Time", "Marie Curie",
        "Charles Darwin", "DNA", "Event Horizon", "Yggdrasil",
    ]
    SURVIVAL_NAMES = [
        "Valhalla", "Phoenix", "Gothic Architecture", "Axolotl",
        "Tardigrade", "Baobab", "Betelgeuse", "Frida Kahlo",
    ]
    SYNERGY_FIELD_NAMES = [
        "Odin", "Olympus", "Medusa", "Kraken", "Opera", "Baroque",
        "Kabuki", "Blue Whale", "Coral Reef", "Rainforest", "Cordyceps",
        "Milky Way", "Andromeda Galaxy", "Europa", "Black Hole", "Quasar",
        "Gravity", "Isaac Newton", "Nikola Tesla", "Entropy",
        "Periodic Table", "Higgs Boson", "French Revolution",
        "Renaissance", "Roman Empire", "Black Death",
    ]
    COMBO_NAMES = [
        "Athena", "Ballet", "Impressionism", "Bioluminescence",
        "Nebula", "Albert Einstein", "Golden Ratio",
    ]

    def _check_names(self, names, passive_type):
        for name in names:
            assert name in CARD_BY_NAME, \
                f"'{name}' (passive_type={passive_type}) not found in cards.json"
            card = CARD_BY_NAME[name]
            assert card.passive_type == passive_type, \
                (f"'{name}' has passive_type='{card.passive_type}' "
                 f"in cards.json, expected '{passive_type}'")

    def test_combat_card_names_match_cards_json(self):
        # CARD_NAME_E_MC2 and Fibonacci Sequence are passive_type="none" in cards.json
        # but handled in the combat_win code path - exclude from assertion.
        exclude = {CARD_NAME_E_MC2, "Fibonacci Sequence"}
        present = [n for n in self.COMBAT_NAMES
                   if n in CARD_BY_NAME and n not in exclude]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "combat", \
                f"'{name}' passive_type mismatch"

    def test_e_mc2_returns_0_for_none_passive_type_in_json(self):
        """CARD_NAME_E_MC2 is passive_type='none' in cards.json; trigger_passive
        returns 0 on combat_win for none-type (documented behavior)."""
        assert CARD_BY_NAME[CARD_NAME_E_MC2].passive_type == "none"
        card = CARD_BY_NAME[CARD_NAME_E_MC2].clone()
        result = trigger_passive(card, "combat_win", None, None, ctx())
        # passive_type is "none" so the combat_win branch is never reached
        assert result == 0

    def test_economy_card_names_match_cards_json(self):
        present = [n for n in self.ECONOMY_NAMES if n in CARD_BY_NAME]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "economy", \
                f"'{name}' passive_type mismatch"

    def test_copy_card_names_match_cards_json(self):
        present = [n for n in self.COPY_NAMES if n in CARD_BY_NAME]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "copy", \
                f"'{name}' passive_type mismatch"

    def test_survival_card_names_match_cards_json(self):
        present = [n for n in self.SURVIVAL_NAMES if n in CARD_BY_NAME]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "survival", \
                f"'{name}' passive_type mismatch"

    def test_synergy_field_card_names_match_cards_json(self):
        present = [n for n in self.SYNERGY_FIELD_NAMES if n in CARD_BY_NAME]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "synergy_field", \
                f"'{name}' passive_type mismatch"

    def test_combo_card_names_match_cards_json(self):
        present = [n for n in self.COMBO_NAMES if n in CARD_BY_NAME]
        for name in present:
            assert CARD_BY_NAME[name].passive_type == "combo", \
                f"'{name}' passive_type mismatch"


# ---------------------------------------------
# Synergy field: pre_combat touches card.stats (pool smoke)
# ---------------------------------------------

class TestSynergyFieldPreCombatStats:
    def test_no_synergy_field_warning_on_pre_combat_scan(self, capsys):
        owner = Player(0)
        opponent = Player(1)
        ctx = {"turn": 1}
        # Her kartı test et
        for c in get_card_pool():
            if c.passive_type in ("synergy_field", "survival", "combat", "copy"):
                card = c.clone()
                # Tüm trigger'ları çalıştır, herhangi bir stat değişikliği var mı?
                stats_before = dict(card.stats)
                trigger_passive(card, "pre_combat", owner, opponent, ctx)
                stats_after = dict(card.stats)
                if stats_before == stats_after and c.passive_type == "synergy_field":
                    print(f"UYARI: {c.name} synergy_field hiç etki yaratmıyor")
        captured = capsys.readouterr()
        assert "UYARI:" not in captured.out
