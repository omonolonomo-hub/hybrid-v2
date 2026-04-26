"""
tests/test_damage_calculator.py
═══════════════════════════════════════════════════════════════════
DamageCalculator extraction tests (P1-1 Phase 2).

Verifies that resolve_single_combat() and calculate_damage() produce
identical results after extraction from board.py to damage_calculator.py.
Also tests CombatResult dataclass.
"""

from engine_core.board import Board
from engine_core.card import Card
from engine_core.damage_calculator import (
    CombatResult, resolve_single_combat, calculate_damage,
)
from engine_core.constants import (
    EARLY_GAME_TURNS, SCALING_END_TURN, EARLY_DAMAGE_MULTIPLIER,
    LATE_DAMAGE_MULTIPLIER, EARLY_CAP_TURNS, EARLY_DAMAGE_CAP,
)


def _make_card(name: str, *, rarity: str = "1", category: str = "fighter",
               stats: list = None) -> Card:
    if stats is None:
        stats = [("Power", 5), ("Durability", 5), ("Meaning", 3),
                 ("Secret", 3), ("Gravity", 2), ("Spread", 2)]
    c = Card(name=name, rarity=rarity, category=category, stats=stats)
    c.uid = id(c)
    return c


class TestDamageCalculatorExtraction:
    """Verify damage calculation works correctly after extraction."""

    def test_combat_result_dataclass(self):
        cr = CombatResult(
            winner_coord=(0, 0), loser_coord=(1, 0),
            card_killed=True, points_a=10, points_b=0,
            edge_wins_a=4, edge_wins_b=2,
        )
        assert cr.winner_coord == (0, 0)
        assert cr.card_killed is True
        assert cr.edge_wins_a == 4

    def test_resolve_single_combat_draw(self):
        """Two identical cards should draw (equal edge wins)."""
        c1 = _make_card("A")
        c2 = _make_card("B")
        a_wins, b_wins = resolve_single_combat(c1, c2)
        # Same stats, same edges — should be equal
        assert a_wins == b_wins

    def test_calculate_damage_early_game_capped(self):
        """Early game damage should be capped at EARLY_DAMAGE_CAP."""
        board = Board()
        # High point diff but early turn → cap applies
        dmg = calculate_damage(100, 0, board, turn=1)
        assert dmg <= EARLY_DAMAGE_CAP
        assert dmg >= 1  # minimum 1

    def test_calculate_damage_late_game_no_cap(self):
        """Late game damage should not be capped."""
        board = Board()
        dmg = calculate_damage(100, 0, board, turn=20)
        assert dmg >= EARLY_DAMAGE_CAP  # should exceed cap

    def test_calculate_damage_uses_constants(self):
        """Verify damage constants match the expected behavior."""
        assert EARLY_GAME_TURNS == 5
        assert SCALING_END_TURN == 15
        assert EARLY_DAMAGE_MULTIPLIER == 0.5
        assert LATE_DAMAGE_MULTIPLIER == 1.0
        assert EARLY_CAP_TURNS == 10
        assert EARLY_DAMAGE_CAP == 15

    def test_backward_compat_imports(self):
        """Verify backward-compat imports from board.py work."""
        from engine_core.board import (
            CombatResult as BoardCombatResult,
            resolve_single_combat as board_resolve,
            calculate_damage as board_calc_dmg,
        )
        assert BoardCombatResult is CombatResult
        assert board_resolve is resolve_single_combat
        assert board_calc_dmg is calculate_damage
