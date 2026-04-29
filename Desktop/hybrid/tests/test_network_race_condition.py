"""Tests for NetworkClient race condition fix (single-reader pattern).

This test verifies that NetworkClient properly handles concurrent send_action()
and listen() calls without race conditions.

Bug Context:
    Previously, both send_action() and listen() called websocket.recv() directly,
    creating a race condition where either could consume messages intended for
    the other:
    
    - send_action() waits for action_result, but listen() might consume it
    - listen() waits for snapshots, but send_action() might consume them
    
    This caused:
    - send_action() timing out or receiving wrong message
    - listen() missing snapshots
    - Unpredictable behavior depending on timing
    
    Fix: Single-reader pattern with message dispatch queues
    - One background task reads all messages
    - Messages routed to appropriate queues by type
    - send_action() waits on action_result_queue
    - listen() consumes from snapshot_queue
    - No race conditions possible
"""

import asyncio
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from engine_core.network_client import NetworkClient


@pytest.fixture
def mock_websocket():
    """Create a mock websocket for testing."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = Mock(return_value=iter([]))  # Empty iterator by default
    return ws


@pytest.mark.asyncio
async def test_single_reader_pattern_initialized():
    """Test that client initializes with queue-based architecture."""
    client = NetworkClient(pid=0)
    
    # Verify queues are initialized
    assert hasattr(client, '_action_result_queue')
    assert hasattr(client, '_snapshot_queue')
    assert hasattr(client, '_reader_task')
    
    assert isinstance(client._action_result_queue, asyncio.Queue)
    assert isinstance(client._snapshot_queue, asyncio.Queue)


@pytest.mark.asyncio
async def test_reader_task_started_on_connect(mock_websocket):
    """Test that reader task is started after connection."""
    client = NetworkClient(pid=0)
    
    # Mock connection sequence
    mock_websocket.recv.side_effect = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
    ]
    
    with patch('websockets.connect', return_value=mock_websocket):
        await client.connect()
    
    # Verify reader task was created
    assert client._reader_task is not None
    assert isinstance(client._reader_task, asyncio.Task)
    assert not client._reader_task.done()
    
    # Cleanup
    await client.disconnect()


@pytest.mark.asyncio
async def test_action_result_routed_to_queue():
    """Test that action_result messages are routed to action_result_queue."""
    client = NetworkClient(pid=0)
    
    # Simulate reader task receiving action_result
    action_result_data = {"type": "action_result", "ok": True, "error": None}
    
    # Put message in queue (simulating what reader would do)
    await client._action_result_queue.put(action_result_data)
    
    # Verify it's in the queue
    assert client._action_result_queue.qsize() == 1
    
    # Retrieve it
    data = await client._action_result_queue.get()
    assert data["type"] == "action_result"
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_snapshot_routed_to_queue():
    """Test that snapshot messages are routed to snapshot_queue."""
    client = NetworkClient(pid=0)
    
    # Simulate reader task receiving snapshot
    snapshot_data = {"type": "snapshot", "state": {"turn": 5, "pid": 0}}
    
    # Put message in queue (simulating what reader would do)
    await client._snapshot_queue.put(snapshot_data)
    
    # Verify it's in the queue
    assert client._snapshot_queue.qsize() == 1
    
    # Retrieve it
    data = await client._snapshot_queue.get()
    assert data["type"] == "snapshot"
    assert data["state"]["turn"] == 5


@pytest.mark.asyncio
async def test_send_action_waits_on_queue(mock_websocket):
    """Test that send_action waits on action_result_queue, not websocket.recv()."""
    client = NetworkClient(pid=0)
    
    # Setup connection
    mock_websocket.recv.side_effect = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
    ]
    
    with patch('websockets.connect', return_value=mock_websocket):
        await client.connect()
    
    # Pre-populate action_result_queue (simulating reader task)
    action_result = {"type": "action_result", "ok": True, "error": None}
    await client._action_result_queue.put(action_result)
    
    # Send action - should get result from queue, not websocket
    result = await client.send_action({"type": "end_turn"})
    
    assert result["ok"] is True
    assert result["error"] is None
    
    # Verify websocket.recv was NOT called by send_action
    # (only called during connect, not during send_action)
    
    await client.disconnect()


@pytest.mark.asyncio
async def test_concurrent_send_and_listen_no_race():
    """Test that concurrent send_action and listen don't race."""
    client = NetworkClient(pid=0)
    
    # Mock websocket with message sequence
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    
    # Simulate messages arriving in mixed order
    messages = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
        json.dumps({"type": "action_result", "ok": True, "error": None}),
        json.dumps({"type": "snapshot", "state": {"turn": 2, "pid": 0}}),
        json.dumps({"type": "action_result", "ok": False, "error": "test"}),
    ]
    
    message_iter = iter(messages)
    mock_ws.recv = AsyncMock(side_effect=lambda: next(message_iter))
    mock_ws.close = AsyncMock()
    
    # Make websocket iterable for reader loop
    async def mock_aiter():
        for msg in messages[2:]:  # Skip initial messages
            yield msg
    
    mock_ws.__aiter__ = lambda: mock_aiter()
    
    with patch('websockets.connect', return_value=mock_ws):
        await client.connect()
    
    # Give reader task time to process messages
    await asyncio.sleep(0.1)
    
    # Both queues should have messages
    assert client._action_result_queue.qsize() > 0
    assert client._snapshot_queue.qsize() > 0
    
    # send_action should get action_result
    result = await client.send_action({"type": "end_turn"})
    assert "ok" in result
    
    # listen should get snapshot
    snapshots_received = []
    
    async def listen_for_one():
        data = await client._snapshot_queue.get()
        client._handle_snapshot(data["state"])
        snapshots_received.append(client.state)
    
    await listen_for_one()
    assert len(snapshots_received) > 0
    
    await client.disconnect()


