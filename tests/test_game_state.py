import pytest
from v2.core.game_state import GameState
from v2.mock.engine_mock import MockGame

@pytest.fixture
def mock_game_instance():
    """Testler için temiz ve deterministik bir sahte motor başlatır."""
    game = MockGame()
    game.initialize_deterministic_fixture()
    return game

@pytest.fixture
def game_state_instance(mock_game_instance):
    """Her test için temizlenmiş bir GameState singleton yaratır."""
    GameState._instance = None
    state = GameState.get()
    state.hook_engine(mock_game_instance)  # Engine'i bağla
    return state

def test_gamestate_buys_card_successfully_if_gold_is_enough(game_state_instance):
    """Oyuncunun đủ altını varsa, buy_card ActionResult.OK dönmeli ve altını eksiltmelidir."""
    # 0. Player'ın başlangıç statlarında 10 altın var. Fiyatı 3 olan kartı alalım.
    initial_gold = game_state_instance.get_gold(player_index=0)
    assert initial_gold == 10
    
    # 3 Altınlık bir işlem yapıyoruz (şimdilik kart ID'sini 99 simüle edelim)
    result = game_state_instance.buy_card(player_index=0, card_id=99, cost=3)
    
    assert result == 0  # Beklenen başarılı dönüş (ActionResult.OK)
    
    # Altın miktarı 7'ye düşmüş olmalı
    final_gold = game_state_instance.get_gold(player_index=0)
    assert final_gold == 7

def test_gamestate_returns_err_if_gold_insufficient(mock_game_instance, game_state_instance):
    """Oyuncunun đủ altını yoksa, buy_card ERR_INSUFFICIENT_GOLD dönmeli ve altın eksilmemeli."""
    # Oyuncunun altınını manipüle edip 2 yapalım. 3 altınlık kart almak istesin.
    mock_game_instance.players[0].gold = 2
    
    # Test
    result = game_state_instance.buy_card(player_index=0, card_id=99, cost=3)
    
    # 1 değeri (ActionResult.ERR_INSUFFICIENT_GOLD) dönmeli
    assert result == 1 
    
    # Altın azalmamış olmalı (işlem iptal edildi)
    final_gold = game_state_instance.get_gold(player_index=0)
    assert final_gold == 2
