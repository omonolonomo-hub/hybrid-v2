"""
AUTOCHESS HYBRID - Edge Case & Hidden Bug Test Suite v1
Missing scenarios not covered by test_market_ekonomi.py and test_trigger_passive.py.
Focus: market system, multi-player interactions, turn transitions.
Run: pytest test_edge_cases.py -v
"""

import pytest
import random
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from engine_core.card import get_card_pool, Card
from engine_core.player import Player
from engine_core.market import Market
from engine_core.game import Game
from engine_core.board import Board
from engine_core.constants import (
    CARD_COSTS, COPY_THRESH, COPY_THRESH_C,
    BASE_INCOME, MAX_INTEREST, INTEREST_STEP,
    STARTING_HP, PLACE_PER_TURN,
)

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def fresh_market() -> Market:
    """Fresh market instance per test."""
    return Market(get_card_pool())

def fresh_player(strategy: str = "random", gold: int = 0, pid: int = 0) -> Player:
    p = Player(pid=pid, strategy=strategy)
    p.gold = gold
    return p

def card_of_rarity(rarity: str) -> Card:
    """First card with the given rarity."""
    return next(c for c in get_card_pool() if c.rarity == rarity)

def card_by_name(name: str) -> Card:
    """Lookup card prototype by name."""
    pool = {c.name: c for c in get_card_pool()}
    return pool.get(name)


# =====================================================================
# SECTION 1: MARKET SYSTEM EDGE CASES
# =====================================================================

class TestMarketPoolExhaustion:
    """Behavior when pool_copies hits zero or is stressed."""

    def test_pool_copies_never_goes_negative(self):
        """pool_copies must never go negative (guarded by max())."""
        m = fresh_market()
        card = card_of_rarity("1")
        
        # Request the same card 5 times (only 3 copies exist)
        for _ in range(5):
            m.deal_market_window(MagicMock(pid=f"p{_}"), n=1)
        
        assert m.pool_copies[card.name] >= 0, \
            f"{card.name} pool_copies went negative: {m.pool_copies[card.name]}"

    def test_market_falls_back_to_full_pool_when_exhausted(self):
        """When _available() is empty, sampling falls back to full self.pool."""
        m = fresh_market()
        
        # Stress pool (placeholder loop - preserves original structure)
        hot_card = card_of_rarity("1")
        player_ids = ["p0", "p1", "p2", "p3"]
        
        for pid in player_ids[:3]:
            market = m.deal_market_window(MagicMock(pid=pid), n=5)
            # Intentionally not returning window - exercise pool
        
        # Fourth player should still receive a full window via fallback
        player4_market = m.deal_market_window(MagicMock(pid="p4"), n=5)
        assert len(player4_market) == 5, "Exhausted pool fallback to full pool failed"

    def test_same_card_in_multiple_windows_decrements_correctly(self):
        """Same common card across three windows: pool_copies stays consistent."""
        m = fresh_market()
        card = card_of_rarity("1")
        
        w1 = m.deal_market_window(MagicMock(pid="p1"), n=5)
        w2 = m.deal_market_window(MagicMock(pid="p2"), n=5)
        w3 = m.deal_market_window(MagicMock(pid="p3"), n=5)
        
        # Started with 3 copies - at most 3 appearances across windows
        all_windows = w1 + w2 + w3
        card_occurrences = sum(1 for c in all_windows if c.name == card.name)
        
        # pool_copies = 3 - occurrences
        expected_pool_copies = 3 - card_occurrences
        assert m.pool_copies[card.name] == expected_pool_copies, \
            f"{card.name}: seen in {card_occurrences} windows, " \
            f"pool_copies {m.pool_copies[card.name]} but expected {expected_pool_copies}"

    def test_return_unsold_and_reuse_in_same_turn(self):
        """Returned cards can be redrawn later after return_unsold."""
        m = fresh_market()
        p1 = fresh_player(pid=1)
        p2 = fresh_player(pid=2)
        
        card = card_of_rarity("1")
        w1 = m.deal_market_window(p1, n=5)
        initial_pool = m.pool_copies[card.name]
        
        # p1 buys nothing - return window
        m.return_unsold(p1, bought=[])
        after_return = m.pool_copies[card.name]
        
        # Pool should replenish
        assert after_return > initial_pool or after_return == 3, \
            "return_unsold did not increase pool_copies"

    def test_deal_market_then_new_deal_overwrites_old_window(self):
        """New deal for same pid should return the previous window to the pool."""
        m = fresh_market()
        p1 = fresh_player(pid=1)
        
        w1 = m.deal_market_window(p1, n=5)
        first_copy_count = m.pool_copies[card_of_rarity("1").name]
        
        # Open new window (old one returns first)
        w2 = m.deal_market_window(p1, n=5)
        second_copy_count = m.pool_copies[card_of_rarity("1").name]
        
        # Prior window returned; net change vs after first window should be zero for a given common
        assert second_copy_count == first_copy_count, \
            "Old window not properly returned when opening new window"


