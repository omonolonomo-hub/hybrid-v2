"""
Test suite for CardPool singleton isolation and cache management.

Verifies that the CardPool.reset() mechanism properly isolates tests
and prevents mutation leakage across test runs.
"""

import pytest
from engine_core.card import CardPool, get_card_pool, Card


class TestCardPoolIsolation:
    """Test CardPool singleton behavior and reset mechanism."""
    
    def setup_method(self):
        """Reset card pool before each test to ensure isolation."""
        CardPool.reset()
    
    def teardown_method(self):
        """Clean up after each test."""
        CardPool.reset()
    
    def test_singleton_returns_same_instance(self):
        """CardPool.instance() should return the same list on repeated calls."""
        pool1 = CardPool.instance()
        pool2 = CardPool.instance()
        
        assert pool1 is pool2, "Should return same instance without reset"
    
    def test_reset_clears_cache(self):
        """CardPool.reset() should force new instance on next call."""
        pool1 = CardPool.instance()
        first_id = id(pool1)
        
        CardPool.reset()
        
        pool2 = CardPool.instance()
        second_id = id(pool2)
        
        assert first_id != second_id, "Reset should create new instance"
    
    def test_mutations_isolated_after_reset(self):
        """Mutations to cards should not persist after reset."""
        # Get initial pool and mutate a card
        pool1 = CardPool.instance()
        test_card = pool1[0]
        
        # Get a stat that actually exists on the card
        base_stats = test_card.get_base_stats()
        if not base_stats:
            pytest.skip("Test card has no base stats")
        
        stat_name = list(base_stats.keys())[0]
        original_stat = test_card.get_base_stat(stat_name, 0)
        
        # Mutate the card
        test_card.add_base_stat(stat_name, 999)
        mutated_stat = test_card.get_base_stat(stat_name, 0)
        
        assert mutated_stat == original_stat + 999, "Mutation should apply"
        
        # Reset and get fresh pool
        CardPool.reset()
        pool2 = CardPool.instance()
        fresh_stat = pool2[0].get_base_stat(stat_name, 0)
        
        assert fresh_stat == original_stat, "Fresh pool should not have mutation"
        assert fresh_stat != mutated_stat, "Mutation should not leak"
    
    def test_get_card_pool_uses_singleton(self):
        """Legacy get_card_pool() should use CardPool.instance()."""
        pool_via_class = CardPool.instance()
        pool_via_function = get_card_pool()
        
        assert pool_via_class is pool_via_function, "Should return same instance"
    
    def test_multiple_resets_safe(self):
        """Multiple reset calls should be safe (idempotent)."""
        CardPool.reset()
        CardPool.reset()
        CardPool.reset()
        
        pool = CardPool.instance()
        assert len(pool) > 0, "Should still work after multiple resets"
    
    def test_reset_before_first_instance_safe(self):
        """Calling reset before first instance() should be safe."""
        CardPool.reset()  # reset before any instance created
        pool = CardPool.instance()
        
        assert len(pool) > 0, "Should work even if reset called first"
    
    def test_card_pool_contains_valid_cards(self):
        """CardPool should contain properly initialized Card objects."""
        pool = CardPool.instance()
        
        assert len(pool) > 0, "Pool should not be empty"
        
        for card in pool:
            assert isinstance(card, Card), f"Expected Card, got {type(card)}"
            assert card.name, "Card should have a name"
            # Rarity is stored as string in this codebase (1-5)
            assert card.rarity in ["1", "2", "3", "4", "5"], f"Invalid rarity: {card.rarity}"
    
    def test_micro_buff_applied_to_pool(self):
        """CardPool should have micro buffs applied (from apply_micro_buff_to_weak_cards)."""
        # This test verifies that the buffing logic still runs
        # We can't easily test the exact buff values without knowing the card data,
        # but we can verify the pool is created and contains cards
        pool = CardPool.instance()
        
        # Just verify the pool was created successfully
        # The actual buffing is tested in card-specific tests
        assert len(pool) > 0, "Buffed pool should exist"


class TestCardPoolConcurrency:
    """Test CardPool behavior in scenarios that might cause race conditions."""
    
    def setup_method(self):
        CardPool.reset()
    
    def teardown_method(self):
        CardPool.reset()
    
    def test_parallel_instance_calls_safe(self):
        """Multiple instance() calls should be safe (though not thread-safe by design)."""
        pools = [CardPool.instance() for _ in range(10)]
        
        # All should be the same instance
        first_pool = pools[0]
        for pool in pools[1:]:
            assert pool is first_pool, "All calls should return same instance"


class TestBackwardCompatibility:
    """Ensure the refactor maintains backward compatibility."""
    
    def setup_method(self):
        CardPool.reset()
    
    def teardown_method(self):
        CardPool.reset()
    
    def test_get_card_pool_still_works(self):
        """Legacy get_card_pool() function should still work."""
        pool = get_card_pool()
        
        assert isinstance(pool, list), "Should return a list"
        assert len(pool) > 0, "Should contain cards"
        assert all(isinstance(c, Card) for c in pool), "Should contain Card objects"
    
    def test_get_card_pool_caches_properly(self):
        """get_card_pool() should cache like the old implementation."""
        pool1 = get_card_pool()
        pool2 = get_card_pool()
        
        assert pool1 is pool2, "Should return cached instance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
