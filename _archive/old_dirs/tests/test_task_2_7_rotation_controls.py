"""
Test Task 2.7: Rotation Controls

Tests for rotation control implementation in run_game2.py:
- R key press increments pending_rotation
- Right mouse button click increments pending_rotation
- Rotation stays in range 0-5 (modulo 6)
- Rotation resets on deselection

**Validates: Requirements 10.1, 10.2**
"""

import sys
import os
import pygame
from hypothesis import given, strategies as st, settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from run_game2 import HybridGameState, build_game, handle_input, initialize_fonts
from ui.board_renderer_v3 import BoardRendererV3 as BoardRenderer
from scenes.asset_loader import AssetLoader


class TestRotationControls:
    """Test suite for rotation controls (Task 2.7)."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        pygame.init()
        self.screen = pygame.display.set_mode((1600, 960))
        self.fonts = initialize_fonts()
        self.game = build_game()
        self.state = HybridGameState(game=self.game)
        self.renderer = BoardRenderer(origin=(800, 470), strategy=self.game.players[0].strategy)
        self.asset_loader = AssetLoader("assets/cards")
    
    def teardown_method(self):
        """Clean up after each test."""
        pygame.quit()
    
    def test_r_key_increments_rotation(self):
        """Test that R key increments pending_rotation when card is selected."""
        print("\n=== Testing R Key Rotation Increment ===")
        
        # Select a card first
        self.state.selected_hand_idx = 0
        self.state.pending_rotation = 0
        
        # Simulate R key press
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 1, \
            f"Expected rotation 1, got {self.state.pending_rotation}"
        print("✓ R key incremented rotation from 0 to 1")
        
        # Press R again
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 2, \
            f"Expected rotation 2, got {self.state.pending_rotation}"
        print("✓ R key incremented rotation from 1 to 2")
    
    def test_r_key_no_effect_without_selection(self):
        """Test that R key has no effect when no card is selected."""
        print("\n=== Testing R Key Without Selection ===")
        
        # No card selected
        self.state.selected_hand_idx = None
        self.state.pending_rotation = 0
        
        # Simulate R key press
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 0, \
            f"Expected rotation to stay 0, got {self.state.pending_rotation}"
        print("✓ R key had no effect without card selection")
    
    def test_right_click_increments_rotation(self):
        """Test that right mouse button increments pending_rotation when card is selected."""
        print("\n=== Testing Right Click Rotation Increment ===")
        
        # Select a card first
        self.state.selected_hand_idx = 0
        self.state.pending_rotation = 0
        
        # Simulate right click
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (100, 100)})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 1, \
            f"Expected rotation 1, got {self.state.pending_rotation}"
        print("✓ Right click incremented rotation from 0 to 1")
        
        # Right click again
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (100, 100)})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 2, \
            f"Expected rotation 2, got {self.state.pending_rotation}"
        print("✓ Right click incremented rotation from 1 to 2")
    
    def test_right_click_no_effect_without_selection(self):
        """Test that right click has no effect when no card is selected."""
        print("\n=== Testing Right Click Without Selection ===")
        
        # No card selected
        self.state.selected_hand_idx = None
        self.state.pending_rotation = 0
        
        # Simulate right click
        events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': (100, 100)})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 0, \
            f"Expected rotation to stay 0, got {self.state.pending_rotation}"
        print("✓ Right click had no effect without card selection")
    
    def test_rotation_wraparound(self):
        """Test that rotation wraps around from 5 to 0 (modulo 6)."""
        print("\n=== Testing Rotation Wraparound ===")
        
        # Select a card
        self.state.selected_hand_idx = 0
        self.state.pending_rotation = 5
        
        # Press R to wrap around
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.pending_rotation == 0, \
            f"Expected rotation to wrap to 0, got {self.state.pending_rotation}"
        print("✓ Rotation wrapped from 5 to 0")
    
    def test_rotation_reset_on_deselection(self):
        """Test that rotation resets to 0 when card is deselected."""
        print("\n=== Testing Rotation Reset on Deselection ===")
        
        # Select a card and rotate it
        self.state.selected_hand_idx = 0
        self.state.pending_rotation = 3
        
        # Deselect by pressing ESC
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.selected_hand_idx is None, \
            "Expected card to be deselected"
        assert self.state.pending_rotation == 0, \
            f"Expected rotation to reset to 0, got {self.state.pending_rotation}"
        print("✓ Rotation reset to 0 on deselection")
    
    def test_rotation_reset_on_player_switch(self):
        """Test that rotation resets when switching players."""
        print("\n=== Testing Rotation Reset on Player Switch ===")
        
        # Select a card and rotate it
        self.state.selected_hand_idx = 0
        self.state.pending_rotation = 3
        
        # Switch player with TAB
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_TAB})]
        handle_input(events, self.state, self.game, self.renderer, self.screen, self.fonts, self.asset_loader)
        
        assert self.state.selected_hand_idx is None, \
            "Expected card to be deselected"
        assert self.state.pending_rotation == 0, \
            f"Expected rotation to reset to 0, got {self.state.pending_rotation}"
        print("✓ Rotation reset to 0 on player switch")


# ── Property-Based Tests ──────────────────────────────────────

class TestRotationProperties:
    """Property-based tests for rotation controls."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        pygame.init()
        self.screen = pygame.display.set_mode((1600, 960))
        self.fonts = initialize_fonts()
        self.asset_loader = AssetLoader("assets/cards")
    
    def teardown_method(self):
        """Clean up after each test."""
        pygame.quit()
    
    @given(rotation=st.integers(min_value=0, max_value=5))
    @settings(max_examples=100)
    def test_property_rotation_increment_with_wraparound(self, rotation):
        """
        Property 13: Rotation Increment with Wraparound
        
        For any rotation value (0-5), incrementing rotation SHALL produce 
        (rotation + 1) % 6, ensuring rotation stays in range 0-5.
        
        **Validates: Requirements 10.1, 10.2**
        Feature: run_game2-ui-and-placement, Property 13: Rotation increment with wraparound
        """
        game = build_game()
        state = HybridGameState(game=game)
        renderer = BoardRenderer(origin=(800, 470), strategy=game.players[0].strategy)
        
        # Select a card and set initial rotation
        state.selected_hand_idx = 0
        state.pending_rotation = rotation
        
        # Press R to increment
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
        handle_input(events, state, game, renderer, self.screen, self.fonts, self.asset_loader)
        
        expected = (rotation + 1) % 6
        assert state.pending_rotation == expected, \
            f"Rotation increment failed: {rotation} + 1 should be {expected}, got {state.pending_rotation}"
        
        # Verify rotation is in valid range
        assert 0 <= state.pending_rotation <= 5, \
            f"Rotation out of range: {state.pending_rotation}"
    
    @given(rotation=st.integers(min_value=0, max_value=5))
    @settings(max_examples=100)
    def test_property_rotation_reset_on_deselection(self, rotation):
        """
        Property 14: Rotation Reset on Deselection
        
        For any rotation value, deselecting a card (setting selected_hand_idx 
        to None) SHALL reset pending_rotation to 0.
        
        **Validates: Requirements 10.5**
        Feature: run_game2-ui-and-placement, Property 14: Rotation reset on deselection
        """
        game = build_game()
        state = HybridGameState(game=game)
        renderer = BoardRenderer(origin=(800, 470), strategy=game.players[0].strategy)
        
        # Select a card and set rotation
        state.selected_hand_idx = 0
        state.pending_rotation = rotation
        
        # Deselect with ESC
        events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})]
        handle_input(events, state, game, renderer, self.screen, self.fonts, self.asset_loader)
        
        assert state.selected_hand_idx is None, \
            "Card should be deselected"
        assert state.pending_rotation == 0, \
            f"Rotation should reset to 0, got {state.pending_rotation}"
    
    @given(
        rotation=st.integers(min_value=0, max_value=5),
        increments=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_property_multiple_rotation_increments(self, rotation, increments):
        """
        Property: Multiple Rotation Increments
        
        For any starting rotation and number of increments, the final rotation
        SHALL equal (rotation + increments) % 6.
        
        **Validates: Requirements 10.1, 10.2**
        Feature: run_game2-ui-and-placement, Property 13: Rotation increment with wraparound
        """
        game = build_game()
        state = HybridGameState(game=game)
        renderer = BoardRenderer(origin=(800, 470), strategy=game.players[0].strategy)
        
        # Select a card and set initial rotation
        state.selected_hand_idx = 0
        state.pending_rotation = rotation
        
        # Press R multiple times
        for _ in range(increments):
            events = [pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_r})]
            handle_input(events, state, game, renderer, self.screen, self.fonts, self.asset_loader)
        
        expected = (rotation + increments) % 6
        assert state.pending_rotation == expected, \
            f"After {increments} increments from {rotation}, expected {expected}, got {state.pending_rotation}"
        
        # Verify rotation is in valid range
        assert 0 <= state.pending_rotation <= 5, \
            f"Rotation out of range: {state.pending_rotation}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
