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
