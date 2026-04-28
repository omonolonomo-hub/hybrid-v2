"""Test to verify the None-in-hand fix for AI strategies."""

import sys
sys.path.insert(0, '.')

from engine_core.player import Player
from engine_core.card import Card
from engine_core.ai.strategies.random import _place_smart_default
from engine_core.ai.strategies.tempo import _place_aggressive
from engine_core.ai.strategies.builder import _place_fast_synergy

def test_none_in_hand():
    """Test that AI strategies handle None values in player.hand correctly."""
    
    # Create a test player
    player = Player(pid=1, strategy="evolver")
    
    # Create some test cards with proper stats dict
    stats1 = {"science": 10, "nature": 10, "culture": 5, "history": 5, "art": 5, "tech": 5, "space": 5}
    stats2 = {"science": 20, "nature": 20, "culture": 10, "history": 10, "art": 10, "tech": 10, "space": 10}
    stats3 = {"history": 15, "culture": 15, "science": 8, "nature": 8, "art": 8, "tech": 8, "space": 8}
    
    card1 = Card("Test Card 1", "Science", "1", stats1)
    card2 = Card("Test Card 2", "Science", "E", stats2)
    card3 = Card("Test Card 3", "History", "2", stats3)
    
    # Add cards to hand with None values (simulating the positional integrity system)
    player.hand = [card1, None, card2, None, card3]
    
    print("Testing with hand containing None values:")
    print(f"Hand: {[c.name if c else 'None' for c in player.hand]}")
    
    # Test 1: _place_smart_default (used by evolver, warrior, economist, etc.)
    print("\n1. Testing _place_smart_default (evolver strategy)...")
    try:
        _place_smart_default(player, rng=None)
        print("   ✅ SUCCESS: No AttributeError!")
        print(f"   Cards placed on board: {len(player.board.alive_cards())}")
    except AttributeError as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Reset for next test
    player2 = Player(pid=2, strategy="tempo")
    player2.hand = [card1.clone(), None, card2.clone(), None, card3.clone()]
    
    # Test 2: _place_aggressive (used by tempo strategy)
    print("\n2. Testing _place_aggressive (tempo strategy)...")
    try:
        _place_aggressive(player2)
        print("   ✅ SUCCESS: No AttributeError!")
        print(f"   Cards placed on board: {len(player2.board.alive_cards())}")
    except AttributeError as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Reset for next test
    player3 = Player(pid=3, strategy="builder")
    player3.hand = [card1.clone(), None, card2.clone(), None, card3.clone()]
    
    # Test 3: _place_fast_synergy (used by builder strategy)
    print("\n3. Testing _place_fast_synergy (builder strategy)...")
    try:
        _place_fast_synergy(player3)
        print("   ✅ SUCCESS: No AttributeError!")
        print(f"   Cards placed on board: {len(player3.board.alive_cards())}")
    except AttributeError as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED! None-in-hand fix is working correctly.")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_none_in_hand()
    sys.exit(0 if success else 1)