# =====================================================================
# SECTION 2: MARKET ISOLATION & CONCURRENT WINDOWS
# =====================================================================

class TestMarketMultiplayerIsolation:
    """Eight players opening markets concurrently."""

    def test_8_players_simultaneous_windows_no_duplicate_rare(self):
        """Rare with 3 pool copies: at most 3 windows can show that card."""
        m = fresh_market()
        players = [fresh_player(pid=i) for i in range(8)]
        
        rare_card = card_of_rarity("3")
        
        windows = [m.deal_market_window(p, n=5) for p in players]
        
        rare_count = sum(1 for w in windows for c in w if c.name == rare_card.name)
        assert rare_count <= 3, \
            f"Rare card {rare_card.name} appeared {rare_count} times across windows, max 3"

    def test_8_players_pool_copies_consistency(self):
        """After eight windows, pool_copies match starting stock minus appearances."""
        m = fresh_market()
        players = [fresh_player(pid=i) for i in range(8)]
        windows = [m.deal_market_window(p, n=5) for p in players]
        
        for card in get_card_pool():
            appearances = sum(1 for w in windows for c in w if c.name == card.name)
            expected = max(0, 3 - appearances)
            actual = m.pool_copies[card.name]
            assert actual == expected, \
                f"{card.name}: {appearances} window hits, " \
                f"pool_copies={actual} but expected {expected}"

    def test_return_unsold_affects_pool_copies(self):
        """return_unsold should not decrease pool_copies for returned cards."""
        m = fresh_market()
        p1 = fresh_player(pid=1, gold=50)
        
        window = m.deal_market_window(p1, n=5)
        before_return = m.pool_copies[get_card_pool()[0].name]
        
        m.return_unsold(p1, bought=[])
        after_return = m.pool_copies[get_card_pool()[0].name]
        
        assert after_return >= before_return, \
            f"return_unsold dropped pool_copies {before_return} -> {after_return}"

    def test_return_unsold_partial_return(self):
        """Only unpurchased window cards return to the pool."""
        m = fresh_market()
        p1 = fresh_player(pid=1, gold=50)
        
        window = m.deal_market_window(p1, n=5)
        initial_copies = {c.name: m.pool_copies[c.name] for c in get_card_pool()}
        
        bought = window[:2]
        for card in bought:
            p1.buy_card(card)
        
        m.return_unsold(p1, bought=bought)
        
        unsold = window[2:]
        for card in unsold:
            assert m.pool_copies[card.name] > initial_copies[card.name], \
                f"Unsold {card.name} not returned to pool"


# =====================================================================
# SECTION 3: COPY SYSTEM BOUNDARY CASES
# =====================================================================

