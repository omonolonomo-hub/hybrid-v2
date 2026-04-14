"""
engine_core — Autochess Hybrid Game Engine

Public API:
    Card, build_card_pool  — card data model and pool factory
    Board                  — hex grid board state
    Player                 — player state and economy
    Market                 — card market and offerings
    Game                   — single game orchestration
    run_simulation         — multi-game simulation runner
    combat_phase           — default combat resolution function
    StrategyLogger         — parametre bazlı strategy analytics logger
    init_strategy_logger   — global logger factory
    get_strategy_logger    — global logger accessor
"""

try:
    from .card import Card, build_card_pool
    from .board import Board, combat_phase
    from .player import Player
    from .market import Market
    from .game import Game
    from .simulation import run_simulation
    from .strategy_logger import StrategyLogger, init_strategy_logger, get_strategy_logger
except ImportError as e:
    raise ImportError(
        f"engine_core failed to load: {e}\n"
        f"Ensure all modules are present in the engine_core/ directory."
    ) from e

__all__ = [
    "Card",
    "build_card_pool",
    "Board",
    "Player",
    "Market",
    "Game",
    "run_simulation",
    "combat_phase",
    "StrategyLogger",
    "init_strategy_logger",
    "get_strategy_logger",
]

__version__ = "0.7.0"
