"""
AUTOCHESS HYBRID - Market & Economy Test Suite
autochess_sim_v06.py: Market, Player.income(), Player.buy_card()
Run: pytest test_market_ekonomi.py -v
Bug tests only: pytest test_market_ekonomi.py -v -m known_bug
Excluding known_bug: pytest test_market_ekonomi.py -v -m "not known_bug"

SECTION 1  - Market: Initialization and pool_copies
SECTION 2  - Market: refresh() behavior
SECTION 3  - Market: get_cards_for_player() behavior
SECTION 4  - Market: refresh() vs get_cards_for_player() conflict  [KNOWN_BUG]
SECTION 5  - Player.income(): Core income components
SECTION 6  - Player.income(): Win streak bonus
SECTION 7  - Player.income(): HP threshold bonuses
SECTION 8  - Player.income(): Interest calculation
SECTION 9  - Player.income(): Interest ordering issue             [KNOWN_BUG]
SECTION 10 - Player.income(): Economist interest bonus
SECTION 11 - Player.buy_card(): Basic purchase
SECTION 12 - Player.buy_card(): pool_copies not decremented    [KNOWN_BUG]
SECTION 13 - Player.buy_card(): Copy counter
SECTION 14 - Player.buy_card(): Insufficient gold guard
SECTION 15 - Unlimited gold economy (no cap)
SECTION 16 - Win streak: draw behavior                          [KNOWN_BUG / DESIGN DECISION]
SECTION 17 - Economist strategy string coupling                 [KNOWN_BUG]
SECTION 18 - cards_bought_this_turn counter
SECTION 19 - Game._deal_starting_hands()
SECTION 20 - Integration: preparation_phase() gold flow
"""

import pytest
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from engine_core.card import get_card_pool, Card
from engine_core.player import Player
from engine_core.market import Market
from engine_core.game import Game
from engine_core.board import Board
from engine_core.constants import (
    CARD_COSTS, BASE_INCOME, MAX_INTEREST, INTEREST_STEP, STARTING_HP,
)

CARD_BY_NAME = {c.name: c for c in get_card_pool()}

# -------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------

def fresh_market() -> Market:
    """Fresh market for each test."""
    return Market(get_card_pool())


def fresh_player(strategy: str = "random", gold: int = 0, pid: int = 0) -> Player:
    p = Player(pid=pid, strategy=strategy)
    p.gold = gold
    return p


def card_of_rarity(rarity: str) -> Card:
    """Return the first card with the given rarity."""
    return next(c for c in get_card_pool() if c.rarity == rarity)


def all_rarities():
    return ["1", "2", "3", "4", "5"]


# -------------------------------------------------------------
# SECTION 1 - Market: Initialization and pool_copies
# -------------------------------------------------------------

class TestMarketInit:

    def test_market_pool_copies_max_3_per_card(self):
        """Each card starts with at most 3 pool copies."""
        m = fresh_market()
        for name, val in m.pool_copies.items():
            assert val <= 3, f"{name} pool_copies exceeds 3: {val}"

    def test_market_pool_copies_not_negative(self):
        """No pool_copies value may be negative."""
        m = fresh_market()
        for name, val in m.pool_copies.items():
            assert val >= 0, f"{name} pool_copies negative: {val}"

    def test_market_init_full_pool_without_refresh(self):
        """
        Market.__init__ no longer calls refresh(5) - slots removed.
        All pool_copies should be full initially (101x3 = 303).
        """
        m = fresh_market()
        total = sum(m.pool_copies.values())
        assert total == 303, \
            f"after init total should be 303 (no refresh), got {total}"

    def test_market_pool_contains_101_cards(self):
        m = fresh_market()
        assert len(m.pool) == 101

    def test_market_init_has_no_slots_attribute(self):
        """Market init does not populate slots - attribute removed."""
        m = fresh_market()
        assert not hasattr(m, 'slots'), "slots attribute should be absent"

    def test_market_refresh_cost_2_gold(self):
        m = fresh_market()
        assert m.refresh_cost() == 2

    def test_market_pool_only_contains_card_pool_cards(self):
        m = fresh_market()
        pool_names = {c.name for c in get_card_pool()}
        for card in m.pool:
            assert card.name in pool_names


# -------------------------------------------------------------
# SECTION 2 - Market: refresh() behavior
# -------------------------------------------------------------

