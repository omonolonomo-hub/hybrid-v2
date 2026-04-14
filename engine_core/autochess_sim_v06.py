"""
================================================================
|         AUTOCHESS HYBRID - Simulation Engine v0.6            |
|  All core mechanics implemented. AI-driven automated play.   |
================================================================

CHANGELOG v0.6 (turn pacing + hand limit + placement cap):
  RULE 1 - Each turn a player may place only 1 card on the board.
             Cards waiting in hand are not discarded; they carry to the next turn.
  RULE 2 - Hand capacity is at most 6 cards.
             When a 7th card is bought, the oldest card in hand is removed
             and returned to the market pool.
  PERF 1  - AI max_cards buy limit lowered to 1 (aligned with RULE 1).
  FIX 1   - Version label made consistent in-file (v0.6).

CHANGELOG v0.5 (rare-hunter pressure + economist/evolver buffs + 3 bug fixes):
  BAL 1 - Rarity 4 cost 4->8, rarity 5 cost 5->10 gold; CARD_COSTS constant added
  BAL 2 - Economist: 1.5x interest bonus, gold-threshold-aware buying
  BAL 3 - Evolver: +100/+200 priority score for cards near copy thresholds
  BAL 4 - HP penalty thresholds 30/50 -> 45/75 (aligned with STARTING_HP=150)
  BUG 1 - copy_turns: use t >= instead of t == (late-acquired copies skipped strengthen)
  BUG 2 - rare_hunter: rarity-3 fallback until 8 gold (early-game stall fix)
  BUG 3 - is_eliminated: single-stat-group cards (66 cards!) eliminated too early; require min 2 stats at 0

CHANGELOG v0.4:
  BAL 1 - RARITY_DMG_BONUS removed
  BAL 2 - Combo system rewritten (card-group based)
  BAL 3 - Synergy bonus max lowered to 4
  BAL 4 - STARTING_HP 100->150

Usage:
    python autochess_sim_v06.py              -> 100 games, 4 players
    python autochess_sim_v06.py --games 500  -> 500 games
    python autochess_sim_v06.py --players 8  -> 8 players
    python autochess_sim_v06.py --verbose    -> turn-by-turn detail
"""

import argparse
from typing import Dict, List, Optional, Tuple

# Import dependencies
try:
    from .simulation import run_simulation, print_results
    from .card import get_card_pool, build_card_pool, apply_micro_buff_to_weak_cards, RARITY_TAVAN
    from .constants import KILL_PTS
    from .board import Board, resolve_single_combat, combat_phase
    from .passive_trigger import trigger_passive
except ImportError:
    from simulation import run_simulation, print_results
    from card import get_card_pool, build_card_pool, apply_micro_buff_to_weak_cards, RARITY_TAVAN
    from constants import KILL_PTS
    from board import Board, resolve_single_combat, combat_phase
    from passive_trigger import trigger_passive


# ===================================================================
# CARD POOL VALIDATION
# ===================================================================

def verify_card_pool():
    """Validate card pool stat totals vs rarity caps."""
    errors = []
    for card in get_card_pool():
        if card.rarity == "E":
            continue  # evolved cards are runtime-generated, skip
        total = card.total_power()
        cap   = RARITY_TAVAN[card.rarity]
        if total > cap:
            errors.append(f"  ERROR: {card.name} {card.rarity}: {total}/{cap}")
        if len(card.stats) != 6:
            errors.append(f"  ERROR: {card.name} must have 6 stats, has {len(card.stats)}")
    if errors:
        print("Card pool errors:")
        for e in errors:
            print(e)
    else:
        print(f"OK: {len(get_card_pool())} cards validated - no cap violations.")
    return not errors


# ===================================================================
# ENTRY POINT
# ===================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autochess Hybrid simulation")
    parser.add_argument("--games",   type=int, default=100, help="Number of games (default: 100)")
    parser.add_argument("--players", type=int, default=4,   help="Players per game (default: 4)")
    parser.add_argument("--strategies", type=str, default=None, 
                        help="Comma-separated list of strategies (e.g., 'random,warrior,builder')")
    parser.add_argument("--verbose", action="store_true",   help="Show first game turn-by-turn")
    parser.add_argument("--verify",  action="store_true",   help="Validate card pool only")
    args = parser.parse_args()
    
    strategies = args.strategies.split(",") if args.strategies else None

    print(f"\n{'='*60}")
    print("  AUTOCHESS HYBRID - Simulation Engine v0.6")
    print(f"{'='*60}\n")

    if args.verify:
        verify_card_pool()
        print()

    print(f"  Starting {args.games} games ({args.players} players, {len(get_card_pool())}-card pool)...\n")
    results = run_simulation(
        n_games=args.games,
        n_players=args.players,
        strategies=strategies,
        verbose=args.verbose,
        combat_phase_fn=combat_phase,
    )
    print_results(results)
