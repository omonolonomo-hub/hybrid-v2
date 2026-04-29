"""NetworkServer — WebSocket server for multiplayer game orchestration.

This module provides a thin network layer over ServerOrchestrator using asyncio
and websockets. It handles client connections, message routing, and state
snapshot distribution without any game logic.

DESIGN RATIONALE:
- Zero game logic: Pure message routing to orchestrator
- Async-first: Built on asyncio + websockets
- Resilient: Connection errors logged, never crash
- Stateless protocol: Each message is self-contained JSON
- Non-blocking: Game operations run in thread pool to avoid blocking event loop

THREADING MODEL:
- Main event loop: Handles all WebSocket I/O and message routing
- Thread pool: Executes blocking game operations (submit_action → _advance_turn)
- Critical: submit_action can trigger finish_turn() + combat_phase() + start_turn()
  which can take 50-500ms. Running these in the event loop would block all clients.
- Solution: Use asyncio.run_in_executor() to offload to thread pool
- Thread safety: Single-worker executor ensures game state is never mutated in parallel

THREAD SAFETY GUARANTEE:
- Game engine (Game, GameSession, ServerOrchestrator) is NOT thread-safe
- Using ThreadPoolExecutor(max_workers=1) ensures serial execution
- This prevents race conditions where:
  * Multiple submit_action calls could mutate game state simultaneously
  * _generate_snapshots() writes to _outbox while _broadcast_snapshots() reads it
  * Combat calculations run in parallel with state queries
- Python GIL provides some protection, but explicit serialization is safer
- Future-proof: If asyncio code directly reads game.players[x].hp while thread
  pool is mutating state, inconsistent reads can occur. Single worker prevents this.

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
import concurrent.futures
import json
import logging
from typing import Dict, Optional

try:
    import websockets
    from websockets.asyncio.server import ServerConnection
except ImportError:
    raise ImportError(
        "websockets library required. Install with: pip install websockets"
    )

from engine_core.packet_factory import PacketFactory
from engine_core.server_orchestrator import ServerOrchestrator
from v2.core.action_result import ActionResult

logger = logging.getLogger(__name__)


class NetworkServer:
    """WebSocket server for multiplayer game sessions.
    
    NetworkServer wraps a ServerOrchestrator and provides network transport
    for action submission and state distribution. Each client connects with
    a player ID and receives state snapshots when the game progresses.
    
    Attributes:
        orchestrator: ServerOrchestrator managing game logic
        host: Server bind address
        port: Server bind port
        _connections: Dict mapping pid → websocket connection
        _server: WebSocket server instance (when running)
        _action_lock: asyncio.Lock for serializing action submissions
        _executor: ThreadPoolExecutor with max_workers=1 for game operations
    
    Usage:
        orchestrator = ServerOrchestrator(session)
        server = NetworkServer(orchestrator)
        
        await server.start()  # Blocks until server stops
        # Clients can now connect and play
        
        await server.stop()  # Graceful shutdown
    
    Thread-safety:
        Two-layer protection ensures game state consistency:
        
        1. asyncio.Lock: Serializes action submission at the async level
           - Prevents race where two clients send end_turn simultaneously
           - Ensures _advance_turn is never called twice in parallel
        
        2. ThreadPoolExecutor(max_workers=1): Serializes at the thread level
           - Game engine is NOT thread-safe (no locks in Game/GameSession)
           - Single worker ensures game state is never mutated in parallel
           - Prevents race where:
             * submit_action mutates game state in thread A
             * Another submit_action reads/writes in thread B
             * _generate_snapshots writes _outbox while _broadcast_snapshots reads
           - Python GIL helps but is not sufficient for complex mutations
        
        Without single-worker executor, future code could introduce bugs:
        - Asyncio coroutine reads game.players[x].hp during combat calculation
        - Two combat phases run simultaneously (data corruption)
        - Snapshot generation races with state mutation (inconsistent views)
    """

    def __init__(
        self,
        orchestrator: ServerOrchestrator,
        host: str = "localhost",
        port: int = 8765
    ):
        """Initialize network server.
        
        Args:
            orchestrator: ServerOrchestrator to route actions to
            host: Server bind address (default: localhost)
            port: Server bind port (default: 8765)
        """
        self._orchestrator = orchestrator
        self._host = host
        self._port = port
        self._connections: Dict[int, ServerConnection] = {}
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._stop_event: Optional[asyncio.Event] = None
        self._action_lock = asyncio.Lock()
        
        # THREAD SAFETY: Single-worker executor ensures game engine is never
        # accessed from multiple threads simultaneously. Game/GameSession/
        # ServerOrchestrator have no internal locking and assume serial access.
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="game_worker"
        )

    async def start(self) -> None:
        """Start the WebSocket server and listen for connections.
        
        This method blocks until stop() is called or the server encounters
        an error. Each incoming connection spawns a _handle_client() task.
        
        Example:
            server = NetworkServer(orchestrator)
            await server.start()  # Blocks here
        """
        self._running = True
        self._stop_event = asyncio.Event()
        
        async with websockets.serve(
            self._handle_client,
            self._host,
            self._port
        ) as server:
            self._server = server
            logger.info("NetworkServer listening on %s:%s", self._host, self._port)
            await self._stop_event.wait()
        
        logger.info("NetworkServer stopped")

    async def stop(self) -> None:
        """Stop the server and close all client connections.
        
        Gracefully closes all active connections, shuts down the server,
        and cleans up the thread pool executor.
        """
        logger.info("Stopping NetworkServer...")
        self._running = False
        if self._stop_event is not None:
            self._stop_event.set()
        
        # Close all client connections
        for pid, ws in list(self._connections.items()):
            try:
                await ws.close()
            except Exception:
                logger.exception("Error closing connection for pid=%s", pid)
        
        self._connections.clear()
        
        # Shutdown thread pool executor
        self._executor.shutdown(wait=True)
        logger.debug("Thread pool executor shut down")

    async def _handle_client(self, websocket: ServerConnection) -> None:
        """Handle a single client connection.
        
        Protocol flow:
        1. Wait for join message with pid
        2. Send game_start message with RNG seed (MULTIPLAYER SYNC)
        3. Send initial state snapshot
        4. Loop: receive actions, send results, broadcast snapshots
        5. On disconnect: clean up connection
        
        Args:
            websocket: WebSocket connection to client
        """
        pid: Optional[int] = None
        
        try:
            # Wait for join message
            join_msg = await websocket.recv()
            join_data = json.loads(join_msg)
            
            if join_data.get("type") != "join":
                logger.warning("First message must be join, got: %s", join_data.get("type"))
                await websocket.close()
                return
            
            pid = join_data.get("pid")
            if pid is None or not isinstance(pid, int):
                logger.warning("Invalid pid in join message: %s", pid)
                await websocket.close()
                return
            
            # Register connection
            self._connections[pid] = websocket
            logger.info("Client connected: pid=%s", pid)
            
            # Send game_start with RNG seed (BEFORE snapshot)
            await self._send_game_start(websocket, pid)
            
            # Send initial snapshot
            await self._send_initial_snapshot(websocket, pid)
            
            # Message loop
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, pid, data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from pid=%s: %s", pid, message)
                except Exception:
                    logger.exception("Error handling message from pid=%s", pid)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected: pid=%s", pid)
        except Exception:
            logger.exception("Error in client handler for pid=%s", pid)
        finally:
            # Clean up connection
            if pid is not None and pid in self._connections:
                del self._connections[pid]

    async def _send_game_start(self, websocket: ServerConnection, pid: int) -> None:
        """Send GAME_START packet with RNG seed to newly connected client.
        
        Always sends the packet, even if seed is None (test/local games).
        Client always expects this packet before the snapshot.
        
        Packet format:
            {"type": "game_start", "seed": int | null}
        
        Args:
            websocket: Client connection
            pid: Player ID
        """
        seed = getattr(self._orchestrator.session.game, "_rng_seed", None)
        if seed is None:
            logger.debug("_send_game_start: no _rng_seed on game for pid=%s, sending null", pid)
        
        await websocket.send(PacketFactory.make_game_start(seed))
        logger.info("Sent game_start seed=%s to pid=%s", seed, pid)

    async def _send_initial_snapshot(self, websocket: ServerConnection, pid: int) -> None:
        """Send initial state snapshot to newly connected client.
        
        Generates a snapshot for the player and sends it immediately after join.
        
        Args:
            websocket: Client connection
            pid: Player ID
        """
        try:
            # Generate snapshot using orchestrator's internal method
            player_index = self._orchestrator._get_player_index(pid)
            if player_index is None:
                logger.warning("Cannot generate snapshot: pid=%s not found", pid)
                return
            
            # Build snapshot
            if self._orchestrator._state_builder is not None:
                from v2.core.serialization import to_dict
                
                original_view_index = self._orchestrator._state_builder.view_index
                self._orchestrator._state_builder.view_index = player_index
                
                public_state = self._orchestrator._state_builder.get_public_state()
                snapshot_dict = to_dict(public_state)
                
                self._orchestrator._state_builder.view_index = original_view_index
            else:
                snapshot_dict = self._orchestrator._build_minimal_snapshot(player_index)
            
            # Send snapshot
            await websocket.send(PacketFactory.make_snapshot(snapshot_dict))
            logger.debug("Sent initial snapshot to pid=%s", pid)
        
        except Exception:
            logger.exception("Failed to send initial snapshot to pid=%s", pid)

    async def _handle_message(
        self,
        websocket: ServerConnection,
        pid: int,
        data: Dict
    ) -> None:
        """Handle a message from a client.
        
        Routes action messages to orchestrator and sends back results.
        After each action, checks outbox and broadcasts snapshots.
        
        Args:
            websocket: Client connection
            pid: Player ID
            data: Parsed JSON message
        """
        msg_type = data.get("type")
        
        if msg_type == "action":
            action = data.get("action")
            if action is None:
                logger.warning("Action message missing 'action' field from pid=%s", pid)
                return
            
            # Serialize action processing to prevent race conditions
            async with self._action_lock:
                # Submit action to orchestrator and handle result
                try:
                    # CRITICAL: Run blocking submit_action in dedicated single-worker thread pool
                    # 
                    # Why thread pool?
                    # - submit_action can trigger _advance_turn() → finish_turn() + combat_phase()
                    # - These operations can take 50-500ms and would block the event loop
                    # - Blocking the event loop freezes all WebSocket handlers
                    # 
                    # Why max_workers=1?
                    # - Game engine (Game/GameSession/ServerOrchestrator) is NOT thread-safe
                    # - No internal locking — assumes serial access
                    # - Single worker guarantees no parallel mutations
                    # - Prevents races like:
                    #   * Thread A: submit_action mutates game.players[0].hp
                    #   * Thread B: submit_action reads game.players[0].hp (stale/torn read)
                    #   * Thread A: _generate_snapshots writes _outbox
                    #   * Event loop: _broadcast_snapshots reads _outbox (race condition)
                    # 
                    # Python GIL provides some protection but is insufficient for:
                    # - Complex multi-step mutations (combat calculations)
                    # - Dict operations that can resize during iteration
                    # - Future asyncio code that might read game state directly
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        self._executor,  # Use dedicated single-worker executor
                        self._orchestrator.submit_action,
                        pid,
                        action
                    )
                    
                    # Normalize result (can be ActionResult enum or bool)
                    if result == ActionResult.OK or result is True:
                        ok = True
                        error = None
                    else:
                        ok = False
                        # Extract error name if it's an enum, otherwise convert to string
                        error = result.name if hasattr(result, "name") else str(result)
                
                except Exception as e:
                    logger.exception("submit_action failed for pid=%s", pid)
                    ok = False
                    error = str(e)
                
                # Always send result back to client
                await websocket.send(PacketFactory.make_action_result(ok, error))
                
                # Check outbox and broadcast snapshots
                await self._broadcast_snapshots()
        
        else:
            logger.warning("Unknown message type '%s' from pid=%s", msg_type, pid)

    async def _broadcast_snapshots(self) -> None:
        """Poll orchestrator outbox and send snapshots to clients.
        
        Called after each action to distribute state updates to all players.
        """
        snapshots = self._orchestrator.pop_outbox()
        
        for pid, snapshot_dict in snapshots.items():
            if pid not in self._connections:
                logger.debug("No connection for pid=%s, skipping snapshot", pid)
                continue
            
            try:
                await self._connections[pid].send(PacketFactory.make_snapshot(snapshot_dict))
                logger.debug("Sent snapshot to pid=%s", pid)
            except Exception:
                logger.exception("Failed to send snapshot to pid=%s", pid)
