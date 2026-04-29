"""
Game Factory

Factory function for creating Game instances with all dependencies.

This module was extracted from run_game.py to remove circular dependencies
and enable clean imports in main.py.

RNG SEED SYNCHRONIZATION (Multiplayer Critical):
    build_game() now accepts an optional seed parameter to ensure deterministic
    behavior across multiple machines in LAN play. When seed is provided, all
    RNG operations (card dealing, market windows, swiss pairing) produce identical
    results on all clients.
    
    The generated seed is stored in game._rng_seed for network layer access.
"""

import random
import secrets
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


def build_game(strategies: list = None, seed: int | None = None):
    """Build a new Game instance with specified strategies.
    
    Creates a game with:
    - Random number generator (seeded for multiplayer determinism)
    - Card pool
    - Players with strategies
    - Game instance with all dependencies
    
    Args:
        strategies: List of strategy names for players.
                   If None, uses shuffled default strategies.
        seed: RNG seed for deterministic behavior (multiplayer sync).
              If None, generates a cryptographically secure random seed.
              The seed is stored in game._rng_seed for network distribution.
    
    Returns:
        Game instance ready to play
    
    Example:
        >>> game = build_game(["random", "warrior"], seed=42)
        >>> game._rng_seed
        42
        >>> game.turn
        0
    """
    # Generate seed if not provided (local/test compatibility)
    if seed is None:
        seed = secrets.randbits(64)
    
    pool = get_card_pool()
    
    # Note: We pass seed= directly to Game() instead of creating rng here.
    # This ensures Game._rng_seed is set correctly for multiplayer sync.
    
    if strategies is None:
        strategies = STRATEGIES[:]
        # Use temporary RNG for strategy shuffle (doesn't affect game RNG)
        temp_rng = random.Random(seed)
        temp_rng.shuffle(strategies)
    
    players = [Player(pid=i, strategy=strategies[i]) for i in range(len(strategies))]
    
    game = Game(
        players,
        verbose=False,
        seed=seed,  # FIXED: Use seed= instead of rng= for proper multiplayer sync
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=pool,
    )
    
    return game
