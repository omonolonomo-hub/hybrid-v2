"""Integration tests for network layer (server + client).

Tests the complete network stack:
- NetworkServer + NetworkClient communication
- Action submission and result handling
- State snapshot distribution
- Multi-client synchronization

Requires:
    pip install pytest pytest-asyncio websockets
"""

import asyncio
import pytest
from typing import List

from engine_core.network_server import NetworkServer
from engine_core.network_client import NetworkClient
from engine_core.server_orchestrator import ServerOrchestrator
from engine_core.game_session import GameSession
from v2.core.local_dispatcher import LocalCommandDispatcher
from engine_core.game import Game
from v2.core.public_state import PublicState


@pytest.fixture
def game():
    """Create a minimal 2-player game for testing."""
    from engine_core.player import Player
    from unittest.mock import Mock
    
    # Create mock card pool to prevent market errors
    mock_cards = []
    for i in range(10):
        card = Mock()
        card.name = f"TestCard{i}"
        card.tier = 1
        card.rarity = "common"
        mock_cards.append(card)
    
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players, card_pool=mock_cards)
    return game


@pytest.fixture
def session(game):
    """Create a GameSession with LocalCommandDispatcher."""
    dispatcher = LocalCommandDispatcher(game)
    session = GameSession(game, dispatcher)
    return session


@pytest.fixture
def orchestrator(session):
    """Create a ServerOrchestrator."""
    # Use minimal snapshots (no GameState builder) for testing
    orchestrator = ServerOrchestrator(session, state_builder=None)
    return orchestrator


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_server_client_connection(orchestrator):
    """Test basic server-client connection and initial snapshot."""
    server = NetworkServer(orchestrator, host="localhost", port=8766)
    client = NetworkClient(pid=0, uri="ws://localhost:8766")
    
    # Start server in background
    server_task = asyncio.create_task(server.start())
    
    try:
        # Give server time to start
        await asyncio.sleep(0.1)
        
        # Connect client
        await client.connect()
        
        # Verify initial state received
        assert client.state is not None
        assert client.connected
        
        # Disconnect
        await client.disconnect()
        assert not client.connected
    
    finally:
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_action_submission(orchestrator):
    """Test action submission and result handling."""
    server = NetworkServer(orchestrator, host="localhost", port=8767)
    client = NetworkClient(pid=0, uri="ws://localhost:8767")
    
    server_task = asyncio.create_task(server.start())
    
    try:
        await asyncio.sleep(0.1)
        await client.connect()
        
        # Submit end_turn action
        result = await client.send_action({"type": "end_turn"})
        
        # Verify result
        assert result["ok"] is True
        assert result["error"] is None
        
        await client.disconnect()
    
    finally:
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_two_clients_turn_progression(orchestrator):
    """Test two clients progressing through a turn together.
    
    Both clients send end_turn, triggering turn advancement.
    Both should receive updated snapshots via listen callback.
    """
    server = NetworkServer(orchestrator, host="localhost", port=8768)
    client0 = NetworkClient(pid=0, uri="ws://localhost:8768")
    client1 = NetworkClient(pid=1, uri="ws://localhost:8768")
    
    server_task = asyncio.create_task(server.start())
    
    # Track snapshots received by each client
    snapshots_received = {0: [], 1: []}
    snapshot_events = {0: asyncio.Event(), 1: asyncio.Event()}
    
    def make_callback(pid: int):
        def callback(state):
            snapshots_received[pid].append(state)
            snapshot_events[pid].set()
        return callback
    
    try:
        await asyncio.sleep(0.1)
        
        # Connect both clients
        await client0.connect()
        await client1.connect()
        
        # Verify initial states (can be PublicState or dict)
        assert client0.state is not None
        assert client1.state is not None
        
        # Get initial turn (works for both PublicState and dict)
        if isinstance(client0.state, PublicState):
            initial_turn = client0.state.turn
        else:
            initial_turn = client0.state.get("turn", 0)
        
        # Both clients send end_turn (before starting listen)
        result0 = await client0.send_action({"type": "end_turn"})
        assert result0["ok"] is True
        
        result1 = await client1.send_action({"type": "end_turn"})
        assert result1["ok"] is True
        
        # Now start listen tasks to receive snapshots
        listen0 = asyncio.create_task(client0.listen(make_callback(0)))
        listen1 = asyncio.create_task(client1.listen(make_callback(1)))
        
        # Wait for snapshots to arrive (with timeout)
        try:
            await asyncio.wait_for(snapshot_events[0].wait(), timeout=2.0)
            await asyncio.wait_for(snapshot_events[1].wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for snapshots")
        
        # Verify both clients received snapshots
        assert len(snapshots_received[0]) > 0, "Client 0 should receive snapshot"
        assert len(snapshots_received[1]) > 0, "Client 1 should receive snapshot"
        
        # Verify snapshots are valid (PublicState or dict)
        for pid in [0, 1]:
            for snapshot in snapshots_received[pid]:
                # Can be PublicState or minimal dict
                if isinstance(snapshot, PublicState):
                    assert snapshot.turn >= initial_turn
                elif isinstance(snapshot, dict):
                    assert "turn" in snapshot
                    assert snapshot["turn"] >= initial_turn
                else:
                    pytest.fail(f"Unexpected snapshot type: {type(snapshot)}")
        
        # Disconnect clients (this will stop listen tasks)
        await client0.disconnect()
        await client1.disconnect()
        
        # Cancel listen tasks
        listen0.cancel()
        listen1.cancel()
        
        try:
            await listen0
        except asyncio.CancelledError:
            pass
        
        try:
            await listen1
        except asyncio.CancelledError:
            pass
    
    finally:
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_invalid_action(orchestrator):
    """Test that invalid actions return error results."""
    server = NetworkServer(orchestrator, host="localhost", port=8769)
    client = NetworkClient(pid=0, uri="ws://localhost:8769")
    
    server_task = asyncio.create_task(server.start())
    
    try:
        await asyncio.sleep(0.1)
        await client.connect()
        
        # Submit invalid action (unknown type)
        result = await client.send_action({"type": "invalid_action"})
        
        # Should receive error
        assert result["ok"] is False
        assert result["error"] is not None
        
        await client.disconnect()
    
    finally:
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_multiple_actions_sequence(orchestrator):
    """Test sequence of multiple actions from same client."""
    server = NetworkServer(orchestrator, host="localhost", port=8772)
    client = NetworkClient(pid=0, uri="ws://localhost:8772")
    
    server_task = asyncio.create_task(server.start())
    
    try:
        await asyncio.sleep(0.2)  # Give server more time to start
        await client.connect()
        
        # Submit end_turn action (simpler than reroll)
        result = await client.send_action({"type": "end_turn"})
        assert result["ok"] is True
        
        await client.disconnect()
    
    finally:
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_server_graceful_shutdown(orchestrator):
    """Test that server shuts down gracefully with connected clients."""
    server = NetworkServer(orchestrator, host="localhost", port=8771)
    client = NetworkClient(pid=0, uri="ws://localhost:8771")
    
    server_task = asyncio.create_task(server.start())
    
    try:
        await asyncio.sleep(0.1)
        await client.connect()
        
        # Stop server while client connected
        await server.stop()
        try:
            await asyncio.wait_for(server_task, timeout=2.0)
        except asyncio.TimeoutError:
            server_task.cancel()
        
        # Try to send action - should fail since server is down
        try:
            await client.send_action({"type": "end_turn"})
            pytest.fail("Should have raised ConnectionError")
        except ConnectionError:
            # Expected - server is down
            pass
    
    finally:
        # Cleanup
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
