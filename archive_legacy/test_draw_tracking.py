#!/usr/bin/env python3
"""Quick test for draw tracking implementation."""

import sys
sys.path.insert(0, 'engine_core')

from autochess_sim_v06 import run_simulation, print_results

print("Testing draw tracking with 10 games...\n")
results = run_simulation(n_games=10, n_players=4, verbose=False, seed=42)
print_results(results)

print("\n✓ Draw tracking test completed successfully!")
