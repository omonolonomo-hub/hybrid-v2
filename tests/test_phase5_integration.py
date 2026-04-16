import pytest
import pygame
from unittest.mock import MagicMock, call

from v2.constants import Screen
from v2.core.game_state import GameState
from v2.scenes.shop import ShopScene

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((Screen.W, Screen.H))
    yield
    pygame.quit()

@pytest.fixture
def mock_engine_and_state():
    GameState._instance = None
    gs = GameState.get()
    
    # Gerçek Engine yerine Phase 5 metodlarını bekleyen bir Mock
    engine_mock = MagicMock()
    engine_mock.players = [MagicMock(), MagicMock()]
    
    gs.hook_engine(engine_mock)
    yield gs, engine_mock
    GameState._instance = None

def test_commit_human_turn_triggers_engine_preparation_and_pairings(mock_engine_and_state):
    """
    Kullanıcı 'Hazır' dediğinde GameState.commit_human_turn() çalışmalı.
    
    Phase 5e Time-Dilation Fix: commit_human_turn artık preparation_phase() değil
    finish_turn() çağırır (eğer motor destekliyorsa). Bu, insan shopunu
    kitlemeyen split-turn mimarisinin temelidir.
    """
    gs, engine = mock_engine_and_state
    
    # Mock engine: finish_turn mevcut (MagicMock her attr'u oto-Mock yapar)
    engine.swiss_pairs.return_value = [(engine.players[0], engine.players[1])]
    
    # Act
    gs.commit_human_turn()
    
    # Split-turn mimarisinde finish_turn çağrılmalı, preparation_phase DEĞİL
    engine.finish_turn.assert_called_once()
    # preparation_phase çağrılmamalı (Time-Dilation Bug'ı önlendi)
    engine.preparation_phase.assert_not_called()
    
    assert len(gs.get_current_pairings()) == 1

def test_shopscene_transitions_to_versus_after_commit_human_turn(mock_engine_and_state):
    """
    ShopScene üzerindeki 'Hazır' butonuna tıklandığında (ve human_turn commit edildiğinde)
    Sahne faz makinesi STATE_VERSUS fazına geçer.
    """
    gs, engine = mock_engine_and_state
    engine.swiss_pairs.return_value = [(engine.players[0], engine.players[1])]
    
    scene = ShopScene()
    assert scene.phase == "STATE_PREPARATION"
    
    # Ready butonuna tıklama eventini simüle et
    click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, 
        button=1, 
        pos=scene.ready_btn_rect.center
    )
    
    scene.handle_event(click_event)
    
    # Hazıra tıklandıysa transition gerçekleşmeli
    assert scene.phase == "STATE_VERSUS"

def test_sync_state_pulls_hp_and_gold_from_real_engine(mock_engine_and_state):
    """
    Sync state çağrıldığında, GameState motorun oyuncularından (HP, Gold vs.)
    veri okuma fonksiyonlarının çökmediğini ve UI verisine başarıyla normalize
    edilebildiğini doğrular.
    """
    gs, engine = mock_engine_and_state
    
    # MagicMock'un get_hp() çağrısında gerçek bir int döndürmesini ayarla
    engine.get_hp.return_value = 55
    # get_gold players[idx].gold üzerinden okuyor, return_value değil
    engine.players[0].gold = 10

    # Phase 5 senkronizasyonu
    assert gs.get_hp(0) == 55
    assert gs.get_gold(0) == 10
