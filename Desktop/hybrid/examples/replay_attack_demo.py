"""Demonstration of replay attack protection.

This example shows:
1. How sequence numbers protect against replay attacks
2. What happens when a replay attack is attempted
3. How to properly implement sequence numbers in clients
"""

import asyncio
from engine_core.game import Game
from engine_core.player import Player
from engine_core.game_session import GameSession
from engine_core.server_orchestrator import ServerOrchestrator
from engine_core.network_server import NetworkServer
from engine_core.network_client import NetworkClient


async def demo_replay_attack_protection():
    """Demonstrate replay attack protection with sequence numbers."""
    
    print("=" * 70)
    print("REPLAY ATTACK PROTECTION DEMO")
    print("=" * 70)
    
    # Setup: Create a 2-player game
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    
    print("\n1. NORMAL OPERATION (with sequence numbers)")
    print("-" * 70)
    
    # Player 0 sends end_turn with seq=1
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    print(f"Player 0 end_turn (seq=1): {result}")
    print(f"  → Last seq for player 0: {session.get_last_seq(0)}")
    
    # Player 1 sends end_turn with seq=1
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 1})
    print(f"Player 1 end_turn (seq=1): {result}")
    print(f"  → Last seq for player 1: {session.get_last_seq(1)}")
    print(f"  → Turn advanced! Ready set cleared.")
    
    print("\n2. REPLAY ATTACK ATTEMPT (duplicate sequence number)")
    print("-" * 70)
    
    # Malicious client tries to replay player 0's action
    print("Attacker replays player 0's end_turn with seq=1...")
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    print(f"Result: {result}")
    print(f"  → REJECTED! Sequence number 1 already seen (last_seq=1)")
    print(f"  → Last seq for player 0 unchanged: {session.get_last_seq(0)}")
    
    print("\n3. OUT-OF-ORDER ATTACK (lower sequence number)")
    print("-" * 70)
    
    # Player 0 sends valid seq=2
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 2})
    print(f"Player 0 end_turn (seq=2): {result}")
    print(f"  → Last seq for player 0: {session.get_last_seq(0)}")
    
    # Attacker tries to send seq=1 (lower than last seen)
    print("\nAttacker tries to send seq=1 (lower than last_seq=2)...")
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 1})
    print(f"Result: {result}")
    print(f"  → REJECTED! Sequence number 1 < last_seq=2")
    
    print("\n4. VALID PROGRESSION (increasing sequence numbers)")
    print("-" * 70)
    
    # Player 1 sends seq=2
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 2})
    print(f"Player 1 end_turn (seq=2): {result}")
    print(f"  → Turn advanced!")
    
    # Next turn - both players use seq=3
    result = orchestrator.submit_action(0, {"type": "end_turn", "seq": 3})
    print(f"Player 0 end_turn (seq=3): {result}")
    
    result = orchestrator.submit_action(1, {"type": "end_turn", "seq": 3})
    print(f"Player 1 end_turn (seq=3): {result}")
    print(f"  → Turn advanced!")
    
    print("\n5. BACKWARD COMPATIBILITY (no sequence numbers)")
    print("-" * 70)
    
    # Create new session for clean test
    game2 = Game(players=[Player(pid=0), Player(pid=1)])
    session2 = GameSession(game2)
    orchestrator2 = ServerOrchestrator(session2)
    
    # Actions without seq still work (no replay protection)
    result = orchestrator2.submit_action(0, {"type": "end_turn"})
    print(f"Player 0 end_turn (no seq): {result}")
    print(f"  → Last seq for player 0: {session2.get_last_seq(0)} (unchanged)")
    
    # Can even call multiple times (idempotent without seq)
    result = orchestrator2.submit_action(0, {"type": "end_turn"})
    print(f"Player 0 end_turn again (no seq): {result}")
    print(f"  → Still works (no replay protection without seq)")
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


async def demo_network_client_with_seq():
    """Demonstrate NetworkClient with automatic sequence numbers."""
    
    print("\n" + "=" * 70)
    print("NETWORK CLIENT WITH SEQUENCE NUMBERS")
    print("=" * 70)
    
    # Setup server
    game = Game(players=[Player(pid=0), Player(pid=1)])
    session = GameSession(game)
    orchestrator = ServerOrchestrator(session)
    server = NetworkServer(orchestrator, host="localhost", port=8766)
    
    # Start server in background
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # Let server start
    
    try:
        print("\n1. CLIENT WITH SEQUENCE NUMBERS (default)")
        print("-" * 70)
        
        # Create client with seq enabled (default)
        client0 = NetworkClient(pid=0, uri="ws://localhost:8766", use_seq=True)
        await client0.connect()
        print(f"Client 0 connected (use_seq=True)")
        
        # Send action - seq is automatically added
        result = await client0.send_action({"type": "end_turn"})
        print(f"Sent end_turn: {result}")
        print(f"  → Sequence number automatically added (seq=1)")
        
        # Send another action - seq increments
        result = await client0.send_action({"type": "end_turn"})
        print(f"Sent end_turn again: {result}")
        print(f"  → Sequence number automatically incremented (seq=2)")
        
        await client0.disconnect()
        
        print("\n2. CLIENT WITHOUT SEQUENCE NUMBERS (backward compatible)")
        print("-" * 70)
        
        # Create client with seq disabled
        client1 = NetworkClient(pid=1, uri="ws://localhost:8766", use_seq=False)
        await client1.connect()
        print(f"Client 1 connected (use_seq=False)")
        
        # Send action - no seq added
        result = await client1.send_action({"type": "end_turn"})
        print(f"Sent end_turn: {result}")
        print(f"  → No sequence number added (backward compatible)")
        
        await client1.disconnect()
        
        print("\n" + "=" * 70)
        print("NETWORK DEMO COMPLETE")
        print("=" * 70)
    
    finally:
        # Cleanup
        await server.stop()
        await server_task


if __name__ == "__main__":
    print("\nRunning replay attack protection demos...\n")
    
    # Run local demo (no network)
    asyncio.run(demo_replay_attack_protection())
    
    # Run network demo
    asyncio.run(demo_network_client_with_seq())
    
    print("\n✅ All demos completed successfully!")
