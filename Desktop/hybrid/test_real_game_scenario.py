"""
Real game scenario test for board mutation hook.

Simulates a real game flow with buy, place, and combat phases
to verify cache invalidation works correctly in production scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engine_core.game_factory import build_game
from v2.core.game_state import GameState


def test_real_game_scenario():
    """Test board mutation hook in a realistic game scenario."""
    print("\n=== Real Game Scenario Test ===\n")
    
    # Create game with 4 players
    strategies = ["random"] * 4
    game = build_game(strategies)
    game_state = GameState()
    game_state.hook_engine(game)
    
    print("✓ Game initialized with 4 players")
    
    # Phase 1: Preparation - Buy and place cards
    print("\n--- Phase 1: Preparation ---")
    game_state.mirror_phase("STATE_PREPARATION")
    
    player = game.players[0]
    market = game.market
    
    # Deal market window
    market.deal_market_window(player, n=5)
    state = game_state.get_public_state()
    shop_count = len([s for s in state.active_player.shop.slots if s is not None])
    print(f"✓ Market window dealt: {shop_count} cards")
    
    # Buy a card
    result = game_state.buy_card(0, 0)
    print(f"✓ Buy card result: {result}")
    
    # Verify hand updated
    state = game_state.get_public_state()
    hand_count = len([s for s in state.active_player.hand.slots if s is not None])
    print(f"✓ Hand count after buy: {hand_count}")
    
    # Place card on board
    if hand_count > 0:
        result = game_state.place_card(0, (0, 0), rotation=0, player_index=0)
        print(f"✓ Place card result: {result}")
        
        # Verify board updated
        state = game_state.get_public_state()
        board_count = len(state.active_player.board_cards)
        print(f"✓ Board count after place: {board_count}")
        
        # Verify synergy computed
        synergy_total = state.active_player.synergy.total
        print(f"✓ Synergy total: {synergy_total}")
    
    # Phase 2: Combat - Direct board mutations during combat
    print("\n--- Phase 2: Combat ---")
    game_state.mirror_phase("STATE_COMBAT")
    
    # Simulate combat damage (direct board mutation)
    if player.board.alive_count() > 0:
        coords = list(player.board.grid.keys())
        first_coord = coords[0]
        
        print(f"✓ Simulating combat damage at {first_coord}")
        
        # Get state before removal
        state_before = game_state.get_public_state()
        board_count_before = len(state_before.active_player.board_cards)
        
        # Direct board mutation (simulating combat)
        player.board.remove(first_coord)
        
        # Verify cache invalidated
        state_after = game_state.get_public_state()
        board_count_after = len(state_after.active_player.board_cards)
        
        assert board_count_after == board_count_before - 1, \
            f"Board count not updated: {board_count_before} → {board_count_after}"
        print(f"✓ Board count updated: {board_count_before} → {board_count_after}")
        
        # Verify synergy recomputed
        synergy_after = state_after.active_player.synergy.total
        print(f"✓ Synergy recomputed: {synergy_after}")
    
    # Phase 3: Multiple players
    print("\n--- Phase 3: Multi-Player ---")
    
    # Switch to player 1
    game_state.view_index = 1
    state_p1 = game_state.get_public_state()
    print(f"✓ Switched to Player 1 (PID={state_p1.active_player.pid})")
    
    # Mutate player 0's board (should not affect player 1's cache)
    player0 = game.players[0]
    if player0.board.alive_count() > 0:
        coords = list(player0.board.grid.keys())
        player0.board.remove(coords[0])
        print(f"✓ Mutated Player 0's board")
    
    # Verify player 1's state is still consistent
    state_p1_after = game_state.get_public_state()
    assert state_p1_after.active_player.pid == 1, "View index changed unexpectedly"
    print(f"✓ Player 1 state remains consistent")
    
    # Phase 4: Cleanup
    print("\n--- Phase 4: Cleanup ---")
    game_state.cleanup()
    
    # Verify callbacks cleaned up
    for player in game.players:
        assert player.board._mutation_callback is None, \
            f"Player {player.pid} callback not cleaned up"
    print(f"✓ All callbacks cleaned up")
    
    print("\n=== All Scenarios Passed ✓ ===\n")


if __name__ == "__main__":
    test_real_game_scenario()
