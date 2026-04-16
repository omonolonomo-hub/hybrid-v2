import pytest
from v2.core.game_state import GameState, ActionResult
from v2.mock.engine_mock import MockGame

@pytest.fixture
def spectate_setup():
    """Arrange: Set up a game with 2 players (P0 human, P1 AI)."""
    GameState._instance = None
    gs = GameState.get()
    engine = MockGame()
    engine.initialize_deterministic_fixture() # Sets P0: 10G, P1: 50G
    gs.hook_engine(engine)
    return gs, engine

def test_aaa_view_switching_data_accuracy(spectate_setup):
    """
    Test: Data getters should follow view_index.
    Arrange: Managed by spectate_setup. Explicitly set P1 gold/hp.
    Act: Set view_index to 1 (P1).
    Assert: get_gold() returns P1's gold.
    """
    gs, engine = spectate_setup
    engine.players[0].gold = 10
    engine.players[1].gold = 50
    engine.players[1].hp = 42
    
    # Act
    gs.view_index = 1
    
    # Assert
    assert gs.get_gold() == 50
    assert gs.get_hp() == 42
    assert gs.get_gold(0) == 10 # Explicit query still works

def test_aaa_action_gating_security(spectate_setup):
    """
    Test: Write operations should fail if view_index != 0.
    Arrange: Set view_index to 1 (Spectating AI).
    Act: Try to buy card.
    Assert: Return error and gold remains unchanged.
    """
    gs, engine = spectate_setup
    engine.players[1].gold = 50
    gs.view_index = 1
    
    # Act
    # ActionResult.ERR_NOT_OWNER (8) should be returned
    result = gs.buy_card_from_slot(player_index=1, slot_index=0)
    
    # Assert
    assert result == ActionResult.ERR_NOT_OWNER
    assert engine.players[1].gold == 50 # Unchanged
