"""
Property-based tests for title plate rarity consistency.

This test validates that the title plate styling (excluding rarity-specific accents)
is consistent across different rarities.

Feature: board-shop-ui-cleanup-v3
Task: 6.3 Write property test for title plate rarity consistency
Property 9: Title Plate Rarity Consistency
Validates: Requirements 4.5
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


# Strategy for generating pairs of cards with different rarities but similar other attributes
def card_pair_different_rarities_strategy():
    """Generate pairs of cards with different rarities."""
    # Generate base attributes that will be shared
    name = st.text(min_size=5, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    category = st.sampled_from(["EXISTENCE", "MIND", "CONNECTION"])
    stats_dict = st.fixed_dictionaries({
        "Power": st.integers(min_value=1, max_value=15),
        "Durability": st.integers(min_value=1, max_value=15),
        "Size": st.integers(min_value=1, max_value=15),
        "Speed": st.integers(min_value=1, max_value=15),
        "Meaning": st.integers(min_value=1, max_value=15),
        "Secret": st.integers(min_value=1, max_value=15),
    })
    passive = st.sampled_from(["none", "power_boost", "shield"])
    
    # Generate two different rarities
    rarity1 = st.sampled_from(["1", "2", "3", "4", "5", "E"])
    rarity2 = st.sampled_from(["1", "2", "3", "4", "5", "E"])
    
    # Build two cards with same attributes but different rarities
    return st.tuples(
        name, category, stats_dict, passive, rarity1, rarity2
    ).map(lambda t: (
        Card(name=t[0], category=t[1], rarity=t[4], stats=t[2], passive_type=t[3]),
        Card(name=t[0], category=t[1], rarity=t[5], stats=t[2], passive_type=t[3])
    ))


def extract_title_plate_structure(surface: pygame.Surface, 
                                  title_plate_rect: pygame.Rect) -> Dict[str, any]:
    """
    Extract structural properties of the title plate (excluding rarity-specific colors).
    
    Returns a dict with:
    - has_background: whether a background is present
    - has_border: whether a border is present
    - has_text: whether text is present
    - text_area_size: approximate size of text area
    """
    # Sample pixels to detect structure
    background_pixels = 0
    border_pixels = 0
    text_pixels = 0
    total_samples = 0
    
    # Sample the title plate area
    for x in range(title_plate_rect.x, title_plate_rect.right, 3):
        for y in range(title_plate_rect.y, title_plate_rect.bottom, 3):
            if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                pixel = surface.get_at((x, y))[:3]
                total_samples += 1
                
                # Classify pixel
                brightness = sum(pixel)
                
                if brightness < 50:
                    # Very dark - likely background
                    background_pixels += 1
                elif brightness > 200:
                    # Bright - likely text
                    text_pixels += 1
                else:
                    # Medium - likely border or accent
                    border_pixels += 1
    
    return {
        'has_background': background_pixels > 0,
        'has_border': border_pixels > 0,
        'has_text': text_pixels > 10,
        'total_samples': total_samples,
        'background_ratio': background_pixels / max(1, total_samples),
        'border_ratio': border_pixels / max(1, total_samples),
        'text_ratio': text_pixels / max(1, total_samples),
    }


def structures_are_consistent(struct1: Dict, struct2: Dict, tolerance: float = 0.15) -> bool:
    """
    Check if two title plate structures are consistent (within tolerance).
    
    We check that the ratios of background, border, and text are similar,
    which indicates consistent styling.
    """
    # Check that both have the same structural elements
    if struct1['has_background'] != struct2['has_background']:
        return False
    if struct1['has_border'] != struct2['has_border']:
        return False
    if struct1['has_text'] != struct2['has_text']:
        return False
    
    # Check that ratios are similar (within tolerance)
    bg_diff = abs(struct1['background_ratio'] - struct2['background_ratio'])
    border_diff = abs(struct1['border_ratio'] - struct2['border_ratio'])
    text_diff = abs(struct1['text_ratio'] - struct2['text_ratio'])
    
    return bg_diff <= tolerance and border_diff <= tolerance and text_diff <= tolerance


class TestTitlePlateRarityConsistency:
    """Property-based tests for title plate rarity consistency."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(card_pair=card_pair_different_rarities_strategy())
    def test_title_plate_styling_consistent_across_rarities(self, card_pair):
        """
        **Validates: Requirements 4.5**
        
        Property 9: Title Plate Rarity Consistency
        
        For any two cards with different rarities, the title plate styling 
        (excluding rarity-specific accents) SHALL be consistent.
        
        This test generates pairs of cards with different rarities, renders them
        as shop cards, and verifies that the title plate structure is consistent.
        """
        card1, card2 = card_pair
        
        # Skip if rarities are the same (nothing to test)
        if card1.rarity == card2.rarity:
            return
        
        # Create surfaces and render both cards
        surface1 = pygame.Surface((800, 600))
        surface1.fill((0, 0, 0))
        
        surface2 = pygame.Surface((800, 600))
        surface2.fill((0, 0, 0))
        
        card_rect = pygame.Rect(100, 100, 240, 360)
        
        # Render both cards
        self.renderer.draw_shop_card(surface1, card1, card_rect, cost=3)
        self.renderer.draw_shop_card(surface2, card2, card_rect, cost=3)
        
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
        
        # Extract structures
        struct1 = extract_title_plate_structure(surface1, title_plate_rect)
        struct2 = extract_title_plate_structure(surface2, title_plate_rect)
        
        # Verify structures are consistent
        consistent = structures_are_consistent(struct1, struct2, tolerance=0.15)
        
        assert consistent, (
            f"Title plate styling is inconsistent between rarities {card1.rarity} and {card2.rarity}.\n"
            f"Card name: {card1.name}\n"
            f"Rarity {card1.rarity} structure: {struct1}\n"
            f"Rarity {card2.rarity} structure: {struct2}"
        )
    
    def test_all_rarities_have_consistent_structure(self):
        """
        Deterministic test: verify all rarities have consistent title plate structure.
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        structures = []
        
        for rarity in rarities:
            test_card = Card(
                name="TEST_CARD",
                category="EXISTENCE",
                rarity=rarity,
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
            
            # Extract structure
            struct = extract_title_plate_structure(surface, title_plate_rect)
            structures.append((rarity, struct))
        
        # Compare all structures pairwise
        reference_rarity, reference_struct = structures[0]
        
        for rarity, struct in structures[1:]:
            consistent = structures_are_consistent(reference_struct, struct, tolerance=0.15)
            
            assert consistent, (
                f"Title plate styling is inconsistent between rarity {reference_rarity} "
                f"and rarity {rarity}.\n"
                f"Reference structure: {reference_struct}\n"
                f"Current structure: {struct}"
            )
    
    def test_title_plate_has_expected_elements(self):
        """
        Deterministic test: verify title plate has expected structural elements.
        """
        test_card = Card(
            name="ELEMENT_TEST",
            category="MIND",
            rarity="3",
            stats={
                "Power": 10,
                "Durability": 8,
                "Size": 6,
                "Speed": 12,
                "Meaning": 7,
                "Secret": 9,
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
        
        # Extract structure
        struct = extract_title_plate_structure(surface, title_plate_rect)
        
        # Verify expected elements are present
        assert struct['has_background'], "Title plate should have a background"
        assert struct['has_border'], "Title plate should have a border"
        assert struct['has_text'], "Title plate should have text (card name)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
