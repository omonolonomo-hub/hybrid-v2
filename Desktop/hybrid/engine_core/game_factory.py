"""
Game Factory

Factory function for creating Game instances with all dependencies.

This module was extracted from run_game.py to remove circular dependencies
and enable clean imports in main.py.
"""

import random
from engine_core.player import Player
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.board import combat_phase
from engine_core.card import get_card_pool

# Default strategies (can be overridden)
STRATEGIES = [
    "random",
    "warrior",
    "builder",
    "defender",
    "economist",
    "synergist",
    "adaptive",
    "aggressive"
]


def build_game(strategies: list = None):
    """Build a new Game instance with specified strategies.
    
    Creates a game with:
    - Random number generator
    - Card pool
    - Players with strategies
    - Game instance with all dependencies
    
    Args:
        strategies: List of strategy names for players.
                   If None, uses shuffled default strategies.
    
    Returns:
        Game instance ready to play
    
    Example:
        >>> game = build_game(["random", "warrior"])
        >>> game.turn
        0
    """
    rng = random.Random()
    pool = get_card_pool()
    
    if strategies is None:
        strategies = STRATEGIES[:]
        rng.shuffle(strategies)
    
    players = [Player(pid=i, strategy=strategies[i]) for i in range(len(strategies))]
    
    game = Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=pool,
    )
    
    return game