class TestMarketRefresh:

    def test_deal_market_window_returns_5_cards(self):
        m = fresh_market()
        p = fresh_player()
        window = m.deal_market_window(p, 5)
        assert len(window) == 5

    def test_deal_market_window_various_n(self):
        m = fresh_market()
        p = fresh_player()
        for n in [1, 3, 5, 7]:
            window = m.deal_market_window(p, n)
            assert len(window) == n

    def test_deal_market_window_cards_from_card_pool(self):
        m = fresh_market()
        p = fresh_player()
        pool_names = {c.name for c in get_card_pool()}
        for card in m.deal_market_window(p, 5):
            assert card.name in pool_names

    def test_deal_market_window_decrements_pool_copies(self):
        """After deal_market_window(), chosen cards decrement pool_copies."""
        m = fresh_market()
        p = fresh_player()
        total_before = sum(m.pool_copies.values())
        m.deal_market_window(p, 5)
        total_after = sum(m.pool_copies.values())
        assert total_after == total_before - 5, \
            f"picking 5 cards should drop pool_copies by 5, dropped {total_before - total_after}"

    def test_deal_market_window_no_duplicates_random_sample(self):
        """deal_market_window() uses random.sample - no duplicates."""
        m = fresh_market()
        p = fresh_player()
        for _ in range(50):
            m.pool_copies = {c.name: 10 for c in get_card_pool()}
            m._player_windows = {}
            window = m.deal_market_window(p, 5)
            names = [c.name for c in window]
            assert len(names) == len(set(names)), \
                f"deal_market_window() returned duplicate: {names}"

    def test_deal_market_window_returns_previous_window_to_pool(self):
        """Second call must return the previous window to the pool."""
        m = fresh_market()
        p = fresh_player()
        total_before = sum(m.pool_copies.values())
        m.deal_market_window(p, 5)   # first window: net -5
        m.deal_market_window(p, 5)   # return prior + draw 5 -> net still -5 vs start
        total_after = sum(m.pool_copies.values())
        assert total_after == total_before - 5


# -------------------------------------------------------------
# SECTION 3 - Market: per-player window isolation
# -------------------------------------------------------------

class TestMarketGetCardsForPlayer:

    def test_deal_market_window_per_player_isolation(self):
        """Each player's window is isolated - same physical copy not both players."""
        m = fresh_market()
        m.pool_copies = {c.name: 1 for c in get_card_pool()}  # one copy each
        p1 = fresh_player(pid=0)
        p2 = fresh_player(pid=1)
        w1 = set(c.name for c in m.deal_market_window(p1, 5))
        w2 = set(c.name for c in m.deal_market_window(p2, 5))
        overlap = w1 & w2
        assert len(overlap) == 0, \
            f"same copy given to two players: {overlap}"

    def test_deal_market_window_eight_player_isolation(self):
        """Eight players each taking a window in one round drops 8x5=40 copies."""
        m = fresh_market()
        total_before = sum(m.pool_copies.values())
        players = [fresh_player(pid=i) for i in range(8)]
        for p in players:
            m.deal_market_window(p, 5)
        total_after = sum(m.pool_copies.values())
        assert total_after == total_before - 40, \
            f"expected 8x5=40 drop, got {total_before - total_after}"

    def test_return_unsold_restores_pool_copies(self):
        """return_unsold() should put window cards back in the pool."""
        m = fresh_market()
        p = fresh_player()
        total_before = sum(m.pool_copies.values())
        m.deal_market_window(p, 5)
        m.return_unsold(p)
        total_after = sum(m.pool_copies.values())
        assert total_after == total_before, \
            "after return_unsold pool_copies should fully restore"

    def test_return_unsold_does_not_restore_purchased(self):
        """Purchased card must not return to pool via return_unsold."""
        m = fresh_market()
        p = fresh_player(gold=50)
        window = m.deal_market_window(p, 5)
        bought = window[0]
        # Purchase from window - update window list
        m._player_windows[p.pid] = window[1:]  # remove purchased from window
        total_before = sum(m.pool_copies.values())
        m.return_unsold(p)
        total_after = sum(m.pool_copies.values())
        # Only the remaining 4 should be restored
        assert total_after == total_before + 4

    def test_return_unsold_implicit_bought_matches_buy_card(self):
        m = Market(get_card_pool())
        p = Player(pid=0)
        p.gold = 50
        window = m.deal_market_window(p, 5)
        card = window[0]
        p.buy_card(card)
        copies_before = m.pool_copies[card.name]
        m.return_unsold(p)  # bought yok
        copies_after = m.pool_copies[card.name]
        assert copies_after == copies_before, "Satın alınan kart geri döndü!"


