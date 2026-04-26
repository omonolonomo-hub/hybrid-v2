"""
v2/ui/hex_grid_config.py
═══════════════════════════════════════════════════════════════════════
Hex Grid Configuration — Decoupled from Engine Initialization

Replaces module-level engine queries with lazy initialization pattern.
This allows:
  • Tests to import hex_grid without full engine stack
  • Dynamic hex invalidation (e.g., "Wind card" disabling hexes per turn)
  • Dependency injection for testing
═══════════════════════════════════════════════════════════════════════
"""

from typing import FrozenSet, Tuple
from v2.core.engine_adapter import EngineAdapter


class HexGridConfig:
    """
    Encapsulates hex grid constants that were previously module-level.
    
    Usage:
        config = HexGridConfig.from_engine()
        for coord in config.valid_coords:
            ...
    """
    
    def __init__(self, board_radius: int, valid_coords: FrozenSet[Tuple[int, int]]):
        self.board_radius = board_radius
        self.valid_coords = valid_coords
    
    @classmethod
    def from_engine(cls) -> "HexGridConfig":
        """
        Lazy initialization from EngineAdapter.
        Only called when actually needed, not at import time.
        """
        constants = EngineAdapter.get_constants()
        coords = frozenset(EngineAdapter.get_hex_coords(constants.BOARD_RADIUS))
        return cls(constants.BOARD_RADIUS, coords)
    
    @classmethod
    def from_custom(cls, board_radius: int, valid_coords: FrozenSet[Tuple[int, int]]) -> "HexGridConfig":
        """
        For testing or dynamic hex invalidation.
        
        Example (Wind card):
            base_config = HexGridConfig.from_engine()
            disabled_hex = (1, 2)
            new_coords = base_config.valid_coords - {disabled_hex}
            wind_config = HexGridConfig.from_custom(base_config.board_radius, new_coords)
        """
        return cls(board_radius, valid_coords)


# Global singleton for backward compatibility
# Initialized lazily on first access
_DEFAULT_CONFIG: HexGridConfig | None = None


def get_default_config() -> HexGridConfig:
    """
    Get or create the default hex grid configuration.
    This replaces the old module-level VALID_HEX_COORDS.
    """
    global _DEFAULT_CONFIG
    if _DEFAULT_CONFIG is None:
        _DEFAULT_CONFIG = HexGridConfig.from_engine()
    return _DEFAULT_CONFIG


def reset_default_config() -> None:
    """
    Reset the default configuration singleton.
    
    This is primarily for test isolation — allows tests to run with
    different BOARD_RADIUS values in the same process without cross-contamination.
    
    Example:
        # In test teardown or setup
        reset_default_config()
        # Next call to get_default_config() will re-initialize from engine
    """
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = None
