"""Tests for ServerOrchestrator — turn flow and action submission."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from engine_core.server_orchestrator import ServerOrchestrator
from engine_core.game_session import GameSession
from v2.core.action_result import ActionResult
from v2.core.serialization import from_dict


class TestServerOrchestrator:
    """Test suite for ServerOrchestrator turn flow."""

    def test_submit_action_end_turn_triggers_advance(self):
        """Test that end_turn from all players triggers turn advancement."""
        # Setup: 2-player game with mock components
        game = Mock()
        game.players = [
            Mock(pid=0, alive=True),
            Mock(pid=1, alive=True),
        ]
        game.turn = 1
        
        # Mock turn progression methods
        game.finish_turn = Mock()
        game.combat_phase = Mock()
        game.start_turn = Mock()
        
        # Create session with dispatcher
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        
        # Create orchestrator (no state_builder = minimal snapshots)
        orchestrator = ServerOrchestrator(session)
        
        # Player 0 ends turn
        result = orchestrator.submit_action(0, {"type": "end_turn"})
        assert result == ActionResult.OK
        
        # Turn should NOT advance yet (waiting for player 1)
        game.finish_turn.assert_not_called()
        game.combat_phase.assert_not_called()
        game.start_turn.assert_not_called()
        
        # Player 1 ends turn
        result = orchestrator.submit_action(1, {"type": "end_turn"})
        assert result == ActionResult.OK
        
        # Now turn should advance
        game.finish_turn.assert_called_once()
        game.combat_phase.assert_called_once()
        game.start_turn.assert_called_once()

    def test_pop_outbox_returns_snapshots(self):
        """Test that pop_outbox returns snapshots after turn advancement."""
        # Setup: 2-player game
        game = Mock()
        game.players = [
            Mock(pid=0, alive=True, hp=100, gold=10),
            Mock(pid=1, alive=True, hp=90, gold=15),
        ]
        game.turn = 1
        game.finish_turn = Mock()
        game.combat_phase = Mock()
        game.start_turn = Mock()
        
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Both players end turn
        orchestrator.submit_action(0, {"type": "end_turn"})
        orchestrator.submit_action(1, {"type": "end_turn"})
        
        # Pop outbox
        snapshots = orchestrator.pop_outbox()
        
        # Should have snapshots for both players
        assert len(snapshots) == 2
        assert 0 in snapshots
        assert 1 in snapshots
        
        # Verify snapshot structure (minimal snapshots)
        assert snapshots[0]["pid"] == 0
        assert snapshots[1]["pid"] == 1
        assert "turn" in snapshots[0]
        assert "alive_pids" in snapshots[0]
        
        # Outbox should be empty after pop
        snapshots_2 = orchestrator.pop_outbox()
        assert len(snapshots_2) == 0

    def test_eliminated_player_action_rejected(self):
        """Test that actions from eliminated players are rejected."""
        # Setup: 2-player game, player 1 is dead
        game = Mock()
        game.players = [
            Mock(pid=0, alive=True),
            Mock(pid=1, alive=False),  # Dead player
        ]
        
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Eliminated player tries to buy
        result = orchestrator.submit_action(1, {"type": "buy", "slot": 0})
        assert result == ActionResult.ERR_NOT_IN_PREP_PHASE
        
        # Dispatcher should not be called
        dispatcher.perform_buy_card.assert_not_called()

    def test_buy_action_delegates_to_dispatcher(self):
        """Test that buy action delegates to dispatcher correctly."""
        # Setup
        game = Mock()
        game.players = [Mock(pid=0, alive=True)]
        
        dispatcher = Mock()
        dispatcher.perform_buy_card.return_value = ActionResult.OK
        
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Submit buy action
        result = orchestrator.submit_action(0, {"type": "buy", "slot": 2})
        
        # Should delegate to dispatcher
        assert result == ActionResult.OK
        dispatcher.perform_buy_card.assert_called_once_with(0, 2)

    def test_reroll_action_delegates_to_dispatcher(self):
        """Test that reroll action delegates to dispatcher correctly."""
        # Setup
        game = Mock()
        game.players = [Mock(pid=0, alive=True)]
        
        dispatcher = Mock()
        dispatcher.perform_reroll.return_value = True
        
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Submit reroll action
        result = orchestrator.submit_action(0, {"type": "reroll"})
        
        # Should delegate to dispatcher
        assert result == ActionResult.OK
        dispatcher.perform_reroll.assert_called_once_with(0)

    def test_place_action_converts_coord_list_to_tuple(self):
        """Test that place action converts coord list to tuple."""
        # Setup
        game = Mock()
        game.players = [Mock(pid=0, alive=True)]
        
        dispatcher = Mock()
        dispatcher.perform_placement.return_value = ActionResult.OK
        
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Submit place action with coord as list (from serialization)
        result = orchestrator.submit_action(0, {
            "type": "place",
            "hand_index": 1,
            "coord": [2, -1],  # List from JSON
            "rotation": 3
        })
        
        # Should convert to tuple and delegate
        assert result == ActionResult.OK
        dispatcher.perform_placement.assert_called_once_with(0, 1, (2, -1), 3)

    def test_unknown_action_type_returns_error(self):
        """Test that unknown action types return error."""
        # Setup
        game = Mock()
        game.players = [Mock(pid=0, alive=True)]
        
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Submit unknown action
        result = orchestrator.submit_action(0, {"type": "unknown_action"})
        
        # Should return error
        assert result == ActionResult.ERR_ENGINE_EXCEPTION

    def test_invalid_pid_returns_error(self):
        """Test that actions from invalid pid return error."""
        # Setup
        game = Mock()
        game.players = [Mock(pid=0, alive=True)]
        
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        orchestrator = ServerOrchestrator(session)
        
        # Submit action from non-existent player
        result = orchestrator.submit_action(999, {"type": "buy", "slot": 0})
        
        # Should return error
        assert result == ActionResult.ERR_ENGINE_EXCEPTION

    def test_snapshots_readable_with_from_dict(self):
        """Test that full snapshots (with GameState builder) can be deserialized with from_dict."""
        # Setup: 2-player game
        game = Mock()
        game.players = [
            Mock(pid=0, alive=True, hp=100, gold=10),
            Mock(pid=1, alive=True, hp=90, gold=15),
        ]
        game.turn = 1
        game.finish_turn = Mock()
        game.combat_phase = Mock()
        game.start_turn = Mock()
        
        dispatcher = Mock()
        session = GameSession(game, dispatcher)
        
        # Create a minimal valid PublicState dict structure
        # This matches the structure expected by from_dict()
        valid_state_dict = {
            "turn": 2,
            "alive_pids": [0, 1],
            "pairings": [[0, 1]],
            "lobby_players": [],
            "endgame_stats": [],
            "phase": "STATE_PREPARATION",
            "view_index": 0,
            "place_locked": False,
            "active_player": {
                "index": 0,
                "pid": 0,
                "display_name": "P0",
                "strategy": "unknown",
                "hp": 100,
                "gold": 10,
                "alive": True,
                "turns_played": 0,
                "stats": {},
                "has_catalyst": False,
                "has_eclipse": False,
                "shop": {"slots": [None, None, None, None, None], "is_locked": False, "rarity_probabilities": {}},
                "hand": {"slots": [None, None, None, None, None, None]},
                "hud": {
                    "hp": 100,
                    "gold": 10,
                    "win_streak": 0,
                    "total_pts": 0,
                    "turn": 2,
                    "next_gold": 3,
                    "interest_multiplier": 1.0,
                },
                "combat": {
                    "last_results": [],
                    "logs": [],
                    "passive_feed": []
                },
                "synergy": {
                    "groups": [],
                    "total": 0,
                    "passive_feed": [],
                    "active_effects": []
                },
                "board_cards": {},
                "board_rotations": {},
                "board_card_info": {},
                "eliminated_coords": [],
                "adjacency_pairs": [],
                "copies_by_name": {},
                "copy_milestones": [],
                "prefix_bonus": 0,
                "shop_card_info": {},
                "hand_card_info": {}
            }
        }
        
        # Mock GameState builder
        mock_state_builder = Mock()
        mock_state_builder.view_index = 0
        
        # Mock get_public_state to return a mock PublicState
        mock_public_state = Mock()
        mock_state_builder.get_public_state.return_value = mock_public_state
        
        orchestrator = ServerOrchestrator(session, state_builder=mock_state_builder)
        
        with patch("v2.core.serialization.to_dict") as mock_to_dict:
            # Return valid state dicts for both players
            mock_to_dict.side_effect = [
                {**valid_state_dict, "active_player": {**valid_state_dict["active_player"], "pid": 0}},
                {**valid_state_dict, "active_player": {**valid_state_dict["active_player"], "pid": 1}}
            ]
            
            # Both players end turn
            orchestrator.submit_action(0, {"type": "end_turn"})
            orchestrator.submit_action(1, {"type": "end_turn"})
            
            # Pop outbox
            snapshots = orchestrator.pop_outbox()
            
            # Verify snapshots can be deserialized
            for pid, snapshot_dict in snapshots.items():
                # This should not raise an exception
                public_state = from_dict(snapshot_dict)
                assert public_state.turn == 2
                assert pid in [0, 1]
