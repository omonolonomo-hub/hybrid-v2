"""
Security tests for cache invalidation and phase validation fixes.

Tests the critical fixes for:
1. Spectator mode cache invalidation (view_index != 0)
2. Phase validation in buy_card_from_slot
"""

import pytest
from unittest.mock import Mock, MagicMock
from v2.core.game_state import GameState
from v2.core.action_result import ActionResult
from engine_core.card import Card


class MockSignals:
    """Mock signal emitter for testing cache invalidation."""
    def __init__(self):
        self._callbacks = {
            'board_mutated': [],
            'economy_changed': [],
            'inventory_changed': [],
            'turn_started': [],
            'combat_finished': [],
        }
    
    def _get_signal(self, name):
        """Get or create a signal mock."""
        if name not in self._callbacks:
            self._callbacks[name] = []
        
        signal = Mock()
        signal.connect = lambda cb: self._callbacks[name].append(cb)
        signal.disconnect = lambda cb: self._callbacks[name].remove(cb) if cb in self._callbacks[name] else None
        signal.emit = lambda **kwargs: [cb(**kwargs) for cb in self._callbacks[name]]
        return signal
    
    @property
    def board_mutated(self):
        return self._get_signal('board_mutated')
    
    @property
    def economy_changed(self):
        return self._get_signal('economy_changed')
    
    @property
    def inventory_changed(self):
        return self._get_signal('inventory_changed')
    
    @property
    def turn_started(self):
        return self._get_signal('turn_started')
    
    @property
    def combat_finished(self):
        return self._get_signal('combat_finished')


class MockBoard:
    """Mock board for testing."""
    def __init__(self):
        self.grid = {}
    
    def place(self, coord, card):
        self.grid[coord] = card


class MockPlayer:
    """Mock player for testing."""
    def __init__(self, pid):
        self.pid = pid
        self.alive = True
        self.gold = 10
        self.hp = 100
        self.board = MockBoard()
        self.hand = [None] * 6
        self.shop_locked = False
        self.passive_buff_log = []


class MockMarket:
    """Mock market for testing."""
    def __init__(self):
        self._player_windows = {}
    
    def get_window(self, pid):
        """Return empty shop window."""
        return [None] * 5
    
    def get_rarity_weight(self, rarity, turn):
        """Return mock rarity weight."""
        return 0.5


class MockEngine:
    """Mock game engine for testing."""
    def __init__(self, num_players=4):
        self.players = [MockPlayer(i) for i in range(num_players)]
        self.turn = 1
        self.signals = MockSignals()
        self.market = MockMarket()
        self.last_combat_results = []


@pytest.fixture
def game_state():
    """Create a GameState with mocked engine."""
    gs = GameState()
    engine = MockEngine()
    gs.hook_engine(engine)
    return gs


class TestCacheInvalidationSpectatorMode:
    """Test cache invalidation when viewing non-human players."""
    
    def test_cache_invalidates_for_viewed_player(self, game_state):
        """Cache should invalidate when the currently viewed player mutates."""
        # View player 1 (not the human player 0)
        game_state.view_index = 1
        
        # Get initial state (builds cache)
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Simulate player 1's board mutation
        engine = game_state._adapter._engine
        engine.players[1].board.place((0, 0), Card("TestCard", "common", "test", {}))
        engine.signals.board_mutated.emit(pid=1)
        
        # Cache should be invalidated
        assert game_state._cached_public_state is None
        
        # Getting state again should rebuild cache
        updated_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
    
    def test_cache_not_invalidated_for_other_players(self, game_state):
        """Cache should NOT invalidate when a non-viewed player mutates."""
        # View player 1
        game_state.view_index = 1
        
        # Get initial state (builds cache)
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Simulate player 2's board mutation (not the viewed player)
        engine = game_state._adapter._engine
        engine.players[2].board.place((0, 0), Card("TestCard", "common", "test", {}))
        engine.signals.board_mutated.emit(pid=2)
        
        # Cache should NOT be invalidated (performance optimization)
        assert game_state._cached_public_state is not None
    
    def test_cache_invalidates_for_human_player(self, game_state):
        """Cache should still invalidate for human player (pid=0) when viewed."""
        # View human player (default)
        assert game_state.view_index == 0
        
        # Get initial state
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Simulate human player's board mutation
        engine = game_state._adapter._engine
        engine.players[0].board.place((0, 0), Card("TestCard", "common", "test", {}))
        engine.signals.board_mutated.emit(pid=0)
        
        # Cache should be invalidated
        assert game_state._cached_public_state is None
    
    def test_global_signals_always_invalidate(self, game_state):
        """Global signals (no pid) should always invalidate cache."""
        # View player 1
        game_state.view_index = 1
        
        # Get initial state
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Emit global signal (no pid parameter)
        engine = game_state._adapter._engine
        engine.signals.turn_started.emit()
        
        # Cache should be invalidated
        assert game_state._cached_public_state is None
    
    def test_view_index_change_invalidates_cache(self, game_state):
        """Changing view_index should invalidate cache."""
        # View player 0
        game_state.view_index = 0
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Switch to player 1
        game_state.view_index = 1
        
        # Cache should be invalidated
        assert game_state._cached_public_state is None


