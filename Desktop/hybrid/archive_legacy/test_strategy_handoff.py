"""
Test T1.4 Phase 2: GameLoopScene owns CoreGameState

This test verifies that:
1. Strategies are correctly passed from LobbyScene to GameLoopScene
2. GameLoopScene builds the game using strategies
3. GameLoopScene creates CoreGameState
4. Game is initialized only once
"""

import sys
import pygame

# Initialize pygame (required for scene creation)
pygame.init()

# Core systems
from core.scene_manager import SceneManager
from core.core_game_state import CoreGameState

# Scenes
from scenes.lobby_scene import LobbyScene
from scenes.game_loop_scene import GameLoopScene


def test_game_loop_ownership():
    """Test that GameLoopScene becomes the owner of CoreGameState."""
    
    print("=" * 60)
    print("TEST: T1.4 Phase 2 - GameLoopScene owns CoreGameState")
    print("=" * 60)
    
    # Create dummy game for initial CoreGameState (will be ignored by GameLoopScene)
    class DummyGame:
        def __init__(self):
            self.players = []
            self.market = None
            self.turn = 0
        def alive_players(self):
            return []
    
    dummy_game = DummyGame()
    core_game_state = CoreGameState(dummy_game)
    
    # Create lobby scene
    lobby_scene = LobbyScene(core_game_state)
    
    # Create scene manager
    scene_manager = SceneManager(lobby_scene)
    
    # Register game_loop factory
    def create_game_loop(core_game_state, **kwargs):
        strategies = kwargs.get('strategies', None)
        return GameLoopScene(core_game_state, strategies=strategies)
    
    scene_manager.register_scene_factory("game_loop", create_game_loop)
    
    # Simulate lobby selecting strategies
    test_strategies = ["aggro", "control", "midrange", "combo", "tempo", "builder", "evolver", "warrior"]
    
    print(f"\n1. Lobby selects strategies: {test_strategies}")
    
    # Request transition with strategies
    scene_manager.request_transition("game_loop", strategies=test_strategies)
    
    print("2. Requesting transition to game_loop with strategies...")
    
    # Execute transition (this happens in scene_manager.update)
    scene_manager._execute_transition()
    
    print("3. Transition executed")
    
    # Verify GameLoopScene received strategies
    active_scene = scene_manager.active_scene
    
    print(f"\n4. Active scene type: {type(active_scene).__name__}")
    
    if isinstance(active_scene, GameLoopScene):
        print("   ✓ Active scene is GameLoopScene")
        
        # Check strategies
        if hasattr(active_scene, 'strategies'):
            print(f"   ✓ GameLoopScene has 'strategies' attribute")
            print(f"   ✓ Strategies received: {active_scene.strategies}")
            
            if active_scene.strategies == test_strategies:
                print("   ✓ Strategies match")
            else:
                print(f"   ✗ ERROR: Strategies don't match!")
                print(f"      Expected: {test_strategies}")
                print(f"      Got: {active_scene.strategies}")
                return False
        else:
            print("   ✗ ERROR: GameLoopScene missing 'strategies' attribute")
            return False
        
        # Check game initialization
        print("\n5. Checking game initialization...")
        if hasattr(active_scene, 'game') and active_scene.game is not None:
            print("   ✓ Game instance created")
            print(f"   ✓ Number of players: {len(active_scene.game.players)}")
            
            # Verify players match strategies
            for i, player in enumerate(active_scene.game.players):
                expected_strategy = test_strategies[i]
                if player.strategy == expected_strategy:
                    print(f"   ✓ Player {i+1}: {player.strategy} (Gold: {player.gold}, HP: {player.hp})")
                else:
                    print(f"   ✗ ERROR: Player {i+1} strategy mismatch!")
                    print(f"      Expected: {expected_strategy}")
                    print(f"      Got: {player.strategy}")
                    return False
        else:
            print("   ✗ ERROR: Game not initialized")
            return False
        
        # Check CoreGameState
        print("\n6. Checking CoreGameState...")
        if hasattr(active_scene, 'core_game_state') and active_scene.core_game_state is not None:
            print("   ✓ CoreGameState created")
            print(f"   ✓ Turn: {active_scene.core_game_state.turn}")
            print(f"   ✓ Current player: {active_scene.core_game_state.current_player.strategy}")
            print(f"   ✓ Alive players: {len(active_scene.core_game_state.alive_players)}")
            
            # Verify CoreGameState references the game
            if active_scene.core_game_state.game is active_scene.game:
                print("   ✓ CoreGameState references the correct game instance")
            else:
                print("   ✗ ERROR: CoreGameState references wrong game instance")
                return False
        else:
            print("   ✗ ERROR: CoreGameState not created")
            return False
        
        # Test re-entering scene (should not re-initialize)
        print("\n7. Testing re-entry (should not re-initialize)...")
        game_id_before = id(active_scene.game)
        core_state_id_before = id(active_scene.core_game_state)
        
        active_scene.on_exit()
        active_scene.on_enter()
        
        game_id_after = id(active_scene.game)
        core_state_id_after = id(active_scene.core_game_state)
        
        if game_id_before == game_id_after and core_state_id_before == core_state_id_after:
            print("   ✓ Game and CoreGameState not re-initialized (same instances)")
        else:
            print("   ✗ ERROR: Game or CoreGameState was re-initialized!")
            return False
        
        print("\n" + "=" * 60)
        print("✓✓✓ TEST PASSED ✓✓✓")
        print("=" * 60)
        print("GameLoopScene successfully owns CoreGameState!")
        print(f"- Strategies: {test_strategies}")
        print(f"- Players: {len(active_scene.game.players)}")
        print(f"- Game initialized: YES")
        print(f"- CoreGameState created: YES")
        print(f"- No duplicate initialization: YES")
        return True
    else:
        print(f"   ✗ ERROR: Active scene is not GameLoopScene")
        return False


if __name__ == "__main__":
    try:
        success = test_game_loop_ownership()
        pygame.quit()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
