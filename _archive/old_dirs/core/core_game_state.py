"""
Core Game State

SAVEABLE state that persists across scenes and can be saved/loaded.

CRITICAL RULE: Only domain state here, NO UI state.
This state represents the actual game logic and can be serialized.
"""

from typing import Optional, Dict, Any, Set, Tuple


class CoreGameState:
    """SAVEABLE - persists across scenes, can be saved/loaded.
    
    This class contains ONLY domain state:
    - Game instance (players, market, turn, etc.)
    - Which player we're viewing
    - Game speed settings
    
    NO UI state (selections, hovers, animations) should be here.
    """
    
    def __init__(self, game: 'Game'):
        """Initialize with game instance.
        
        Args:
            game: The Game instance containing players, market, etc.
        """
        self.game: 'Game' = game
        self.view_player_index: int = 0  # Which player we're viewing (0-7)
        self.fast_mode: bool = False  # Game speed setting
        # Locked coordinates per player (cards placed this turn, immutable until turn end)
        self.locked_coords_per_player: Dict[int, Set[Tuple[int, int]]] = {
            p.pid: set() for p in game.players
        }
    
    @property
    def current_player(self) -> 'Player':
        """Get currently viewed player.
        
        Returns:
            Player instance being viewed
        """
        return self.game.players[self.view_player_index]
    
    @property
    def turn(self) -> int:
        """Get current turn number.
        
        Returns:
            Current turn number
        """
        return self.game.turn
    
    @property
    def alive_players(self) -> list:
        """Get list of alive players.
        
        Returns:
            List of alive Player instances
        """
        return self.game.alive_players()
    
    def switch_player(self, direction: int = 1) -> None:
        """Switch to next/previous player.
        
        Args:
            direction: 1 for next, -1 for previous
        """
        num_players = len(self.game.players)
        self.view_player_index = (self.view_player_index + direction) % num_players
    
    def clear_locked_coords(self, player_id: int) -> None:
        """Clear locked coordinates for a player (called at turn start).
        
        Args:
            player_id: Player ID whose locked coordinates to clear
        """
        if player_id in self.locked_coords_per_player:
            self.locked_coords_per_player[player_id].clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for saving.
        
        This method should serialize all SAVEABLE state.
        Game instance serialization would need to be implemented separately.
        
        Returns:
            Dictionary containing serializable state
        """
        return {
            "view_player_index": self.view_player_index,
            "fast_mode": self.fast_mode,
            "locked_coords_per_player": {
                pid: list(coords) for pid, coords in self.locked_coords_per_player.items()
            },
            # Note: Game serialization would go here
            # "game": self.game.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], game: 'Game') -> 'CoreGameState':
        """Deserialize from dictionary for loading.
        
        Args:
            data: Dictionary containing serialized state
            game: Game instance (reconstructed separately)
        
        Returns:
            CoreGameState instance
        """
        state = cls(game)
        state.view_player_index = data.get("view_player_index", 0)
        state.fast_mode = data.get("fast_mode", False)
        
        # Restore locked coordinates
        locked_coords_data = data.get("locked_coords_per_player", {})
        state.locked_coords_per_player = {
            int(pid): set(tuple(coord) for coord in coords)
            for pid, coords in locked_coords_data.items()
        }
        
        return state
