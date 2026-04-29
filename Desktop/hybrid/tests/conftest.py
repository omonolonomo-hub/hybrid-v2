import os

# ==========================================
# TEST ENV LEAK PROTECTION
# Eğer Pytest çalışıyorsa, gerçek diskteki .env ayarlarının (Örn: sizin test 
# için 1500 FPS yapmanızın) test runner'a sızmasını (State Leak) engelleriz.
# ==========================================
os.environ["DEBUG_MODE"] = "False"
os.environ["VSYNC"]      = "1"
os.environ["FPS"]        = "60"

import pytest
import pygame

@pytest.fixture(scope="session", autouse=True)
def pygame_mock_init():
    """
    INVARIANT: Pygame donanım katmanının test ortamını çökertmemesi garantisi.
    Testleri fiziksel bir monitöre ihtiyaç duymadan (headless) dummy driver ile çalıştırır.
    AssetLoader'ın convert_alpha() metodu için sahte bir Surface (1, 1) ayağa kaldırır.
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def reset_class_state(request):
    """Her test öncesi/sonrası class-level mutable state'leri sıfırla.

    H3-6: GameState._instance gibi singleton/mutable class değişkenleri 
    test izolasyonunu zedeler. Bu fixture her test öncesi ve sonrası bunları temizler.
    
    Note: SynergyCalculator artık instance-level cache kullanıyor, 
    bu yüzden global temizlik gerektirmiyor.
    
    Special handling: Tests that explicitly test CardPool singleton behavior
    (like test_card_pool_isolation.py) can disable CardPool reset by using
    the 'no_cardpool_reset' marker.
    """
    # Check if this test should skip CardPool reset
    skip_cardpool = request.node.get_closest_marker('no_cardpool_reset') is not None
    
    # Test öncesi temizlik
    try:
        from v2.core.game_state import GameState
        GameState._instance = None
    except ImportError:
        pass
    
    if not skip_cardpool:
        try:
            from engine_core.card import CardPool
            CardPool.reset()
        except ImportError:
            pass
    
    try:
        from v2.ui.hex_grid_config import reset_default_config
        reset_default_config()
    except ImportError:
        pass

    yield

    # Test sonrası temizlik
    try:
        from v2.core.game_state import GameState
        GameState._instance = None
    except ImportError:
        pass
    
    if not skip_cardpool:
        try:
            from engine_core.card import CardPool
            CardPool.reset()
        except ImportError:
            pass
    
    try:
        from v2.ui.hex_grid_config import reset_default_config
        reset_default_config()
    except ImportError:
        pass
