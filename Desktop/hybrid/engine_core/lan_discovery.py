"""LAN Discovery — UDP broadcast-based server discovery for multiplayer games.

This module provides automatic server discovery in LAN environments, eliminating
the need for clients to manually enter server IP addresses. Servers broadcast
their presence via UDP, and clients can scan for available servers.

DESIGN RATIONALE:
- Zero configuration: Clients automatically discover servers on the same network
- UDP broadcast: Simple, lightweight, no central registry needed
- Non-blocking: Async-first design integrates with existing asyncio architecture
- Resilient: Network errors logged, never crash
- Minimal overhead: Small JSON packets, configurable broadcast interval

PROTOCOL:
    Server → Broadcast (UDP):
        {
            "type": "server_hello",
            "host": "192.168.1.100",
            "port": 8765,
            "game": "AutoChess",
            "version": "1.0.0",
            "players": "2/4",
            "timestamp": 1703275200.123
        }
    
    Client → Scan:
        Returns list of discovered servers with metadata

SECURITY CONSIDERATIONS:
- UDP broadcast is inherently insecure (no authentication)
- Only use on trusted LANs (home networks, private game sessions)
- Do not expose sensitive information in broadcast packets
- Consider adding optional pre-shared key validation in future

NETWORK REQUIREMENTS:
- Clients and servers must be on the same subnet
- Firewall must allow UDP broadcast on DISCOVERY_PORT
- Some networks may block broadcast traffic (corporate, public WiFi)

Dependencies:
    Standard library only (socket, asyncio, json)
"""

import asyncio
import json
import logging
import socket
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default UDP port for discovery broadcasts
DISCOVERY_PORT = 8766

# Default broadcast interval (seconds)
DEFAULT_BROADCAST_INTERVAL = 2.0

# Default discovery timeout (seconds)
DEFAULT_DISCOVERY_TIMEOUT = 5.0


@dataclass
class ServerInfo:
    """Information about a discovered server.
    
    Attributes:
        host: Server IP address (e.g., "192.168.1.100")
        port: WebSocket server port (e.g., 8765)
        game: Game name/identifier (e.g., "AutoChess")
        version: Game version (e.g., "1.0.0")
        players: Player count string (e.g., "2/4")
        timestamp: Unix timestamp when broadcast was sent
        last_seen: Unix timestamp when last received (client-side)
    """
    host: str
    port: int
    game: str
    version: str = "unknown"
    players: str = "?/?"
    timestamp: float = 0.0
    last_seen: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "host": self.host,
            "port": self.port,
            "game": self.game,
            "version": self.version,
            "players": self.players,
            "timestamp": self.timestamp,
            "last_seen": self.last_seen
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerInfo":
        """Create ServerInfo from dict."""
        return cls(
            host=data.get("host", ""),
            port=data.get("port", 0),
            game=data.get("game", ""),
            version=data.get("version", "unknown"),
            players=data.get("players", "?/?"),
            timestamp=data.get("timestamp", 0.0),
            last_seen=data.get("last_seen", 0.0)
        )
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.game} @ {self.host}:{self.port} ({self.players}) v{self.version}"


