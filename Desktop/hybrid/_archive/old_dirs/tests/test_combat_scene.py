"""
Integration test for CombatScene card placement flow.

This test verifies that the card placement system works correctly, including:
- Hand card selection and deselection
- Card rotation (R key or right-click)
- Card placement on hex grid
- Placement limit enforcement (1 card per turn)
- Locked coordinates tracking and persistence
- Placement preview rendering

Feature: run-game-scene-integration
Task: T3.9 — Integration test: Card placement flow
Requirements: 6, 7, 15, 16, 24

Validates:
- Card selection from hand panel works
- Rotation increments correctly (0-5 range, 60° steps)
- Placement on valid hexes succeeds
- Placement limit enforced (placed_this_turn counter)
- Locked coordinates prevent re-placement
- Locked coordinates persist across scene transitions
"""

import pytest
import pygame
import sys
import os
from typing import Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scene_manager import SceneManager
from core.core_game_state import CoreGameState
from core.input_state import InputState
from scenes.combat_scene import CombatScene, InputMode
from scenes.game_loop_scene import GameLoopScene
from engine_core.card import Card
from engine_core.game_factory import build_game


class TestCombatSceneCardPlacement:
    """Integration test suite for CombatScene card placement flow."""

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
    
    def create_test_game(self):
        """Create a test game instance with 2 players.
        
        Returns:
            Game instance ready for testing
        """
        game = build_game(["random", "random"])
        return game
    
    def create_test_card(self, name: str = "Test Card", rotation: int = 0) -> Card:
        """Create a test card with specified properties.
        
        Args:
            name: Card name
            rotation: Initial rotation (0-5)
            
        Returns:
            Card instance for testing
        """
        return Card(
            name=name,
            category="Test",
            rarity="3",
            stats={"Power": 5, "Durability": 4, "Speed": 3,
                   "Intelligence": 0, "Harmony": 0, "Spread": 0},
            passive_type="test_passive",
            rotation=rotation
        )
    
    def create_input_state_with_key(self, key: int) -> InputState:
        """Create InputState with a specific key pressed.
        
        Args:
            key: Pygame key constant (e.g., pygame.K_r)
            
        Returns:
            InputState with the key pressed
        """
        event = pygame.event.Event(pygame.KEYDOWN, {'key': key, 'mod': 0})
        return InputState([event])
    
    def create_input_state_with_mouse_click(self, x: int, y: int, 
                                           button: int = 1) -> InputState:
        """Create InputState with a mouse click at (x, y).
        
        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            button: Mouse button (1=left, 3=right)
            
        Returns:
            InputState with mouse click event
        """
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, 
                                   {'pos': (x, y), 'button': button})
        return InputState([event])
    
    def create_empty_input_state(self) -> InputState:
        """Create InputState with no events.
        
        Returns:
            InputState with empty event list
        """
        return InputState([])

    def test_hand_card_selection(self):
        """
        Verify that clicking a hand card selects it.
        
        Validates:
        - Requirement 6.1: Click hand card to select
        - Requirement 15: Hand panel display
        - T3.3: Card selection logic
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test cards to player's hand
        current_player = core_game_state.current_player
        test_card_1 = self.create_test_card("Card 1")
        test_card_2 = self.create_test_card("Card 2")
        current_player.hand.append(test_card_1)
        current_player.hand.append(test_card_2)
        
        # Render hand panel to populate slot rects
        combat_scene.hand_panel.draw(self.screen)
        
        # Get first hand slot position (approximate)
        # HandPanel: SLOT_PADDING=16, SLOT_WIDTH=88, HEX_SIZE=76
        # First slot center: x ≈ 16 + 88/2 = 60
        # Y position: screen_h - PANEL_HEIGHT + HEADER_HEIGHT + cards_h/2
        screen_h = self.screen.get_height()
        hand_x = 60  # First slot center X
        hand_y = screen_h - 175 + 26 + 70  # Approximate Y in card area
        
        # Click on first hand card
        input_state = self.create_input_state_with_mouse_click(hand_x, hand_y)
        combat_scene.handle_input(input_state)
        
        # Verify card is selected
        assert combat_scene.ui_state.selected_hand_idx == 0, \
            f"First card should be selected. " \
            f"Expected selected_hand_idx=0, got {combat_scene.ui_state.selected_hand_idx}"
        
        # Verify pending_rotation is copied from card
        assert combat_scene.ui_state.pending_rotation == test_card_1.rotation, \
            f"Pending rotation should match card rotation. " \
            f"Expected {test_card_1.rotation}, got {combat_scene.ui_state.pending_rotation}"
        
        print(f"✓ Hand card selected: Card 1 (index 0)")
        print(f"✓ Pending rotation: {combat_scene.ui_state.pending_rotation}")

    def test_hand_card_deselection(self):
        """
        Verify that clicking the same hand card deselects it.
        
        Validates:
        - Requirement 6.1: Click same card to deselect
        - T3.3: Card selection logic (toggle)
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card")
        current_player.hand.append(test_card)
        
        # Render hand panel to populate slot rects
        combat_scene.hand_panel.draw(self.screen)
        
        # Get first hand slot position
        screen_h = self.screen.get_height()
        hand_x = 60
        hand_y = screen_h - 175 + 26 + 70
        
        # Click to select
        input_state = self.create_input_state_with_mouse_click(hand_x, hand_y)
        combat_scene.handle_input(input_state)
        assert combat_scene.ui_state.selected_hand_idx == 0
        
        # Click again to deselect
        input_state = self.create_input_state_with_mouse_click(hand_x, hand_y)
        combat_scene.handle_input(input_state)
        
        # Verify card is deselected
        assert combat_scene.ui_state.selected_hand_idx is None, \
            f"Card should be deselected. " \
            f"Expected selected_hand_idx=None, got {combat_scene.ui_state.selected_hand_idx}"
        
        print("✓ Hand card deselected")

    def test_card_rotation_with_r_key(self):
        """
        Verify that pressing R rotates the selected card.
        
        Validates:
        - Requirement 6.3: Press R to rotate card
        - T3.3: Rotation logic (increment pending_rotation mod 6)
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card", rotation=0)
        current_player.hand.append(test_card)
        
        # Select card manually
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = test_card.rotation
        
        # Press R to rotate
        input_state = self.create_input_state_with_key(pygame.K_r)
        combat_scene.handle_input(input_state)
        
        # Verify rotation incremented
        assert combat_scene.ui_state.pending_rotation == 1, \
            f"Rotation should increment to 1. " \
            f"Got {combat_scene.ui_state.pending_rotation}"
        
        # Press R again
        input_state = self.create_input_state_with_key(pygame.K_r)
        combat_scene.handle_input(input_state)
        
        assert combat_scene.ui_state.pending_rotation == 2, \
            f"Rotation should increment to 2. " \
            f"Got {combat_scene.ui_state.pending_rotation}"
        
        # Test wrap-around (5 → 0)
        combat_scene.ui_state.pending_rotation = 5
        input_state = self.create_input_state_with_key(pygame.K_r)
        combat_scene.handle_input(input_state)
        
        assert combat_scene.ui_state.pending_rotation == 0, \
            f"Rotation should wrap to 0. " \
            f"Got {combat_scene.ui_state.pending_rotation}"
        
        print("✓ Card rotation with R key: 0 → 1 → 2")
        print("✓ Rotation wrap-around: 5 → 0")

    def test_card_rotation_with_right_click(self):
        """
        Verify that right-clicking rotates the selected card.
        
        Validates:
        - Requirement 6.3: Right-click to rotate card
        - T3.3: Rotation logic (right-click alternative)
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card", rotation=0)
        current_player.hand.append(test_card)
        
        # Select card manually
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = test_card.rotation
        
        # Right-click to rotate
        input_state = self.create_input_state_with_mouse_click(800, 450, button=3)
        combat_scene.handle_input(input_state)
        
        # Verify rotation incremented
        assert combat_scene.ui_state.pending_rotation == 1, \
            f"Rotation should increment to 1. " \
            f"Got {combat_scene.ui_state.pending_rotation}"
        
        print("✓ Card rotation with right-click: 0 → 1")

    def test_card_placement_on_valid_hex(self):
        """
        Verify that clicking a valid hex places the selected card.
        
        Validates:
        - Requirement 6.4: Click empty hex to place card
        - Requirement 6.5: Increment placed_this_turn counter
        - T3.4: Placement limit enforcement
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card", rotation=0)
        current_player.hand.append(test_card)
        
        # Select card manually
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = test_card.rotation
        
        # Verify initial placed_this_turn counter
        assert combat_scene.ui_state.placed_this_turn == 0, \
            f"Initial placed_this_turn should be 0. " \
            f"Got {combat_scene.ui_state.placed_this_turn}"
        
        # Get a valid hex coordinate (center hex at origin)
        target_hex = (0, 0)
        
        # Ensure hex is empty
        if target_hex in current_player.board.grid:
            current_player.board.remove(target_hex)
        
        # Get pixel position for target hex
        pixel_pos = combat_scene.hex_system.hex_to_pixel(target_hex)
        
        # Click on target hex to place card
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos[0]), int(pixel_pos[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify card was placed
        placed_card = current_player.board.get_card_at(target_hex)
        assert placed_card is not None, \
            f"Card should be placed at {target_hex}"
        
        # Verify placed_this_turn incremented
        assert combat_scene.ui_state.placed_this_turn == 1, \
            f"placed_this_turn should increment to 1. " \
            f"Got {combat_scene.ui_state.placed_this_turn}"
        
        # Verify card removed from hand
        assert test_card not in current_player.hand, \
            "Card should be removed from hand after placement"
        
        # Verify selection cleared
        assert combat_scene.ui_state.selected_hand_idx is None, \
            "Selection should be cleared after placement"
        
        print(f"✓ Card placed at {target_hex}")
        print(f"✓ placed_this_turn: 0 → {combat_scene.ui_state.placed_this_turn}")
        print("✓ Card removed from hand")
        print("✓ Selection cleared")

    def test_placement_limit_enforcement(self):
        """
        Verify that placement limit (1 card per turn) is enforced.
        
        Validates:
        - Requirement 6.6: Reject placement when limit reached
        - Requirement 24: Placement limit enforcement
        - T3.4: Placement limit logic
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test cards to player's hand
        current_player = core_game_state.current_player
        test_card_1 = self.create_test_card("Card 1")
        test_card_2 = self.create_test_card("Card 2")
        current_player.hand.append(test_card_1)
        current_player.hand.append(test_card_2)
        
        # Place first card (should succeed)
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = 0
        
        target_hex_1 = (0, 0)
        if target_hex_1 in current_player.board.grid:
            current_player.board.remove(target_hex_1)
        pixel_pos_1 = combat_scene.hex_system.hex_to_pixel(target_hex_1)
        
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos_1[0]), int(pixel_pos_1[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify first placement succeeded
        assert combat_scene.ui_state.placed_this_turn == 1
        assert current_player.board.get_card_at(target_hex_1) is not None
        print("✓ First card placed successfully")
        
        # Try to place second card (should fail due to limit)
        combat_scene.ui_state.selected_hand_idx = 0  # Card 2 is now at index 0
        combat_scene.ui_state.pending_rotation = 0
        
        target_hex_2 = (1, 0)
        if target_hex_2 in current_player.board.grid:
            current_player.board.remove(target_hex_2)
        pixel_pos_2 = combat_scene.hex_system.hex_to_pixel(target_hex_2)
        
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos_2[0]), int(pixel_pos_2[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify second placement was rejected
        assert combat_scene.ui_state.placed_this_turn == 1, \
            f"placed_this_turn should remain 1 (limit reached). " \
            f"Got {combat_scene.ui_state.placed_this_turn}"
        
        # Verify card was NOT placed
        placed_card_2 = current_player.board.get_card_at(target_hex_2)
        assert placed_card_2 is None, \
            f"Second card should NOT be placed (limit reached)"
        
        # Verify card still in hand
        assert test_card_2 in current_player.hand, \
            "Card should remain in hand when placement rejected"
        
        print("✓ Second placement rejected (limit reached)")
        print(f"✓ placed_this_turn: {combat_scene.ui_state.placed_this_turn} (limit: 1)")

    def test_locked_coordinates_tracking(self):
        """
        Verify that placed cards are added to locked_coords_per_player.
        
        Validates:
        - Requirement 7.1: Add hex to locked_coords on placement
        - Requirement 6.7: Add coord to locked set
        - T3.5: Locked coordinates tracking
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card")
        current_player.hand.append(test_card)
        
        # Verify locked_coords is empty initially
        locked_coords = core_game_state.locked_coords_per_player[current_player.pid]
        assert len(locked_coords) == 0, \
            f"locked_coords should be empty initially. Got {len(locked_coords)}"
        
        # Place card
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = 0
        
        target_hex = (0, 0)
        if target_hex in current_player.board.grid:
            current_player.board.remove(target_hex)
        pixel_pos = combat_scene.hex_system.hex_to_pixel(target_hex)
        
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos[0]), int(pixel_pos[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify hex was added to locked_coords
        locked_coords = core_game_state.locked_coords_per_player[current_player.pid]
        assert target_hex in locked_coords, \
            f"Hex {target_hex} should be in locked_coords. " \
            f"Got {locked_coords}"
        
        assert len(locked_coords) == 1, \
            f"locked_coords should contain 1 hex. Got {len(locked_coords)}"
        
        print(f"✓ Hex {target_hex} added to locked_coords")
        print(f"✓ locked_coords size: {len(locked_coords)}")

    def test_locked_coordinates_prevent_placement(self):
        """
        Verify that locked coordinates prevent card placement.
        
        Validates:
        - Requirement 7.2: Prevent placement on locked coords
        - Requirement 6.8: Check if coord in locked set
        - T3.5: Locked coordinates validation
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test cards to player's hand
        current_player = core_game_state.current_player
        test_card_1 = self.create_test_card("Card 1")
        test_card_2 = self.create_test_card("Card 2")
        current_player.hand.append(test_card_1)
        current_player.hand.append(test_card_2)
        
        # Place first card
        target_hex = (0, 0)
        if target_hex in current_player.board.grid:
            current_player.board.remove(target_hex)
        
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = 0
        
        pixel_pos = combat_scene.hex_system.hex_to_pixel(target_hex)
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos[0]), int(pixel_pos[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify hex is locked
        locked_coords = core_game_state.locked_coords_per_player[current_player.pid]
        assert target_hex in locked_coords
        print(f"✓ Hex {target_hex} is locked")
        
        # Reset placement counter to allow another placement attempt
        combat_scene.ui_state.placed_this_turn = 0
        
        # Try to place second card on same hex (should fail)
        combat_scene.ui_state.selected_hand_idx = 0  # Card 2 is now at index 0
        combat_scene.ui_state.pending_rotation = 0
        combat_scene.ui_state.input_mode = InputMode.PLACING
        
        input_state = self.create_input_state_with_mouse_click(
            int(pixel_pos[0]), int(pixel_pos[1])
        )
        combat_scene.handle_input(input_state)
        
        # Verify placement was rejected
        # Card 2 should still be in hand
        assert test_card_2 in current_player.hand, \
            "Card should remain in hand when placement on locked hex rejected"
        
        print("✓ Placement on locked hex rejected")
        print("✓ Card remains in hand")

    def test_locked_coordinates_persist_across_scenes(self):
        """
        Verify that locked coordinates persist across scene transitions.
        
        Validates:
        - Requirement 7: Locked coordinates persistence
        - Requirement 23.2: locked_coords_per_player persists across scenes
        - T3.5: Locked coordinates in CoreGameState
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add locked coordinates manually
        current_player = core_game_state.current_player
        test_hex = (0, 0)
        core_game_state.locked_coords_per_player[current_player.pid].add(test_hex)
        
        # Verify locked coords exist
        locked_coords_before = core_game_state.locked_coords_per_player[current_player.pid]
        assert test_hex in locked_coords_before
        print(f"✓ Locked coords before transition: {locked_coords_before}")
        
        # Exit CombatScene
        combat_scene.on_exit()
        
        # Create GameLoopScene (simulating scene transition)
        game_loop_scene = GameLoopScene(core_game_state)
        game_loop_scene.on_enter()
        
        # Verify locked coords still exist in CoreGameState
        locked_coords_after = core_game_state.locked_coords_per_player[current_player.pid]
        assert test_hex in locked_coords_after, \
            f"Locked coords should persist across scene transitions. " \
            f"Expected {test_hex} in {locked_coords_after}"
        
        print(f"✓ Locked coords after transition: {locked_coords_after}")
        print("✓ Locked coordinates persisted across scene transition")

    def test_placement_preview_rendering(self):
        """
        Verify that placement preview renders without errors.
        
        Validates:
        - Requirement 16: Placement preview display
        - T3.6: Placement preview integration
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Add test card to player's hand
        current_player = core_game_state.current_player
        test_card = self.create_test_card("Test Card", rotation=2)
        current_player.hand.append(test_card)
        
        # Select card
        combat_scene.ui_state.selected_hand_idx = 0
        combat_scene.ui_state.pending_rotation = test_card.rotation
        
        # Set hover hex
        target_hex = (0, 0)
        combat_scene.ui_state.hover_hex = target_hex
        
        # Try to render scene with placement preview
        try:
            combat_scene.draw(self.screen)
            render_success = True
        except Exception as e:
            render_success = False
            error_msg = str(e)
        
        assert render_success, \
            f"Placement preview rendering should not crash. " \
            f"Error: {error_msg if not render_success else ''}"
        
        print("✓ Placement preview rendered without errors")
        print(f"✓ Preview hex: {target_hex}")
        print(f"✓ Preview rotation: {combat_scene.ui_state.pending_rotation}")

    def test_placement_counter_reset_on_scene_exit(self):
        """
        Verify that placed_this_turn counter resets when exiting scene.
        
        Validates:
        - Requirement 24.5: Reset counter on scene exit
        - T3.4: Placement limit counter lifecycle
        """
        # Create game and CombatScene
        game = self.create_test_game()
        core_game_state = CoreGameState(game)
        combat_scene = CombatScene(core_game_state, asset_loader=self.asset_loader)
        
        # Enter scene to initialize
        combat_scene.on_enter()
        
        # Verify initial counter is 0
        assert combat_scene.ui_state.placed_this_turn == 0
        
        # Simulate placement
        combat_scene.ui_state.placed_this_turn = 1
        
        # Exit scene
        combat_scene.on_exit()
        
        # Re-enter scene (simulating new turn)
        combat_scene.on_enter()
        
        # Verify counter was reset
        assert combat_scene.ui_state.placed_this_turn == 0, \
            f"placed_this_turn should reset to 0 on scene re-entry. " \
            f"Got {combat_scene.ui_state.placed_this_turn}"
        
        print("✓ placed_this_turn counter reset on scene exit/re-entry")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
