"""
Property-based tests for title plate name display.

This test validates that the card name appears in the title plate
of shop cards.

Feature: board-shop-ui-cleanup-v3
Task: 6.2 Write property test for title plate name display
Property 8: Title Plate Name Display
Validates: Requirements 4.2
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st, assume
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer
from engine_core.card import Card


# Strategy for generating card data with various names
def card_with_various_names_strategy():
    """Generate cards with various name lengths and characters."""
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
        passive_type=st.sampled_from(["none", "power_boost", "shield"]),
    )


def extract_title_plate_text(surface: pygame.Surface, 
                             title_plate_rect: pygame.Rect) -> str:
    """
    Extract text from the title plate by checking for non-black pixels.
    
    Returns a string indicating whether text was found in the title plate area.
    """
    # Sample pixels in the title plate area to detect if text was rendered
    non_black_pixels = 0
    total_samples = 0
    
    # Sample across the title plate area
    for x in range(title_plate_rect.x, title_plate_rect.right, 4):
        for y in range(title_plate_rect.y, title_plate_rect.bottom, 4):
            if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                pixel = surface.get_at((x, y))[:3]
                total_samples += 1
                
                # Check if pixel is not black (background)
                if pixel != (0, 0, 0) and sum(pixel) > 30:
                    non_black_pixels += 1
    
    # If we found enough non-black pixels, text is present
    if non_black_pixels > 20 and total_samples > 0:
        return "TEXT_PRESENT"
    else:
        return "NO_TEXT"


class TestTitlePlateNameDisplay:
    """Property-based tests for title plate name display."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card=card_with_various_names_strategy())
    def test_card_name_appears_in_title_plate(self, card):
        """
        **Validates: Requirements 4.2**
        
        Property 8: Title Plate Name Display
        
        For any card in the shop, the title plate SHALL contain the card's name.
        
        This test generates cards with various names, renders them as shop cards,
        and verifies that the title plate contains text (the card name).
        """
        # Skip cards with empty names
        assume(len(card.name.strip()) > 0)
        
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
        
        # Calculate title plate rect position (same as in draw_shop_card)
        margin = 12
        bottom_pad = 12
        plate_h = 30
        
        # Title plate is at the bottom of the card
        title_plate_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.bottom - bottom_pad - plate_h,
            card_rect.width - margin * 2 - 64,  # Subtract cost area
            plate_h
        )
        
        # Extract text presence from title plate
        text_status = extract_title_plate_text(surface, title_plate_rect)
        
        # Verify text is present in title plate
        assert text_status == "TEXT_PRESENT", (
            f"Card name '{card.name}' not found in title plate.\n"
            f"Card rarity: {card.rarity}\n"
            f"Title plate rect: {title_plate_rect}\n"
            f"Text status: {text_status}"
        )
    
    def test_specific_card_short_name(self):
        """
        Deterministic test: verify a card with a short name.
        """
        # Create a card with a short name
        test_card = Card(
            name="FIRE",
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
        
        # Calculate title plate rect
        margin = 12
        bottom_pad = 12
        plate_h = 30
        
        title_plate_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.bottom - bottom_pad - plate_h,
            card_rect.width - margin * 2 - 64,
            plate_h
        )
        
        # Extract text presence
        text_status = extract_title_plate_text(surface, title_plate_rect)
        
        # Verify text is present
        assert text_status == "TEXT_PRESENT", (
            f"Expected card name 'FIRE' to appear in title plate, "
            f"but no text was detected."
        )
    
    def test_specific_card_long_name(self):
        """
        Deterministic test: verify a card with a long name (should be truncated).
        """
        # Create a card with a long name
        test_card = Card(
            name="VERY LONG CARD NAME",
            category="MIND",
            rarity="4",
            stats={
                "Power": 10,
                "Durability": 0,
                "Size": 6,
                "Speed": 0,
                "Meaning": 8,
                "Secret": 0,
            },
            passive_type="shield",
        )
        
        # Create surface and render
        surface = pygame.Surface((800, 600))
        surface.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        self.renderer.draw_shop_card(surface, test_card, card_rect, cost=4)
        
        # Calculate title plate rect
        margin = 12
        bottom_pad = 12
        plate_h = 30
        
        title_plate_rect = pygame.Rect(
            card_rect.x + margin,
            card_rect.bottom - bottom_pad - plate_h,
            card_rect.width - margin * 2 - 64,
            plate_h
        )
        
        # Extract text presence
        text_status = extract_title_plate_text(surface, title_plate_rect)
        
        # Verify text is present (even if truncated)
        assert text_status == "TEXT_PRESENT", (
            f"Expected card name 'VERY LONG CARD NAME' (possibly truncated) "
            f"to appear in title plate, but no text was detected."
        )
    
    def test_title_plate_with_different_rarities(self):
        """
        Deterministic test: verify title plate displays name for all rarities.
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        
        for rarity in rarities:
            test_card = Card(
                name=f"RARITY_{rarity}",
                category="CONNECTION",
                rarity=rarity,
                stats={
                    "Power": 5,
                    "Durability": 7,
                    "Size": 3,
                    "Speed": 9,
                    "Meaning": 11,
                    "Secret": 6,
                },
                passive_type="none",
            )
            
            # Create surface and render
            surface = pygame.Surface((800, 600))
            surface.fill((0, 0, 0))
            
            card_rect = pygame.Rect(100, 100, 240, 360)
            self.renderer.draw_shop_card(surface, test_card, card_rect, cost=3)
            
            # Calculate title plate rect
            margin = 12
            bottom_pad = 12
            plate_h = 30
            
            title_plate_rect = pygame.Rect(
                card_rect.x + margin,
                card_rect.bottom - bottom_pad - plate_h,
                card_rect.width - margin * 2 - 64,
                plate_h
            )
            
            # Extract text presence
            text_status = extract_title_plate_text(surface, title_plate_rect)
            
            # Verify text is present
            assert text_status == "TEXT_PRESENT", (
                f"Expected card name 'RARITY_{rarity}' to appear in title plate "
                f"for rarity {rarity}, but no text was detected."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
