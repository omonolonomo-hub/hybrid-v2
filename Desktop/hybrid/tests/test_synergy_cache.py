"""
tests/test_synergy_cache.py
═══════════════════════════════════════════════════════════════════
Synergy BFS Caching tests (P1-2).

Verifies that SynergyCalculator properly caches results and
invalidates cache when board state changes.
"""

from v2.core.synergy_calculator import SynergyCalculator, SynergyComputeResult


class TestSynergyCache:
    """Test synergy calculator caching behavior."""

    def setup_method(self):
        """Clear cache before each test."""
        SynergyCalculator.invalidate_cache()

    def test_empty_board_returns_empty_result(self):
        result = SynergyCalculator.compute({}, None)
        assert result.total == 0

    def test_cache_returns_same_result_for_same_input(self):
        """Same board_cards dict should return cached result."""
        board_cards = {
            (0, 0): {"name": "TestCard", "stats": {"Power": 5}, "rotation": 0},
        }
        # First call computes
        result1 = SynergyCalculator.compute(board_cards, _MockDB())
        # Second call should use cache
        result2 = SynergyCalculator.compute(board_cards, _MockDB())
        assert result1 is result2  # same object from cache

    def test_cache_invalidated_on_board_change(self):
        """Different board state should produce fresh computation."""
        board1 = {
            (0, 0): {"name": "CardA", "stats": {"Power": 5}, "rotation": 0},
        }
        board2 = {
            (0, 0): {"name": "CardB", "stats": {"Power": 5}, "rotation": 0},
        }
        db = _MockDB()
        result1 = SynergyCalculator.compute(board1, db)
        result2 = SynergyCalculator.compute(board2, db)
        # Different board hash → different result object
        assert result1 is not result2

    def test_explicit_cache_invalidation(self):
        """invalidate_cache() should clear cached result."""
        board = {
            (0, 0): {"name": "CardA", "stats": {"Power": 5}, "rotation": 0},
        }
        db = _MockDB()
        result1 = SynergyCalculator.compute(board, db)

        SynergyCalculator.invalidate_cache()
        assert SynergyCalculator._last_board_hash is None
        assert SynergyCalculator._cached_result is None

        result2 = SynergyCalculator.compute(board, db)
        # After invalidation, new computation produces new object
        assert result1 is not result2
        # But same values
        assert result1.total == result2.total

    def test_cache_hash_stability(self):
        """Same board content should produce same hash."""
        board = {
            (0, 0): {"name": "CardA", "rotation": 0},
            (1, -1): {"name": "CardB", "rotation": 1},
        }
        h1 = SynergyCalculator._compute_board_hash(board)
        h2 = SynergyCalculator._compute_board_hash(board)
        assert h1 == h2

    def test_rotation_change_invalidates_cache(self):
        """Different rotation should produce different hash."""
        board1 = {(0, 0): {"name": "CardA", "rotation": 0}}
        board2 = {(0, 0): {"name": "CardA", "rotation": 1}}
        h1 = SynergyCalculator._compute_board_hash(board1)
        h2 = SynergyCalculator._compute_board_hash(board2)
        assert h1 != h2


class _MockDB:
    """Minimal mock for CardDatabase used in tests."""

    class CardData:
        def __init__(self, name):
            self.name = name
            self.stats = {"Power": 5, "Durability": 3, "Meaning": 2,
                          "Secret": 2, "Gravity": 1, "Spread": 1}

    def lookup(self, name):
        return self.CardData(name)
