"""
Automated test for Task 1.3: Verify HEX_SIZE accommodates card assets

This test verifies mathematically that:
- HEX_SIZE=85 is large enough for 140x160px card assets
- Cards fit with appropriate padding
- Hex edges remain visible
"""

import sys
import os
import math

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from ui.renderer_v3 import HEX_SIZE

# Card asset dimensions
CARD_WIDTH = 140
CARD_HEIGHT = 160

def test_hex_size_accommodates_cards():
    """Verify HEX_SIZE is large enough for card assets with padding."""
    print("=" * 60)
    print("Task 1.3: Hex Size Calculation Test")
    print("=" * 60)
    print()
    
    # Calculate card diagonal (worst case for rotation)
    card_diagonal = math.sqrt(CARD_WIDTH**2 + CARD_HEIGHT**2)
    print(f"Card dimensions: {CARD_WIDTH}x{CARD_HEIGHT}px")
    print(f"Card diagonal: {card_diagonal:.2f}px")
    print()
    
    # For a flat-top hexagon:
    # - Width (point to point): 2 * HEX_SIZE
    # - Height (flat to flat): sqrt(3) * HEX_SIZE
    # Cards are rendered scaled down to fit within the hex
    hex_width = 2 * HEX_SIZE
    hex_height = math.sqrt(3) * HEX_SIZE
    
    print(f"HEX_SIZE: {HEX_SIZE}px")
    print(f"Hex width (point to point): {hex_width:.2f}px")
    print(f"Hex height (flat to flat): {hex_height:.2f}px")
    print()
    
    # In practice, cards are rendered at a smaller scale to fit within the hex
    # The design doc states HEX_SIZE=85 should accommodate 140x160 cards
    # Let's check if the hex is large enough to contain the card with some margin
    
    # The card needs to fit within the hex's bounding box
    # For a flat-top hex, the bounding box is hex_width x hex_height
    card_fits_width = CARD_WIDTH <= hex_width
    card_fits_height = CARD_HEIGHT <= hex_height
    
    print(f"Card width ({CARD_WIDTH}px) vs Hex width ({hex_width:.2f}px): ", end="")
    if card_fits_width:
        print("✓ FITS")
    else:
        print("✗ TOO LARGE")
    
    print(f"Card height ({CARD_HEIGHT}px) vs Hex height ({hex_height:.2f}px): ", end="")
    if card_fits_height:
        print("✓ FITS")
    else:
        print("✗ TOO LARGE")
    
    print()
    
    # Calculate margins
    width_margin = hex_width - CARD_WIDTH
    height_margin = hex_height - CARD_HEIGHT
    
    print(f"Width margin: {width_margin:.2f}px ({width_margin/CARD_WIDTH*100:.1f}%)")
    print(f"Height margin: {height_margin:.2f}px ({height_margin/CARD_HEIGHT*100:.1f}%)")
    print()
    
    # Verify hex size is adequate
    fits = card_fits_width and card_fits_height
    if fits:
        print("✓ PASS: Cards fit within hexagon bounding box")
    else:
        print("✗ FAIL: Cards do not fit within hexagon bounding box")
    
    # Check if there's enough margin for hex edges to be visible
    min_margin = 10  # At least 10px margin for visible edges
    has_padding = width_margin >= min_margin and height_margin >= min_margin
    
    if has_padding:
        print("✓ PASS: Adequate margin for hex edges to be visible")
    else:
        print("✗ FAIL: Insufficient margin, hex edges may not be visible")
    
    print()
    
    # Check against design requirements
    # Design doc specifies HEX_SIZE should be at least 80px for 140x160px cards
    min_required_hex_size = 80
    if HEX_SIZE >= min_required_hex_size:
        print(f"✓ PASS: HEX_SIZE ({HEX_SIZE}) meets minimum requirement ({min_required_hex_size})")
        meets_requirement = True
    else:
        print(f"✗ FAIL: HEX_SIZE ({HEX_SIZE}) below minimum requirement ({min_required_hex_size})")
        meets_requirement = False
    
    print()
    print("=" * 60)
    
    if fits and has_padding and meets_requirement:
        print("✅ Task 1.3: All checks passed")
        print("   - Cards fit properly in hexagons")
        print("   - Hex edges are visible for edge stat display")
        print("   - HEX_SIZE meets design requirements")
        return True
    else:
        print("❌ Task 1.3: Some checks failed")
        return False

if __name__ == "__main__":
    success = test_hex_size_accommodates_cards()
    sys.exit(0 if success else 1)
