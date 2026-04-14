import pytest
import os
import pygame
from v2.assets.loader import AssetLoader

SPRITES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "v2", "assets"
)

@pytest.fixture(autouse=True)
def reset_singleton():
    """Her testten önce singleton'ı sıfırla."""
    AssetLoader._instance = None
    pygame.init()
    pygame.display.set_mode((320, 240))   # convert_alpha() için display context gerekli
    yield
    AssetLoader._instance = None
    pygame.quit()

def test_loader_raises_before_initialize():
    """initialize() çağrılmadan get() çağrısı RuntimeError fırlatmalı."""
    with pytest.raises(RuntimeError):
        AssetLoader.get()

def test_loader_initializes_correctly():
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    assert loader is not None
    assert loader.base_dir == SPRITES_DIR

def test_loader_raises_on_missing_sprite():
    """Var olmayan bir sprite için FileNotFoundError fırlatmalı."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    with pytest.raises(FileNotFoundError):
        loader.get_sprite("cards/OLMAYAN_KART_front.png")

def test_loader_loads_real_card_front():
    """Gerçek bir kart ön yüzü yüklenebilmeli (Surface döndürmeli)."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    surf = loader.get_card_front("Fibonacci Sequence")
    assert isinstance(surf, pygame.Surface)
    assert surf.get_width() > 0

def test_loader_loads_real_card_back():
    """Gerçek bir kart arka yüzü yüklenebilmeli."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    surf = loader.get_card_back("Fibonacci Sequence")
    assert isinstance(surf, pygame.Surface)

def test_loader_caches_sprites():
    """Aynı sprite iki kez istenince RAM'den gelmeli (aynı nesne)."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    surf_a = loader.get_card_front("Fibonacci Sequence")
    surf_b = loader.get_card_front("Fibonacci Sequence")
    assert surf_a is surf_b, "Cache çalışmıyor — her çağrıda yeni Surface üretiliyor!"
    assert loader.cached_sprite_count == 1

def test_loader_get_default_font():
    """Default font (monospace) döndürmeli."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    font = loader.get_default_font(16)
    assert isinstance(font, pygame.font.Font)

def test_loader_font_cached():
    """Aynı font iki kez istenince cache'den gelmeli."""
    AssetLoader.initialize(SPRITES_DIR)
    loader = AssetLoader.get()
    f1 = loader.get_default_font(14)
    f2 = loader.get_default_font(14)
    assert f1 is f2
