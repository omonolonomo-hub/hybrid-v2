"""
Hex System

Centralized hex coordinate math utilities with cube rounding algorithm.

CRITICAL: All hex-to-pixel and pixel-to-hex conversions MUST use cube rounding,
not simple round(q), round(r).
"""

import math
from typing import Tuple, List


class HexSystem:
    """Centralized hex coordinate math utilities.
    
    This is the single source of truth for all hex coordinate operations.
    Uses cube coordinate system with proper cube rounding algorithm.
    """
    
    def __init__(self, hex_size: float, origin: Tuple[int, int]):
        """Initialize hex system.
        
        Args:
            hex_size: Radius of hexagon in pixels
            origin: Screen coordinates of hex (0, 0)
        """
        self.hex_size = hex_size
        self.origin = origin
    
    def pixel_to_hex(self, px: int, py: int) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates using cube rounding.
        
        This is the REQUIRED method for all pixel-to-hex conversions.
        Uses cube rounding algorithm for accurate conversion.
        
        Args:
            px, py: Screen pixel coordinates
        
        Returns:
            (q, r) hex coordinates
        """
        # Translate to origin
        x = (px - self.origin[0]) / self.hex_size
        y = (py - self.origin[1]) / self.hex_size
        
        # Flat-top hex conversion to fractional cube coordinates
        frac_q = (2.0 / 3.0) * x
        frac_r = (-1.0 / 3.0) * x + (math.sqrt(3) / 3.0) * y
        
        # CRITICAL: Use cube rounding, not simple round()
        return self.cube_round(frac_q, frac_r)
    
    def hex_to_pixel(self, q: int, r: int) -> Tuple[int, int]:
        """Convert hex coordinates to pixel coordinates.
        
        Args:
            q, r: Hex coordinates
        
        Returns:
            (px, py) screen pixel coordinates
        """
        # Flat-top hex conversion
        x = self.hex_size * (3.0 / 2.0) * q
        y = self.hex_size * (math.sqrt(3) / 2.0 * q + math.sqrt(3) * r)
        
        # Translate to origin
        px = int(x + self.origin[0])
        py = int(y + self.origin[1])
        
        return (px, py)
    
    def cube_round(self, frac_q: float, frac_r: float) -> Tuple[int, int]:
        """Round fractional cube coordinates to nearest hex using cube rounding.
        
        This is the REQUIRED algorithm for all hex coordinate conversions.
        Simple round(q), round(r) is INCORRECT and will cause coordinate bugs.
        
        Algorithm:
        1. Calculate third coordinate s = -q - r (cube constraint)
        2. Round all three coordinates
        3. Find coordinate with largest rounding error
        4. Reset that coordinate to satisfy cube constraint
        
        Args:
            frac_q, frac_r: Fractional hex coordinates
        
        Returns:
            (q, r) integer hex coordinates
        """
        # Calculate third coordinate (cube constraint: q + r + s = 0)
        frac_s = -frac_q - frac_r
        
        # Round all three coordinates
        q = round(frac_q)
        r = round(frac_r)
        s = round(frac_s)
        
        # Calculate rounding errors
        q_diff = abs(q - frac_q)
        r_diff = abs(r - frac_r)
        s_diff = abs(s - frac_s)
        
        # Reset coordinate with largest rounding error
        # This ensures the cube constraint q + r + s = 0 is satisfied
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
        else:
            s = -q - r
        
        return (q, r)
    
    def neighbors(self, q: int, r: int) -> List[Tuple[int, int]]:
        """Get all 6 neighbors of a hex.
        
        Args:
            q, r: Hex coordinates
        
        Returns:
            List of 6 neighbor coordinates
        """
        # Cube coordinate directions for flat-top hexagons
        directions = [
            (1, 0),   # East
            (1, -1),  # Northeast
            (0, -1),  # Northwest
            (-1, 0),  # West
            (-1, 1),  # Southwest
            (0, 1),   # Southeast
        ]
        return [(q + dq, r + dr) for dq, dr in directions]
    
    def distance(self, q1: int, r1: int, q2: int, r2: int) -> int:
        """Calculate hex distance between two coordinates.
        
        Uses cube coordinate distance formula:
        distance = (|q1-q2| + |q1+r1-q2-r2| + |r1-r2|) / 2
        
        Args:
            q1, r1: First hex coordinates
            q2, r2: Second hex coordinates
        
        Returns:
            Manhattan distance in hex space
        """
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2
    
    def ring(self, center_q: int, center_r: int, radius: int) -> List[Tuple[int, int]]:
        """Get all hexes in a ring at specified radius from center.
        
        Args:
            center_q, center_r: Center hex coordinates
            radius: Ring radius (0 = center only, 1 = immediate neighbors, etc.)
        
        Returns:
            List of hex coordinates in the ring
        """
        if radius == 0:
            return [(center_q, center_r)]
        
        results = []
        # Start at a corner of the ring
        q, r = center_q - radius, center_r + radius
        
        # Walk around the ring
        directions = [(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)]
        for direction in directions:
            dq, dr = direction
            for _ in range(radius):
                results.append((q, r))
                q += dq
                r += dr
        
        return results
    
    def spiral(self, center_q: int, center_r: int, max_radius: int) -> List[Tuple[int, int]]:
        """Get all hexes in a spiral from center up to max_radius.
        
        Args:
            center_q, center_r: Center hex coordinates
            max_radius: Maximum radius to include
        
        Returns:
            List of hex coordinates in spiral order
        """
        results = [(center_q, center_r)]
        for radius in range(1, max_radius + 1):
            results.extend(self.ring(center_q, center_r, radius))
        return results
    
    def radial_grid(self, radius: int, center_q: int = 0, center_r: int = 0) -> List[Tuple[int, int]]:
        """Generate a radial hex grid using proper cube coordinate system.
        
        This method generates all hexes within a given radius from the center,
        using the mathematically correct cube coordinate iteration algorithm.
        For radius=3, this generates exactly 37 hexes.
        
        Args:
            radius: Grid radius (3 for 37 hexes)
            center_q: Center hex q coordinate (default: 0)
            center_r: Center hex r coordinate (default: 0)
        
        Returns:
            List of (q, r) hex coordinates in the radial grid
        """
        coords = []
        
        # Proper cube coordinate iteration (MATHEMATICAL CORRECTNESS)
        for q in range(-radius, radius + 1):
            for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
                coords.append((center_q + q, center_r + r))
        
        return coords
