"""
Test suite for Inventory batch clear operations.

Verifies that clear_slots_batch emits only ONE signal for N operations,
preventing the N-signal emission pattern mismatch.
"""

import pytest
from engine_core.inventory import Inventory
from engine_core.card import Card


class TestInventoryBatchClear:
    """Test batch clear operations and signal emission."""
    
    def test_clear_slot_emits_signal(self):
        """Single clear_slot should emit one signal."""
        inv = Inventory()
        signal_count = 0
        
        def on_change():
            nonlocal signal_count
            signal_count += 1
        
        inv._on_change = on_change
        
        # Add a card
        card = Card(name="Test", category="test", rarity="1", stats={"a": 5}, passive_type="none")
        inv.add_to_hand(card)
        signal_count = 0  # Reset after add
        
        # Clear one slot
        inv.clear_slot(0)
        
        assert signal_count == 1, "clear_slot should emit exactly 1 signal"
    
    def test_clear_slots_batch_emits_one_signal(self):
        """Batch clear should emit only ONE signal for N operations."""
        inv = Inventory()
        signal_count = 0
        
        def on_change():
            nonlocal signal_count
            signal_count += 1
        
        inv._on_change = on_change
        
        # Add 3 cards
        for i in range(3):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv.add_to_hand(card)
        
        signal_count = 0  # Reset after adds
        
        # Clear 3 slots in batch
        inv.clear_slots_batch([0, 1, 2])
        
        assert signal_count == 1, "clear_slots_batch should emit exactly 1 signal for N clears"
    
    def test_clear_slots_batch_vs_individual_signal_count(self):
        """Batch clear should emit fewer signals than individual clears."""
        # Setup for individual clears
        inv1 = Inventory()
        signal_count1 = 0
        
        def on_change1():
            nonlocal signal_count1
            signal_count1 += 1
        
        inv1._on_change = on_change1
        
        for i in range(5):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv1.add_to_hand(card)
        
        signal_count1 = 0
        
        # Individual clears
        for i in range(5):
            inv1.clear_slot(i)
        
        # Setup for batch clear
        inv2 = Inventory()
        signal_count2 = 0
        
        def on_change2():
            nonlocal signal_count2
            signal_count2 += 1
        
        inv2._on_change = on_change2
        
        for i in range(5):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv2.add_to_hand(card)
        
        signal_count2 = 0
        
        # Batch clear
        inv2.clear_slots_batch([0, 1, 2, 3, 4])
        
        assert signal_count1 == 5, "Individual clears should emit 5 signals"
        assert signal_count2 == 1, "Batch clear should emit 1 signal"
        assert signal_count2 < signal_count1, "Batch should emit fewer signals"
    
    def test_clear_slots_batch_clears_all_specified_slots(self):
        """Batch clear should actually clear all specified slots."""
        inv = Inventory()
        
        # Add 5 cards
        for i in range(5):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv.add_to_hand(card)
        
        # Batch clear slots 1, 3
        inv.clear_slots_batch([1, 3])
        
        assert inv.hand[0] is not None, "Slot 0 should not be cleared"
        assert inv.hand[1] is None, "Slot 1 should be cleared"
        assert inv.hand[2] is not None, "Slot 2 should not be cleared"
        assert inv.hand[3] is None, "Slot 3 should be cleared"
        assert inv.hand[4] is not None, "Slot 4 should not be cleared"
    
    def test_clear_slots_batch_empty_list_no_signal(self):
        """Batch clear with empty list should not emit signal."""
        inv = Inventory()
        signal_count = 0
        
        def on_change():
            nonlocal signal_count
            signal_count += 1
        
        inv._on_change = on_change
        
        # Clear empty list
        inv.clear_slots_batch([])
        
        assert signal_count == 0, "Empty batch should not emit signal"
    
    def test_clear_slots_batch_out_of_bounds_safe(self):
        """Batch clear should safely ignore out-of-bounds indices."""
        inv = Inventory()
        signal_count = 0
        
        def on_change():
            nonlocal signal_count
            signal_count += 1
        
        inv._on_change = on_change
        
        # Add 2 cards
        for i in range(2):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv.add_to_hand(card)
        
        signal_count = 0
        
        # Try to clear including out-of-bounds indices
        inv.clear_slots_batch([0, 1, 5, 10])
        
        assert signal_count == 1, "Should emit 1 signal even with out-of-bounds"
        assert inv.hand[0] is None, "Valid index 0 should be cleared"
        assert inv.hand[1] is None, "Valid index 1 should be cleared"
    
    def test_clear_slots_batch_duplicate_indices(self):
        """Batch clear should handle duplicate indices gracefully."""
        inv = Inventory()
        
        # Add 3 cards
        for i in range(3):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            inv.add_to_hand(card)
        
        # Clear with duplicates
        inv.clear_slots_batch([0, 1, 0, 1])
        
        assert inv.hand[0] is None, "Slot 0 should be cleared"
        assert inv.hand[1] is None, "Slot 1 should be cleared"
        assert inv.hand[2] is not None, "Slot 2 should not be cleared"


class TestPlayerPlaceCardsBatchOptimization:
    """Test that Player.place_cards uses batch clear."""
    
    def test_place_cards_emits_one_signal_for_multiple_placements(self):
        """place_cards should emit 1 signal when placing N cards."""
        from engine_core.player import Player
        from engine_core.board import Board
        
        player = Player(pid=0)
        signal_count = 0
        
        def on_change():
            nonlocal signal_count
            signal_count += 1
        
        player.inventory._on_change = on_change
        
        # Add 3 cards to hand
        for i in range(3):
            card = Card(name=f"Card{i}", category="test", rarity="1", stats={"a": 5}, passive_type="none")
            player.inventory.add_to_hand(card)
        
        signal_count = 0  # Reset after adds
        
        # Place cards (should place up to PLACE_PER_TURN)
        player.place_cards()
        
        # Should emit exactly 1 signal for the batch clear
        assert signal_count == 1, f"place_cards should emit 1 signal, got {signal_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
