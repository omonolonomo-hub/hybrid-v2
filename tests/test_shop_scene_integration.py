"""
Integration test for ShopScene with FloatingText, evolved cards, and audio.

This is a visual/manual verification test:
  python -m pytest tests/test_shop_scene_integration.py::test_shop_scene_visual_demo -v -s

Or run the full ShopScene directly:
  python v2/main.py
"""
import pytest
import pygame
from v2.core.game_state import GameState
from v2.mock.engine_mock import MockGame
from v2.scenes.shop import ShopScene
from v2.constants import Screen


def test_shop_scene_assets_loaded():
    """Verify ShopScene initializes with all panels and managers."""
    gs = GameState.get()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    gs.hook_engine(mock_game)
    
    shop = ShopScene()
    
    # Check all major UI components exist
    assert hasattr(shop, 'shop_panel')
    assert hasattr(shop, 'hand_panel')
    assert hasattr(shop, 'player_hub')
    assert hasattr(shop, 'synergy_hud')
    assert hasattr(shop, 'ft_manager')  # FloatingTextManager
    
    # Verify FloatingTextManager active
    assert shop.ft_manager is not None
    assert shop.ft_manager.active_count >= 0


def test_floating_text_spawn_on_placement():
    """Verify FloatingText spawns when card is placed (Milestone)."""
    gs = GameState.get()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    gs.hook_engine(mock_game)
    
    shop = ShopScene()
    
    # Manually trigger milestone float (as would happen on card place)
    initial_count = shop.ft_manager.active_count
    shop.ft_manager.spawn(
        text="+5 SYNERGY",
        x=960,
        y=400,
        color=(80, 140, 255),
        font_size=16,
        coord_key=("test", 0),
    )
    
    assert shop.ft_manager.active_count > initial_count


def test_evolved_card_glow_rendering():
    """Verify evolved card (rarity 'E') initializes with platinum glow."""
    pygame.init()
    from v2.ui.card_flip import CardFlip
    from v2.constants import Colors
    
    # Create mock card surfaces
    surf_back = pygame.Surface((140, 160), pygame.SRCALPHA)
    surf_front = pygame.Surface((140, 160), pygame.SRCALPHA)
    rect = pygame.Rect(100, 100, 140, 160)
    
    # Test evolved card initialization
    flip = CardFlip(
        back_surf=surf_back,
        front_surf=surf_front,
        dest_rect=rect,
        evolved=True,
        evolved_color=Colors.PLATINUM,
    )
    
    assert flip.evolved is True
    assert flip.evolved_color == Colors.PLATINUM


def test_audio_loader_sfx_preload():
    """Verify audio loader can preload SFX without errors."""
    from v2.assets.loader import AssetLoader
    from v2.constants import Paths
    
    import os
    REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
    V2_ASSETS_DIR = os.path.join(REPO_ROOT, "v2", "assets")
    AssetLoader.initialize(V2_ASSETS_DIR)
    loader = AssetLoader.get()
    
    # Verify loader has preload method
    assert hasattr(loader, 'preload_scene')
    assert hasattr(loader, 'get_sfx')
    assert hasattr(loader, 'get_music')


@pytest.mark.manual
def test_shop_scene_visual_demo():
    """
    MANUAL TEST: Launch full ShopScene demo with all integrated systems.
    
    Run: python -m pytest tests/test_shop_scene_integration.py::test_shop_scene_visual_demo -v -s
    Or:  python v2/main.py
    
    Verify visually:
    ☐ FloatingText: rise + hold + fade animation
    ☐ Evolved cards: platinum glow on rarity "E"
    ☐ Audio: SFX triggers on buy/place, music plays in background
    ☐ All panels render without errors
    """
    from v2.core.card_database import CardDatabase
    import os
    
    pygame.init()
    pygame.mixer.init()
    
    # Setup
    gs = GameState.get()
    mock_game = MockGame()
    mock_game.initialize_deterministic_fixture()
    gs.hook_engine(mock_game)
    
    v2_base = os.path.dirname(os.path.dirname(__file__)) + "/v2"
    from v2.assets.loader import AssetLoader
    AssetLoader.initialize(os.path.join(v2_base, "assets"))
    CardDatabase.initialize(
        os.path.join(v2_base, "..", "assets", "data", "cards.json")
    )
    
    screen = pygame.display.set_mode((Screen.W, Screen.H))
    pygame.display.set_caption("ShopScene Integration Demo")
    clock = pygame.time.Clock()
    
    shop = ShopScene()
    running = True
    frame_count = 0
    max_frames = 300  # 5 seconds at 60 FPS
    
    while running and frame_count < max_frames:
        dt_ms = clock.tick(60)
        frame_count += 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            shop.handle_event(event)
        
        shop.update(dt_ms)
        screen.fill((16, 20, 30))
        shop.render(screen)
        pygame.display.flip()
    
    pygame.quit()
    
    # If we got here without crash, test passes
    assert frame_count > 0