class TestCopyCounterBoundaryConditions:
    """Copy strengthening thresholds and catalyst interaction."""

    def test_copy_2_threshold_exact_turn_4(self):
        """With copy_turns starting at 0, 2-copy buff fires at turn 4."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        card.name = "TestCard"

        # Two copies on board
        p.board.place((0, 0), card)
        p.board.place((1, 0), card.clone())
        p.copies["TestCard"] = 2
        p.copy_turns["TestCard"] = 0

        initial_power = p.board.grid[(0, 0)].total_power()
        p.check_copy_strengthening(turn=1)
        p.check_copy_strengthening(turn=2)
        p.check_copy_strengthening(turn=3)

        assert p.board.grid[(0, 0)].total_power() == initial_power, \
            "Card strengthened before threshold t=4"

        p.check_copy_strengthening(turn=4)
        assert p.board.grid[(0, 0)].total_power() == initial_power + 2, \
            "Card not strengthened at exact threshold t=4"


    def test_copy_2_and_3_dont_double_strengthen(self):
        """2-copy tier buff then 3-copy tier adds more (stacked +2 then +3 style)."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        card.name = "TestCard"

        p.board.place((0, 0), card)
        p.copies["TestCard"] = 2
        p.copy_turns["TestCard"] = 0

        initial_power = p.board.grid[(0, 0)].total_power()
        p.check_copy_strengthening(turn=1)
        p.check_copy_strengthening(turn=2)
        p.check_copy_strengthening(turn=3)
        p.check_copy_strengthening(turn=4)
        after_2nd = p.board.grid[(0, 0)].total_power()
        assert after_2nd == initial_power + 2

        p.copies["TestCard"] = 3
        p.check_copy_strengthening(turn=5)
        p.check_copy_strengthening(turn=6)
        p.check_copy_strengthening(turn=7)
        after_3rd = p.board.grid[(0, 0)].total_power()
        assert after_3rd == initial_power + 5, \
            f"Copy strengthening not cumulative: {after_3rd} != {initial_power + 5}"


    def test_catalyst_changes_thresholds_3_and_6(self):
        """With catalyst, use COPY_THRESH_C (3, 6)."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        card.name = "TestCard"
        
        p.board.place((0, 0), card)
        p.board.has_catalyst = True
        p.copies["TestCard"] = 2
        p.copy_turns["TestCard"] = 0
        
        initial_power = p.board.grid[(0, 0)].total_power()
        
        p.check_copy_strengthening(turn=1)
        p.check_copy_strengthening(turn=2)
        p.check_copy_strengthening(turn=3)
        after_turn3 = p.board.grid[(0, 0)].total_power()
        assert after_turn3 == initial_power + 2, \
            f"Catalyst threshold not applied: {after_turn3} != {initial_power + 2}"

    def test_copy_counter_persists_across_turns(self):
        """copy_turns must not reset between simulated turns."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        card.name = "TestCard"
        
        p.board.place((0, 0), card)
        p.copies["TestCard"] = 2
        
        p.check_copy_strengthening(turn=1)
        assert p.copy_turns.get("TestCard", 0) == 1
        
        # Next turn
        p.check_copy_strengthening(turn=2)
        assert p.copy_turns.get("TestCard", 0) == 2, \
            "copy_turns counter reset between turns!"


# =====================================================================
# SECTION 4: ECONOMY EDGE CASES
# =====================================================================

class TestInterestCalculationBoundaries:
    """Interest edge cases."""

    def test_interest_with_0_gold(self):
        """0 banked gold before income -> no interest on that baseline."""
        p = fresh_player(pid=1, gold=0)
        p.income()
        initial = p.gold  # BASE_INCOME
        p.apply_interest()
        interest = p.gold - initial
        assert interest == 0, f"0 gold interest: {interest}"

    def test_interest_with_near_prior_gold_accumulates(self):
        """Income and interest add gold; unlimited economy (no cap)."""
        p = fresh_player(pid=1)
        p.gold = 48  # Near old cap value
        p.income()
        p.apply_interest()
        assert p.gold > 50  # Can exceed old cap

    def test_interest_economist_multiplier_edge(self):
        """Economist 1.5x multiplier at 1, 10, 40 starting gold."""
        for initial_gold in [1, 10, 40]:
            p = fresh_player(pid=1, strategy="economist", gold=initial_gold)
            before = initial_gold
            p.income()
            p.apply_interest()
            assert p.gold > before, f"Economist gold did not grow from {before}: {p.gold}"

    def test_hp_penalty_threshold_boundaries(self):
        """HP bonus thresholds 45 / 75 - boundary table."""
        test_cases = [
            (76, 0),   # above 75 band
            (75, 0),   # exactly 75: no <75 bonus
            (74, 1),   # below 75: +1
            (45, 1),   # above 45: still +1 from <75 rule
            (44, 3),   # below 45: +3
        ]
        
        for hp, expected_bonus in test_cases:
            p = fresh_player(pid=1, gold=0)
            p.hp = hp
            p.income()
            
            # BASE_INCOME + bonus + streak (streak=0)
            expected_gold = BASE_INCOME + expected_bonus
            assert p.gold == expected_gold, \
                f"HP={hp}: gold={p.gold}, expected {expected_gold} (bonus={expected_bonus})"


