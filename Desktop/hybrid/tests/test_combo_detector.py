"""
tests/test_combo_detector.py
═══════════════════════════════════════════════════════════════════
ComboDetector extraction tests (P1-1 Phase 1).

Verifies that find_combos() produces identical results after extraction
from board.py to combo_detector.py.
"""

from engine_core.board import Board
from engine_core.card import Card
from engine_core.combo_detector import find_combos


def _make_card(name: str, *, rarity: str = "1", category: str = "fighter", stats: list = None) -> Card:
    """Create a minimal card for testing."""
    if stats is None:
        stats = [("Power", 5), ("Durability", 5), ("Meaning", 3),
                 ("Secret", 3), ("Gravity", 2), ("Spread", 2)]
    c = Card(name=name, rarity=rarity, category=category, stats=stats)
    c.uid = id(c)
    return c


class TestComboDetectorExtraction:
    """Verify find_combos works correctly after extraction."""

    def test_empty_board_returns_zero_combos(self):
        board = Board()
        count, bonus = find_combos(board)
        assert count == 0
        assert bonus == {}

    def test_single_card_no_combos(self):
        board = Board()
        card = _make_card("TestCard")
        board.place((0, 0), card)
        count, bonus = find_combos(board)
        assert count == 0

    def test_two_adjacent_same_group_cards_produce_combo(self):
        board = Board()
        # NE neighbor: direction 1 (OPP=4/SW). For combo, edges[1] and edges[4] must be same group.
        # stats[1]="Secret"->MIND, stats[4]="Intelligence"->MIND → combo!
        stats_mind = [("Meaning", 5), ("Secret", 5), ("Power", 3),
                      ("Durability", 3), ("Intelligence", 2), ("Trace", 2)]
        c1 = _make_card("Mind1", stats=stats_mind)
        c2 = _make_card("Mind2", stats=stats_mind)
        board.place((0, 0), c1)
        board.place((1, -1), c2)  # NE neighbor
        count, bonus = find_combos(board)
        assert count >= 1

    def test_backward_compat_import_from_board(self):
        """Verify that 'from engine_core.board import find_combos' still works."""
        from engine_core.board import find_combos as board_find_combos
        assert board_find_combos is find_combos

    def test_combo_bonus_structure(self):
        """Verify bonus dict structure has correct types."""
        board = Board()
        card = _make_card("TestCard")
        board.place((0, 0), card)
        count, bonus = find_combos(board)
        assert isinstance(count, int)
        assert isinstance(bonus, dict)
