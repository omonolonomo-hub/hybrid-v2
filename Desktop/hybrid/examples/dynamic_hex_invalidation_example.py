"""
Dynamic Hex Invalidation Example
═══════════════════════════════════════════════════════════════════════
Demonstrates how to use HexGridConfig for dynamic hex invalidation.

Use Case: "Wind Card" passive that disables a random hex each turn.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from v2.ui.hex_grid_config import HexGridConfig


def example_wind_card_passive():
    """
    Example: Wind card disables a random hex each turn.
    """
    # 1. Get the base configuration from engine
    base_config = HexGridConfig.from_engine()
    print(f"Base config has {len(base_config.valid_coords)} valid hexes")
    
    # 2. Simulate "Wind" effect: disable a random hex
    disabled_hex = random.choice(list(base_config.valid_coords))
    print(f"Wind card disables hex: {disabled_hex}")
    
    # 3. Create a new config with the disabled hex removed
    wind_config = HexGridConfig.from_custom(
        board_radius=base_config.board_radius,
        valid_coords=base_config.valid_coords - {disabled_hex}
    )
    print(f"Wind config has {len(wind_config.valid_coords)} valid hexes")
    
    # 4. Use wind_config for this turn's rendering
    # render_hex_grid(surface, board_cards, camera, config=wind_config)
    
    return wind_config


def example_earthquake_card_passive():
    """
    Example: Earthquake card disables all hexes in a radius around a point.
    """
    base_config = HexGridConfig.from_engine()
    
    # Earthquake epicenter
    epicenter = (1, 1)
    radius = 2
    
    # Calculate affected hexes (simple distance check)
    disabled_hexes = set()
    for q, r in base_config.valid_coords:
        # Axial distance formula
        distance = (abs(q - epicenter[0]) + 
                   abs(r - epicenter[1]) + 
                   abs((q + r) - (epicenter[0] + epicenter[1]))) / 2
        if distance <= radius:
            disabled_hexes.add((q, r))
    
    print(f"Earthquake at {epicenter} disables {len(disabled_hexes)} hexes")
    
    # Create config with disabled hexes removed
    earthquake_config = HexGridConfig.from_custom(
        board_radius=base_config.board_radius,
        valid_coords=base_config.valid_coords - disabled_hexes
    )
    
    return earthquake_config


def example_testing_with_custom_layout():
    """
    Example: Testing with a custom hex layout (no engine initialization needed).
    """
    # Create a small test layout
    test_coords = frozenset([
        (0, 0),   # Center
        (1, 0),   # East
        (0, 1),   # Southeast
        (-1, 1),  # Southwest
        (-1, 0),  # West
        (0, -1),  # Northwest
        (1, -1),  # Northeast
    ])
    
    test_config = HexGridConfig.from_custom(
        board_radius=1,
        valid_coords=test_coords
    )
    
    print(f"Test config has {len(test_config.valid_coords)} hexes")
    print(f"Test coords: {sorted(test_config.valid_coords)}")
    
    # Use in tests without engine initialization!
    # render_hex_grid(test_surface, {}, test_camera, config=test_config)
    
    return test_config


if __name__ == "__main__":
    print("=" * 70)
    print("Dynamic Hex Invalidation Examples")
    print("=" * 70)
    
    print("\n1. Wind Card Example:")
    print("-" * 70)
    example_wind_card_passive()
    
    print("\n2. Earthquake Card Example:")
    print("-" * 70)
    example_earthquake_card_passive()
    
    print("\n3. Testing with Custom Layout:")
    print("-" * 70)
    example_testing_with_custom_layout()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