class ServerBroadcaster:
    """Broadcasts server presence on LAN via UDP.
    
    ServerBroadcaster runs in the background and periodically sends UDP
    broadcast packets announcing the server's availability. Clients on the
    same network can discover the server without manual IP configuration.
    
    Attributes:
        host: Server IP address to advertise
        port: WebSocket server port to advertise
        game_name: Game identifier (e.g., "AutoChess")
        version: Game version string
        interval: Broadcast interval in seconds
        _running: Flag indicating if broadcaster is active
        _task: Background asyncio task
    
    Usage:
        broadcaster = ServerBroadcaster(
            host="192.168.1.100",
            port=8765,
            game_name="AutoChess",
            version="1.0.0"
        )
        
        await broadcaster.start()  # Start broadcasting
        # ... server runs ...
        await broadcaster.stop()   # Stop broadcasting
    
    Thread-safety: Not thread-safe (use within single asyncio event loop)
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        game_name: str,
        version: str = "1.0.0",
        interval: float = DEFAULT_BROADCAST_INTERVAL,
        get_player_count: Optional[callable] = None
    ):
        """Initialize server broadcaster.
        
        Args:
            host: Server IP address to advertise (use local IP, not 0.0.0.0)
            port: WebSocket server port
            game_name: Game identifier
            version: Game version string (default: "1.0.0")
            interval: Broadcast interval in seconds (default: 2.0)
            get_player_count: Optional callback returning "current/max" string
        """
        self._host = host
        self._port = port
        self._game_name = game_name
        self._version = version
        self._interval = interval
        self._get_player_count = get_player_count
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._sock: Optional[socket.socket] = None
    
    async def start(self) -> None:
        """Start broadcasting server presence.
        
        Creates a UDP socket with broadcast enabled and starts a background
        task that sends periodic broadcast packets.
        
        Raises:
            OSError: If socket creation or configuration fails
        """
        if self._running:
            logger.warning("ServerBroadcaster already running")
            return
        
        try:
            # Create UDP socket with broadcast enabled
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.setblocking(False)  # Non-blocking for asyncio
            
            self._running = True
            self._task = asyncio.create_task(self._broadcast_loop())
            
            logger.info(
                "ServerBroadcaster started: %s:%s (%s)",
                self._host, self._port, self._game_name
            )
        
        except Exception as e:
            logger.exception("Failed to start ServerBroadcaster")
            self._cleanup()
            raise OSError(f"Failed to start broadcaster: {e}")
    
    async def stop(self) -> None:
        """Stop broadcasting and clean up resources.
        
        Cancels the background task and closes the UDP socket.
        """
        if not self._running:
            return
        
        logger.info("Stopping ServerBroadcaster...")
        self._running = False
        
        # Cancel broadcast task
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._cleanup()
        logger.info("ServerBroadcaster stopped")
    
    def _cleanup(self) -> None:
        """Clean up socket resources."""
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                logger.exception("Error closing broadcast socket")
            finally:
                self._sock = None
    
    async def _broadcast_loop(self) -> None:
        """Background task that sends periodic broadcast packets."""
        while self._running:
            try:
                await self._send_broadcast()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in broadcast loop")
                await asyncio.sleep(self._interval)
    
    async def _send_broadcast(self) -> None:
        """Send a single broadcast packet.
        
        Constructs a server_hello packet with current server info and sends
        it via UDP broadcast to DISCOVERY_PORT.
        """
        if self._sock is None:
            return
        
        try:
            # Get current player count if callback provided
            players = "?/?"
            if self._get_player_count is not None:
                try:
                    players = self._get_player_count()
                except Exception:
                    logger.exception("Error getting player count")
            
            # Build broadcast packet
            packet = {
                "type": "server_hello",
                "host": self._host,
                "port": self._port,
                "game": self._game_name,
                "version": self._version,
                "players": players,
                "timestamp": time.time()
            }
            
            message = json.dumps(packet).encode("utf-8")
            
            # Send to broadcast address
            # Use asyncio.get_event_loop().sock_sendto for non-blocking send
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(
                self._sock,
                message,
                ("<broadcast>", DISCOVERY_PORT)
            )
            
            logger.debug("Sent broadcast: %s", packet)
        
        except Exception:
            logger.exception("Failed to send broadcast")


class ServerDiscovery:
    """Discovers servers on LAN via UDP broadcast.
    
    ServerDiscovery listens for UDP broadcast packets from servers and
    maintains a list of discovered servers. Clients can scan for servers
    and select one to connect to.
    
    Attributes:
        timeout: Discovery timeout in seconds
        _servers: Dict mapping (host, port) → ServerInfo
        _sock: UDP socket for receiving broadcasts
    
    Usage:
        discovery = ServerDiscovery(timeout=5.0)
        servers = await discovery.discover_servers()
        
        if servers:
            server = servers[0]
            print(f"Found: {server}")
            # Connect to ws://{server.host}:{server.port}
    
    Thread-safety: Not thread-safe (use within single asyncio event loop)
    """
    
    def __init__(self, timeout: float = DEFAULT_DISCOVERY_TIMEOUT):
        """Initialize server discovery.
        
        Args:
            timeout: Discovery timeout in seconds (default: 5.0)
        """
        self._timeout = timeout
        self._servers: Dict[tuple, ServerInfo] = {}
        self._sock: Optional[socket.socket] = None
    
    async def discover_servers(
        self,
        game_filter: Optional[str] = None
    ) -> List[ServerInfo]:
        """Scan for servers on LAN.
        
        Listens for UDP broadcast packets for the specified timeout duration
        and returns a list of discovered servers. Optionally filters by game name.
        
        Args:
            game_filter: Only return servers matching this game name (optional)
        
        Returns:
            List of ServerInfo objects for discovered servers
        
        Example:
            servers = await discovery.discover_servers(game_filter="AutoChess")
            for server in servers:
                print(f"Found: {server}")
        """
        self._servers.clear()
        
        try:
            # Create UDP socket for receiving broadcasts
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("", DISCOVERY_PORT))
            self._sock.setblocking(False)  # Non-blocking for asyncio
            
            logger.info("Scanning for servers (timeout=%ss)...", self._timeout)
            
            # Listen for broadcasts until timeout
            try:
                await asyncio.wait_for(
                    self._listen_loop(game_filter),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                # Expected - timeout means scan is complete
                pass
            
            # Return discovered servers sorted by last_seen (most recent first)
            servers = sorted(
                self._servers.values(),
                key=lambda s: s.last_seen,
                reverse=True
            )
            
            logger.info("Discovery complete: found %s server(s)", len(servers))
            return servers
        
        except Exception as e:
            logger.exception("Error during server discovery")
            return []
        
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up socket resources."""
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                logger.exception("Error closing discovery socket")
            finally:
                self._sock = None
    
    async def _listen_loop(self, game_filter: Optional[str]) -> None:
        """Listen for broadcast packets until cancelled.
        
        Args:
            game_filter: Only process servers matching this game name
        """
        if self._sock is None:
            return
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Receive UDP packet (non-blocking)
                data, addr = await loop.sock_recvfrom(self._sock, 4096)
                
                # Parse packet
                try:
                    packet = json.loads(data.decode("utf-8"))
                    
                    if packet.get("type") == "server_hello":
                        self._process_server_hello(packet, game_filter)
                
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in broadcast packet from %s", addr)
                except Exception:
                    logger.exception("Error processing broadcast packet")
            
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in listen loop")
                await asyncio.sleep(0.1)
    
    def _process_server_hello(
        self,
        packet: Dict[str, Any],
        game_filter: Optional[str]
    ) -> None:
        """Process a server_hello packet.
        
        Args:
            packet: Parsed JSON packet
            game_filter: Only process if game matches this filter
        """
        try:
            host = packet.get("host")
            port = packet.get("port")
            game = packet.get("game")
            
            if not host or not port or not game:
                logger.warning("Incomplete server_hello packet: %s", packet)
                return
            
            # Apply game filter
            if game_filter is not None and game != game_filter:
                return
            
            # Create or update server info
            key = (host, port)
            server = ServerInfo.from_dict(packet)
            server.last_seen = time.time()
            
            if key not in self._servers:
                logger.info("Discovered server: %s", server)
            
            self._servers[key] = server
        
        except Exception:
            logger.exception("Error processing server_hello")


