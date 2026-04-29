"""ServerOrchestrator — manages turn flow and action submission for multiplayer games.

This module provides server-side orchestration of game turns without any network code.
It wraps a GameSession and handles action submission, turn advancement, and state
snapshot distribution.

DESIGN RATIONALE:
- Zero network code: Pure turn orchestration, transport-agnostic
- Outbox pattern: Snapshots queued for network layer to poll
- Mutation safety: All actions go through dispatcher
- Eliminated player handling: Rejects actions from dead players
- Input validation: All action parameters validated before dispatch
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

from engine_core.constants import HAND_LIMIT
from engine_core.game_session import GameSession
from v2.core.action_result import ActionResult

if TYPE_CHECKING:
    from v2.core.game_state import GameState

logger = logging.getLogger(__name__)

# Market window size (slots 0-4)
MARKET_WINDOW_SIZE = 5


class ServerOrchestrator:
    """Orchestrates turn flow for a multiplayer game session.
    
    ServerOrchestrator wraps a GameSession and provides:
    - Action submission with validation
    - Turn advancement when all players ready
    - State snapshot generation and distribution
    
    The orchestrator maintains an outbox of serialized PublicState snapshots
    that the network layer can poll and distribute to clients.
    
    Attributes:
        session: GameSession being orchestrated
        _outbox: Dict mapping pid → serialized PublicState snapshot
        _state_builder: Optional GameState instance for building snapshots
    
    Usage:
        orchestrator = ServerOrchestrator(session)
        
        # Players submit actions
        result = orchestrator.submit_action(0, {"type": "buy", "slot": 2})
        result = orchestrator.submit_action(1, {"type": "end_turn"})
        
        # When last player ends turn, _advance_turn() triggers automatically
        # and snapshots are queued in outbox
        
        # Network layer polls for snapshots
        snapshots = orchestrator.pop_outbox()
        for pid, snapshot_dict in snapshots.items():
            send_to_client(pid, snapshot_dict)
    
    Thread-safety: Not thread-safe (same as Game and GameSession)
    """

    def __init__(self, session: GameSession, state_builder: Optional["GameState"] = None):
        """Initialize orchestrator with a game session.
        
        Args:
            session: GameSession to orchestrate
            state_builder: Optional GameState instance for building PublicState snapshots.
                          If None, snapshots will be minimal dicts with basic game state.
        """
        self._session = session
        self._state_builder = state_builder
        self._outbox: Dict[int, Dict[str, Any]] = {}

    @property
    def session(self) -> GameSession:
        """Access to underlying GameSession."""
        return self._session

    def submit_action(self, pid: int, action: Dict[str, Any]) -> ActionResult:
        """Submit an action from a player.
        
        Validates the action, executes it through the dispatcher, and handles
        turn advancement when all players are ready.
        
        Args:
            pid: Player ID submitting the action
            action: Action dict with structure:
                {"type": "buy", "slot": int, "seq": int}
                {"type": "reroll", "seq": int}
                {"type": "place", "hand_index": int, "coord": [q, r], "rotation": int, "seq": int}
                {"type": "end_turn", "seq": int}
                
                The "seq" field is optional but recommended for replay attack protection.
                If provided, it must be a strictly increasing integer per player.
        
        Returns:
            ActionResult enum indicating success or failure reason
            
        Side effects:
            - On "end_turn": marks player ready, may trigger _advance_turn()
            - On _advance_turn(): generates snapshots and queues in outbox
        """
        # Check if player exists in session
        if pid not in self._session.players:
            logger.warning("submit_action: pid=%s not found in session", pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        # Check if player is alive
        player = self._session.players[pid]
        if not getattr(player, "alive", True):
            logger.info("submit_action: pid=%s is eliminated, rejecting action", pid)
            return ActionResult.ERR_NOT_IN_PREP_PHASE
        
        action_type = action.get("type")
        
        # Extract optional sequence number for replay protection
        seq_no = action.get("seq")
        if seq_no is not None and (isinstance(seq_no, bool) or not isinstance(seq_no, int)):
            logger.warning("submit_action: seq must be integer, got %s from pid=%s", type(seq_no).__name__, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        if action_type == "buy":
            return self._handle_buy(pid, action)
        elif action_type == "reroll":
            return self._handle_reroll(pid)
        elif action_type == "place":
            return self._handle_place(pid, action)
        elif action_type == "end_turn":
            return self._handle_end_turn(pid, seq_no=seq_no)
        else:
            logger.warning("submit_action: unknown action_type=%s from pid=%s", action_type, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION

    def _handle_buy(self, pid: int, action: Dict[str, Any]) -> ActionResult:
        """Handle buy action with slot range validation."""
        slot = action.get("slot")
        
        # SECURITY: Validate slot is integer and within valid range
        # Invalid slots could cause IndexError or undefined behavior
        # Note: Explicitly reject bool (which is int subclass in Python)
        if isinstance(slot, bool) or not isinstance(slot, int):
            logger.warning("_handle_buy: slot must be integer, got %s from pid=%s", type(slot).__name__, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        if not (0 <= slot < MARKET_WINDOW_SIZE):
            logger.warning("_handle_buy: slot out of range (got %s, valid 0-%d) from pid=%s", 
                          slot, MARKET_WINDOW_SIZE - 1, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        dispatcher = self._session.dispatcher
        if dispatcher is None:
            logger.error("_handle_buy: no dispatcher available")
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        # Find player index from pid
        player_index = self._get_player_index(pid)
        if player_index is None:
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        return dispatcher.perform_buy_card(player_index, slot)

    def _handle_reroll(self, pid: int) -> ActionResult:
        """Handle reroll action."""
        dispatcher = self._session.dispatcher
        if dispatcher is None:
            logger.error("_handle_reroll: no dispatcher available")
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        player_index = self._get_player_index(pid)
        if player_index is None:
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        # Normalize bool result to ActionResult
        success = dispatcher.perform_reroll(player_index)
        return ActionResult.OK if success else ActionResult.ERR_INSUFFICIENT_GOLD

    def _handle_place(self, pid: int, action: Dict[str, Any]) -> ActionResult:
        """Handle place action.
        
        Converts coord from list to tuple (serialization layer sends lists).
        """
        hand_index = action.get("hand_index")
        coord = action.get("coord")
        rotation = action.get("rotation")
        
        # Validate parameters
        if hand_index is None or not isinstance(hand_index, int):
            logger.warning("_handle_place: invalid hand_index=%s from pid=%s", hand_index, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        if not (0 <= hand_index < HAND_LIMIT):
            logger.warning("_handle_place: hand_index out of range (got %s, valid 0-%d) from pid=%s",
                          hand_index, HAND_LIMIT - 1, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        if coord is None or not isinstance(coord, (list, tuple)) or len(coord) != 2:
            logger.warning("_handle_place: invalid coord=%s from pid=%s", coord, pid)
            return ActionResult.ERR_INVALID_COORD
        
        if rotation is None or not isinstance(rotation, int):
            logger.warning("_handle_place: invalid rotation=%s from pid=%s", rotation, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        if not (0 <= rotation <= 5):
            logger.warning("_handle_place: rotation out of range (got %s, valid 0-5) from pid=%s",
                          rotation, pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        # Convert coord list to tuple (serialization sends lists)
        coord_tuple = tuple(coord)
        
        dispatcher = self._session.dispatcher
        if dispatcher is None:
            logger.error("_handle_place: no dispatcher available")
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        player_index = self._get_player_index(pid)
        if player_index is None:
            return ActionResult.ERR_ENGINE_EXCEPTION
        
        return dispatcher.perform_placement(player_index, hand_index, coord_tuple, rotation)

    def _handle_end_turn(self, pid: int, seq_no: Optional[int] = None) -> ActionResult:
        """Handle end_turn action.
        
        Marks player ready and triggers turn advancement if all players ready.
        
        Args:
            pid: Player ID ending turn
            seq_no: Optional sequence number for replay attack protection
        
        Returns:
            ActionResult indicating success or failure
        """
        try:
            all_ready = self._session.mark_ready(pid, seq_no=seq_no)
            
            if all_ready:
                logger.info("All players ready, advancing turn")
                self._advance_turn()
            
            return ActionResult.OK
        except KeyError:
            logger.error("_handle_end_turn: pid=%s not found in session", pid)
            return ActionResult.ERR_ENGINE_EXCEPTION
        except ValueError as e:
            # Replay attack detected
            logger.warning("_handle_end_turn: replay attack from pid=%s: %s", pid, e)
            return ActionResult.ERR_ENGINE_EXCEPTION

    def _advance_turn(self) -> None:
        """Advance the game to the next turn.
        
        Executes turn progression sequence:
        1. Finish current turn (commit boards, etc.)
        2. Run combat phase
        3. Start next turn (deal gold, refresh shops, etc.)
        4. Generate and queue state snapshots for all alive players
        
        This is a private method called automatically when all players are ready.
        """
        game = self._session.game
        
        # Turn progression sequence - wrap in try/except to prevent crashes
        try:
            if hasattr(game, "finish_turn"):
                game.finish_turn()
            
            if hasattr(game, "combat_phase"):
                game.combat_phase()
            
            if hasattr(game, "start_turn"):
                game.start_turn()
            
            # Generate snapshots for all alive players
            self._generate_snapshots()
        
        except Exception:
            logger.exception("_advance_turn failed - snapshots not generated")
            # Don't re-raise - allow game to continue even if turn advancement fails

    def _generate_snapshots(self) -> None:
        """Generate PublicState snapshots for all alive players and queue in outbox.
        
        If state_builder is provided, uses it to generate full PublicState snapshots.
        Otherwise, generates minimal state dicts with basic game information.
        """
        game = self._session.game
        
        for player in game.players:
            if not getattr(player, "alive", True):
                continue
            
            # Find player index
            player_index = self._get_player_index(player.pid)
            if player_index is None:
                logger.warning("_generate_snapshots: could not find index for pid=%s", player.pid)
                continue
            
            # Build snapshot
            try:
                if self._state_builder is not None:
                    # Use GameState to build full PublicState
                    from v2.core.serialization import to_dict
                    
                    # Set view_index to this player
                    original_view_index = self._state_builder.view_index
                    self._state_builder.view_index = player_index
                    
                    # Get PublicState and serialize
                    public_state = self._state_builder.get_public_state()
                    snapshot_dict = to_dict(public_state)
                    
                    # Restore original view_index
                    self._state_builder.view_index = original_view_index
                else:
                    # Generate minimal snapshot without full UI stack
                    snapshot_dict = self._build_minimal_snapshot(player_index)
                
                # Queue in outbox
                self._outbox[player.pid] = snapshot_dict
                
                logger.debug("Generated snapshot for pid=%s", player.pid)
            except Exception:
                logger.exception("Failed to generate snapshot for pid=%s", player.pid)

    def _build_minimal_snapshot(self, player_index: int) -> Dict[str, Any]:
        """Build a minimal state snapshot without full UI dependencies.
        
        This is used when no GameState builder is provided. Returns a basic
        dict with essential game state that can be used for testing or simple
        network protocols.
        """
        game = self._session.game
        player = game.players[player_index]
        
        return {
            "turn": getattr(game, "turn", 0),
            "pid": getattr(player, "pid", player_index),
            "hp": getattr(player, "hp", 0),
            "gold": getattr(player, "gold", 0),
            "alive": getattr(player, "alive", True),
            "alive_pids": [p.pid for p in game.players if getattr(p, "alive", True)],
        }

    def pop_outbox(self) -> Dict[int, Dict[str, Any]]:
        """Pop all queued snapshots from the outbox.
        
        The network layer should poll this method to retrieve snapshots
        and distribute them to clients.
        
        Returns:
            Dict mapping pid → serialized PublicState snapshot
            Empty dict if no snapshots queued
            
        Side effects:
            Clears the outbox after returning
        """
        snapshots = dict(self._outbox)
        self._outbox.clear()
        return snapshots

    def _get_player_index(self, pid: int) -> Optional[int]:
        """Get player index from pid.
        
        Args:
            pid: Player ID
            
        Returns:
            Player index (0-based) or None if not found
        """
        for idx, player in enumerate(self._session.game.players):
            if player.pid == pid:
                return idx
        return None
