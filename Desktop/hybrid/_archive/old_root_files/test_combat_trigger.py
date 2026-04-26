"""
Manual test for T1.13 - Combat phase triggering

This test verifies that:
1. GameLoopScene receives trigger_combat flag via kwargs
2. GameLoopScene sets needs_combat_trigger flag in on_enter()
3. GameLoopScene.update() calls trigger_combat_and_cleanup()
4. Combat phase is triggered and results are stored
5. Locked coordinates are cleared for all players
"""

import pygame
from core.core_game_state import CoreGameState
from scenes.game_loop_scene import GameLoopScene
from engine_core.game_factory import build_game


def test_combat_trigger():
    """Test combat phase triggering logic."""
    
    print("\n=== Testing T1.13: Combat Phase Triggering ===\n")
    
    # Initialize pygame
    pygame.init()
    
    # Build a test game
    strategies = ["random"] * 4
    game = build_game(strategies)
    core_game_state = CoreGameState(game)
    
    print("✓ Game initialized")
    
    # Test 1: Create GameLoopScene without trigger_combat flag
    print("\n--- Test 1: GameLoopScene without trigger_combat flag ---")
    scene1 = GameLoopScene(core_game_state)
    scene1.on_enter()
    assert scene1.ui_state is not None, "UIState should be created"
    assert not scene1.ui_state.needs_combat_trigger, "Combat trigger should be False by default"
    print("✓ Default state: needs_combat_trigger = False")
    scene1.on_exit()
    
    # Test 2: Create GameLoopScene with trigger_combat flag
    print("\n--- Test 2: GameLoopScene with trigger_combat=True flag ---")
    scene2 = GameLoopScene(core_game_state, trigger_combat=True)
    scene2.on_enter()
    assert scene2.ui_state is not None, "UIState should be created"
    assert scene2.ui_state.needs_combat_trigger, "Combat trigger should be True when flag is set"
    print("✓ With flag: needs_combat_trigger = True")
    
    # Test 3: Add locked coordinates and verify they get cleared
    print("\n--- Test 3: Locked Coordinates Clearing ---")
    core_game_state.locked_coords_per_player[0].add((0, 0))
    core_game_state.locked_coords_per_player[0].add((1, 1))
    core_game_state.locked_coords_per_player[1].add((2, 2))
    print(f"Added locked coords: Player 0: {len(core_game_state.locked_coords_per_player[0])} coords, Player 1: {len(core_game_state.locked_coords_per_player[1])} coords")
    
    # Test 4: Trigger combat phase via update()
    print("\n--- Test 4: Combat Phase Triggering via update() ---")
    initial_turn = core_game_state.turn
    print(f"Initial turn: {initial_turn}")
    
    # Call update to trigger combat
    scene2.update(16.0)
    
    # Verify combat was triggered
    assert not scene2.ui_state.needs_combat_trigger, "Combat trigger flag should be cleared after triggering"
    print("✓ Combat trigger flag cleared")
    
    assert core_game_state.turn == initial_turn + 1, f"Turn should increment after combat (was {initial_turn}, now {core_game_state.turn})"
    print(f"✓ Turn incremented to {core_game_state.turn}")
    
    # Verify locked coordinates were cleared
    for player in game.players:
        assert len(core_game_state.locked_coords_per_player[player.pid]) == 0, \
            f"Player {player.pid} locked coords should be cleared"
    print("✓ All locked coordinates cleared")
    
    # Test 5: Verify combat results stored (if available)
    print("\n--- Test 5: Combat Results Storage ---")
    if hasattr(game, 'last_combat_results') and game.last_combat_results:
        assert len(scene2.ui_state.popup_data) > 0, "Popup data should contain combat results"
        assert scene2.ui_state.popup_timer == 3000, "Popup timer should be set to 3 seconds"
        print(f"✓ Combat results stored: {len(scene2.ui_state.popup_data)} battles")
        print(f"✓ Popup timer set to {scene2.ui_state.popup_timer}ms")
    else:
        print("⚠ No combat results available (game.last_combat_results not set)")
    
    # Test 6: Verify popup timer decrements
    print("\n--- Test 6: Popup Timer Decrement ---")
    if scene2.ui_state.popup_timer > 0:
        initial_timer = scene2.ui_state.popup_timer
        scene2.update(100.0)  # 100ms
        assert scene2.ui_state.popup_timer == initial_timer - 100, "Popup timer should decrement by dt"
        print(f"✓ Popup timer decremented from {initial_timer}ms to {scene2.ui_state.popup_timer}ms")
    
    scene2.on_exit()
    
    print("\n=== All Tests Passed! ===\n")
    
    pygame.quit()


if __name__ == "__main__":
    test_combat_trigger()