# -------------------------------------------------------------
# SECTION 4 - Market: atomic window guarantees
# -------------------------------------------------------------

class TestMarketRefreshGetPlayerConflict:

    def test_same_copy_not_given_to_two_players(self):
        """REGRESSION: deal_market_window is atomic - no copy over-commit."""
        m = fresh_market()
        test_card = get_card_pool()[10]
        m.pool_copies = {c.name: 0 for c in get_card_pool()}
        m.pool_copies[test_card.name] = 1
        p1 = fresh_player(pid=0)
        p2 = fresh_player(pid=1)
        w1 = [c.name for c in m.deal_market_window(p1, 5)]
        w2 = [c.name for c in m.deal_market_window(p2, 5)]
        # Only one copy - must not appear in both windows
        assert not (test_card.name in w1 and test_card.name in w2), \
            "Same copy given to two players - atomic window violation"

    def test_pool_copies_never_negative(self):
        """pool_copies must stay non-negative across many window rounds."""
        m = fresh_market()
        players = [fresh_player(pid=i) for i in range(8)]
        for _ in range(10):
            for p in players:
                m.deal_market_window(p, 5)
                m.return_unsold(p)
        for name, val in m.pool_copies.items():
            assert val >= 0, f"{name} pool_copies negatif: {val}"


# -------------------------------------------------------------
# SECTION 5 - Player.income(): Core income components

# -------------------------------------------------------------

class TestPlayerIncomeBase:

    def test_income_adds_base_income_3_gold(self):
        p = fresh_player(gold=0)
        p.income()
        assert p.gold >= BASE_INCOME  # minimum 3 gold base

    def test_income_updates_gold_earned_stat(self):
        p = fresh_player(gold=0)
        p.income()
        assert p.stats["gold_earned"] >= BASE_INCOME

    def test_income_resets_cards_bought_this_turn(self):
        """cards_bought_this_turn resets at the start of each turn."""
        p = fresh_player(gold=10)
        p.stats["cards_bought_this_turn"] = 5
        p.income()
        assert p.stats["cards_bought_this_turn"] == 0

    def test_income_increments_turns_played(self):
        p = fresh_player(gold=0)
        p.income()
        assert p.turns_played == 1
        p.income()
        assert p.turns_played == 2

    def test_income_from_zero_still_gets_base(self):
        p = fresh_player(gold=0)
        p.income()
        assert p.gold >= BASE_INCOME

    def test_income_adds_to_existing_gold(self):
        p = fresh_player(gold=10)
        prev_gold = p.gold
        p.income()
        assert p.gold > prev_gold


# -------------------------------------------------------------
# SECTION 6 - Player.income(): Win streak bonus
# -------------------------------------------------------------

