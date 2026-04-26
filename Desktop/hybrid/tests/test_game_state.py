import pytest
from v2.core.game_state import GameState
from v2.core.action_result import ActionResult
from engine_core.game_factory import build_game

@pytest.fixture
def real_game_instance():
    """Testler için gerçek bir motor başlatır."""
    strategies = ["random", "random"]
    game = build_game(strategies=strategies)
    return game

@pytest.fixture
def game_state_instance(real_game_instance):
    """Her test için taze bir GameState yaratır."""
    state = GameState()
    state.hook_engine(real_game_instance)
    real_game_instance.start_turn()
    return state

def test_gamestate_buys_card_successfully_if_gold_is_enough(game_state_instance):
    """Oyuncunun yeterli altını varsa, buy_card_from_slot başarılı olmalı."""
    # Faz 4: get_gold() kaldırıldı — get_public_state().active_player.gold kullanılır.
    initial_gold = game_state_instance.get_public_state().active_player.gold
    assert initial_gold > 0

    result = game_state_instance.buy_card_from_slot(player_index=0, slot_index=0)
    assert result == ActionResult.OK

    final_gold = game_state_instance.get_public_state().active_player.gold
    assert final_gold < initial_gold

def test_gamestate_returns_err_if_gold_insufficient(game_state_instance):
    """Oyuncunun altını yetersizse hata dönmeli."""
    player = game_state_instance._adapter.get_player(0)
    player.gold = 0

    result = game_state_instance.buy_card_from_slot(player_index=0, slot_index=0)

    assert result == ActionResult.ERR_INSUFFICIENT_GOLD
    # Faz 4: get_gold() yerine get_public_state() kullanılır.
    assert game_state_instance.get_public_state().active_player.gold == 0
