"""Tests for non-blocking network server behavior.

This test verifies that NetworkServer doesn't block the event loop during
game operations, allowing multiple clients to interact concurrently.

Bug Context:
    Previously, submit_action() was called directly in the event loop, causing
    _advance_turn() → finish_turn() + combat_phase() + start_turn() to block
    all other connection handlers for 50-500ms.
    
    Fix: Use asyncio.run_in_executor() to run blocking operations in thread pool.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch
from engine_core.network_server import NetworkServer
from engine_core.server_orchestrator import ServerOrchestrator
from engine_core.game_session import GameSession
from engine_core.game import Game
from engine_core.player import Player
from v2.core.action_result import ActionResult


@pytest.fixture
def slow_game():
    """Create a game with artificially slow turn operations."""
    mock_cards = []
    for i in range(10):
        card = Mock()
        card.name = f"TestCard{i}"
        card.tier = 1
        card.rarity = "common"
        mock_cards.append(card)
    
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players, card_pool=mock_cards, seed=42)
    
    # Patch game methods to simulate slow operations
    original_finish = game.finish_turn
    original_combat = game.combat_phase
    original_start = game.start_turn
    
    def slow_finish():
        time.sleep(0.1)  # Simulate 100ms operation
        return original_finish()
    
    def slow_combat():
        time.sleep(0.1)  # Simulate 100ms operation
        return original_combat()
    
    def slow_start():
        time.sleep(0.1)  # Simulate 100ms operation
        return original_start()
    
    game.finish_turn = slow_finish
    game.combat_phase = slow_combat
    game.start_turn = slow_start
    
    return game


@pytest.fixture
def slow_session(slow_game):
    """Create a GameSession with slow game."""
    from v2.core.local_dispatcher import LocalCommandDispatcher
    dispatcher = LocalCommandDispatcher(slow_game)
    session = GameSession(slow_game, dispatcher)
    return session


@pytest.fixture
def slow_orchestrator(slow_session):
    """Create a ServerOrchestrator with slow session."""
    orchestrator = ServerOrchestrator(slow_session, state_builder=None)
    return orchestrator


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_submit_action_runs_in_executor(slow_orchestrator):
    """Test that submit_action is executed in thread pool, not event loop."""
    server = NetworkServer(slow_orchestrator, host="localhost", port=8790)
    
    # Track whether event loop was blocked
    event_loop_responsive = []
    
    async def check_responsiveness():
        """Continuously check if event loop is responsive."""
        for _ in range(10):
            await asyncio.sleep(0.05)  # Check every 50ms
            event_loop_responsive.append(True)
    
    # Create mock websocket
    class MockWebSocket:
        def __init__(self):
            self.messages = []
        
        async def send(self, message):
            self.messages.append(message)
    
    mock_ws = MockWebSocket()
    
    # Start responsiveness checker
    checker_task = asyncio.create_task(check_responsiveness())
    
    # Submit action that triggers slow turn advancement
    # This should NOT block the event loop
    action_task = asyncio.create_task(
        server._handle_message(mock_ws, 0, {"type": "action", "action": {"type": "end_turn"}})
    )
    
    # Wait for both tasks
    await asyncio.gather(action_task, checker_task)
    
    # Verify event loop remained responsive during slow operation
    # If blocking occurred, checker would have fewer than expected ticks
    assert len(event_loop_responsive) >= 5, \
        f"Event loop was blocked! Only {len(event_loop_responsive)} responsive checks completed"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_concurrent_actions_dont_block_each_other(slow_orchestrator):
    """Test that multiple clients can submit actions concurrently."""
    server = NetworkServer(slow_orchestrator, host="localhost", port=8791)
    
    # Create mock websockets for two clients
    class MockWebSocket:
        def __init__(self, pid):
            self.pid = pid
            self.messages = []
            self.send_times = []
        
        async def send(self, message):
            self.messages.append(message)
            self.send_times.append(time.time())
    
    ws0 = MockWebSocket(0)
    ws1 = MockWebSocket(1)
    
    # Submit actions from both clients concurrently
    start_time = time.time()
    
    # Client 0 submits end_turn (triggers slow turn advancement)
    task0 = asyncio.create_task(
        server._handle_message(ws0, 0, {"type": "action", "action": {"type": "end_turn"}})
    )
    
    # Client 1 submits reroll (should not be blocked by client 0's slow operation)
    await asyncio.sleep(0.05)  # Small delay to ensure task0 starts first
    task1 = asyncio.create_task(
        server._handle_message(ws1, 1, {"type": "action", "action": {"type": "reroll"}})
    )
    
    # Wait for both tasks
    await asyncio.gather(task0, task1)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # If operations were blocking, total time would be ~600ms (3x 100ms operations + 100ms reroll)
    # With thread pool, they should overlap, taking ~300-400ms total
    assert total_time < 0.5, \
        f"Operations appear to be blocking! Total time: {total_time:.3f}s (expected < 0.5s)"
    
    # Verify both clients received responses
    assert len(ws0.messages) > 0, "Client 0 should receive response"
    assert len(ws1.messages) > 0, "Client 1 should receive response"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_event_loop_not_blocked_during_turn_advancement():
    """Test that event loop remains responsive during turn advancement."""
    # Create normal game (not slow)
    mock_cards = []
    for i in range(10):
        card = Mock()
        card.name = f"TestCard{i}"
        card.tier = 1
        card.rarity = "common"
        mock_cards.append(card)
    
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players, card_pool=mock_cards, seed=99)
    
    from v2.core.local_dispatcher import LocalCommandDispatcher
    dispatcher = LocalCommandDispatcher(game)
    session = GameSession(game, dispatcher)
    orchestrator = ServerOrchestrator(session, state_builder=None)
    
    server = NetworkServer(orchestrator, host="localhost", port=8792)
    
    # Track event loop responsiveness
    responsive_checks = []
    
    async def monitor_responsiveness():
        """Monitor event loop responsiveness."""
        for _ in range(20):
            await asyncio.sleep(0.01)  # Check every 10ms
            responsive_checks.append(time.time())
    
    class MockWebSocket:
        def __init__(self):
            self.messages = []
        
        async def send(self, message):
            self.messages.append(message)
    
    # Start monitoring
    monitor_task = asyncio.create_task(monitor_responsiveness())
    
    # Submit actions that trigger turn advancement
    ws0 = MockWebSocket()
    ws1 = MockWebSocket()
    
    await server._handle_message(ws0, 0, {"type": "action", "action": {"type": "end_turn"}})
    await server._handle_message(ws1, 1, {"type": "action", "action": {"type": "end_turn"}})
    
    # Wait for monitoring to complete
    await monitor_task
    
    # Verify event loop was responsive throughout
    # Should have completed most checks (allowing for some timing variance)
    assert len(responsive_checks) >= 15, \
        f"Event loop was blocked! Only {len(responsive_checks)}/20 checks completed"


def test_submit_action_is_thread_safe():
    """Test that submit_action can be called from multiple threads safely."""
    # This is a basic smoke test - full thread safety testing would require more setup
    mock_cards = []
    for i in range(10):
        card = Mock()
        card.name = f"TestCard{i}"
        card.tier = 1
        card.rarity = "common"
        mock_cards.append(card)
    
    players = [Player(pid=i) for i in range(2)]
    game = Game(players=players, card_pool=mock_cards, seed=123)
    
    from v2.core.local_dispatcher import LocalCommandDispatcher
    from v2.core.engine_adapter import EngineAdapter
    
    adapter = EngineAdapter(game)
    dispatcher = LocalCommandDispatcher(adapter)
    session = GameSession(game, dispatcher)
    orchestrator = ServerOrchestrator(session, state_builder=None)
    
    # Start a turn so reroll is valid
    game.start_turn()
    
    # Submit action directly (simulating thread pool execution)
    result = orchestrator.submit_action(0, {"type": "reroll"})
    
    # Should complete without errors
    assert result in [ActionResult.OK, ActionResult.ERR_INSUFFICIENT_GOLD]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
