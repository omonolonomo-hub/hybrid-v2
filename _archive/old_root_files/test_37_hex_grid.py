"""Test 37-hex grid geometry."""

def get_37_hex_coords():
    """Get all 37 hex coordinates using PROPER CUBE COORDINATE system."""
    coords = []
    radius = 3
    
    # Proper cube coordinate iteration (MATHEMATICAL CORRECTNESS)
    for q in range(-radius, radius + 1):
        for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1):
            coords.append((q, r))
    
    return coords


if __name__ == "__main__":
    coords = get_37_hex_coords()
    print(f"✓ Total hexes: {len(coords)}")
    print(f"✓ Unique hexes: {len(set(coords))}")
    print(f"✓ All unique: {len(coords) == len(set(coords))}")
    
    # Verify center exists
    print(f"✓ Center (0,0) exists: {(0, 0) in coords}")
    
    # Show ring distribution
    from collections import Counter
    distances = Counter()
    for q, r in coords:
        # Cube distance from origin
        s = -q - r
        dist = (abs(q) + abs(r) + abs(s)) // 2
        distances[dist] += 1
    
    print("\n✓ Ring distribution:")
    for ring in sorted(distances.keys()):
        expected = 1 if ring == 0 else ring * 6
        actual = distances[ring]
        status = "✓" if actual == expected else "✗"
        print(f"  {status} Ring {ring}: {actual} hexes (expected {expected})")
    
    print(f"\n✓ Grid is mathematically correct: {len(coords) == 37}")
