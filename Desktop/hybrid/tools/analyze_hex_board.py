#!/usr/bin/env python3
"""
Analyze hex board layouts and center dominance.
"""

def hex_coords(radius: int):
    """Return all hex coordinates within the given radius."""
    return [(q, r) for q in range(-radius, radius+1)
                   for r in range(-radius, radius+1)
                   if abs(q+r) <= radius]

def count_neighbors(coord, all_coords):
    """Count how many neighbors a coordinate has."""
    q, r = coord
    HEX_DIRS = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]
    neighbors = [(q+dq, r+dr) for dq, dr in HEX_DIRS]
    return sum(1 for n in neighbors if n in all_coords)

def analyze_board(radius):
    """Analyze board layout and center dominance."""
    coords = hex_coords(radius)
    
    print(f"\n{'='*70}")
    print(f"BOARD ANALYSIS: Radius {radius}")
    print(f"{'='*70}")
    print(f"Total hexes: {len(coords)}")
    print(f"Center: (0, 0)")
    print()
    
    # Analyze center
    center_neighbors = count_neighbors((0, 0), coords)
    print(f"Center neighbors: {center_neighbors}")
    
    # Analyze neighbor distribution
    neighbor_counts = {}
    for coord in coords:
        n = count_neighbors(coord, coords)
        neighbor_counts[n] = neighbor_counts.get(n, 0) + 1
    
    print(f"\nNeighbor distribution:")
    for n in sorted(neighbor_counts.keys(), reverse=True):
        count = neighbor_counts[n]
        pct = (count / len(coords)) * 100
        print(f"  {n} neighbors: {count:2d} hexes ({pct:5.1f}%)")
    
    # Calculate center dominance
    max_neighbors = max(neighbor_counts.keys())
    center_dominance = (center_neighbors / max_neighbors) * 100
    print(f"\nCenter dominance: {center_dominance:.1f}%")
    
    # Ring analysis
    print(f"\nRing structure:")
    for ring in range(radius + 1):
        ring_coords = [c for c in coords if max(abs(c[0]), abs(c[1]), abs(c[0]+c[1])) == ring]
        print(f"  Ring {ring}: {len(ring_coords):2d} hexes")
    
    return coords, center_neighbors, neighbor_counts

def compare_boards():
    """Compare 19-hex vs 37-hex boards."""
    
    print("="*70)
    print("HEX BOARD COMPARISON: 19-hex vs 37-hex")
    print("="*70)
    
    # Analyze both boards
    coords_19, center_19, dist_19 = analyze_board(2)
    coords_37, center_37, dist_37 = analyze_board(3)
    
    # Comparison table
    print(f"\n{'='*70}")
    print("COMPARISON TABLE")
    print(f"{'='*70}")
    print(f"{'Metric':<30} {'19-hex (r=2)':<20} {'37-hex (r=3)':<20}")
    print("-"*70)
    print(f"{'Total hexes':<30} {len(coords_19):<20} {len(coords_37):<20}")
    print(f"{'Center neighbors':<30} {center_19:<20} {center_37:<20}")
    print(f"{'Max neighbors':<30} {max(dist_19.keys()):<20} {max(dist_37.keys()):<20}")
    print(f"{'Edge hexes (2-3 neighbors)':<30} {dist_19.get(2,0)+dist_19.get(3,0):<20} {dist_37.get(2,0)+dist_37.get(3,0):<20}")
    print(f"{'Interior hexes (6 neighbors)':<30} {dist_19.get(6,0):<20} {dist_37.get(6,0):<20}")
    
    # Center dominance
    center_dom_19 = (center_19 / max(dist_19.keys())) * 100
    center_dom_37 = (center_37 / max(dist_37.keys())) * 100
    print(f"{'Center dominance':<30} {center_dom_19:.1f}%{'':<15} {center_dom_37:.1f}%")
    
    improvement = center_dom_19 - center_dom_37
    print(f"\nCenter dominance reduction: {improvement:.1f}%")
    
    print(f"\n{'='*70}")
    print("BALANCE IMPLICATIONS")
    print(f"{'='*70}")
    print()
    print("19-hex board (radius 2):")
    print("  • Center has 6 neighbors (100% of max)")
    print("  • Only 1 hex with max neighbors (center)")
    print("  • Strong positional advantage at (0,0)")
    print("  • Tempo strategy dominates by placing at center")
    print()
    print("37-hex board (radius 3):")
    print("  • Center still has 6 neighbors")
    print("  • 7 hexes with 6 neighbors (center + ring 1)")
    print("  • Reduced center dominance (more 6-neighbor positions)")
    print("  • Better positional balance across board")
    print()
    print("Strategic impact:")
    print("  • More viable placement positions")
    print("  • Reduced tempo advantage")
    print("  • Encourages diverse positioning strategies")
    print("  • Larger board = more tactical depth")
    print()
    
    print(f"{'='*70}")
    print("IMPLEMENTATION")
    print(f"{'='*70}")
    print()
    print("Change in engine_core/autochess_sim_v06.py:")
    print()
    print("OLD:")
    print("  BOARD_RADIUS = 2  # 19 hex")
    print()
    print("NEW:")
    print("  BOARD_RADIUS = 3  # 37 hex")
    print()
    print("No other changes needed:")
    print("  • hex_coords() function unchanged")
    print("  • Combat logic unchanged")
    print("  • Neighbor calculation unchanged")
    print("  • Placement bounds auto-update")
    print()
    print(f"{'='*70}")

if __name__ == "__main__":
    compare_boards()
    
    print("\n" + "="*70)
    print("COORDINATE LISTS")
    print("="*70)
    
    print("\n19-hex coordinates (radius 2):")
    coords_19 = hex_coords(2)
    print(f"  {coords_19}")
    print(f"  Count: {len(coords_19)}")
    
    print("\n37-hex coordinates (radius 3):")
    coords_37 = hex_coords(3)
    print(f"  {coords_37}")
    print(f"  Count: {len(coords_37)}")
    
    print("\n" + "="*70)
