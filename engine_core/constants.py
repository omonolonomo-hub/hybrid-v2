"""
================================================================
|         AUTOCHESS HYBRID - Constants Module                  |
|  All game constants and configuration values                 |
================================================================

This module contains all constant values used throughout the game engine.
Extracted from autochess_sim_v06.py for better organization.
"""

from typing import Dict, List, Tuple

# ===================================================================
# STAT GROUPS & MAPPINGS
# ===================================================================

STAT_GROUPS: Dict[str, List[str]] = {
    "EXISTENCE":  ["Power", "Durability", "Size", "Speed"],
    "MIND":       ["Meaning", "Secret", "Intelligence", "Trace"],
    "CONNECTION": ["Gravity", "Harmony", "Spread", "Prestige"],
}
STAT_TO_GROUP = {s: g for g, ss in STAT_GROUPS.items() for s in ss}

# ===================================================================
# RARITY CONSTANTS
# ===================================================================

# cards.json keeps diamond rarity strings; runtime uses ASCII "1".."5".
_RARITY_DIAMOND = "\u25c6"
_LEGACY_RARITY_TO_ID: Dict[str, str] = {
    _RARITY_DIAMOND * 1: "1",
    _RARITY_DIAMOND * 2: "2",
    _RARITY_DIAMOND * 3: "3",
    _RARITY_DIAMOND * 4: "4",
    _RARITY_DIAMOND * 5: "5",
}

# ===================================================================
# GROUP ADVANTAGE SYSTEM
# ===================================================================

# Group advantage matrix: EXISTENCE beats CONNECTION (+1 combat bonus)
GROUP_BEATS = {"EXISTENCE": "CONNECTION", "MIND": "EXISTENCE", "CONNECTION": "MIND"}

# ===================================================================
# RARITY POWER TARGETS
# ===================================================================

RARITY_TAVAN = {"1": 30, "2": 36, "3": 42, "4": 48, "5": 54, "E": 72}
# Proportional evolved targets by rarity
EVOLVED_TAVAN = {
    "1": 40,   # round(30 * 72/54)
    "2": 48,   # round(36 * 72/54)
    "3": 56,   # round(42 * 72/54)
    "4": 64,   # round(48 * 72/54)
    "5": 72,   # rarity-5 unchanged
    "E": 72,   # already evolved
}
RARITY_DMG_BONUS = {}  # v0.4: removed rarity damage bonus (rare_hunter double-advantage trim)

# ===================================================================
# HEX GRID DIRECTIONS
# ===================================================================

# Hex directions in axial coords: N, NE, SE, S, SW, NW
HEX_DIRS = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]
DIR_NAME  = ["N", "NE", "SE", "S", "SW", "NW"]
OPP_DIR   = {0:3, 1:4, 2:5, 3:0, 4:1, 5:2}

# ===================================================================
# BOARD & GAME RULES
# ===================================================================

# v0.7 BOARD SIZE INCREASE: 19-hex → 37-hex
# 
# Problem: On 19-hex board (radius 2), center hex (0,0) had strong positional dominance:
#   • Only 7 hexes with 6 neighbors (36.8% of board)
#   • Center was unique optimal position
#   • Tempo strategy dominated by placing strong units at (0,0)
#
# Solution: Increased board to 37-hex (radius 3):
#   • 19 hexes with 6 neighbors (51.4% of board)
#   • Center no longer unique (ring 1 also has 6 neighbors)
#   • More viable placement positions
#   • Reduced tempo advantage
#
# Impact:
#   • Better positional balance
#   • More tactical depth (37 vs 19 positions)
#   • Encourages diverse positioning strategies
#   • Larger board = longer games, more strategic options
#
BOARD_RADIUS  = 3  # 37 hex (was 2 for 19 hex)
STARTING_HP   = 150  # v0.4: opened space for late-game strategies (100->150)
KILL_PTS      = 8
COPY_THRESH   = [4, 7]    # 2nd copy turn 4, 3rd copy turn 7
COPY_THRESH_C = [3, 6]    # when Catalyst active
BASE_INCOME   = 3         # gold per turn start
MARKET_REFRESH_COST = 2
MAX_INTEREST  = 5         # max interest gold (50 gold = +5)
INTEREST_STEP = 10        # +1 interest per 10 gold banked

# ===================================================================
# ECONOMY & COSTS
# ===================================================================
# v0.7 RARITY COST REBALANCE:
# 
# Problem: Previous costs created broken power/gold efficiency:
#   r1 = 29.00 power/gold (baseline)
#   r2 = 16.38 power/gold (0.56x)
#   r3 = 12.68 power/gold (0.44x)
#   r4 =  5.54 power/gold (0.19x) ← BROKEN
#   r5 =  4.93 power/gold (0.17x) ← BROKEN
#
# This caused rare_hunter to stall early game (couldn't afford r4/r5).
#
# Solution: Reduced r4 and r5 costs for better efficiency curve:
#   r4: 8 → 5 gold (37.5% reduction, +60% efficiency)
#   r5: 10 → 7 gold (30% reduction, +43% efficiency)
#
# New efficiency:
#   r1 = 29.00 power/gold (1.00x baseline)
#   r2 = 16.38 power/gold (0.56x)
#   r3 = 12.68 power/gold (0.44x)
#   r4 =  8.86 power/gold (0.31x) ← IMPROVED
#   r5 =  7.05 power/gold (0.24x) ← IMPROVED
#
# Impact:
#   • Rare cards accessible earlier (mid-game viable)
#   • rare_hunter no longer stalls
#   • Better cost/power balance across all rarities
#   • Shop roll odds unchanged (only costs adjusted)
#
CARD_COSTS = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0}  # E rarity costs 0 (earned via evolution)
EVOLVE_COPIES_REQUIRED = 3   # copies needed to trigger evolution
# Note: Unlimited gold economy - no gold cap enforced
HAND_LIMIT    = 6   # v0.6: hand size - 7th buy drops oldest card
PLACE_PER_TURN = 1  # v0.6: max cards placed on board per turn

# ===================================================================
# AI STRATEGIES
# ===================================================================

STRATEGIES = ["random", "warrior", "builder", "evolver", "economist", "balancer", "rare_hunter", "tempo"]
