"""
Exception hierarchy for EngineAdapter operations.

This module defines explicit exceptions to replace silent failure patterns
(returning None) that lead to delayed AttributeErrors. All exceptions inherit
from EngineAdapterError for easy catching of adapter-related issues.
"""


class EngineAdapterError(Exception):
    """Base exception for all EngineAdapter errors.
    
    Catch this to handle any adapter-related failure. Subclasses provide
    specific error types for granular handling.
    """
    pass


class PlayerNotFoundError(EngineAdapterError):
    """Raised when a player index is invalid or player doesn't exist.
    
    Examples:
        - get_player(999) when only 4 players exist
        - get_player(-1) with negative index
        - Player list is empty or corrupted
    """
    def __init__(self, index: int, player_count: int = None):
        self.index = index
        self.player_count = player_count
        msg = f"Player at index {index} not found"
        if player_count is not None:
            msg += f" (valid range: 0-{player_count - 1})"
        super().__init__(msg)


class MarketNotAvailableError(EngineAdapterError):
    """Raised when market operations are attempted but market is unavailable.
    
    Examples:
        - Market not initialized in engine
        - Market missing required methods (get_window, etc.)
        - Market in invalid state
    """
    pass


class InvalidSlotError(EngineAdapterError):
    """Raised when a slot index is out of bounds or invalid.
    
    Examples:
        - Shop slot index >= 5
        - Hand slot index >= 6
        - Negative slot indices
    """
    def __init__(self, slot_index: int, max_slots: int, slot_type: str = "slot"):
        self.slot_index = slot_index
        self.max_slots = max_slots
        self.slot_type = slot_type
        super().__init__(
            f"Invalid {slot_type} index {slot_index} (valid range: 0-{max_slots - 1})"
        )


class InvalidCoordinateError(EngineAdapterError):
    """Raised when board coordinates are invalid or out of bounds.
    
    Examples:
        - Coordinate outside board radius
        - Malformed coordinate tuple
        - Coordinate already occupied (when placement attempted)
    """
    def __init__(self, coord, reason: str = None):
        self.coord = coord
        msg = f"Invalid coordinate {coord}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class InsufficientResourcesError(EngineAdapterError):
    """Raised when player lacks required resources (gold, etc.).
    
    Examples:
        - Attempting to buy card with insufficient gold
        - Attempting to reroll without enough gold
    """
    def __init__(self, resource: str, required: int, available: int):
        self.resource = resource
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {resource}: need {required}, have {available}"
        )


class PlayerDeadError(EngineAdapterError):
    """Raised when operations are attempted on a dead/eliminated player.
    
    Dead players cannot perform shop actions, placements, or other game actions.
    """
    def __init__(self, player_index: int):
        self.player_index = player_index
        super().__init__(f"Player {player_index} is eliminated and cannot perform actions")


class InvalidGameStateError(EngineAdapterError):
    """Raised when operation is invalid for current game state.
    
    Examples:
        - Attempting shop actions during combat phase
        - Attempting placement during wrong phase
        - Engine in corrupted state
    """
    pass


class CardDataError(EngineAdapterError):
    """Raised when card data is missing, corrupted, or invalid.
    
    Examples:
        - Card not found in database
        - Hand contains non-Card object (type violation)
        - Card missing required attributes
    """
    def __init__(self, card_identifier, reason: str = None):
        self.card_identifier = card_identifier
        msg = f"Card data error for '{card_identifier}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


# Legacy exceptions for backward compatibility
class AutochessException(Exception):
    """Base exception for autochess game errors (legacy)."""
    pass


class DatabaseError(AutochessException):
    """Raised when database operations fail (legacy).
    
    Used by CardDatabase and other data access layers.
    """
    pass


class AssetLoadError(AutochessException):
    """Raised when asset loading fails.
    
    Examples:
        - AssetLoader accessed before initialization
        - Asset file not found
        - Invalid asset format
        - Pygame loading error
    """
    pass


class EngineException(AutochessException):
    """Raised when engine operations fail (legacy).
    
    Used by game engine and related systems.
    """
    pass
