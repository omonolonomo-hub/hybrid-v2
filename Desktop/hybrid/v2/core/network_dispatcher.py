"""NetworkCommandDispatcher — client-side dispatcher that routes commands over WebSocket to server.

This implementation provides a network-based command dispatcher that sends actions
to a remote game server via WebSocket and waits for results. It implements the same
ICommandDispatcher interface as LocalCommandDispatcher but executes commands remotely.

DESIGN RATIONALE:
- Single responsibility: Only serializes and transmits commands
- Network-transparent: Same interface as LocalCommandDispatcher
- Async-to-sync bridge: Uses asyncio.get_event_loop().run_until_complete()
- Type-safe: Enforces ICommandDispatcher contract
- Error handling: Maps network errors to ActionResult.ERR_ENGINE_EXCEPTION

THREADING MODEL:
- Synchronous API: All methods are sync (matches ICommandDispatcher)
- Async implementation: Uses asyncio internally via NetworkClient
- Event loop: Uses asyncio.get_event_loop().run_until_complete() for sync wrapper
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Tuple

from engine_core.command_dispatcher import ICommandDispatcher
from v2.core.action_result import ActionResult

if TYPE_CHECKING:
    from engine_core.network_client import NetworkClient

logger = logging.getLogger(__name__)


class NetworkCommandDispatcher(ICommandDispatcher):
    """Client-side dispatcher — routes commands over WebSocket to server.
    
    This class implements ICommandDispatcher by serializing commands and sending
    them to a remote game server via NetworkClient. It provides the same interface
    as LocalCommandDispatcher but executes commands over the network.
    
    Usage:
        client = NetworkClient(pid=0)
        await client.connect()
        dispatcher = NetworkCommandDispatcher(client, loop=client.loop)
        result = dispatcher.perform_buy_card(0, 2)
    
    Thread-safety: Not thread-safe (same as NetworkClient)
    Network: All commands are sent over WebSocket
    """

    def __init__(self, client: "NetworkClient", loop=None):
        """Initialize dispatcher with a NetworkClient instance.
        
        Args:
            client: NetworkClient instance to send commands through
            loop: Event loop running the NetworkClient's async operations.
                  The loop parameter should be the event loop running the NetworkClient's
                  async operations — prevents RuntimeError when called from a context with
                  an already-running event loop.
        """
        self._client = client
        self._loop = loop or asyncio.get_event_loop()

    def perform_buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        """Send buy_card action to server and wait for result.
        
        Args:
            player_index: Player performing the purchase (0 = human)
            slot_index: Shop slot index (0-4)
            
        Returns:
            ActionResult.OK if successful, ActionResult.ERR_ENGINE_EXCEPTION on error
        """
        try:
            action = {
                "type": "buy",
                "slot": slot_index
            }
            fut = asyncio.run_coroutine_threadsafe(self._client.send_action(action), self._loop)
            result = fut.result(timeout=5.0)
            
            if result["ok"]:
                logger.debug("Buy card succeeded: player=%s, slot=%s", player_index, slot_index)
                return ActionResult.OK
            else:
                logger.warning("Buy card failed: player=%s, slot=%s, error=%s", 
                             player_index, slot_index, result.get("error"))
                return ActionResult.ERR_ENGINE_EXCEPTION
        
        except Exception:
            logger.exception("Network error during buy_card: player=%s, slot=%s", 
                           player_index, slot_index)
            return ActionResult.ERR_ENGINE_EXCEPTION

    def perform_reroll(self, player_index: int) -> bool:
        """Send reroll action to server and wait for result.
        
        Args:
            player_index: Player performing the reroll (0 = human)
            
        Returns:
            True if reroll succeeded, False on error
        """
        try:
            action = {
                "type": "reroll"
            }
            fut = asyncio.run_coroutine_threadsafe(self._client.send_action(action), self._loop)
            result = fut.result(timeout=5.0)
            
            if result["ok"]:
                logger.debug("Reroll succeeded: player=%s", player_index)
                return True
            else:
                logger.warning("Reroll failed: player=%s, error=%s", 
                             player_index, result.get("error"))
                return False
        
        except Exception:
            logger.exception("Network error during reroll: player=%s", player_index)
            return False

    def perform_placement(
        self, 
        player_index: int, 
        hand_index: int, 
        coord: Tuple[int, int], 
        rotation: int
    ) -> ActionResult:
        """Send placement action to server and wait for result.
        
        Args:
            player_index: Player performing the placement (0 = human)
            hand_index: Hand slot index (0-5)
            coord: Board coordinate tuple (q, r)
            rotation: Card rotation (0-5)
            
        Returns:
            ActionResult.OK if successful, ActionResult.ERR_ENGINE_EXCEPTION on error
        """
        try:
            action = {
                "type": "place",
                "hand_index": hand_index,
                "coord": list(coord),  # Convert tuple to list for JSON serialization
                "rotation": rotation
            }
            fut = asyncio.run_coroutine_threadsafe(self._client.send_action(action), self._loop)
            result = fut.result(timeout=5.0)
            
            if result["ok"]:
                logger.debug("Placement succeeded: player=%s, hand=%s, coord=%s, rot=%s", 
                           player_index, hand_index, coord, rotation)
                return ActionResult.OK
            else:
                logger.warning("Placement failed: player=%s, hand=%s, coord=%s, rot=%s, error=%s", 
                             player_index, hand_index, coord, rotation, result.get("error"))
                return ActionResult.ERR_ENGINE_EXCEPTION
        
        except Exception:
            logger.exception("Network error during placement: player=%s, hand=%s, coord=%s, rot=%s", 
                           player_index, hand_index, coord, rotation)
            return ActionResult.ERR_ENGINE_EXCEPTION
