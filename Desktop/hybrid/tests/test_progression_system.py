import pytest
import random
from engine_core.player import Player
from engine_core.card import Card
from engine_core.progression_system import ProgressionSystem
from engine_core.constants import EVOLVE_COPIES_REQUIRED, COPY_THRESH, STARTING_HP

class MockMarket:
    def __init__(self, pool):
        self.pool = pool
        self.pool_copies = {c.name: 100 for c in pool}

def test_copy_strengthening_basic():
    player = Player(pid=0)
    card = Card("Warrior", "1", "1", {"power": 10})
    player.inventory.copies["Warrior"] = 2
    player.board.place((0, 0), card)
    
    # Threshold for 2 copies is COPY_THRESH[0] = 3
    # First turn
    ProgressionSystem.check_copy_strengthening(player, turn=1)
    assert player.inventory.copy_turns["Warrior"] == 1
    assert card.total_power() == 10
    
    # Second turn
    ProgressionSystem.check_copy_strengthening(player, turn=2)
    assert player.inventory.copy_turns["Warrior"] == 2
    assert card.total_power() == 10
    
    # Third turn
    ProgressionSystem.check_copy_strengthening(player, turn=3)
    assert player.inventory.copy_turns["Warrior"] == 3
    assert card.total_power() == 10 # still 10, thresh is 4
    
    # Fourth turn - should strengthen
    ProgressionSystem.check_copy_strengthening(player, turn=4)
    assert player.inventory.copy_turns["Warrior"] == 4
    assert card.total_power() == 12 # thresh_val "2" adds 2 to power
    assert player.inventory.copy_applied["Warrior"]["2"] is True

def test_evolution_basic():
    player = Player(pid=0, strategy="evolver")
    base_card = Card("Soldier", "1", "1", {"power": 10})
    player.inventory.copies["Soldier"] = EVOLVE_COPIES_REQUIRED
    
    # Add 2 to hand
    player.inventory.hand.append(base_card.clone())
    player.inventory.hand.append(base_card.clone())
    
    market = MockMarket([base_card])
    card_by_name = {"Soldier": base_card}
    
    evolved_names = ProgressionSystem.check_evolution(player, market=market, card_by_name=card_by_name)
    
    assert "Soldier" in evolved_names
    assert len(player.inventory.hand) == 1
    assert player.inventory.hand[0].name == "Evolved Soldier"
    assert player.inventory.copies["Soldier"] == EVOLVE_COPIES_REQUIRED - 2
    assert player.inventory.copies["Evolved Soldier"] == 1
    assert player.stats["evolutions"] == 1

def test_player_backward_compatibility():
    player = Player(pid=0, strategy="evolver")
    base_card = Card("Soldier", "1", "1", {"power": 10})
    player.inventory.copies["Soldier"] = EVOLVE_COPIES_REQUIRED
    player.inventory.hand.append(base_card.clone())
    player.inventory.hand.append(base_card.clone())
    
    card_by_name = {"Soldier": base_card}
    
    with pytest.warns(DeprecationWarning, match="Player.check_evolution is deprecated"):
        evos = player.check_evolution(card_by_name=card_by_name)
        
    assert "Soldier" in evos
    assert player.inventory.hand[0].name == "Evolved Soldier"

    # Test copy strengthening backward compat
    player2 = Player(pid=1)
    card2 = Card("Mage", "1", "1", {"power": 10})
    player2.inventory.copies["Mage"] = 2
    player2.board.place((0, 0), card2)
    player2.inventory.copy_turns["Mage"] = 3
    
    with pytest.warns(DeprecationWarning, match="Player.check_copy_strengthening is deprecated"):
        player2.check_copy_strengthening(turn=4)
        
    assert card2.total_power() == 12