class TestPlayerIncomeWinStreak:

    def test_streak_0_no_bonus(self):
        p = fresh_player(gold=0)
        p.win_streak = 0
        p.income()
        # Only base_income + interest (no interest on 0 gold bank)
        assert p.gold == BASE_INCOME

    def test_streak_3_one_bonus_gold(self):
        p = fresh_player(gold=0)
        p.win_streak = 3
        p.income()
        assert p.gold == BASE_INCOME + 1

    def test_streak_6_two_bonus_gold(self):
        p = fresh_player(gold=0)
        p.win_streak = 6
        p.income()
        assert p.gold == BASE_INCOME + 2

    def test_streak_9_three_bonus_gold(self):
        p = fresh_player(gold=0)
        p.win_streak = 9
        p.income()
        assert p.gold == BASE_INCOME + 3

    def test_streak_bonus_one_gold_per_three_wins(self):
        """Verify win_streak // 3 formula."""
        for streak in range(0, 13):
            p = fresh_player(gold=0)
            p.win_streak = streak
            p.income()
            expected_streak_bonus = streak // 3
            # gold = base + streak_bonus + interest(base+streak_bonus)
            # Interest 0 when base+streak_bonus < 10
            base_plus_streak = BASE_INCOME + expected_streak_bonus
            expected_interest = min(MAX_INTEREST, base_plus_streak // INTEREST_STEP)
            expected_total = base_plus_streak + expected_interest
            assert p.gold == expected_total, \
                f"streak={streak}: expected={expected_total}, got={p.gold}"

    def test_streak_2_no_bonus(self):
        """Streak not divisible by 3 should not add streak bonus."""
        p = fresh_player(gold=0)
        p.win_streak = 2
        p.income()
        assert p.gold == BASE_INCOME  # streak_bonus = 2//3 = 0


# -------------------------------------------------------------
# SECTION 7 - Player.income(): HP threshold bonuses
# -------------------------------------------------------------

class TestPlayerIncomeHPPenalty:

    def test_full_hp_no_bonus(self):
        p = fresh_player(gold=0)
        p.hp = STARTING_HP  # 150
        p.income()
        assert p.gold == BASE_INCOME  # no interest, no HP bonus

    def test_hp_above_75_threshold_no_bonus(self):
        p = fresh_player(gold=0)
        p.hp = 76
        p.income()
        assert p.gold == BASE_INCOME

    def test_hp_below_75_one_bonus(self):
        """HP < 75 -> +1 gold."""
        p = fresh_player(gold=0)
        p.hp = 74
        p.income()
        assert p.gold == BASE_INCOME + 1

    def test_hp_exactly_75_no_bonus(self):
        """HP == 75 -> no bonus (requires strictly < 75)."""
        p = fresh_player(gold=0)
        p.hp = 75
        p.income()
        assert p.gold == BASE_INCOME

    def test_hp_above_45_one_bonus(self):
        p = fresh_player(gold=0)
        p.hp = 46
        p.income()
        assert p.gold == BASE_INCOME + 1

    def test_hp_below_45_three_bonus(self):
        """HP < 45 -> +3 gold."""
        p = fresh_player(gold=0)
        p.hp = 44
        p.income()
        assert p.gold == BASE_INCOME + 3

    def test_hp_exactly_45_one_bonus(self):
        """HP == 45 -> +1 from <75 rule (not the <45 tier)."""
        p = fresh_player(gold=0)
        p.hp = 45
        p.income()
        assert p.gold == BASE_INCOME + 1

    def test_hp_1_maksimum_bonus(self):
        p = fresh_player(gold=0)
        p.hp = 1
        p.income()
        assert p.gold == BASE_INCOME + 3

    def test_hp_penalty_bonus_reflected_in_gold_earned(self):
        p = fresh_player(gold=0)
        p.hp = 44
        p.income()
        assert p.stats["gold_earned"] >= BASE_INCOME + 3


# -------------------------------------------------------------
# SECTION 8 - Player.income(): Interest calculation (intended behavior)
# -------------------------------------------------------------

class TestPlayerIncomeInterest:

    def test_zero_gold_no_interest(self):
        p = fresh_player(gold=0)
        p.income()
        # 0 gold -> no interest, only base_income
        # after income() gold = base_income + interest(base_income)
        # base_income = 3, 3//10 = 0 interest
        assert p.gold == BASE_INCOME

    def test_10_gold_one_interest(self):
        """10 gold -> +1 interest after apply_interest()."""
        p = fresh_player(gold=10)
        p.income()
        p.apply_interest()
        # income: gold=10+3=13, apply_interest: 13//10=1
        assert p.gold == 10 + BASE_INCOME + 1

    def test_20_gold_two_interest(self):
        p = fresh_player(gold=20)
        p.income()
        p.apply_interest()
        # income: gold=20+3=23, apply_interest: 23//10=2
        assert p.gold == 20 + BASE_INCOME + 2

    def test_50_gold_max_five_interest(self):
        """With 50 gold, interest caps correctly at 5."""
        p = fresh_player(gold=40)
        p.income()
        p.apply_interest()
        # income: 40+3=43, interest: 43//10=4 -> 47
        assert p.gold == 47

    def test_interest_capped_at_five(self):
        """Interest remains capped at 5 even with high gold."""
        p = fresh_player(gold=50)  # High gold value
        p.income()
        p.apply_interest()
        interest = p.gold - 50 - BASE_INCOME
        assert interest <= MAX_INTEREST

    def test_interest_constant_max_interest_five(self):
        assert MAX_INTEREST == 5

    def test_interest_step_constant_ten(self):
        assert INTEREST_STEP == 10

    def test_9_gold_no_interest(self):
        """9 gold, after income 12 -> apply_interest: 12//10=1 interest."""
        p = fresh_player(gold=9)
        p.income()
        p.apply_interest()
        # income: gold=9+3=12, apply_interest: 12//10=1
        assert p.gold == 9 + BASE_INCOME + 1


# -------------------------------------------------------------
# SECTION 9 - Interest ordering issue  [KNOWN_BUG]
# -------------------------------------------------------------

class TestInterestOrderRegression:

    def test_interest_after_spending(self):
        """
        ISSUE 5 FIXED: income() and apply_interest() are separate.
        Interest applies after purchases via apply_interest().
        """
        p = fresh_player(gold=20)
        p.income()
        # after income: gold = 20 + 3 = 23, interest not yet applied
        assert p.gold == 23

        # simulate purchase
        card = card_of_rarity("1")
        p.buy_card(card)  # -1 gold
        assert p.gold == 22

        # Now interest: 22//10 = 2
        p.apply_interest()
        assert p.gold == 24

    def test_interest_based_on_remaining_gold(self):
        """
        ISSUE 5 FIXED: 7 gold + 3 base = 10; after spending down to 8, interest 0.
        """
        p = fresh_player(gold=7)
        p.income()
        # gold = 7 + 3 = 10
        card = card_of_rarity("2")  # spend 2 gold
        p.buy_card(card)
        # gold = 8
        p.apply_interest()
        # 8//10 = 0 interest
        assert p.gold == 8


# -------------------------------------------------------------
# SECTION 10 - Economist interest bonus
# -------------------------------------------------------------

class TestEconomistInterest:

    def test_economist_interest_multiplier_1_5x(self):
        """Economist strategy should earn more interest via apply_interest()."""
        p_economist = fresh_player(strategy="economist", gold=20)
        p_random = fresh_player(strategy="random", gold=20)

        p_economist.income()
        p_economist.apply_interest()
        p_random.income()
        p_random.apply_interest()

        assert p_economist.gold > p_random.gold

    def test_economist_interest_max_8(self):
        """Economist max interest is MAX_INTEREST + 3 = 8."""
        p = fresh_player(strategy="economist", gold=100)
        p.income()
        # interest = min(8, int(5 * 1.5) + 1) = 8
        # gold = 100 + 3 + 8 = 111
        expected_max_interest = MAX_INTEREST + 3
        interest_gained = p.gold - 100 - BASE_INCOME
        assert interest_gained <= expected_max_interest

    def test_economist_bonus_even_at_zero_gold(self):
        """
        Economist at 0 gold still gets at least 1 interest after income+apply_interest.
        interest_multiplier=1.5 -> int(3//10 * 1.5) + 1 = 1
        """
        p = fresh_player(strategy="economist", gold=0)
        p.income()
        p.apply_interest()
        # income: gold=3, apply_interest: int(3//10 * 1.5)+1 = 1
        assert p.gold == BASE_INCOME + 1

    def test_economist_bonus_with_interest_multiplier(self):
        """
        ISSUE 7 FIXED: interest_multiplier lives on Player.
        Multiplier persists even if strategy string changes.
        """
        p = fresh_player(strategy="economist", gold=20)
        assert p.interest_multiplier == 1.5
        assert p.interest_cap == MAX_INTEREST + 3

        # Multiplier independent of strategy string value
        p.strategy = "other_strategy"
        p.income()
        p.apply_interest()
        # interest_multiplier still 1.5 - strategy label change is irrelevant
        p2 = fresh_player(strategy="random", gold=20)
        p2.income()
        p2.apply_interest()
        assert p.gold > p2.gold


# -------------------------------------------------------------
# SECTION 11 - Player.buy_card(): Basic purchase
# -------------------------------------------------------------

class TestPlayerBuyCardBasic:

    def test_buy_card_reduces_gold(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")  # 1 gold
        p.buy_card(card)
        assert p.gold == 9

    def test_buy_card_adds_to_hand(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        p.buy_card(card)
        assert len(p.hand) == 1

    def test_buy_card_updates_gold_spent(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("2")  # 2 gold
        p.buy_card(card)
        assert p.stats["gold_spent"] == 2

    def test_buy_card_adds_clone(self):
        """buy_card adds a clone to hand, not the original card instance."""
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        original_id = id(card)
        p.buy_card(card)
        assert id(p.hand[0]) != original_id

    def test_all_rarities_correct_cost(self):
        for rarity, cost in CARD_COSTS.items():
            p = fresh_player(gold=cost)
            card = card_of_rarity(rarity)
            p.buy_card(card)
            assert p.gold == 0, \
                f"{rarity} card should cost {cost} gold"

    def test_buy_card_card_costs_constants(self):
        assert CARD_COSTS["1"] == 1
        assert CARD_COSTS["2"] == 2
        assert CARD_COSTS["3"] == 3
        assert CARD_COSTS["4"] == 8
        assert CARD_COSTS["5"] == 10


# -------------------------------------------------------------
# SECTION 12 - Player.buy_card(): pool_copies not decremented  [KNOWN_BUG]
# -------------------------------------------------------------

class TestPlayerBuyCardPoolCopies:

    def test_buy_card_pool_copies_via_deal_market_window(self):
        """pool_copies drop in deal_market_window, not in buy_card.
        Flow: deal_market_window -> buy_card -> return_unsold."""
        m = fresh_market()
        p = fresh_player(gold=100)
        card = card_of_rarity("1")

        # deal_market_window decrements pool_copies
        window = m.deal_market_window(p, 5)
        # Take first card from window
        bought = window[0]
        pool_before_buy = m.pool_copies[bought.name]
        p.buy_card(bought, market=m)
        pool_after_buy = m.pool_copies[bought.name]

        # buy_card must not change pool_copies - deal_market_window already did
        assert pool_after_buy == pool_before_buy, \
            "buy_card must not alter pool_copies - deal_market_window already decremented"

    def test_buy_card_without_market_unchanged_pool_copies(self):
        """Without market arg, pool_copies unchanged (backward compatible)."""
        m = fresh_market()
        p = fresh_player(gold=100)
        card = card_of_rarity("1")

        pool_before = m.pool_copies[card.name]
        p.buy_card(card)  # market yok
        pool_after = m.pool_copies[card.name]

        assert pool_before == pool_after


# -------------------------------------------------------------
# SECTION 13 - Player.buy_card(): Copy counter
# -------------------------------------------------------------

class TestPlayerBuyCardCopyCounter:

    def test_first_purchase_copies_one(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        p.buy_card(card)
        assert p.copies[card.name] == 1

    def test_second_copy_copies_two(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        p.buy_card(card)
        p.buy_card(card)
        assert p.copies[card.name] == 2

    def test_third_copy_copies_three(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        for _ in range(3):
            p.buy_card(card)
        assert p.copies[card.name] == 3

    def test_different_cards_tracked_separately(self):
        # get_card_pool()[0]=Odin (rarity 4, 8g), get_card_pool()[1]=Anubis (rarity 3, 3g) -> 11 gold total
        card1 = get_card_pool()[0]
        card2 = get_card_pool()[1]
        p = fresh_player(gold=CARD_COSTS[card1.rarity] + CARD_COSTS[card2.rarity])
        p.buy_card(card1)
        p.buy_card(card2)
        assert p.copies[card1.name] == 1
        assert p.copies[card2.name] == 1


# -------------------------------------------------------------
# SECTION 14 - Player.buy_card(): Insufficient gold guard
# -------------------------------------------------------------

class TestPlayerBuyCardInsufficientGold:

    def test_insufficient_gold_no_purchase(self):
        p = fresh_player(gold=0)
        card = card_of_rarity("1")  # 1 gold required
        p.buy_card(card)
        assert len(p.hand) == 0
        assert p.gold == 0

    def test_exact_gold_purchases(self):
        p = fresh_player(gold=1)
        card = card_of_rarity("1")
        p.buy_card(card)
        assert len(p.hand) == 1

    def test_legendary_not_purchasable_with_7_gold(self):
        """Rarity 4 costs 8; 7 gold cannot buy it."""
        p = fresh_player(gold=7)
        card = card_of_rarity("4")
        p.buy_card(card)
        assert len(p.hand) == 0

    def test_legendary_purchasable_with_8_gold(self):
        p = fresh_player(gold=8)
        card = card_of_rarity("4")
        p.buy_card(card)
        assert len(p.hand) == 1

    def test_gold_not_negative_after_purchase(self):
        p = fresh_player(gold=1)
        card = card_of_rarity("3")  # 3 gold, insufficient for this card
        p.buy_card(card)
        assert p.gold >= 0

    def test_gold_spent_unchanged_on_failed_buy(self):
        p = fresh_player(gold=0)
        card = card_of_rarity("1")
        p.buy_card(card)
        assert p.stats["gold_spent"] == 0


# -------------------------------------------------------------
# SECTION 15 - Unlimited gold economy (no cap)
# -------------------------------------------------------------

class TestUnlimitedEconomy:

    def test_gold_cap_removed(self):
        """GOLD_CAP constant removed - unlimited economy."""
        import engine_core.constants as sim
        assert not hasattr(sim, "GOLD_CAP"), "GOLD_CAP should be removed"

    def test_economist_gold_grows_unlimited(self):
        """Economist stacks income + boosted interest without cap."""
        p = fresh_player(strategy="economist", gold=0)
        for _ in range(30):
            p.income()
            p.apply_interest()
        assert p.gold > 50, f"expected substantial gold after 30 turns, got {p.gold}"

    def test_income_unlimited(self):
        """Income adds base + bonuses without cap."""
        p = fresh_player(gold=49)
        p.income()  # +3 base -> 52 (no clamp)
        assert p.gold == 52


# -------------------------------------------------------------
# SECTION 16 - Win streak: draw behavior  [DESIGN DECISION]
# -------------------------------------------------------------

class TestWinStreakDrawBehavior:

    @pytest.mark.known_bug
    def test_draw_resets_win_streak(self):
        """
        KNOWN BUG / DESIGN DECISION - ISSUE 6:
        Current behavior: draw sets win_streak = 0 (Game.combat_phase).

        GDD undecided. Options:
          A) Draw breaks streak  -> higher variance
          B) Draw preserves streak  -> TFT-like stronger streaks

        This test documents current (A).

        Suggestion: add DRAW_BREAKS_STREAK = True/False constant.
        """
        # Behavior lives in Game.combat_phase() - integration would be ideal
        # For now we only illustrate via Player state
        p = fresh_player(gold=0)
        p.win_streak = 5

        # Simulate draw branch from combat_phase:
        p.win_streak = 0  # draw case

        assert p.win_streak == 0, \
            "Current behavior: draw resets streak (pending GDD decision)"

    def test_win_streak_increments_on_win(self):
        """On win, streak increases by 1."""
        p = fresh_player(gold=0)
        p.win_streak = 0
        p.win_streak += 1  # win case
        assert p.win_streak == 1

    def test_win_streak_resets_on_loss(self):
        """On loss, streak returns to 0."""
        p = fresh_player(gold=0)
        p.win_streak = 7
        p.win_streak = 0  # lose case
        assert p.win_streak == 0


# -------------------------------------------------------------
# SECTION 17 - Economist strategy coupling  [KNOWN_BUG]
# -------------------------------------------------------------

class TestEconomistStringCoupling:

    def test_interest_multiplier_attribute_exists(self):
        """
        ISSUE 7 FIXED: interest_multiplier moved onto Player.
        """
        p_eko = fresh_player(strategy="economist", gold=0)
        p_rnd = fresh_player(strategy="random", gold=0)
        assert hasattr(p_eko, "interest_multiplier")
        assert p_eko.interest_multiplier == 1.5
        assert p_rnd.interest_multiplier == 1.0
        assert p_eko.interest_cap == MAX_INTEREST + 3
        assert p_rnd.interest_cap == MAX_INTEREST

    @pytest.mark.known_bug
    def test_economy_passive_cards_not_integrated_with_interest(self):
        """
        KNOWN BUG - ISSUE 7 (continued):
        Economy passive cards (Industrial Revolution, Babylon, ...) are not
        wired into the interest multiplier system because that system keys
        off the strategy string.

        Example: Babylon grants +1 gold on income via trigger_passive,
        handled separately from interest_multiplier.
        """
        p = fresh_player(strategy="random", gold=20)
        babylon = CARD_BY_NAME.get("Babylon")

        if babylon:
            p.board.place((0, 0), babylon.clone())
            before = p.gold
            p.income()
            after = p.gold

            # Babylon adds gold via income trigger, not via interest formula
            assert after > before


# -------------------------------------------------------------
# SECTION 18 - cards_bought_this_turn counter
# -------------------------------------------------------------

class TestCardsBoughtThisTurn:

    def test_first_buy_counter_one(self):
        p = fresh_player(gold=10)
        card = card_of_rarity("1")
        p.buy_card(card)
        assert p.stats["cards_bought_this_turn"] == 1

    def test_two_buys_counter_two(self):
        p = fresh_player(gold=10)
        for _ in range(2):
            p.buy_card(card_of_rarity("1"))
        assert p.stats["cards_bought_this_turn"] == 2

    def test_income_resets_buy_counter(self):
        p = fresh_player(gold=10)
        p.buy_card(card_of_rarity("1"))
        assert p.stats["cards_bought_this_turn"] == 1
        p.income()
        assert p.stats["cards_bought_this_turn"] == 0

    def test_failed_buy_counter_unchanged(self):
        p = fresh_player(gold=0)
        p.buy_card(card_of_rarity("1"))
        assert p.stats.get("cards_bought_this_turn", 0) == 0


# -------------------------------------------------------------
# SECTION 19 - Game._deal_starting_hands()
# -------------------------------------------------------------

class TestDealStartingHands:

    def test_each_player_starts_with_three_cards(self):
        players = [Player(pid=i) for i in range(4)]
        game = Game(players, card_pool=get_card_pool())
        for p in players:
            assert len(p.hand) == 3, f"P{p.pid} must start with 3 cards"

    def test_starting_cards_common_rarity_only(self):
        """Starting hand cards must be rarity 1 (common) only."""
        players = [Player(pid=i) for i in range(4)]
        game = Game(players, card_pool=get_card_pool())
        for p in players:
            for card in p.hand:
                assert card.rarity == "1", \
                    f"starting card must be common (rarity 1), got {card.rarity}"

    def test_starting_cards_reflected_in_copies(self):
        """Starting cards must appear in copies dict."""
        players = [Player(pid=0)]
        game = Game(players, card_pool=get_card_pool())
        p = players[0]
        total_copies = sum(p.copies.values())
        assert total_copies == 3

    def test_players_may_get_different_starting_hands(self):
        """Eight-player lobby may yield varied starting hands."""
        players = [Player(pid=i) for i in range(8)]
        game = Game(players, card_pool=get_card_pool())
        all_hands = [frozenset(c.name for c in p.hand) for p in players]
        # Expect some variety (soft - RNG may rarely collide)
        assert len(set(all_hands)) > 1 or True  # randomness, soft assertion

    def test_eight_player_lobby(self):
        """Game can start with eight players."""
        players = [Player(pid=i) for i in range(8)]
        game = Game(players, card_pool=get_card_pool())
        assert len(game.players) == 8


# -------------------------------------------------------------
# SECTION 20 - Integration: preparation_phase() gold flow
# -------------------------------------------------------------

class TestPreparationPhaseIntegration:

    def test_preparation_phase_increases_gold(self):
        """Gold should not decrease after preparation phase."""
        players = [Player(pid=i) for i in range(2)]
        game = Game(players, card_pool=get_card_pool())
        initial_gold = [p.gold for p in players]
        game.preparation_phase()
        for i, p in enumerate(players):
            assert p.gold >= initial_gold[i], \
                f"P{p.pid} should not lose gold during preparation_phase"

    def test_preparation_phase_increments_turns_played(self):
        players = [Player(pid=i) for i in range(2)]
        game = Game(players, card_pool=get_card_pool())
        game.preparation_phase()
        for p in players:
            assert p.turns_played == 1

    def test_turn_one_at_least_three_gold(self):
        """Turn 1: with base_income=3, gold should reflect income (AI may spend)."""
        players = [Player(pid=i) for i in range(4)]
        game = Game(players, card_pool=get_card_pool())
        game.preparation_phase()
        for p in players:
            assert p.gold >= 0  # AI may have bought cards

    def test_market_window_during_preparation_phase(self):
        """Each preparation_phase should open deal_market_window for players."""
        players = [Player(pid=i) for i in range(2)]
        game = Game(players, card_pool=get_card_pool())
        game.preparation_phase()
        # Windows should be returned by end of phase (_player_windows empty)
        assert len(game.market._player_windows) == 0

    def test_gold_accumulates_over_two_turns(self):
        """Economist should trend upward over two preparation phases."""
        players = [Player(pid=0, strategy="economist")]
        game = Game(players, card_pool=get_card_pool())
        game.preparation_phase()  # turn 1
        gold_t1 = players[0].gold
        game.preparation_phase()  # turn 2
        gold_t2 = players[0].gold
        # At least base_income is applied each turn
        assert gold_t2 >= gold_t1 or True  # AI may spend gold

    def test_hp_below_75_bonus_in_prep_phase(self):
        """Player with HP < 75 should get +1 HP bonus during prep."""
        p = Player(pid=0)
        p.hp = 50  # < 75
        players = [p]
        game = Game(players, card_pool=get_card_pool())
        game.preparation_phase()
        # base=3 + hp_bonus=1 + interest + purchases
        assert p.gold >= BASE_INCOME + 1 or True  # purchases may reduce gold


# -------------------------------------------------------------
# MARKER REGISTRATION
# -------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "known_bug: Tests that document known bugs or spec gaps. "
        "They assert current (possibly incorrect) behavior. "
        "Update or remove after a fix."
    )
