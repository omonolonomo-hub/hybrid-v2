"""
Test script for T3.2b-i and T3.2b-ii - HandPanel AssetLoader Integration

This script verifies that:
1. HandPanel requires asset_loader parameter (ValueError if None)
2. HandPanel stores asset_loader reference
3. HandPanel.preload() loads hand card assets
4. HandPanel.draw() uses AssetLoader to render card images
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from ui.hand_panel import HandPanel
from core.core_game_state import CoreGameState
from core.ui_state import UIState


def test_asset_loader_required():
    """Test that asset_loader=None raises ValueError."""
    print("\n=== Test 1: AssetLoader Required (T3.2b-i) ===")
    
    # Create mock objects
    class MockPlayer:
        def __init__(self):
            self.pid = 0
            self.hp = 100
            self.hand = []
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer()]
            self.turn = 1
        
        def alive_players(self):
            return self.players
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    
    # Test 1: asset_loader=None should raise ValueError
    try:
        hand_panel = HandPanel(core_state, ui_state, asset_loader=None)
        print("✗ FAILED: Should have raised ValueError for asset_loader=None")
        return False
    except ValueError as e:
        if "asset_loader is required" in str(e):
            print(f"✓ Correctly raised ValueError: {e}")
        else:
            print(f"✗ FAILED: Wrong error message: {e}")
            return False
    
    return True


def test_asset_loader_stored():
    """Test that asset_loader is stored correctly."""
    print("\n=== Test 2: AssetLoader Stored (T3.2b-i) ===")
    
    # Create mock objects
    class MockPlayer:
        def __init__(self):
            self.pid = 0
            self.hp = 100
            self.hand = []
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer()]
            self.turn = 1
        
        def alive_players(self):
            return self.players
    
    class MockAssetLoader:
        def __init__(self):
            self.preloaded = []
        
        def preload(self, card_names):
            self.preloaded.extend(card_names)
        
        def get(self, card_name):
            # Return mock faces
            class MockFaces:
                def __init__(self):
                    self.front = pygame.Surface((100, 100))
                    self.back = pygame.Surface((100, 100))
                    self.is_placeholder = False
            return MockFaces()
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    mock_loader = MockAssetLoader()
    
    # Test 2: asset_loader should be stored
    hand_panel = HandPanel(core_state, ui_state, asset_loader=mock_loader)
    
    assert hasattr(hand_panel, 'asset_loader'), "asset_loader attribute not found"
    assert hand_panel.asset_loader is mock_loader, "asset_loader not stored correctly"
    print("✓ asset_loader stored correctly")
    
    return True


def test_preload_method():
    """Test that preload() method loads hand card assets."""
    print("\n=== Test 3: Preload Method (T3.2b-ii) ===")
    
    # Create mock objects
    class MockCard:
        def __init__(self, name):
            self.name = name
            self.rotation = 0
            self.rarity = 'A'
            self.group = 'MIND'
            self.passive = None
            self.edges = [('N', 5), ('S', 3)]
    
    class MockPlayer:
        def __init__(self):
            self.pid = 0
            self.hp = 100
            self.hand = [
                MockCard("Albert Einstein"),
                MockCard("Algorithm"),
                MockCard("Athena")
            ]
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer()]
            self.turn = 1
        
        def alive_players(self):
            return self.players
    
    class MockAssetLoader:
        def __init__(self):
            self.preloaded = []
        
        def preload(self, card_names):
            self.preloaded.extend(card_names)
            print(f"  [MockAssetLoader] Preloaded: {card_names}")
        
        def get(self, card_name):
            class MockFaces:
                def __init__(self):
                    self.front = pygame.Surface((100, 100))
                    self.back = pygame.Surface((100, 100))
                    self.is_placeholder = False
            return MockFaces()
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    mock_loader = MockAssetLoader()
    
    # Create HandPanel
    hand_panel = HandPanel(core_state, ui_state, asset_loader=mock_loader)
    
    # Test preload
    hand_panel.preload()
    
    # Verify preload was called with correct card names
    expected_names = ["Albert Einstein", "Algorithm", "Athena"]
    assert len(mock_loader.preloaded) == 3, f"Expected 3 cards preloaded, got {len(mock_loader.preloaded)}"
    for name in expected_names:
        assert name in mock_loader.preloaded, f"Card '{name}' not preloaded"
    
    print(f"✓ Preloaded {len(mock_loader.preloaded)} cards correctly")
    
    return True


def test_draw_uses_asset_loader():
    """Test that draw() uses AssetLoader to get card images."""
    print("\n=== Test 4: Draw Uses AssetLoader (T3.2b-ii) ===")
    
    # Initialize pygame for surface creation
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    
    # Create mock objects
    class MockCard:
        def __init__(self, name):
            self.name = name
            self.rotation = 0
            self.rarity = 'A'
            self.group = 'MIND'
            self.passive = "Test passive"
            self.edges = [('N', 5), ('S', 3)]
    
    class MockPlayer:
        def __init__(self):
            self.pid = 0
            self.hp = 100
            self.hand = [MockCard("Albert Einstein")]
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer()]
            self.turn = 1
        
        def alive_players(self):
            return self.players
    
    class MockAssetLoader:
        def __init__(self):
            self.get_calls = []
        
        def preload(self, card_names):
            pass
        
        def get(self, card_name):
            self.get_calls.append(card_name)
            print(f"  [MockAssetLoader] get() called for: {card_name}")
            
            class MockFaces:
                def __init__(self):
                    # Create colored surface for visual verification
                    self.front = pygame.Surface((100, 100))
                    self.front.fill((100, 150, 200))  # Blue
                    self.back = pygame.Surface((100, 100))
                    self.back.fill((200, 100, 100))  # Red
                    self.is_placeholder = False
            return MockFaces()
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    mock_loader = MockAssetLoader()
    
    # Create HandPanel
    hand_panel = HandPanel(core_state, ui_state, asset_loader=mock_loader)
    
    # Call draw
    hand_panel.draw(screen)
    
    # Verify get() was called for the card
    assert len(mock_loader.get_calls) > 0, "AssetLoader.get() was not called"
    assert "Albert Einstein" in mock_loader.get_calls, "AssetLoader.get() not called for 'Albert Einstein'"
    
    print(f"✓ AssetLoader.get() called {len(mock_loader.get_calls)} times")
    print(f"✓ Cards requested: {mock_loader.get_calls}")
    
    pygame.quit()
    return True


def test_placeholder_handling():
    """Test that placeholder cards are handled correctly."""
    print("\n=== Test 5: Placeholder Handling (T3.2b-ii) ===")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    
    # Create mock objects
    class MockCard:
        def __init__(self, name):
            self.name = name
            self.rotation = 0
            self.rarity = 'A'
            self.group = 'MIND'
            self.passive = None
            self.edges = [('N', 5), ('S', 3)]
    
    class MockPlayer:
        def __init__(self):
            self.pid = 0
            self.hp = 100
            self.hand = [MockCard("Missing Card")]
    
    class MockGame:
        def __init__(self):
            self.players = [MockPlayer()]
            self.turn = 1
        
        def alive_players(self):
            return self.players
    
    class MockAssetLoader:
        def __init__(self):
            pass
        
        def preload(self, card_names):
            pass
        
        def get(self, card_name):
            class MockFaces:
                def __init__(self):
                    # Simulate placeholder (neon hex)
                    self.front = pygame.Surface((100, 100))
                    self.front.fill((0, 242, 255))  # Neon cyan
                    self.back = pygame.Surface((100, 100))
                    self.is_placeholder = True  # Mark as placeholder
            return MockFaces()
    
    game = MockGame()
    core_state = CoreGameState(game)
    ui_state = UIState()
    mock_loader = MockAssetLoader()
    
    # Create HandPanel
    hand_panel = HandPanel(core_state, ui_state, asset_loader=mock_loader)
    
    # Call draw (should not crash with placeholder)
    try:
        hand_panel.draw(screen)
        print("✓ Placeholder cards handled correctly (no crash)")
    except Exception as e:
        print(f"✗ FAILED: Exception with placeholder: {e}")
        pygame.quit()
        return False
    
    pygame.quit()
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("T3.2b-i & T3.2b-ii - HandPanel AssetLoader Integration Tests")
    print("=" * 60)
    
    tests = [
        ("AssetLoader Required (T3.2b-i)", test_asset_loader_required),
        ("AssetLoader Stored (T3.2b-i)", test_asset_loader_stored),
        ("Preload Method (T3.2b-ii)", test_preload_method),
        ("Draw Uses AssetLoader (T3.2b-ii)", test_draw_uses_asset_loader),
        ("Placeholder Handling (T3.2b-ii)", test_placeholder_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
