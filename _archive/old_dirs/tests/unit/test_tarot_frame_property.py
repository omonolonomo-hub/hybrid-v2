"""
Property-based tests for tarot frame geometry distinctness.

This test validates that the tarot-style hex frames produce visually distinct
patterns for different rarity levels, ensuring players can easily identify card rarity.

Feature: board-shop-ui-cleanup-v3
Task: 1.2 Write property test for tarot frame geometry distinctness
Property 1: Rarity Frame Geometry Distinctness
Validates: Requirements 1.5, 1.6
"""

import pytest
import pygame
import sys
import os
from hypothesis import given, settings, strategies as st
from typing import Dict, Tuple, Set
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ui.renderer import CyberRenderer
from engine_core.card import Card


# Strategy for generating rarity values
rarity_strategy = st.sampled_from(["1", "2", "3", "4", "5", "E"])


def extract_frame_features(surface: pygame.Surface, cx: int, cy: int, r: int) -> Dict[str, any]:
    """
    Extract geometric features from a rendered tarot frame.
    
    Features extracted:
    - pixel_count: Number of non-background pixels in the frame region
    - edge_pixels: Pixels along the hex edges
    - corner_pixels: Pixels at hex corners
    - inner_pixels: Pixels inside the hex (for inner rings/motifs)
    - pixel_distribution: Distribution of pixels by distance from center
    - color_signature: Unique colors used in the frame (excluding background and text)
    """
    features = {
        'pixel_count': 0,
        'edge_pixels': set(),
        'corner_pixels': set(),
        'inner_pixels': set(),
        'pixel_distribution': {},
        'color_signature': set(),
    }
    
    # Sample region around the hex
    sample_radius = r + 10
    bg_color = (0, 0, 0, 255)  # Black background
    
    # Define frame-relevant colors (exclude text colors which are typically white/gray)
    # Frame colors include: border colors, gold, darkened variants
    # Text colors are typically (255, 255, 255) or close to white
    def is_frame_color(pixel):
        """Check if pixel is likely a frame color (not background or text)"""
        if pixel == bg_color:
            return False
        # Exclude pure white and near-white (text colors)
        r, g, b = pixel[:3]
        if r > 240 and g > 240 and b > 240:
            return False
        return True
    
    for x in range(cx - sample_radius, cx + sample_radius):
        for y in range(cy - sample_radius, cy + sample_radius):
            if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                pixel = surface.get_at((x, y))
                
                # Only count frame-relevant pixels
                if is_frame_color(pixel):
                    features['pixel_count'] += 1
                    features['color_signature'].add(pixel[:3])  # RGB only
                    
                    # Calculate distance from center
                    dist = int(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5)
                    
                    # Categorize pixel by distance
                    if dist > r - 3:  # Near edge
                        features['edge_pixels'].add((x, y))
                    elif dist < 10:  # Near center
                        features['inner_pixels'].add((x, y))
                    
                    # Track distribution
                    dist_bucket = dist // 5
                    features['pixel_distribution'][dist_bucket] = \
                        features['pixel_distribution'].get(dist_bucket, 0) + 1
    
    return features


def compute_feature_signature(features: Dict[str, any]) -> Tuple:
    """
    Compute a signature tuple from extracted features for comparison.
    
    Returns a tuple that uniquely identifies the visual pattern.
    """
    return (
        features['pixel_count'],
        len(features['edge_pixels']),
        len(features['inner_pixels']),
        tuple(sorted(features['pixel_distribution'].items())),
        tuple(sorted(features['color_signature'])),  # Include color signature
    )


