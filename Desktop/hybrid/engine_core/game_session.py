"""GameSession — manages game state and player readiness for turn progression.

This module provides a session container that wraps a Game instance and tracks
which players are ready to proceed to the next phase. Designed for both local
and networked gameplay without containing any network code itself.

DESIGN RATIONALE:
- Separation of concerns: Game logic vs session management
- Network-ready: Ready tracking enables async multiplayer
- Zero network code: Pure state management, transport-agnostic
- Type-safe: Explicit player mapping and dispatcher interface
"""

from typing import Dict, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine_core.game import Game
    from engine_core.player import Player
    from engine_core.command_dispatcher import ICommandDispatcher


class GameSession:
    """Manages a game instance with player readiness tracking.
    
    GameSession wraps a Game instance and provides turn synchronization
    through ready state tracking. When all alive players mark themselves
    ready, the session signals that the turn can progress.
    
    Attributes:
        game: The Game instance being managed
        players: Mapping of pid → Player for fast lookup
        dispatcher: Command dispatcher for mutations (local or network)
        _ready_players: Set of pids that have marked ready for current turn
    
    Usage (local game):
        session = GameSession(game, dispatcher)
        session.mark_ready(0)  # Human player ready
        session.mark_ready(1)  # AI player ready
        if session.mark_ready(2):  # Last player ready
            # All players ready, proceed to next phase
            game.combat_phase()
    
    Usage (network game):
        # Server receives ready message from client
        if session.mark_ready(client_pid):
            # Broadcast to all clients: turn is progressing
            broadcast_turn_start()
    
    Thread-safety: Not thread-safe (same as Game)
    """

    def __init__(
        self,
        game: "Game",
        dispatcher: Optional["ICommandDispatcher"] = None
    ):
        """Initialize session with a game instance and optional dispatcher.
        
        Args:
            game: Game instance to manage
            dispatcher: Command dispatcher for mutations (optional)
        """
        self._game = game
        self._dispatcher = dispatcher
        
        # Build player mapping for O(1) lookup
        self._players: Dict[int, "Player"] = {
            player.pid: player for player in game.players
        }
        
        # Track which players have marked ready for current turn
        self._ready_players: Set[int] = set()
        
        # SECURITY: Track last seen sequence number per player to prevent replay attacks
        # Each player's actions must have monotonically increasing sequence numbers
        self._last_seq: Dict[int, int] = {player.pid: -1 for player in game.players}

    @property
    def game(self) -> "Game":
        """Access to underlying Game instance."""
        return self._game

    @property
    def dispatcher(self) -> Optional["ICommandDispatcher"]:
        """Access to command dispatcher."""
        return self._dispatcher

    @property
    def players(self) -> Dict[int, "Player"]:
        """Mapping of pid → Player for fast lookup."""
        return self._players

    def mark_ready(self, pid: int, seq_no: Optional[int] = None) -> bool:
        """Mark a player as ready and check if all alive players are ready.
        
        When a player marks ready, their pid is added to the ready set.
        If all alive players are now ready, the ready set is cleared and
        True is returned to signal that the turn can progress.
        
        Args:
            pid: Player ID marking ready
            seq_no: Optional sequence number for replay attack protection.
                   If provided, must be greater than last seen seq_no for this player.
            
        Returns:
            True if all alive players are now ready (turn can progress)
            False if still waiting for other players
            
        Raises:
            KeyError: If pid is not in the player mapping
            ValueError: If seq_no is provided but not greater than last seen (replay attack)
            
        Example:
            # Three-player game
            session.mark_ready(0)  # Returns False (waiting for others)
            session.mark_ready(1)  # Returns False (waiting for player 2)
            session.mark_ready(2)  # Returns True (all ready, proceed)
            # Ready set is now empty, ready for next turn
            
            # With sequence numbers (replay protection)
            session.mark_ready(0, seq_no=1)  # OK
            session.mark_ready(0, seq_no=1)  # Raises ValueError (duplicate)
            session.mark_ready(0, seq_no=2)  # OK
        """
        if pid not in self._players:
            raise KeyError(f"Player {pid} not found in session")
        
        # SECURITY: Replay attack protection
        # If seq_no is provided, verify it's greater than last seen
        if seq_no is not None:
            last_seq = self._last_seq.get(pid, -1)
            if seq_no <= last_seq:
                raise ValueError(
                    f"Replay attack detected: pid={pid} sent seq_no={seq_no} "
                    f"but last_seq={last_seq}. Sequence numbers must be strictly increasing."
                )
            # Update last seen sequence number
            self._last_seq[pid] = seq_no
        
        # Add player to ready set
        self._ready_players.add(pid)
        
        # Get all alive player pids
        alive_pids = {
            p.pid for p in self._game.players
            if getattr(p, "alive", True)
        }
        
        # Check if all alive players are ready
        if self._ready_players >= alive_pids:
            # All alive players ready - clear set and signal progression
            self._ready_players.clear()
            return True
        
        # Still waiting for other players
        return False

    def get_ready_players(self) -> Set[int]:
        """Get set of player IDs that have marked ready.
        
        Returns:
            Copy of ready player set (modifications won't affect session)
        """
        return set(self._ready_players)

    def reset_ready_state(self) -> None:
        """Clear all ready markers.
        
        Useful for manual turn reset or error recovery.
        """
        self._ready_players.clear()

    def is_player_ready(self, pid: int) -> bool:
        """Check if a specific player has marked ready.
        
        Args:
            pid: Player ID to check
            
        Returns:
            True if player has marked ready, False otherwise
        """
        return pid in self._ready_players

    def get_alive_count(self) -> int:
        """Get count of alive players.
        
        Returns:
            Number of players with alive=True
        """
        return sum(
            1 for p in self._game.players
            if getattr(p, "alive", True)
        )

    def get_waiting_players(self) -> Set[int]:
        """Get set of alive player IDs that haven't marked ready yet.
        
        Returns:
            Set of pids that are alive but not ready
        """
        alive_pids = {
            p.pid for p in self._game.players
            if getattr(p, "alive", True)
        }
        return alive_pids - self._ready_players

    def get_last_seq(self, pid: int) -> int:
        """Get the last seen sequence number for a player.
        
        Args:
            pid: Player ID
            
        Returns:
            Last seen sequence number, or -1 if no sequences seen yet
            
        Raises:
            KeyError: If pid is not in the player mapping
        """
        if pid not in self._players:
            raise KeyError(f"Player {pid} not found in session")
        return self._last_seq.get(pid, -1)
