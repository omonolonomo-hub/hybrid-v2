"""
Test Board mutation callback integration with GameState.

Verifies that direct Board.place() and Board.remove() calls trigger
cache invalidation through the mutation callback mechanism.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engine_core.game_factory import build_game
from v2.core.game_state import GameState


def test_board_mutation_callback_integration():
    """Test that Board._mutation_callback is properly hooked to GameState."""
    print("\n=== Testing Board Mutation Callback Integration ===\n")
    
    # Create game and GameState
    strategies = ["random", "random"]
    game = build_game(strategies)
    game_state = GameState()
    game_state.hook_engine(game)
    
    # Verify callbacks are attached
    for player in game.players:
        board = player.board
        assert board._mutation_callback is not None, \
            f"Player {player.pid} board callback not attached"
        print(f"✓ Player {player.pid} board callback attached")
    
    # Get initial state
    initial_state = game_state.get_public_state()
    initial_board_count = len(initial_state.active_player.board_cards)
    print(f"\n✓ Initial board card count: {initial_board_count}")
    
    # Direct board mutation (bypassing GameState API)
    player = game.players[0]
    board = player.board
    
    # Add a card directly to board
    # Use a card from the player's hand if available, or create from market
    if player.hand:
        test_card = player.hand[0]
        player.hand.pop(0)
    else:
        # Get a card from market
        market = game.market
        test_card = market.draw_card()
    
    test_coord = (0, 0)
    
    print(f"\n→ Directly calling Board.place({test_coord}, {test_card.name})")
    board.place(test_coord, test_card)
    
    # Verify cache was invalidated
    new_state = game_state.get_public_state()
    new_board_count = len(new_state.active_player.board_cards)
    
    assert new_board_count == initial_board_count + 1, \
        f"Board count not updated: expected {initial_board_count + 1}, got {new_board_count}"
    print(f"✓ Board count updated: {initial_board_count} → {new_board_count}")
    
    assert test_coord in new_state.active_player.board_cards, \
        f"New card not in board_cards: {test_coord}"
    print(f"✓ New card visible in PublicState at {test_coord}")
    
    # Test direct removal
    print(f"\n→ Directly calling Board.remove({test_coord})")
    board.remove(test_coord)
    
    final_state = game_state.get_public_state()
    final_board_count = len(final_state.active_player.board_cards)
    
    assert final_board_count == initial_board_count, \
        f"Board count not restored: expected {initial_board_count}, got {final_board_count}"
    print(f"✓ Board count restored: {new_board_count} → {final_board_count}")
    
    assert test_coord not in final_state.active_player.board_cards, \
        f"Removed card still in board_cards: {test_coord}"
    print(f"✓ Removed card no longer in PublicState")
    
    # Test cleanup
    print("\n→ Testing cleanup()")
    game_state.cleanup()
    
    for player in game.players:
        board = player.board
        assert board._mutation_callback is None, \
            f"Player {player.pid} board callback not cleaned up"
        print(f"✓ Player {player.pid} board callback cleaned up")
    
    print("\n=== All Tests Passed ✓ ===\n")


if __name__ == "__main__":
    test_board_mutation_callback_integration()