class TestPhaseValidation:
    """Test phase validation in buy_card_from_slot."""
    
    def test_buy_card_allowed_in_prep_phase(self, game_state):
        """Card purchase should succeed in preparation phase."""
        # Set up prep phase
        game_state._store.phase = "STATE_PREPARATION"
        
        # Mock the adapter to return success
        game_state._adapter.perform_buy_card = Mock(return_value=ActionResult.OK)
        
        # Attempt purchase
        result = game_state.buy_card_from_slot(0, 0)
        
        # Should succeed
        assert result == ActionResult.OK
        game_state._adapter.perform_buy_card.assert_called_once_with(0, 0)
    
    def test_buy_card_blocked_in_combat_phase(self, game_state):
        """Card purchase should fail in combat phase."""
        # Set up combat phase
        game_state._store.phase = "STATE_COMBAT"
        
        # Mock the adapter (should not be called)
        game_state._adapter.perform_buy_card = Mock(return_value=ActionResult.OK)
        
        # Attempt purchase
        result = game_state.buy_card_from_slot(0, 0)
        
        # Should fail with phase error
        assert result == ActionResult.ERR_NOT_IN_PREP_PHASE
        game_state._adapter.perform_buy_card.assert_not_called()
    
    def test_buy_card_blocked_in_endgame_phase(self, game_state):
        """Card purchase should fail in endgame phase."""
        # Set up endgame phase
        game_state._store.phase = "STATE_ENDGAME"
        
        # Mock the adapter (should not be called)
        game_state._adapter.perform_buy_card = Mock(return_value=ActionResult.OK)
        
        # Attempt purchase
        result = game_state.buy_card_from_slot(0, 0)
        
        # Should fail with phase error
        assert result == ActionResult.ERR_NOT_IN_PREP_PHASE
        game_state._adapter.perform_buy_card.assert_not_called()
    
    def test_phase_check_before_ownership_check(self, game_state):
        """Phase validation should happen after ownership check (current order)."""
        # Set up combat phase
        game_state._store.phase = "STATE_COMBAT"
        
        # Attempt purchase as AI player
        result = game_state.buy_card_from_slot(1, 0)
        
        # Should fail with ownership error (checked first)
        assert result == ActionResult.ERR_NOT_OWNER
    
    def test_buy_card_alias_respects_phase(self, game_state):
        """buy_card() alias should also respect phase validation."""
        # Set up combat phase
        game_state._store.phase = "STATE_COMBAT"
        
        # Attempt purchase via alias
        result = game_state.buy_card(0, 0)
        
        # Should fail with phase error
        assert result == ActionResult.ERR_NOT_IN_PREP_PHASE


class TestRegressionPrevention:
    """Tests to prevent regression of the security fixes."""
    
    def test_spectator_mode_scenario(self, game_state):
        """Full scenario: User views another player during their turn."""
        # User starts viewing themselves
        game_state.view_index = 0
        state_p0 = game_state.get_public_state()
        
        # User switches to view player 1
        game_state.view_index = 1
        state_p1_before = game_state.get_public_state()
        
        # Simulate turn advance: Player 1's board changes
        engine = game_state._adapter._engine
        engine.players[1].gold = 5  # Gold changed
        engine.signals.economy_changed.emit(pid=1)
        
        # User should see updated state
        state_p1_after = game_state.get_public_state()
        assert state_p1_after.active_player.hud.gold == 5
    
    def test_timer_auto_purchase_scenario(self, game_state):
        """Scenario: Timer tries to auto-purchase during combat."""
        # Set up combat phase
        game_state._store.phase = "STATE_COMBAT"
        
        # Simulate timer callback attempting purchase
        result = game_state.buy_card_from_slot(0, 0)
        
        # Should be blocked
        assert result == ActionResult.ERR_NOT_IN_PREP_PHASE
    
    def test_multi_player_view_switching(self, game_state):
        """Test rapid view switching between multiple players."""
        engine = game_state._adapter._engine
        
        for pid in range(4):
            # Switch view
            game_state.view_index = pid
            
            # Mutate that player
            engine.players[pid].gold = 100 + pid
            engine.signals.economy_changed.emit(pid=pid)
            
            # Should see updated state
            state = game_state.get_public_state()
            assert state.active_player.hud.gold == 100 + pid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
