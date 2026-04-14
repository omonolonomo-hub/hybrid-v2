#!/usr/bin/env python3
"""
Final verification test for passive-efficiency-kpi-logging spec
Run 100 games to verify complete integration
"""

import sys
import os

# Modify N_GAMES to 100 for final test
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Import and modify sim1000 module
import sim1000

# Override N_GAMES
sim1000.N_GAMES = 100

if __name__ == "__main__":
    sim1000.main()
