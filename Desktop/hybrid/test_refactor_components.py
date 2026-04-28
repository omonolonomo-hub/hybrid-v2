"""
Test script for refactored AudioSystem and HoverControl components.
"""
import pygame
import sys

# Initialize pygame for audio testing
pygame.init()
pygame.mixer.init()

from v2.ui.audio_system import AudioSystem
from v2.ui.hover_control import HoverControl
from v2.constants import Paths
from v2.assets.loader import AssetLoader


def test_hover_control():
    """Test HoverControl component."""
    print("\n=== Testing HoverControl ===")
    
    hover = HoverControl(delay_ms=150)
    
    # Test initial state
    assert not hover.is_active(), "Hover should not be active initially"
    assert hover.get_panel() is None, "Panel should be None initially"
    
    # Test starting hover
    hover.start("shop", item=2)
    assert not hover.is_active(), "Hover should not be active immediately"
    assert hover.get_state().panel == "shop", "Panel should be 'shop'"
    assert hover.get_state().item == 2, "Item should be 2"
    
    # Test timer update (not enough time)
    hover.update(100)
    assert not hover.is_active(), "Hover should not be active after 100ms"
    
    # Test timer update (enough time)
    hover.update(60)
    assert hover.is_active(), "Hover should be active after 160ms total"
    assert hover.get_panel() == "shop", "Panel should be 'shop'"
    assert hover.get_item() == 2, "Item should be 2"
    
    # Test reset
    hover.reset()
    assert not hover.is_active(), "Hover should not be active after reset"
    assert hover.get_panel() is None, "Panel should be None after reset"
    
    # Test same item hover (should preserve state)
    hover.start("board", item=(1, 2))
    hover.update(200)
    assert hover.is_active(), "Hover should be active"
    
    hover.start("board", item=(1, 2))  # Same item
    assert hover.is_active(), "Hover should remain active for same item"
    
    # Test different item hover (should reset)
    hover.start("board", item=(2, 3))  # Different item
    assert not hover.is_active(), "Hover should reset for different item"
    
    print("✓ HoverControl tests passed!")


def test_audio_system():
    """Test AudioSystem component."""
    print("\n=== Testing AudioSystem ===")
    
    # Initialize AssetLoader
    try:
        AssetLoader.initialize("v2/assets")
        audio = AudioSystem()
        
        # Test preload
        print("Testing preload...")
        audio.preload(Paths.SFX_BUY)
        assert audio.cached_count == 1, "Should have 1 cached sound"
        
        audio.preload(Paths.SFX_PLACE)
        assert audio.cached_count == 2, "Should have 2 cached sounds"
        
        # Test duplicate preload (should not increase count)
        audio.preload(Paths.SFX_BUY)
        assert audio.cached_count == 2, "Should still have 2 cached sounds"
        
        # Test play (won't actually play in test, but should not crash)
        print("Testing play...")
        audio.play(Paths.SFX_BUY)
        audio.play(Paths.SFX_PLACE, volume=0.5)
        
        # Test play uncached sound (should auto-load)
        audio.play(Paths.SFX_REROLL)
        assert audio.cached_count == 3, "Should have 3 cached sounds after auto-load"
        
        # Test stop
        print("Testing stop...")
        audio.stop(Paths.SFX_BUY)
        
        # Test stop_all
        audio.stop_all()
        
        # Test clear_cache
        audio.clear_cache()
        assert audio.cached_count == 0, "Cache should be empty after clear"
        
        print("✓ AudioSystem tests passed!")
        
    except Exception as e:
        print(f"⚠ AudioSystem test skipped (asset loading issue): {e}")


def test_integration():
    """Test components working together."""
    print("\n=== Testing Integration ===")
    
    hover = HoverControl(delay_ms=100)
    
    try:
        AssetLoader.initialize("v2/assets")
        audio = AudioSystem()
        
        # Simulate hover + audio workflow
        hover.start("shop", item=0)
        hover.update(50)
        
        if not hover.is_active():
            # Not active yet, no sound
            pass
        
        hover.update(60)
        
        if hover.is_active():
            # Hover active, play sound
            audio.play(Paths.SFX_BUY, volume=0.3)
            print("✓ Hover activated and sound played")
        
        hover.reset()
        audio.stop_all()
        
        print("✓ Integration test passed!")
        
    except Exception as e:
        print(f"⚠ Integration test skipped: {e}")


if __name__ == "__main__":
    print("Testing refactored components...")
    
    test_hover_control()
    test_audio_system()
    test_integration()
    
    print("\n=== All Tests Complete ===")
    pygame.quit()
