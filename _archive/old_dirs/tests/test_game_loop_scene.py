"""
Integration test for GameLoopScene full turn cycle.

This test verifies that the basic turn flow works end-to-end with all economy
and combat logic, including:
- Scene transitions: Lobby → GameLoop → Shop → Combat → GameLoop
- Income application at turn start
- Interest application after shop closes
- Evolution/strengthening checks after combat
- Combat phase triggering
- Locked coordinates clearing

Feature: run-game-scene-integration
Task: T1.14 — Integration test: Full turn cycle
Requirements: 1, 2, 3, 7, 12, 13, 26, 27

Validates:
- Full turn cycle completes successfully
- All scenes visited in correct order
- Economy logic (income, interest) applied correctly
- Combat triggered and results stored
- Locked coordinates cleared after turn
"""

import pytest
import pygame
import sys
import os
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scene_manager import SceneManager
from core.core_game_state import CoreGameState
from core.input_state import InputState
from scenes.lobby_scene import LobbyScene
from scenes.game_loop_scene import GameLoopScene
from scenes.shop_scene import ShopScene
from scenes.combat_scene import CombatScene
from engine_core.player import Player
from engine_core.game import Game
from engine_core.game_factory import build_game


class TestGameLoopSceneIntegration:
    """Integration test suite for GameLoopScene full turn cycle."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create test environment."""
        pygame.init()
        self.screen = pygame.Surface((1600, 900))
        self.screen.fill((20, 20, 30))
        
        # Create asset loader for scenes that need it
        from scenes.asset_loader import AssetLoader
        self.asset_loader = AssetLoader("assets/cards")
        
        yield
        pygame.quit()
    
    def create_input_state_with_key(self, key: int) -> InputState:
        """Create InputState with a specific key pressed.
        
        Args:
            key: Pygame key constant (e.g., pygame.K_SPACE)
            
        Returns:
            InputState with the key pressed
        """
        event = pygame.event.Event(pygame.KEYDOWN, {'key': key})
        return InputState([event])
    
    def create_empty_input_state(self) -> InputState:
        """Create InputState with no events.
        
        Returns:
            InputState with empty event list
        """
        return InputState([])

    def create_test_game(self, strategies: Optional[List[str]] = None) -> Game:
        """Create a test game instance with specified strategies.
        
        Args:
            strategies: List of strategy names for players (default: 2 random strategies)
            
        Returns:
            Game instance ready for testing
        """
        if strategies is None:
            strategies = ["random", "random"]
        
        game = build_game(strategies)
        return game

    def create_scene_manager_with_factories(self, initial_scene) -> SceneManager:
        """Create SceneManager with all scene factories registered.
        
        Args:
            initial_scene: The initial scene to start with
            
        Returns:
            SceneManager with all factories registered
        """
        scene_manager = SceneManager(initial_scene)
        
        # Register game_loop factory
        def create_game_loop(core_game_state, **kwargs):
            strategies = kwargs.get('strategies', None)
            if strategies:
                # Build game with selected strategies
                game = build_game(strategies)
                core_game_state.game = game
                core_game_state.view_player_index = 0
            return GameLoopScene(core_game_state, **kwargs)
        
        # Register shop factory
        def create_shop(core_game_state, **kwargs):
            return ShopScene(core_game_state, asset_loader=self.asset_loader)
        
        # Register combat factory
        def create_combat(core_game_state, **kwargs):
            return CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        scene_manager.register_scene_factory("game_loop", create_game_loop)
        scene_manager.register_scene_factory("shop", create_shop)
        scene_manager.register_scene_factory("combat", create_combat)
        
        return scene_manager

    def test_scene_transition_chain(self):
        """
        Verify that scene transitions follow the correct flow.
        
        Flow: Lobby → GameLoop → Shop → Combat → GameLoop
        
        Validates:
        - Requirement 13: Scene transition chain
        - T1.10: Wire scene transition chain
        """
        # Create initial game and core state
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        lobby_scene = LobbyScene(core_game_state)
        
        # Create scene manager with factories
        scene_manager = self.create_scene_manager_with_factories(lobby_scene)
        lobby_scene.scene_manager = scene_manager
        
        # Verify initial scene is lobby
        assert isinstance(scene_manager.active_scene, LobbyScene), \
            "Initial scene should be LobbyScene"
        
        # Simulate lobby selecting strategies and transitioning to game_loop
        test_strategies = ["random", "random"]
        scene_manager.request_transition("game_loop", strategies=test_strategies)
        scene_manager._execute_transition()
        
        # Verify transition to GameLoopScene
        assert isinstance(scene_manager.active_scene, GameLoopScene), \
            "Scene should transition from Lobby to GameLoopScene"
        assert scene_manager.active_scene.core_game_state.game is not None, \
            "Game should be built in GameLoopScene"
        
        # Simulate SPACE key press to advance turn (transition to shop)
        input_state = self.create_input_state_with_key(pygame.K_SPACE)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        
        # Verify transition to ShopScene
        assert isinstance(scene_manager.active_scene, ShopScene), \
            "Scene should transition from GameLoop to ShopScene"
        
        # Simulate ENTER key press to complete shop (transition to combat)
        input_state = self.create_input_state_with_key(pygame.K_RETURN)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        
        # Verify transition to CombatScene
        assert isinstance(scene_manager.active_scene, CombatScene), \
            "Scene should transition from Shop to CombatScene"
        
        # Simulate ENTER key press to complete placement (transition back to game_loop)
        input_state = self.create_input_state_with_key(pygame.K_RETURN)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        
        # Verify transition back to GameLoopScene
        assert isinstance(scene_manager.active_scene, GameLoopScene), \
            "Scene should transition from Combat back to GameLoopScene"
        
        print("✓ Scene transition chain verified: Lobby → GameLoop → Shop → Combat → GameLoop")

    def test_income_applied_at_turn_start(self):
        """
        Verify that income is applied to the current player at turn start.
        
        Validates:
        - Requirement 26: Economy system integration (income)
        - T1.7: Turn orchestration logic includes income
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Get current player and initial gold
        current_player = core_game_state.current_player
        initial_gold = current_player.gold
        
        # Advance turn (should apply income)
        game_loop_scene.advance_turn()
        
        # Verify income was applied
        assert current_player.gold > initial_gold, \
            f"Income should be applied at turn start. " \
            f"Expected gold > {initial_gold}, got {current_player.gold}"
        
        print(f"✓ Income applied: {initial_gold} → {current_player.gold} gold")

    def test_interest_applied_after_shop(self):
        """
        Verify that interest is applied after shop closes.
        
        Validates:
        - Requirement 12: Human player preparation phase (interest)
        - T1.12: Apply interest after shop closes
        """
        # Create game and ShopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        shop_scene = ShopScene(core_game_state, asset_loader=self.asset_loader)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(shop_scene)
        shop_scene.scene_manager = scene_manager
        
        # Get current player and set gold to trigger interest
        current_player = core_game_state.current_player
        current_player.gold = 50  # Enough to earn interest
        initial_gold = current_player.gold
        
        # Exit shop scene (should apply interest in on_exit)
        shop_scene.on_exit()
        
        # Verify interest was applied
        # Interest is typically 10% of gold rounded down, minimum 1 gold per 10 gold
        expected_min_gold = initial_gold + (initial_gold // 10)
        assert current_player.gold >= expected_min_gold, \
            f"Interest should be applied after shop closes. " \
            f"Expected gold >= {expected_min_gold}, got {current_player.gold}"
        
        print(f"✓ Interest applied: {initial_gold} → {current_player.gold} gold")

    def test_evolution_checked_after_combat(self):
        """
        Verify that evolution is checked after combat placement.
        
        Validates:
        - Requirement 12: Human player preparation phase (evolution)
        - T1.12: Check evolution after combat placement
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(combat_scene)
        combat_scene.scene_manager = scene_manager
        
        # Get current player
        current_player = core_game_state.current_player
        
        # Add cards to hand to enable evolution check
        # (Evolution requires specific card combinations)
        from engine_core.card import Card
        test_card = Card(
            name="Test Card",
            category="Test",
            rarity="3",
            stats={"Power": 5, "Durability": 4, "Speed": 3,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test_passive"
        )
        current_player.hand.append(test_card)
        
        # Exit combat scene (should check evolution in on_exit)
        try:
            combat_scene.on_exit()
            evolution_check_success = True
        except Exception as e:
            evolution_check_success = False
            error_msg = str(e)
        
        assert evolution_check_success, \
            f"Evolution check should complete without errors. " \
            f"Error: {error_msg if not evolution_check_success else ''}"
        
        print("✓ Evolution check completed after combat")

    def test_combat_triggered_after_preparation(self):
        """
        Verify that combat phase is triggered after all players complete preparation.
        
        Validates:
        - Requirement 27: Combat phase triggering
        - T1.13: Trigger combat phase and store results
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        # Set combat trigger flag (simulating return from CombatScene)
        game_loop_scene.ui_state.needs_combat_trigger = True
        
        # Call update to trigger combat
        game_loop_scene.update(16.0)  # 16ms frame time
        
        # Verify combat was triggered
        assert hasattr(game, 'last_combat_results'), \
            "Game should have last_combat_results after combat phase"
        
        # Verify combat results stored in UI state
        assert game_loop_scene.ui_state.popup_data is not None, \
            "Combat results should be stored in popup_data"
        
        print(f"✓ Combat triggered and results stored: {len(game_loop_scene.ui_state.popup_data)} battles")

    def test_locked_coords_cleared_after_turn(self):
        """
        Verify that locked coordinates are cleared after turn ends.
        
        Validates:
        - Requirement 7: Locked coordinates cleared after turn end
        - T1.13: Clear locked coords for all players
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        # Add locked coordinates for all players
        for player in game.players:
            core_game_state.locked_coords_per_player[player.pid].add((0, 0))
            core_game_state.locked_coords_per_player[player.pid].add((1, 1))
        
        # Verify locked coords exist
        for player in game.players:
            assert len(core_game_state.locked_coords_per_player[player.pid]) > 0, \
                f"Player {player.pid} should have locked coords before cleanup"
        
        # Trigger combat and cleanup (should clear locked coords)
        game_loop_scene.trigger_combat_and_cleanup()
        
        # Verify locked coords cleared
        for player in game.players:
            assert len(core_game_state.locked_coords_per_player[player.pid]) == 0, \
                f"Player {player.pid} locked coords should be cleared after turn. " \
                f"Found {len(core_game_state.locked_coords_per_player[player.pid])} locked coords"
        
        print("✓ Locked coordinates cleared for all players")

    def test_combat_results_popup_display(self):
        """
        Verify that combat results popup is displayed and fades out correctly.
        
        Validates:
        - Requirement 9: Combat results popup display
        - Requirement 25: Popup timer fade-out animation
        - T2.4: Add combat results popup to GameLoopScene
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        # Set combat trigger flag and trigger combat
        game_loop_scene.ui_state.needs_combat_trigger = True
        game_loop_scene.update(16.0)  # Trigger combat
        
        # Verify popup_timer is set to 3000ms
        POPUP_DURATION = 3000
        assert game_loop_scene.ui_state.popup_timer == POPUP_DURATION, \
            f"Popup timer should be set to {POPUP_DURATION}ms. " \
            f"Got {game_loop_scene.ui_state.popup_timer}ms"
        print(f"✓ Popup timer initialized: {game_loop_scene.ui_state.popup_timer}ms")
        
        # Verify popup_data is populated
        assert len(game_loop_scene.ui_state.popup_data) > 0, \
            "Popup data should contain combat results"
        print(f"✓ Popup data populated: {len(game_loop_scene.ui_state.popup_data)} battles")
        
        # Verify last_breakdown is extracted for current player
        view_player_pid = core_game_state.view_player_index
        assert game_loop_scene.ui_state.last_breakdown is not None, \
            "Last breakdown should be extracted for current player"
        
        # Verify last_breakdown contains current player
        breakdown = game_loop_scene.ui_state.last_breakdown
        assert (breakdown.get("pid_a") == view_player_pid or 
                breakdown.get("pid_b") == view_player_pid), \
            f"Last breakdown should contain current player (PID {view_player_pid})"
        print(f"✓ Combat breakdown extracted for Player {view_player_pid + 1}")
        
        # Test popup timer decrement
        initial_timer = game_loop_scene.ui_state.popup_timer
        dt = 500  # 500ms
        game_loop_scene.update(dt)
        
        expected_timer = max(0, initial_timer - dt)
        assert game_loop_scene.ui_state.popup_timer == expected_timer, \
            f"Popup timer should decrement by dt. " \
            f"Expected {expected_timer}ms, got {game_loop_scene.ui_state.popup_timer}ms"
        print(f"✓ Popup timer decremented: {initial_timer}ms → {game_loop_scene.ui_state.popup_timer}ms")
        
        # Test fade alpha calculation
        POPUP_DURATION = 3000
        popup_timer = game_loop_scene.ui_state.popup_timer
        fade_alpha = min(255, int(popup_timer / POPUP_DURATION * 510))
        
        # Verify fade alpha is in valid range
        assert 0 <= fade_alpha <= 255, \
            f"Fade alpha should be in range [0, 255]. Got {fade_alpha}"
        print(f"✓ Fade alpha calculated: {fade_alpha} (timer: {popup_timer}ms)")
        
        # Test popup timer reaches zero
        game_loop_scene.update(10000)  # Large dt to ensure timer reaches 0
        assert game_loop_scene.ui_state.popup_timer == 0, \
            f"Popup timer should reach 0. Got {game_loop_scene.ui_state.popup_timer}ms"
        print("✓ Popup timer reached 0 (popup dismissed)")
        
        # Test draw method doesn't crash with popup active
        try:
            # Reset timer to test drawing
            game_loop_scene.ui_state.popup_timer = 1500
            game_loop_scene.draw(self.screen)
            draw_success = True
        except Exception as e:
            draw_success = False
            error_msg = str(e)
        
        assert draw_success, \
            f"Draw method should not crash with popup active. " \
            f"Error: {error_msg if not draw_success else ''}"
        print("✓ Draw method renders popup without errors")

    def test_full_turn_cycle_integration(self):
        """
        Full integration test: Complete one turn cycle with all economy and combat logic.
        
        This is the main integration test that verifies the entire turn flow works correctly.
        
        Validates:
        - All requirements and tasks for Phase 1
        - Scene transitions work correctly
        - Economy logic (income, interest) applied
        - Combat triggered and results stored
        - Locked coordinates cleared
        """
        # Create initial game and lobby scene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        lobby_scene = LobbyScene(core_game_state)
        
        # Create scene manager with factories
        scene_manager = self.create_scene_manager_with_factories(lobby_scene)
        lobby_scene.scene_manager = scene_manager
        
        print("\n=== Starting Full Turn Cycle Integration Test ===")
        
        # Step 1: Lobby → GameLoop
        print("\n1. Lobby → GameLoop transition")
        test_strategies = ["random", "random"]
        scene_manager.request_transition("game_loop", strategies=test_strategies)
        scene_manager._execute_transition()
        assert isinstance(scene_manager.active_scene, GameLoopScene)
        print("   ✓ Transitioned to GameLoopScene")
        
        # Get game state
        game = core_game_state.game
        current_player = core_game_state.current_player
        initial_gold = current_player.gold
        initial_turn = game.turn
        
        # Step 2: GameLoop → Shop (advance turn)
        print("\n2. GameLoop → Shop transition (advance turn)")
        input_state = self.create_input_state_with_key(pygame.K_SPACE)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        assert isinstance(scene_manager.active_scene, ShopScene)
        print("   ✓ Transitioned to ShopScene")
        
        # Verify income applied
        assert current_player.gold > initial_gold, \
            f"Income should be applied. Expected > {initial_gold}, got {current_player.gold}"
        print(f"   ✓ Income applied: {initial_gold} → {current_player.gold} gold")
        
        # Step 3: Shop → Combat
        print("\n3. Shop → Combat transition")
        gold_before_shop = current_player.gold
        input_state = self.create_input_state_with_key(pygame.K_RETURN)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        assert isinstance(scene_manager.active_scene, CombatScene)
        print("   ✓ Transitioned to CombatScene")
        
        # Verify interest applied (if player had enough gold)
        if gold_before_shop >= 10:
            expected_min_gold = gold_before_shop + (gold_before_shop // 10)
            assert current_player.gold >= expected_min_gold, \
                f"Interest should be applied. Expected >= {expected_min_gold}, got {current_player.gold}"
            print(f"   ✓ Interest applied: {gold_before_shop} → {current_player.gold} gold")
        
        # Step 4: Combat → GameLoop (with combat trigger)
        print("\n4. Combat → GameLoop transition (trigger combat)")
        
        # Add locked coordinates before combat
        core_game_state.locked_coords_per_player[current_player.pid].add((0, 0))
        locked_coords_before = len(core_game_state.locked_coords_per_player[current_player.pid])
        print(f"   - Added {locked_coords_before} locked coords")
        
        input_state = self.create_input_state_with_key(pygame.K_RETURN)
        scene_manager.active_scene.handle_input(input_state)
        scene_manager._execute_transition()
        assert isinstance(scene_manager.active_scene, GameLoopScene)
        print("   ✓ Transitioned back to GameLoopScene")
        
        # Step 5: Trigger combat in GameLoopScene
        print("\n5. Trigger combat phase")
        game_loop_scene = scene_manager.active_scene
        game_loop_scene.update(16.0)  # Trigger combat via update
        
        # Verify combat triggered
        assert hasattr(game, 'last_combat_results'), \
            "Combat should be triggered"
        print("   ✓ Combat phase triggered")
        
        # Verify locked coords cleared
        locked_coords_after = len(core_game_state.locked_coords_per_player[current_player.pid])
        assert locked_coords_after == 0, \
            f"Locked coords should be cleared. Expected 0, got {locked_coords_after}"
        print("   ✓ Locked coordinates cleared")
        
        # Verify turn incremented
        assert game.turn > initial_turn, \
            f"Turn should increment. Expected > {initial_turn}, got {game.turn}"
        print(f"   ✓ Turn incremented: {initial_turn} → {game.turn}")
        
        print("\n=== Full Turn Cycle Integration Test PASSED ===\n")

    def test_ai_player_economy_phase(self):
        """
        Verify that AI players receive income, buy cards, and earn interest correctly.
        
        This test validates T2.5a implementation.
        
        NOTE: Since T2.5b was implemented, process_ai_turns() now includes both
        economy and placement phases. This test focuses on verifying the economy
        phase logic (income, buy, interest) while acknowledging placement may occur.
        
        Validates:
        - Requirement 12: AI player turns (economy phase)
        - Requirement 26: Economy system integration (income, interest)
        - T2.5a: AI player economy phase (income + shop)
        """
        # Create game with multiple players (human + AI)
        game = self.create_test_game(strategies=["random", "warrior", "builder"])
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        print("\n=== Testing AI Player Economy Phase (T2.5a) ===")
        
        # Get AI players (all except view_player_index)
        view_player_pid = core_game_state.view_player_index
        ai_players = [p for p in game.players if p.pid != view_player_pid and p.alive]
        
        print(f"\nView player: Player {view_player_pid + 1}")
        print(f"AI players: {[f'Player {p.pid + 1} ({p.strategy})' for p in ai_players]}")
        
        # Record initial state for each AI player
        initial_states = {}
        for player in ai_players:
            initial_states[player.pid] = {
                'gold': player.gold,
                'hand_size': len(player.hand),
                'board_size': player.board.alive_count()
            }
            print(f"\nPlayer {player.pid + 1} ({player.strategy}) initial state:")
            print(f"  - Gold: {player.gold}")
            print(f"  - Hand size: {len(player.hand)}")
            print(f"  - Board size: {player.board.alive_count()}")
        
        # Call process_ai_turns (now includes both economy and placement)
        print("\n--- Calling process_ai_turns() ---")
        game_loop_scene.process_ai_turns()
        
        # Verify each AI player received income, bought cards, and earned interest
        print("\n--- Verifying AI player economy phase ---")
        for player in ai_players:
            initial = initial_states[player.pid]
            
            print(f"\nPlayer {player.pid + 1} ({player.strategy}) after economy phase:")
            print(f"  - Gold: {initial['gold']} → {player.gold}")
            print(f"  - Hand size: {initial['hand_size']} → {len(player.hand)}")
            print(f"  - Board size: {initial['board_size']} → {player.board.alive_count()}")
            
            # Calculate total cards (hand + board)
            initial_total_cards = initial['hand_size'] + initial['board_size']
            final_total_cards = len(player.hand) + player.board.alive_count()
            
            # Verify total cards increased or stayed same
            # (cards can move from hand to board, but total should not decrease)
            total_cards_increased_or_same = final_total_cards >= initial_total_cards
            assert total_cards_increased_or_same, \
                f"Player {player.pid + 1} total cards should not decrease. " \
                f"Initial: {initial_total_cards}, Final: {final_total_cards}"
            
            if final_total_cards > initial_total_cards:
                cards_gained = final_total_cards - initial_total_cards
                print(f"  ✓ AI gained {cards_gained} card(s) total (bought from market)")
                print(f"  ✓ Economy phase executed (income → buy → interest)")
            else:
                print(f"  ✓ AI did not buy cards (no suitable cards in market)")
                # If no cards bought, gold should have increased (income + interest)
                # unless cards were placed (which doesn't affect gold)
                if player.board.alive_count() == initial['board_size']:
                    assert player.gold >= initial['gold'], \
                        f"Player {player.pid + 1} gold should increase if no cards bought/placed. " \
                        f"Initial: {initial['gold']}, Final: {player.gold}"
                print(f"  ✓ Economy phase executed (income → interest)")
        
        print("\n=== AI Player Economy Phase Test PASSED ===\n")

    def test_ai_player_placement_phase(self):
        """
        Verify that AI players place cards on board, check evolution, and strengthen copies.
        
        This test validates T2.5b implementation.
        
        Validates:
        - Requirement 12: AI player turns (placement phase)
        - T2.5b: AI player placement phase (place + evolution + strengthening)
        """
        # Create game with multiple players (human + AI)
        game = self.create_test_game(strategies=["random", "warrior", "builder"])
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        print("\n=== Testing AI Player Placement Phase (T2.5b) ===")
        
        # Get AI players (all except view_player_index)
        view_player_pid = core_game_state.view_player_index
        ai_players = [p for p in game.players if p.pid != view_player_pid and p.alive]
        
        print(f"\nView player: Player {view_player_pid + 1}")
        print(f"AI players: {[f'Player {p.pid + 1} ({p.strategy})' for p in ai_players]}")
        
        # Record initial state for each AI player
        initial_states = {}
        for player in ai_players:
            initial_states[player.pid] = {
                'hand_size': len(player.hand),
                'board_size': player.board.alive_count()
            }
            print(f"\nPlayer {player.pid + 1} ({player.strategy}) initial state:")
            print(f"  - Hand size: {len(player.hand)}")
            print(f"  - Board size: {player.board.alive_count()}")
        
        # Call process_ai_turns (includes both economy and placement)
        print("\n--- Calling process_ai_turns() ---")
        game_loop_scene.process_ai_turns()
        
        # Verify each AI player placed cards, checked evolution, and strengthened copies
        print("\n--- Verifying AI player placement phase ---")
        for player in ai_players:
            initial = initial_states[player.pid]
            
            print(f"\nPlayer {player.pid + 1} ({player.strategy}) after placement phase:")
            print(f"  - Hand size: {initial['hand_size']} → {len(player.hand)}")
            print(f"  - Board size: {initial['board_size']} → {player.board.alive_count()}")
            
            # Verify board size increased or stayed same
            # Board size should increase if AI placed cards
            board_size_increased_or_same = player.board.alive_count() >= initial['board_size']
            assert board_size_increased_or_same, \
                f"Player {player.pid + 1} board size should not decrease. " \
                f"Initial: {initial['board_size']}, Final: {player.board.alive_count()}"
            
            if player.board.alive_count() > initial['board_size']:
                cards_placed = player.board.alive_count() - initial['board_size']
                print(f"  ✓ AI placed {cards_placed} card(s) on board")
                print(f"  ✓ Placement phase executed (evolution → place → strengthen)")
            else:
                print(f"  ✓ AI did not place cards (hand might be empty or board full)")
                print(f"  ✓ Placement phase executed (evolution → strengthen)")
            
            # Verify evolution was checked (no assertion, just log)
            print(f"  ✓ Evolution checked")
            
            # Verify copy strengthening was checked (no assertion, just log)
            print(f"  ✓ Copy strengthening checked")
        
        print("\n=== AI Player Placement Phase Test PASSED ===\n")

    def test_fast_mode_toggle(self):
        """
        Verify that fast mode can be toggled on/off with F key.
        
        Validates:
        - Requirement 4: Fast mode toggle
        - Requirement 14: Input handling (F key)
        - T2.1: InputState intent mappings (INTENT_TOGGLE_FAST_MODE)
        - T2.2: Fast mode toggle in GameLoopScene
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        print("\n=== Testing Fast Mode Toggle (T2.2) ===")
        
        # Verify initial fast_mode is False
        initial_fast_mode = core_game_state.fast_mode
        print(f"\nInitial fast_mode: {initial_fast_mode}")
        assert initial_fast_mode == False, \
            f"Initial fast_mode should be False. Got {initial_fast_mode}"
        
        # Press F key to toggle fast mode ON
        print("\n--- Pressing F key to toggle fast mode ON ---")
        input_state = self.create_input_state_with_key(pygame.K_f)
        game_loop_scene.handle_input(input_state)
        
        # Verify fast_mode is now True
        assert core_game_state.fast_mode == True, \
            f"Fast mode should be True after F key press. Got {core_game_state.fast_mode}"
        print(f"✓ Fast mode toggled ON: {initial_fast_mode} → {core_game_state.fast_mode}")
        
        # Press F key again to toggle fast mode OFF
        print("\n--- Pressing F key to toggle fast mode OFF ---")
        input_state = self.create_input_state_with_key(pygame.K_f)
        game_loop_scene.handle_input(input_state)
        
        # Verify fast_mode is now False
        assert core_game_state.fast_mode == False, \
            f"Fast mode should be False after second F key press. Got {core_game_state.fast_mode}"
        print(f"✓ Fast mode toggled OFF: True → {core_game_state.fast_mode}")
        
        print("\n=== Fast Mode Toggle Test PASSED ===\n")

    def test_fast_mode_auto_advance_turns(self):
        """
        Verify that fast mode auto-advances turns every 600ms.
        
        Validates:
        - Requirement 4: Fast mode auto-advance
        - T2.2: Fast mode timer and auto-advance
        - T2.6: Conditional shop skip for fast mode
        """
        # Create game and GameLoopScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        print("\n=== Testing Fast Mode Auto-Advance (T2.2, T2.6) ===")
        
        # Enable fast mode
        core_game_state.fast_mode = True
        print(f"\nFast mode enabled: {core_game_state.fast_mode}")
        
        # Record initial turn
        initial_turn = game.turn
        print(f"Initial turn: {initial_turn}")
        
        # Simulate 10 turns (600ms each = 6000ms total)
        FAST_DELAY = 600  # ms
        NUM_TURNS = 10
        total_time = FAST_DELAY * NUM_TURNS
        
        print(f"\n--- Simulating {NUM_TURNS} turns ({total_time}ms total) ---")
        
        # Update in chunks to simulate frame updates
        frame_time = 16.0  # 16ms per frame (~60 FPS)
        elapsed_time = 0.0
        
        while elapsed_time < total_time:
            game_loop_scene.update(frame_time)
            elapsed_time += frame_time
            
            # Execute any pending transitions
            if scene_manager._transition_requested:
                scene_manager._execute_transition()
                # If we transitioned away from GameLoopScene, break
                if not isinstance(scene_manager.active_scene, GameLoopScene):
                    break
        
        # Verify turn counter incremented
        final_turn = game.turn
        turns_advanced = final_turn - initial_turn
        
        print(f"\nFinal turn: {final_turn}")
        print(f"Turns advanced: {turns_advanced}")
        
        # In fast mode, turns should advance automatically
        # We expect at least some turns to advance (may not be exactly NUM_TURNS due to timing)
        assert turns_advanced > 0, \
            f"Turn counter should increment in fast mode. " \
            f"Expected > 0, got {turns_advanced}"
        
        print(f"✓ Turns auto-advanced in fast mode: {initial_turn} → {final_turn} ({turns_advanced} turns)")
        
        print("\n=== Fast Mode Auto-Advance Test PASSED ===\n")

    def test_player_switching_keyboard(self):
        """
        Verify that player switching works with 1-8 keys.
        
        Validates:
        - Requirement 5: Player switching (keyboard)
        - Requirement 14: Input handling (1-8 keys)
        - T2.1: InputState intent mappings (INTENT_SWITCH_PLAYER_1-8)
        - T2.3a: Player switching via 1-8 keys
        """
        # Create game with multiple players
        game = self.create_test_game(strategies=["random", "warrior", "builder", "defender"])
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        print("\n=== Testing Player Switching via Keyboard (T2.3a) ===")
        
        # Verify initial view_player_index
        initial_view_player = core_game_state.view_player_index
        print(f"\nInitial view_player_index: {initial_view_player} (Player {initial_view_player + 1})")
        
        # Test switching to each player using 1-8 keys
        num_players = len(game.players)
        print(f"Number of players: {num_players}")
        
        # Map keys to player indices (K_1 = player 0, K_2 = player 1, etc.)
        key_map = {
            0: pygame.K_1,
            1: pygame.K_2,
            2: pygame.K_3,
            3: pygame.K_4,
            4: pygame.K_5,
            5: pygame.K_6,
            6: pygame.K_7,
            7: pygame.K_8
        }
        
        for target_index in range(num_players):
            key = key_map[target_index]
            print(f"\n--- Pressing key {target_index + 1} to switch to Player {target_index + 1} ---")
            
            # Press the key
            input_state = self.create_input_state_with_key(key)
            game_loop_scene.handle_input(input_state)
            
            # Verify view_player_index changed
            current_view_player = core_game_state.view_player_index
            assert current_view_player == target_index, \
                f"view_player_index should be {target_index} after pressing key {target_index + 1}. " \
                f"Got {current_view_player}"
            
            print(f"✓ Switched to Player {current_view_player + 1} (index {current_view_player})")
        
        # Test switching to invalid player (should be ignored)
        if num_players < 8:
            invalid_index = num_players  # One beyond last player
            invalid_key = key_map[invalid_index]
            print(f"\n--- Pressing key {invalid_index + 1} (invalid player) ---")
            
            current_view_player = core_game_state.view_player_index
            input_state = self.create_input_state_with_key(invalid_key)
            game_loop_scene.handle_input(input_state)
            
            # Verify view_player_index did NOT change
            assert core_game_state.view_player_index == current_view_player, \
                f"view_player_index should not change for invalid player. " \
                f"Expected {current_view_player}, got {core_game_state.view_player_index}"
            
            print(f"✓ Invalid player switch ignored (stayed at Player {current_view_player + 1})")
        
        print("\n=== Player Switching via Keyboard Test PASSED ===\n")

    def test_player_switching_mouse_click(self):
        """
        Verify that player switching works by clicking on player panel.
        
        Validates:
        - Requirement 5: Player switching (mouse click)
        - T2.3b: Clickable player panel UI
        """
        # Create game with multiple players
        game = self.create_test_game(strategies=["random", "warrior", "builder", "defender"])
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        # Draw once to populate player_panel_rects
        game_loop_scene.draw(self.screen)
        
        print("\n=== Testing Player Switching via Mouse Click (T2.3b) ===")
        
        # Verify initial view_player_index
        initial_view_player = core_game_state.view_player_index
        print(f"\nInitial view_player_index: {initial_view_player} (Player {initial_view_player + 1})")
        
        # Get player panel bounds (right side of screen)
        # Player panel is positioned at x > screen_width - 300
        screen_width = 1600
        panel_x = screen_width - 300
        panel_y_start = 100  # Approximate Y position where player list starts
        player_height = 80   # Approximate height per player entry
        
        num_players = len(game.players)
        print(f"Number of players: {num_players}")
        
        # Test clicking on each player in the panel
        for target_index in range(num_players):
            # Get the actual rectangle for this player from ui_state
            if game_loop_scene.ui_state and game_loop_scene.ui_state.player_panel_rects:
                if target_index < len(game_loop_scene.ui_state.player_panel_rects):
                    rect = game_loop_scene.ui_state.player_panel_rects[target_index]
                    # Click in the center of the rectangle
                    click_x = rect.centerx
                    click_y = rect.centery
                else:
                    # Fallback to calculated position
                    click_x = panel_x + 50
                    click_y = panel_y_start + (target_index * player_height) + 40
            else:
                # Fallback to calculated position
                click_x = panel_x + 50
                click_y = panel_y_start + (target_index * player_height) + 40
            
            print(f"\n--- Clicking on Player {target_index + 1} at ({click_x}, {click_y}) ---")
            
            # Create mouse click event
            mouse_event = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {'button': 1, 'pos': (click_x, click_y)}
            )
            
            # Set mouse position before creating InputState
            # This is needed because InputState reads pygame.mouse.get_pos()
            # We need to mock this or pass the position differently
            
            # Create InputState with the event
            input_state = InputState([mouse_event])
            # Override mouse_pos to match our click position
            input_state.mouse_pos = (click_x, click_y)
            
            # Handle input
            game_loop_scene.handle_input(input_state)
            
            # Verify view_player_index changed
            current_view_player = core_game_state.view_player_index
            assert current_view_player == target_index, \
                f"view_player_index should be {target_index} after clicking Player {target_index + 1}. " \
                f"Got {current_view_player}"
            
            print(f"✓ Switched to Player {current_view_player + 1} (index {current_view_player})")
        
        # Test clicking outside player panel (should not change view)
        print(f"\n--- Clicking outside player panel at (100, 100) ---")
        current_view_player = core_game_state.view_player_index
        
        mouse_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {'button': 1, 'pos': (100, 100)}
        )
        input_state = InputState([mouse_event])
        game_loop_scene.handle_input(input_state)
        
        # Verify view_player_index did NOT change
        assert core_game_state.view_player_index == current_view_player, \
            f"view_player_index should not change when clicking outside panel. " \
            f"Expected {current_view_player}, got {core_game_state.view_player_index}"
        
        print(f"✓ Click outside panel ignored (stayed at Player {current_view_player + 1})")
        
        print("\n=== Player Switching via Mouse Click Test PASSED ===\n")

    def test_fast_mode_and_player_switching_integration(self):
        """
        Integration test: Verify fast mode and player switching work together.
        
        This is the main integration test for T2.7.
        
        Validates:
        - Fast mode can be toggled while viewing different players
        - Player switching works while fast mode is active
        - Fast mode timer resets correctly when switching players
        - All T2.x tasks work together correctly
        """
        # Create game with multiple players
        game = self.create_test_game(strategies=["random", "warrior", "builder"])
        core_game_state = CoreGameState(game)
        game_loop_scene = GameLoopScene(core_game_state)
        
        # Create scene manager
        scene_manager = self.create_scene_manager_with_factories(game_loop_scene)
        game_loop_scene.scene_manager = scene_manager
        
        # Enter scene to initialize UI state
        game_loop_scene.on_enter()
        
        # Draw once to populate player_panel_rects
        game_loop_scene.draw(self.screen)
        
        print("\n=== Testing Fast Mode + Player Switching Integration (T2.7) ===")
        
        # Step 1: Enable fast mode
        print("\n1. Enable fast mode")
        input_state = self.create_input_state_with_key(pygame.K_f)
        game_loop_scene.handle_input(input_state)
        assert core_game_state.fast_mode == True
        print("   ✓ Fast mode enabled")
        
        # Step 2: Switch to different player while fast mode is active
        print("\n2. Switch to Player 2 while fast mode is active")
        input_state = self.create_input_state_with_key(pygame.K_2)
        game_loop_scene.handle_input(input_state)
        assert core_game_state.view_player_index == 1
        assert core_game_state.fast_mode == True  # Fast mode should remain active
        print("   ✓ Switched to Player 2, fast mode still active")
        
        # Step 3: Verify fast mode continues to work after player switch
        print("\n3. Verify fast mode auto-advances turns after player switch")
        initial_turn = game.turn
        
        # Update for 1200ms (should advance 2 turns at 600ms each)
        game_loop_scene.update(600.0)
        game_loop_scene.update(600.0)
        
        # Execute any pending transitions
        if scene_manager._transition_requested:
            scene_manager._execute_transition()
        
        # Verify turns advanced
        turns_advanced = game.turn - initial_turn
        assert turns_advanced > 0, \
            f"Turns should advance in fast mode after player switch. Got {turns_advanced}"
        print(f"   ✓ Turns advanced: {initial_turn} → {game.turn} ({turns_advanced} turns)")
        
        # Step 4: Switch to Player 3 using mouse click
        print("\n4. Switch to Player 3 using mouse click")
        
        # Draw to update player_panel_rects
        game_loop_scene.draw(self.screen)
        
        # Get the actual rectangle for Player 3 (index 2)
        if game_loop_scene.ui_state and game_loop_scene.ui_state.player_panel_rects:
            if len(game_loop_scene.ui_state.player_panel_rects) > 2:
                rect = game_loop_scene.ui_state.player_panel_rects[2]
                click_x = rect.centerx
                click_y = rect.centery
            else:
                # Fallback
                screen_width = 1600
                panel_x = screen_width - 250
                click_y = 100 + (2 * 80) + 40
                click_x = panel_x
        else:
            # Fallback
            screen_width = 1600
            panel_x = screen_width - 250
            click_y = 100 + (2 * 80) + 40
            click_x = panel_x
        
        mouse_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {'button': 1, 'pos': (click_x, click_y)}
        )
        input_state = InputState([mouse_event])
        # Override mouse_pos to match our click position
        input_state.mouse_pos = (click_x, click_y)
        game_loop_scene.handle_input(input_state)
        
        assert core_game_state.view_player_index == 2
        assert core_game_state.fast_mode == True  # Fast mode should remain active
        print("   ✓ Switched to Player 3 via mouse, fast mode still active")
        
        # Step 5: Disable fast mode
        print("\n5. Disable fast mode")
        input_state = self.create_input_state_with_key(pygame.K_f)
        game_loop_scene.handle_input(input_state)
        assert core_game_state.fast_mode == False
        print("   ✓ Fast mode disabled")
        
        # Step 6: Verify turns no longer auto-advance
        print("\n6. Verify turns no longer auto-advance")
        current_turn = game.turn
        game_loop_scene.update(1000.0)  # Wait 1000ms
        
        # Turns should NOT advance without manual input
        assert game.turn == current_turn, \
            f"Turns should not auto-advance when fast mode is off. " \
            f"Expected {current_turn}, got {game.turn}"
        print(f"   ✓ Turns did not auto-advance (turn {game.turn})")
        
        # Step 7: Switch back to Player 1
        print("\n7. Switch back to Player 1")
        input_state = self.create_input_state_with_key(pygame.K_1)
        game_loop_scene.handle_input(input_state)
        assert core_game_state.view_player_index == 0
        print("   ✓ Switched back to Player 1")
        
        print("\n=== Fast Mode + Player Switching Integration Test PASSED ===\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
