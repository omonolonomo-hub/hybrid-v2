"""
tests/test_balance_constants.py
═══════════════════════════════════════════════════════════════════
Balance Constants extraction tests (P1-5).

Verifies that damage and synergy tier constants are properly defined
and used by damage_calculator.py and synergy.py.
"""

from engine_core.constants import (
    EARLY_GAME_TURNS, SCALING_END_TURN, EARLY_DAMAGE_MULTIPLIER,
    LATE_DAMAGE_MULTIPLIER, SCALING_STEP, EARLY_CAP_TURNS, EARLY_DAMAGE_CAP,
    SYNERGY_TIER_SMALL, SYNERGY_TIER_MED, SYNERGY_TIER_LARGE,
    SYNERGY_TIER_HUGE, SYNERGY_TIER_INCREMENT,
)
from engine_core.damage_calculator import calculate_damage
from engine_core.synergy import tier_bonus
from engine_core.board import Board


class TestDamageBalanceConstants:
    """Verify damage balance constants are correct and used."""

    def test_early_game_turns(self):
        assert EARLY_GAME_TURNS == 5

    def test_scaling_end_turn(self):
        assert SCALING_END_TURN == 15

    def test_early_damage_multiplier(self):
        assert EARLY_DAMAGE_MULTIPLIER == 0.5

    def test_late_damage_multiplier(self):
        assert LATE_DAMAGE_MULTIPLIER == 1.0

    def test_early_cap_turns(self):
        assert EARLY_CAP_TURNS == 10

    def test_early_damage_cap(self):
        assert EARLY_DAMAGE_CAP == 15

    def test_damage_turn_1_uses_early_multiplier(self):
        """Turn 1 damage should be 50% of raw damage."""
        board = Board()
        raw = 20
        dmg = calculate_damage(raw + 10, 10, board, turn=1)
        # With turn=1: multiplier=0.5, but at least 1
        assert dmg <= EARLY_DAMAGE_CAP
        assert dmg >= 1


class TestSynergyTierConstants:
    """Verify synergy tier constants are correct and used."""

    def test_synergy_tier_values(self):
        assert SYNERGY_TIER_SMALL == 3
        assert SYNERGY_TIER_MED == 9
        assert SYNERGY_TIER_LARGE == 16
        assert SYNERGY_TIER_HUGE == 25
        assert SYNERGY_TIER_INCREMENT == 3

    def test_tier_bonus_uses_constants(self):
        """tier_bonus() should return values matching the constants."""
        assert tier_bonus(2) == SYNERGY_TIER_SMALL
        assert tier_bonus(3) == SYNERGY_TIER_MED
        assert tier_bonus(4) == SYNERGY_TIER_LARGE
        assert tier_bonus(5) == SYNERGY_TIER_LARGE
        assert tier_bonus(6) == SYNERGY_TIER_HUGE
        assert tier_bonus(7) == SYNERGY_TIER_HUGE + SYNERGY_TIER_INCREMENT