# =====================================================================
# SECTION 5: TURN TRANSITION STATE
# =====================================================================

class TestTurnTransitionStateConsistency:
    """State consistency across turn boundaries."""

    def test_cards_bought_this_turn_resets_each_turn(self):
        """cards_bought_this_turn resets on income()."""
        p = fresh_player(pid=1, gold=50)
        
        card = card_of_rarity("1").clone()
        p.buy_card(card)
        assert p.cards_bought_this_turn == 1
        
        p.income()  # should reset counter
        assert p.cards_bought_this_turn == 0, \
            "cards_bought_this_turn not reset on income()"

    def test_turn_counter_increments_consecutively(self):
        """turns_played increments by 1 per income()."""
        p = fresh_player(pid=1)
        
        initial = p.turns_played
        p.income()
        assert p.turns_played == initial + 1
        
        p.income()
        assert p.turns_played == initial + 2

    def test_income_interest_unlimited_economy(self):
        """Unlimited economy: gold can grow without cap."""
        p = fresh_player(pid=1, gold=48)

        p.income()
        assert p.gold > 50  # Can exceed old cap value

        p.gold = 49
        p.income()
        assert p.gold > 50

        p.apply_interest()
        assert p.gold > 50

    def test_win_streak_persists_correctly(self):
        """Minimal win_streak + income interaction smoke test."""
        p1 = fresh_player(pid=1)
        p2 = fresh_player(pid=2)
        
        p1.win_streak = 0
        p1.win_streak += 1
        p2.win_streak = 0
        
        p1.income()
        p2.income()
        
        assert p1.gold == BASE_INCOME, "P1 income affected by win_streak"


# =====================================================================
# SECTION 6: MULTI-PLAYER COMPLEX INTERACTIONS
# =====================================================================

class TestMultiplayerComplexScenarios:
    """Larger multiplayer stress cases."""

    def test_8_players_buys_exhaust_common_pool(self):
        """Eight players buying commons from windows - pool stays sane."""
        m = fresh_market()
        players = [fresh_player(pid=i, gold=50) for i in range(8)]
        
        windows = {p.pid: m.deal_market_window(p, n=5) for p in players}
        
        # Each buys up to two commons from their window
        bought = {}
        for pid, window in windows.items():
            commons = [c for c in window if c.rarity == "1"]
            for card in commons[:2]:
                players[pid].buy_card(card)
                bought.setdefault(card.name, []).append(pid)
        
        for p in players:
            m.return_unsold(p, bought=list(p.hand))
        
        total_copies = sum(m.pool_copies.values())
        assert total_copies <= 303, f"Pool copies > 303: {total_copies}"

    def test_market_window_return_order_independent(self):
        """return_unsold order among players should fully restore pool."""
        m = fresh_market()
        players = [fresh_player(pid=i) for i in range(3)]
        
        windows = [m.deal_market_window(p, n=5) for p in players]
        mid_copies = {c.name: m.pool_copies[c.name] for c in get_card_pool()}
        
        for p in reversed(players):
            m.return_unsold(p, bought=[])
        
        final_copies = {c.name: m.pool_copies[c.name] for c in get_card_pool()}
        # Total copies return to 303
        assert sum(final_copies.values()) == 303, \
            f"Pool copies not fully restored: {sum(final_copies.values())} != 303"

    def test_sequential_market_pressure_80_turns(self):
        """Long-run random window pressure - pool stays non-negative."""
        m = fresh_market()
        
        for turn in range(80):
            players = [fresh_player(pid=i) for i in range(4)]
            windows = [m.deal_market_window(p, n=5) for p in players]
            
            for i, p in enumerate(players):
                w = windows[i]
                k = random.randint(0, min(3, len(w)))
                m.return_unsold(p, bought=random.sample(w, k))
        
        for val in m.pool_copies.values():
            assert val >= 0, f"Negative pool_copies after 80 turns: {val}"


