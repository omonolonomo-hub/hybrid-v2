"""Tests for CommandDispatcher interface and LocalCommandDispatcher implementation.

Verifies that:
1. LocalCommandDispatcher correctly delegates to EngineAdapter
2. All three mutation methods work through the dispatcher
3. Behavior is identical to direct EngineAdapter calls
"""

import pytest
from engine_core.game import Game
from engine_core.player import Player
from engine_core.card import Card
from v2.core.engine_adapter import EngineAdapter
from v2.core.local_dispatcher import LocalCommandDispatcher
from v2.core.action_result import ActionResult


def test_local_dispatcher_buy_card_delegation():
    """Verify LocalCommandDispatcher.perform_buy_card delegates to EngineAdapter."""
    game = Game(players=[Player(pid=0)])
    game.start_turn()
    
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    
    # Buy a card through dispatcher
    result = dispatcher.perform_buy_card(0, 0)
    
    # Should succeed or fail based on game state, but must return ActionResult
    assert isinstance(result, ActionResult)


def test_local_dispatcher_reroll_delegation():
    """Verify LocalCommandDispatcher.perform_reroll delegates to EngineAdapter."""
    game = Game(players=[Player(pid=0)])
    game.start_turn()
    
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    
    # Give player gold for reroll
    game.players[0].gold = 10
    
    # Reroll through dispatcher
    result = dispatcher.perform_reroll(0)
    
    # Should return bool
    assert isinstance(result, bool)
    assert result is True  # Should succeed with 10 gold


def test_local_dispatcher_placement_delegation():
    """Verify LocalCommandDispatcher.perform_placement delegates to EngineAdapter."""
    game = Game(players=[Player(pid=0)])
    game.start_turn()
    
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    
    # Add a card to hand using proper API
    card = Card(name="TestCard", category="MIND", rarity="1", stats={"ATK": 5, "DEF": 5})
    card.uid = 1
    game.players[0].inventory.add_to_hand(card)
    
    # Place through dispatcher
    result = dispatcher.perform_placement(0, 0, (0, 0), 0)
    
    # Should return ActionResult
    assert isinstance(result, ActionResult)
    assert result == ActionResult.OK


def test_dispatcher_behavior_matches_adapter():
    """Verify dispatcher produces identical results to direct adapter calls."""
    # Setup two identical games
    game1 = Game(players=[Player(pid=0)])
    game2 = Game(players=[Player(pid=0)])
    
    game1.start_turn()
    game2.start_turn()
    
    # Give both players gold
    game1.players[0].gold = 10
    game2.players[0].gold = 10
    
    adapter1 = EngineAdapter(game1)
    adapter2 = EngineAdapter(game2)
    dispatcher = LocalCommandDispatcher(adapter2)
    
    # Perform same operation through adapter and dispatcher
    result_adapter = adapter1.perform_reroll(0)
    result_dispatcher = dispatcher.perform_reroll(0)
    
    # Results should be identical
    assert result_adapter == result_dispatcher
    assert game1.players[0].gold == game2.players[0].gold


def test_game_state_uses_dispatcher():
    """Verify GameState uses LocalCommandDispatcher for mutations."""
    from v2.core.game_state import GameState
    
    game = Game(players=[Player(pid=0)])
    gs = GameState()
    gs.hook_engine(game)
    
    # Verify dispatcher is initialized
    assert gs._dispatcher is not None
    assert isinstance(gs._dispatcher, LocalCommandDispatcher)
    
    # Verify mutations go through dispatcher
    game.start_turn()
    game.players[0].gold = 10
    
    result = gs.reroll_market(0)
    assert result == ActionResult.OK
    assert game.players[0].gold == 8  # 10 - 2 for reroll


def test_dispatcher_cleanup():
    """Verify dispatcher is properly cleaned up."""
    from v2.core.game_state import GameState
    
    game = Game(players=[Player(pid=0)])
    gs = GameState()
    gs.hook_engine(game)
    
    assert gs._dispatcher is not None
    
    gs.cleanup()
    
    assert gs._dispatcher is None
    assert gs._adapter is None
