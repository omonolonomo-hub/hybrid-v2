"""Quick integration test for CopyLabelRenderer refactoring."""

import pygame
from v2.scenes.shop import ShopScene
from v2.ui.copy_label_renderer import CopyLabelRenderer
from v2.core.game_state import GameState

def test_integration():
    """Test that ShopScene properly integrates CopyLabelRenderer."""
    pygame.init()
    pygame.display.set_mode((800, 600))
    
    # Create scene with GameState
    game_state = GameState()
    scene = ShopScene(game_state)
    
    # Verify renderer is created
    assert hasattr(scene, '_copy_renderer'), "ShopScene should have _copy_renderer"
    assert isinstance(scene._copy_renderer, CopyLabelRenderer), "Should be CopyLabelRenderer instance"
    
    # Verify renderer has cache
    assert hasattr(scene._copy_renderer, '_cache'), "Renderer should have _cache"
    assert isinstance(scene._copy_renderer._cache, dict), "Cache should be a dict"
    
    # Verify cache starts empty
    assert len(scene._copy_renderer._cache) == 0, "Cache should start empty"
    
    # Verify invalidate works
    scene._copy_renderer._cache[("test", 1)] = pygame.Surface((10, 10))
    assert len(scene._copy_renderer._cache) == 1
    scene._copy_renderer.invalidate()
    assert len(scene._copy_renderer._cache) == 0, "Invalidate should clear cache"
    
    print("✓ ShopScene created successfully")
    print(f"✓ Copy renderer type: {type(scene._copy_renderer).__name__}")
    print(f"✓ Cache initialized: {hasattr(scene._copy_renderer, '_cache')}")
    print("✓ All integration tests passed!")
    
    pygame.quit()

if __name__ == "__main__":
    test_integration()