class TestTarotFrameGeometryDistinctness:
    """Property-based tests for tarot frame geometry distinctness."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize pygame and create renderer instance."""
        pygame.init()
        self.renderer = CyberRenderer()
        yield
        pygame.quit()
    
    @settings(max_examples=100)
    @given(rarity1=rarity_strategy, rarity2=rarity_strategy)
    def test_different_rarities_produce_distinct_frames(self, rarity1: str, rarity2: str):
        """
        **Validates: Requirements 1.5, 1.6**
        
        Property 1: Rarity Frame Geometry Distinctness
        
        For any two cards with different rarity values, the tarot-style hex frame
        SHALL produce visually distinct geometric patterns.
        """
        # Skip if rarities are the same
        if rarity1 == rarity2:
            return
        
        # Create surfaces for rendering
        surface1 = pygame.Surface((400, 400))
        surface2 = pygame.Surface((400, 400))
        surface1.fill((0, 0, 0))
        surface2.fill((0, 0, 0))
        
        # Render parameters
        cx, cy, r = 200, 200, 68
        rarity_col = (255, 255, 255)
        
        # Convert rarity to level
        rarity_level1 = 6 if rarity1 == "E" else int(rarity1)
        rarity_level2 = 6 if rarity2 == "E" else int(rarity2)
        
        # Render both frames
        self.renderer._draw_tarot_frame(
            surface1, cx, cy, r, rarity_col, rarity_level1, False
        )
        self.renderer._draw_tarot_frame(
            surface2, cx, cy, r, rarity_col, rarity_level2, False
        )
        
        # Extract features from both frames
        features1 = extract_frame_features(surface1, cx, cy, r)
        features2 = extract_frame_features(surface2, cx, cy, r)
        
        # Compute signatures
        sig1 = compute_feature_signature(features1)
        sig2 = compute_feature_signature(features2)
        
        # Assert that different rarities produce different visual patterns
        assert sig1 != sig2, (
            f"Frames for rarity {rarity1} (level {rarity_level1}) and "
            f"rarity {rarity2} (level {rarity_level2}) are not visually distinct.\n"
            f"Signature 1: {sig1}\n"
            f"Signature 2: {sig2}"
        )
    
    @settings(max_examples=100)
    @given(rarity=rarity_strategy)
    def test_same_rarity_produces_consistent_frames(self, rarity: str):
        """
        Verify that rendering the same rarity multiple times produces
        consistent visual output (sanity check).
        """
        # Create surfaces for rendering
        surface1 = pygame.Surface((400, 400))
        surface2 = pygame.Surface((400, 400))
        surface1.fill((0, 0, 0))
        surface2.fill((0, 0, 0))
        
        # Render parameters
        cx, cy, r = 200, 200, 68
        rarity_col = (255, 255, 255)
        rarity_level = 6 if rarity == "E" else int(rarity)
        
        # Render same frame twice
        self.renderer._draw_tarot_frame(
            surface1, cx, cy, r, rarity_col, rarity_level, False
        )
        self.renderer._draw_tarot_frame(
            surface2, cx, cy, r, rarity_col, rarity_level, False
        )
        
        # Extract features
        features1 = extract_frame_features(surface1, cx, cy, r)
        features2 = extract_frame_features(surface2, cx, cy, r)
        
        # Compute signatures
        sig1 = compute_feature_signature(features1)
        sig2 = compute_feature_signature(features2)
        
        # Assert consistency
        assert sig1 == sig2, (
            f"Same rarity {rarity} (level {rarity_level}) produced inconsistent frames.\n"
            f"Signature 1: {sig1}\n"
            f"Signature 2: {sig2}"
        )
    
    def test_all_rarity_pairs_are_distinct(self):
        """
        Exhaustive test: verify all pairs of different rarities produce distinct frames.
        This is a deterministic test that complements the property-based tests.
        """
        rarities = ["1", "2", "3", "4", "5", "E"]
        signatures = {}
        
        # Render all rarities and collect signatures
        for rarity in rarities:
            surface = pygame.Surface((400, 400))
            surface.fill((0, 0, 0))
            
            cx, cy, r = 200, 200, 68
            rarity_col = (255, 255, 255)
            rarity_level = 6 if rarity == "E" else int(rarity)
            
            self.renderer._draw_tarot_frame(
                surface, cx, cy, r, rarity_col, rarity_level, False
            )
            
            features = extract_frame_features(surface, cx, cy, r)
            sig = compute_feature_signature(features)
            signatures[rarity] = sig
        
        # Verify all signatures are unique
        sig_list = list(signatures.values())
        unique_sigs = set(sig_list)
        
        assert len(unique_sigs) == len(rarities), (
            f"Not all rarity frames are distinct. Found {len(unique_sigs)} unique "
            f"signatures for {len(rarities)} rarities.\n"
            f"Signatures: {signatures}"
        )
        
        # Verify each pair is distinct
        for i, rarity1 in enumerate(rarities):
            for rarity2 in rarities[i+1:]:
                assert signatures[rarity1] != signatures[rarity2], (
                    f"Frames for rarity {rarity1} and {rarity2} are not distinct.\n"
                    f"Signature {rarity1}: {signatures[rarity1]}\n"
                    f"Signature {rarity2}: {signatures[rarity2]}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
