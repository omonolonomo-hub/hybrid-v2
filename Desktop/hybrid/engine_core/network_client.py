"""NetworkClient — WebSocket client for connecting to multiplayer games.

This module provides a client-side network layer for connecting to a NetworkServer
and participating in multiplayer games. It handles connection management, action
submission, and state synchronization.

DESIGN RATIONALE:
- Zero game logic: Pure network transport
- Async-first: Built on asyncio + websockets
- Callback-based: State updates delivered via callback
- Resilient: Connection errors propagated cleanly
- Single-reader pattern: One task reads from WebSocket, dispatches to queues
  (prevents race condition between send_action and listen)

THREADING MODEL:
- Single reader task: Reads all messages from WebSocket
- Message dispatch: Routes messages to appropriate queues by type
- send_action: Waits on action_result_queue
- listen: Consumes from snapshot_queue
- No race conditions: Only one task calls websocket.recv()

Protocol:
    Client → Server:
        {"type": "join", "pid": int}
        {"type": "action", "action": {...}}
    
    Server → Client:
        {"type": "snapshot", "state": {...}}  # PublicState dict
        {"type": "action_result", "ok": bool, "error": str|null}

Dependencies:
    pip install websockets
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any

try:
    import websockets
    from websockets.asyncio.client import ClientConnection
except ImportError:
    raise ImportError(
        "websockets library required. Install with: pip install websockets"
    )

from engine_core.packet_factory import PacketFactory
from v2.core.serialization import from_dict
from v2.core.public_state import PublicState

logger = logging.getLogger(__name__)


class NetworkClient:
    """WebSocket client for multiplayer game sessions.
    
    NetworkClient connects to a NetworkServer and provides methods for
    submitting actions and receiving state updates. State snapshots are
    delivered via a callback function.
    
    Attributes:
        pid: Player ID for this client
        uri: WebSocket server URI (e.g., "ws://localhost:8765")
        state: Current PublicState (updated when snapshots arrive)
        _websocket: WebSocket connection (when connected)
        _connected: Connection status flag
    
    Usage:
        client = NetworkClient(pid=0)
        await client.connect()
        
        # Send action
        result = await client.send_action({"type": "end_turn"})
        if result["ok"]:
            print("Action succeeded")
        
        # Listen for state updates
        def on_state_update(state: PublicState):
            print(f"Turn {state.turn}, HP: {state.active_player.hud.hp}")
        
        await client.listen(on_state_update)  # Blocks until disconnect
        
        await client.disconnect()
    
    Thread-safety: Not thread-safe (use within single asyncio event loop)
    """

    def __init__(self, pid: int, uri: str = "ws://localhost:8765", use_seq: bool = True):
        """Initialize network client.
        
        Args:
            pid: Player ID for this client
            uri: WebSocket server URI (default: ws://localhost:8765)
            use_seq: Enable sequence number replay attack protection (default: True)
        """
        self._pid = pid
        self._uri = uri
        self._websocket: Optional[ClientConnection] = None
        self._connected = False
        self.state: Optional[PublicState | Dict[str, Any]] = None  # Can be PublicState or minimal dict
        self.seed: Optional[int] = None  # RNG seed received from server (multiplayer sync)
        
        # Single-reader pattern: queues for message dispatch
        self._action_result_queue: asyncio.Queue = asyncio.Queue()
        self._snapshot_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        
        # SECURITY: Sequence number for replay attack protection
        self._use_seq = use_seq
        self._seq = 0

    @property
    def pid(self) -> int:
        """Player ID for this client."""
        return self._pid

    @property
    def connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected

    async def connect_with_retry(self, max_attempts: int = 3, delay: float = 1.0) -> None:
        """Connect to server with automatic retry on failure.
        
        Attempts to connect up to max_attempts times with exponential backoff.
        Useful in LAN environments where brief network interruptions are common.
        
        Args:
            max_attempts: Maximum number of connection attempts (default: 3)
            delay: Base delay in seconds between attempts (default: 1.0)
                   Actual delay increases exponentially: delay * (attempt + 1)
        
        Raises:
            ConnectionError: If all connection attempts fail
            TimeoutError: If initial packets not received within timeout
        
        Example:
            client = NetworkClient(pid=0)
            await client.connect_with_retry(max_attempts=5, delay=2.0)
        """
        for attempt in range(max_attempts):
            try:
                await self.connect()
                logger.info("Connected successfully on attempt %d: pid=%s", attempt + 1, self._pid)
                return
            except (ConnectionError, TimeoutError) as e:
                if attempt == max_attempts - 1:
                    logger.error("All connection attempts failed: pid=%s", self._pid)
                    raise
                wait_time = delay * (attempt + 1)
                logger.warning(
                    "Connection attempt %d/%d failed: %s. Retrying in %.1fs... pid=%s",
                    attempt + 1, max_attempts, e, wait_time, self._pid
                )
                await asyncio.sleep(wait_time)

    async def connect(self) -> None:
        """Connect to server and receive initial state snapshot.
        
        Protocol (new):
            1. Send join
            2. Receive game_start (seed may be null for local games)
            3. Receive snapshot
        
        Protocol (legacy fallback):
            1. Send join
            2. Receive snapshot directly (no game_start)
        
        After connection, starts a background reader task that dispatches
        messages to appropriate queues (single-reader pattern).
        
        For automatic retry on connection failure, use connect_with_retry() instead.
        
        Raises:
            ConnectionError: If connection fails
            TimeoutError: If initial packets not received within timeout
        """
        try:
            self._websocket = await websockets.connect(self._uri)
            self._connected = True
            logger.info("Connected to server: pid=%s", self._pid)
            
            # Send join message
            await self._websocket.send(PacketFactory.make_join(self._pid))
            logger.debug("Sent join message: pid=%s", self._pid)
            
            # Wait for first packet (game_start OR snapshot for legacy servers)
            msg = await asyncio.wait_for(self._websocket.recv(), timeout=5.0)
            data = json.loads(msg)
            
            if data.get("type") == "game_start":
                # New protocol: game_start then snapshot
                self.seed = data.get("seed")  # May be None for local games
                logger.info("Received game_start seed=%s: pid=%s", self.seed, self._pid)
                
                # Now wait for snapshot
                msg = await asyncio.wait_for(self._websocket.recv(), timeout=5.0)
                data = json.loads(msg)
                if data.get("type") == "snapshot":
                    self._handle_snapshot(data["state"])
                    logger.info("Received initial snapshot: pid=%s", self._pid)
                else:
                    logger.warning("Expected snapshot after game_start, got: %s", data.get("type"))
            
            elif data.get("type") == "snapshot":
                # Legacy fallback: snapshot without game_start
                logger.warning("No game_start received, using snapshot directly: pid=%s", self._pid)
                self.seed = None
                self._handle_snapshot(data["state"])
                logger.info("Received initial snapshot (legacy): pid=%s", self._pid)
            
            else:
                logger.warning("Unexpected first packet type: %s, pid=%s", data.get("type"), self._pid)
            
            # Start background reader task (single-reader pattern)
            self._reader_task = asyncio.create_task(self._reader_loop())
            logger.debug("Started reader task: pid=%s", self._pid)
        
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for initial packets: pid=%s", self._pid)
            self._connected = False
            raise TimeoutError("Did not receive initial packets from server")
        except Exception as e:
            logger.exception("Connection failed: pid=%s", self._pid)
            self._connected = False
            raise ConnectionError(f"Failed to connect: {e}")

    async def _reader_loop(self) -> None:
        """Background task that reads all messages and dispatches to queues.
        
        This is the ONLY task that calls websocket.recv(), preventing race
        conditions between send_action() and listen().
        
        Messages are routed to appropriate queues:
        - action_result → _action_result_queue (for send_action)
        - snapshot → _snapshot_queue (for listen)
        
        When the WebSocket closes (normal or error), puts None sentinel in
        snapshot_queue to signal listen() to exit cleanly.
        """
        if self._websocket is None:
            return
        
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "action_result":
                        # Route to send_action()
                        await self._action_result_queue.put(data)
                        logger.debug("Dispatched action_result to queue: pid=%s", self._pid)
                    
                    elif msg_type == "snapshot":
                        # Route to listen()
                        await self._snapshot_queue.put(data)
                        logger.debug("Dispatched snapshot to queue: pid=%s", self._pid)
                    
                    else:
                        logger.warning("Unknown message type in reader: %s, pid=%s", msg_type, self._pid)
                
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in reader: pid=%s", self._pid)
                except Exception:
                    logger.exception("Error processing message in reader: pid=%s", self._pid)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed in reader: pid=%s", self._pid)
            self._connected = False
        except Exception:
            logger.exception("Error in reader loop: pid=%s", self._pid)
            self._connected = False
        finally:
            # Signal listen() that connection is closed (both normal and error cases)
            await self._snapshot_queue.put(None)
            logger.debug("Put sentinel in snapshot_queue: pid=%s", self._pid)

    async def send_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Send an action to the server and wait for result.
        
        Uses single-reader pattern: waits on action_result_queue instead of
        calling websocket.recv() directly (prevents race with listen).
        
        If use_seq is enabled (default), automatically adds a sequence number
        to the action for replay attack protection.
        
        Args:
            action: Action dict with structure:
                {"type": "buy", "slot": int}
                {"type": "reroll"}
                {"type": "place", "hand_index": int, "coord": [q, r], "rotation": int}
                {"type": "end_turn"}
                
                Note: "seq" field is automatically added if use_seq=True
        
        Returns:
            Result dict: {"ok": bool, "error": str|null}
        
        Raises:
            ConnectionError: If not connected to server
        """
        if not self._connected or self._websocket is None:
            raise ConnectionError("Not connected to server")
        
        try:
            # SECURITY: Add sequence number for replay attack protection
            if self._use_seq:
                self._seq += 1
                action = {**action, "seq": self._seq}
                logger.debug("Added seq=%s to action: pid=%s", self._seq, self._pid)
            
            # Send action message
            await self._websocket.send(PacketFactory.make_action(action))
            logger.debug("Sent action: pid=%s, action=%s", self._pid, action.get("type"))
            
            # Wait for result from queue (dispatched by reader task)
            data = await self._action_result_queue.get()
            
            result = {
                "ok": data.get("ok", False),
                "error": data.get("error")
            }
            logger.debug("Received result: pid=%s, ok=%s", self._pid, result["ok"])
            return result
        
        except Exception as e:
            logger.exception("Error sending action: pid=%s", self._pid)
            raise ConnectionError(f"Failed to send action: {e}")

    async def listen(self, callback: Callable[[PublicState | Dict[str, Any]], None]) -> None:
        """Listen for state snapshots and invoke callback on each update.
        
        Uses single-reader pattern: consumes from snapshot_queue instead of
        calling websocket.recv() directly (prevents race with send_action).
        
        This method blocks until the connection is closed. Each time a snapshot
        arrives, it is parsed (either as PublicState or minimal dict) and passed 
        to the callback. When the connection closes, _reader_loop puts None
        sentinel in the queue, causing this method to exit cleanly.
        
        Args:
            callback: Function to call with each new state (PublicState or dict)
                     Signature: callback(state: PublicState | Dict) -> None
        
        Example:
            def on_update(state):
                if isinstance(state, PublicState):
                    print(f"Turn {state.turn}")
                else:
                    print(f"Turn {state['turn']}")
            
            await client.listen(on_update)  # Blocks until disconnect
        
        Raises:
            ConnectionError: If not connected to server
        """
        if not self._connected or self._websocket is None:
            raise ConnectionError("Not connected to server")
        
        try:
            while self._connected:
                # Wait for snapshot from queue (dispatched by reader task)
                data = await self._snapshot_queue.get()
                
                # Check for sentinel (connection closed)
                if data is None:
                    logger.info("Received sentinel, exiting listen: pid=%s", self._pid)
                    return
                
                try:
                    self._handle_snapshot(data["state"])
                    
                    # Invoke callback with updated state
                    if self.state is not None:
                        callback(self.state)
                
                except Exception:
                    logger.exception("Error processing snapshot in listen: pid=%s", self._pid)
        
        except Exception:
            logger.exception("Error in listen loop: pid=%s", self._pid)
            self._connected = False

    async def disconnect(self) -> None:
        """Disconnect from server and clean up resources.
        
        Gracefully closes the WebSocket connection and cancels the reader task.
        """
        if self._websocket is not None:
            try:
                # Cancel reader task
                if self._reader_task is not None and not self._reader_task.done():
                    self._reader_task.cancel()
                    try:
                        await self._reader_task
                    except asyncio.CancelledError:
                        pass
                    logger.debug("Cancelled reader task: pid=%s", self._pid)
                
                # Close websocket
                await self._websocket.close()
                logger.info("Disconnected: pid=%s", self._pid)
            except Exception:
                logger.exception("Error during disconnect: pid=%s", self._pid)
            finally:
                self._connected = False
                self._websocket = None
                self._reader_task = None

    def _handle_snapshot(self, state_dict: Dict[str, Any]) -> None:
        """Parse and store a state snapshot.
        
        Args:
            state_dict: Serialized PublicState dict (or minimal snapshot dict)
        """
        try:
            # Try to parse as full PublicState
            if "active_player" in state_dict:
                self.state = from_dict(state_dict)
                logger.debug("Updated state: pid=%s, turn=%s", self._pid, self.state.turn)
            else:
                # Minimal snapshot - store as dict
                self.state = state_dict
                logger.debug("Updated minimal state: pid=%s, turn=%s", self._pid, state_dict.get("turn"))
        except Exception:
            logger.exception("Failed to parse snapshot: pid=%s", self._pid)