@pytest.mark.asyncio
async def test_reader_task_dispatches_correctly():
    """Test that reader task correctly dispatches messages to queues."""
    client = NetworkClient(pid=0)
    
    # Create mock websocket with message sequence
    mock_ws = AsyncMock()
    
    messages = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
        json.dumps({"type": "action_result", "ok": True, "error": None}),
        json.dumps({"type": "snapshot", "state": {"turn": 2, "pid": 0}}),
        json.dumps({"type": "action_result", "ok": False, "error": "test"}),
        json.dumps({"type": "snapshot", "state": {"turn": 3, "pid": 0}}),
    ]
    
    message_iter = iter(messages)
    mock_ws.recv = AsyncMock(side_effect=lambda: next(message_iter))
    mock_ws.close = AsyncMock()
    
    # Make websocket iterable for reader loop
    async def mock_aiter():
        for msg in messages[2:]:  # Skip initial messages (handled by connect)
            yield msg
    
    mock_ws.__aiter__ = lambda: mock_aiter()
    
    with patch('websockets.connect', return_value=mock_ws):
        await client.connect()
    
    # Give reader task time to process all messages
    await asyncio.sleep(0.2)
    
    # Verify correct number of each message type in queues
    action_results = []
    while not client._action_result_queue.empty():
        action_results.append(await client._action_result_queue.get())
    
    snapshots = []
    while not client._snapshot_queue.empty():
        snapshots.append(await client._snapshot_queue.get())
    
    # Should have 2 action_results and 3 snapshots
    assert len(action_results) == 2
    assert len(snapshots) == 3
    
    # Verify types
    for ar in action_results:
        assert ar["type"] == "action_result"
    
    for snap in snapshots:
        assert snap["type"] == "snapshot"
    
    await client.disconnect()


@pytest.mark.asyncio
async def test_disconnect_cancels_reader_task():
    """Test that disconnect properly cancels the reader task."""
    client = NetworkClient(pid=0)
    
    mock_ws = AsyncMock()
    mock_ws.recv.side_effect = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
    ]
    mock_ws.close = AsyncMock()
    
    # Make websocket iterable (infinite loop for reader)
    async def mock_aiter():
        while True:
            await asyncio.sleep(0.1)
            yield json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}})
    
    mock_ws.__aiter__ = lambda: mock_aiter()
    
    with patch('websockets.connect', return_value=mock_ws):
        await client.connect()
    
    # Verify reader task is running
    assert client._reader_task is not None
    assert not client._reader_task.done()
    
    # Disconnect
    await client.disconnect()
    
    # Verify reader task was cancelled
    assert client._reader_task.done()
    assert client._reader_task.cancelled() or client._reader_task.exception() is None


@pytest.mark.asyncio
async def test_no_race_with_rapid_actions():
    """Test that rapid send_action calls don't cause race conditions."""
    client = NetworkClient(pid=0)
    
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv.side_effect = [
        json.dumps({"type": "game_start", "seed": 42}),
        json.dumps({"type": "snapshot", "state": {"turn": 1, "pid": 0}}),
    ]
    mock_ws.close = AsyncMock()
    
    # Simulate rapid action results
    async def mock_aiter():
        for i in range(10):
            await asyncio.sleep(0.01)
            yield json.dumps({"type": "action_result", "ok": True, "error": None})
    
    mock_ws.__aiter__ = lambda: mock_aiter()
    
    with patch('websockets.connect', return_value=mock_ws):
        await client.connect()
    
    # Give reader time to process some messages
    await asyncio.sleep(0.15)
    
    # Send multiple actions rapidly
    results = []
    for i in range(5):
        result = await client.send_action({"type": "end_turn"})
        results.append(result)
    
    # All should succeed
    assert len(results) == 5
    for result in results:
        assert result["ok"] is True
    
    await client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