# Convenience functions for common use cases

async def start_broadcasting(
    host: str,
    port: int,
    game_name: str,
    version: str = "1.0.0",
    get_player_count: Optional[callable] = None
) -> ServerBroadcaster:
    """Start broadcasting server presence (convenience function).
    
    Args:
        host: Server IP address (use local IP, not 0.0.0.0)
        port: WebSocket server port
        game_name: Game identifier
        version: Game version string
        get_player_count: Optional callback returning "current/max" string
    
    Returns:
        ServerBroadcaster instance (already started)
    
    Example:
        broadcaster = await start_broadcasting(
            host="192.168.1.100",
            port=8765,
            game_name="AutoChess"
        )
        # ... server runs ...
        await broadcaster.stop()
    """
    broadcaster = ServerBroadcaster(
        host=host,
        port=port,
        game_name=game_name,
        version=version,
        get_player_count=get_player_count
    )
    await broadcaster.start()
    return broadcaster


async def find_servers(
    game_name: Optional[str] = None,
    timeout: float = DEFAULT_DISCOVERY_TIMEOUT
) -> List[ServerInfo]:
    """Find servers on LAN (convenience function).
    
    Args:
        game_name: Only return servers for this game (optional)
        timeout: Discovery timeout in seconds
    
    Returns:
        List of discovered servers
    
    Example:
        servers = await find_servers(game_name="AutoChess", timeout=3.0)
        if servers:
            print(f"Found {len(servers)} server(s)")
            for server in servers:
                print(f"  - {server}")
    """
    discovery = ServerDiscovery(timeout=timeout)
    return await discovery.discover_servers(game_filter=game_name)