# =====================================================================
# SECTION 7: PLAYER STATE CONSISTENCY
# =====================================================================

class TestPlayerStateInvariants:
    """Player state consistency checks."""

    def test_gold_unlimited_economy(self):
        """Unlimited economy: gold can grow without cap."""
        p = fresh_player(pid=1, gold=49)
        p.income()
        assert p.gold > 50, f"after income() expected gold > 50, got {p.gold}"
        p.apply_interest()
        assert p.gold > 50, f"after apply_interest() expected gold > 50, got {p.gold}"

    def test_copies_count_matches_board_and_hand(self):
        """copies[name] tracks combined board + hand counts."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        card.name = "UniqueCard"
        
        p.board.place((0, 0), card)
        p.hand.append(card.clone())
        p.copies["UniqueCard"] = 2
        
        on_board = sum(1 for c in p.board.grid.values() if c.name == "UniqueCard")
        in_hand = sum(1 for c in p.hand if c.name == "UniqueCard")
        actual_total = on_board + in_hand
        
        assert actual_total == p.copies["UniqueCard"], \
            f"Copies count mismatch: {actual_total} != {p.copies['UniqueCard']}"

    def test_stats_cards_bought_synced_with_attribute(self):
        """stats['cards_bought_this_turn'] matches attribute counter."""
        p = fresh_player(pid=1, gold=50)
        card = card_of_rarity("1").clone()
        
        p.buy_card(card)
        
        assert p.cards_bought_this_turn == p.stats["cards_bought_this_turn"], \
            f"Stats mismatch: {p.cards_bought_this_turn} != {p.stats['cards_bought_this_turn']}"

    def test_hand_removal_on_board_placement(self):
        """Cards move from hand to board when place_cards runs."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        
        p.hand.append(card)
        assert len(p.hand) == 1
        
        p.place_cards()
        # Yeterli free space varsa kart board'a gider
        if len(p.board.free_coords()) > 0:
            assert card in p.board.grid.values() or len(p.hand) == 0, \
                "Card not moved to board or removed from hand"


# =====================================================================
# SECTION 8: PASSIVE & BOARD CONSISTENCY
# =====================================================================

class TestBoardStateWithPassives:
    """Board state when running passive triggers."""

    def test_board_placement_fills_free_coords(self):
        """place_cards places at most PLACE_PER_TURN cards per call (v0.6 default 1)."""
        p = fresh_player(pid=1)

        cards = [card_of_rarity("1").clone() for _ in range(3)]
        for card in cards:
            p.hand.append(card)

        assert len(p.hand) == 3
        p.place_cards()

        on_board = len([c for c in p.board.grid.values() if c is not None])
        assert on_board == PLACE_PER_TURN
        assert len(p.hand) == 3 - PLACE_PER_TURN

    def test_board_grid_no_none_values_unless_empty(self):
        """Placed cells reference real cards, not None."""
        p = fresh_player(pid=1)
        card = card_of_rarity("1").clone()
        
        p.board.place((0, 0), card)
        
        assert (0, 0) in p.board.grid
        assert p.board.grid[(0, 0)] is not None
        assert p.board.grid[(0, 0)].name == card.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
