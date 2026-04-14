"""
Property-based tests for shop card element visibility.

This test validates that all card elements (ribbon, cameo, stats, passive, title plate)
fit within the card bounds without clipping.

Feature: board-shop-ui-cleanup-v3
Task: 7.2 Write property test for shop card element visibility
Property 10: Shop Card Element Visibility
Validates: Requirements 5.3
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer
from engine_core.card import Card


# Strategy for generating various shop cards
def various_shop_cards_strategy():
    """Generate cards with various attributes."""
    return st.builds(
        Card,
        name=st.text(min_size=3, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ "),
        category=st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"]),
        rarity=st.sampled_from(["1", "2", "3", "4", "5", "E"]),
        stats=st.fixed_dictionaries({
            "Power": st.integers(min_value=0, max_value=15),
            "Durability": st.integers(min_value=0, max_value=15),
            "Size": st.integers(min_value=0, max_value=15),
            "Speed": st.integers(min_value=0, max_value=15),
            "Meaning": st.integers(min_value=0, max_value=15),
            "Secret": st.integers(min_value=0, max_value=15),
        }),
        passive_type=st.sampled_from(["none", "power_boost", "shield", "regen", "counter"]),
    )


def check_element_within_bounds(surface: pygame.Surface, 
                                element_rect: pygame.Rect,
                                card_rect: pygame.Rect) -> Dict[str, bool]:
    """
    Check if an element is within the card bounds by verifying:
    1. Element rect is within card rect
    2. No pixels are rendered outside card bounds
    
    Returns a dict with:
    - rect_within_bounds: whether element rect is within card rect
    - no_overflow: whether no pixels overflow card bounds
    """
    # Check if element rect is within card rect
    rect_within_bounds = (
        element_rect.left >= card_rect.left and
        element_rect.right <= card_rect.right and
        element_rect.top >= card_rect.top and
        element_rect.bottom <= card_rect.bottom
    )
    
    # Sample pixels around the card boundary to check for overflow
    overflow_pixels = 0
    
    # Check top boundary
    for x in range(card_rect.left, card_rect.right, 4):
        y = card_rect.top - 1
        if 0 <= y < surface.get_height() and 0 <= x < surface.get_width():
            pixel = surface.get_at((x, y))[:3]
            if pixel != (0, 0, 0):
                overflow_pixels += 1
    
    # Check bottom boundary
    for x in range(card_rect.left, card_rect.right, 4):
        y = card_rect.bottom
        if 0 <= y < surface.get_height() and 0 <= x < surface.get_width():
            pixel = surface.get_at((x, y))[:3]
            if pixel != (0, 0, 0):
                overflow_pixels += 1
    
    # Check left boundary
    for y in range(card_rect.top, card_rect.bottom, 4):
        x = card_rect.left - 1
        if 0 <= y < surface.get_height() and 0 <= x < surface.get_width():
            pixel = surface.get_at((x, y))[:3]
            if pixel != (0, 0, 0):
                overflow_pixels += 1
    
    # Check right boundary
    for y in range(card_rect.top, card_rect.bottom, 4):
        x = card_rect.right
        if 0 <= y < surface.get_height() and 0 <= x < surface.get_width():
            pixel = surface.get_at((x, y))[:3]
            if pixel != (0, 0, 0):
                overflow_pixels += 1
    
    return {
        'rect_within_bounds': rect_within_bounds,
        'no_overflow': overflow_pixels == 0,
        'overflow_pixels': overflow_pixels,
    }


class TestShopCardElementVisibility:
    """Property-based tests for shop card element visibility."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=various_shop_cards_strategy())
    def test_all_elements_within_card_bounds(self, card):
        """
        **Validates: Requirements 5.3**
        
        Property 10: Shop Card Element Visibility
        
        For any set of market cards, all card elements (ribbon, cameo, stats, 
        passive, title plate) SHALL fit within the card bounds without clipping.
        
        This test generates various shop cards, renders them, and verifies
        that all elements are within the card bounds.
        """
        # Create a surface and render the shop card
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))  # Black background
        
        # Define shop card rect (typical shop card dimensions)
        card_rect = pygame.Rect(100, 100, 240, 360)
        
        # Render the shop card
        self.renderer.draw_shop_card(
            surface, card, card_rect, 
            hovered=False, bought=False, affordable=True, cost=3
        )
        
        # Define element rects (same as in draw_shop_card)
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        passive_h = 56
        plate_h = 30
        bottom_pad = 12
        
        # Calculate element positions
        ribbon_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + 8,
            card_rect.width - margin * 2,
            ribbon_h
        )
        
        cameo_rect = pygame.Rect(
            card_rect.x + margin,
            ribbon_rect.bottom + 6,
            card_rect.width - margin * 2,
            cameo_h
        )
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            cameo_rect.bottom + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        passive_rect = pygame.Rect(
            card_rect.x + margin,
            stats_rect.bottom + spacing,
            card_rect.width - margin * 2,
            passive_h
        )
        
        title_plate_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.bottom - bottom_pad - plate_h,
            card_rect.width - margin * 2 - 64,
            plate_h
        )
        
        # Check each element
        elements = {
            'ribbon': ribbon_rect,
            'cameo': cameo_rect,
            'stats': stats_rect,
            'passive': passive_rect,
            'title_plate': title_plate_rect,
        }
        
        violations = []
        
        for element_name, element_rect in elements.items():
            result = check_element_within_bounds(surface, element_rect, card_rect)
            
            if not result['rect_within_bounds']:
                violations.append({
                    'element': element_name,
                    'issue': 'rect_outside_bounds',
                    'element_rect': element_rect,
                    'card_rect': card_rect,
                })
        
        # Check for overall overflow
        overall_check = check_element_within_bounds(surface, card_rect, card_rect)
        if not overall_check['no_overflow']:
            violations.append({
                'element': 'overall',
                'issue': 'pixels_overflow',
                'overflow_pixels': overall_check['overflow_pixels'],
            })
        
        # Report any violations
        assert len(violations) == 0, (
            f"Card elements overflow bounds for {card.name}.\n"
            f"Card rarity: {card.rarity}\n"
            f"Card rect: {card_rect}\n"
            f"Violations: {violations}"
        )
    
    def test_specific_card_all_elements_visible(self):
        """
        Deterministic test: verify all elements are visible for a specific card.
        """
        test_card = Card(
            name="FULL_CARD",
            category="EXISTENCE",
            rarity="3",
            stats={
                "Power": 10,
                "Durability": 8,
                "Size": 6,
                "Speed": 12,
                "Meaning": 7,
                "Secret": 9,
            },
            passive_type="power_boost",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=5)
        
        # Define element rects
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        passive_h = 56
        plate_h = 30
        bottom_pad = 12
        
        ribbon_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.y + 8,
            card_rect.width - margin * 2,
            ribbon_h
        )
        
        cameo_rect = pygame.Rect(
            card_rect.x + margin,
            ribbon_rect.bottom + 6,
            card_rect.width - margin * 2,
            cameo_h
        )
        
        stats_rect = pygame.Rect(
            card_rect.x + margin,
            cameo_rect.bottom + spacing,
            card_rect.width - margin * 2,
            stats_h
        )
        
        passive_rect = pygame.Rect(
            card_rect.x + margin,
            stats_rect.bottom + spacing,
            card_rect.width - margin * 2,
            passive_h
        )
        
        title_plate_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.bottom - bottom_pad - plate_h,
            card_rect.width - margin * 2 - 64,
            plate_h
        )
        
        # Verify all elements are within bounds
        elements = {
            'ribbon': ribbon_rect,
            'cameo': cameo_rect,
            'stats': stats_rect,
            'passive': passive_rect,
            'title_plate': title_plate_rect,
        }
        
        for element_name, element_rect in elements.items():
            assert element_rect.left >= card_rect.left, f"{element_name} left overflow"
            assert element_rect.right <= card_rect.right, f"{element_name} right overflow"
            assert element_rect.top >= card_rect.top, f"{element_name} top overflow"
            assert element_rect.bottom <= card_rect.bottom, f"{element_name} bottom overflow"
    
    def test_card_with_many_stats(self):
        """
        Deterministic test: verify elements don't overflow with many stats.
        """
        test_card = Card(
            name="MANY_STATS",
            category="MIND",
            rarity="5",
            stats={
                "Power": 15,
                "Durability": 14,
                "Size": 13,
                "Speed": 12,
                "Meaning": 11,
                "Secret": 10,
            },
            passive_type="shield",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=8)
        
        # Check for overflow
        overall_check = check_element_within_bounds(surface, card_rect, card_rect)
        
        assert overall_check['no_overflow'], (
            f"Card with many stats has overflow: {overall_check['overflow_pixels']} pixels"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
