"""
Preservation Unit Tests: ShopController.handle_phase_change() Successful Transitions

This test suite captures baseline behavior for successful phase transitions that must
be preserved after fixing Bug 4 (non-atomic phase transitions).

IMPORTANT: Follow observation-first methodology.
- These tests run on UNFIXED code
- They capture observed behavior patterns from Preservation Requirements
- EXPECTED OUTCOME: Tests PASS (confirms baseline behavior to preserve)

Requirements: 3.10, 3.11, 3.12
"""

import pytest
from unittest.mock import Mock
from v2.core.shop_controller import ShopController
from v2.core.game_state import GameState


class MockSignals:
    """Mock signal emitter for testing."""
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
        signal._observers = self._callbacks[name]
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
        self.has_catalyst = False
        self.has_eclipse = False
    
    def place(self, coord, card):
        self.grid[coord] = card


class MockEconomy:
    """Mock economy for testing."""
    def calculate_total_next_income(self, win_streak, hp):
        return 3


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
        self.win_streak = 0
        self.total_pts = 0
        self.interest_multiplier = 1.0
        self.economy = MockEconomy()
        self.turns_played = 0
        self.stats = {}
        self.strategy = "test"
        self.copies = {}
        self.copy_applied = {}


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
    
    def get_turn(self):
        return self.turn
    
    def get_player(self, pid):
        return self.players[pid] if 0 <= pid < len(self.players) else None
    
    def get_alive_players(self):
        return [p for p in self.players if p.alive]
    
    def get_all_players(self):
        return self.players
    
    def get_player_hp(self, pid):
        return self.players[pid].hp if 0 <= pid < len(self.players) else 0
    
    def get_player_gold(self, pid):
        return self.players[pid].gold if 0 <= pid < len(self.players) else 0
    
    def get_shop_window(self, pid):
        return [None] * 5
    
    def get_hand(self, pid):
        return [None] * 6
    
    def get_passive_buff_log(self, pid):
        return []
    
    def get_last_results(self):
        return []
    
    def is_shop_locked(self, pid):
        return False
    
    def get_rarity_weight(self, rarity, turn):
        return 0.5
    
    def get_eliminated_coords(self, pid):
        return []
    
    def get_market(self):
        return self.market
    
    def start_turn(self):
        """Mock start_turn."""
        pass
    
    def get_alive_pids(self):
        """Return list of alive player IDs."""
        return [p.pid for p in self.players if p.alive]


@pytest.fixture
def game_state():
    """Create a GameState with mocked engine."""
    gs = GameState()
    engine = MockEngine()
    gs.hook_engine(engine)
    return gs


@pytest.fixture
def shop_controller(game_state):
    """Create a ShopController with mocked GameState."""
    return ShopController(game_state)


class TestBug4PreservationPhaseTransitions:
    """
    Preservation Tests: Successful Phase Transitions
    
    Property 2: Preservation - Successful Phase Transitions
    
    These tests capture baseline behavior that must be preserved after fixing Bug 4.
    They run on UNFIXED code and should PASS to confirm what needs to be preserved.
    
    Requirements: 3.10, 3.11, 3.12
    """
    
    def test_successful_state_preparation_transition_executes_sequence(self, shop_controller, game_state):
        """
        Test 1: Successful STATE_PREPARATION transition executes sequence correctly.
        
        Requirement 3.10: When phase transitions complete successfully without exceptions,
        the system SHALL CONTINUE TO execute mirror_phase() → cleanup_dead_cards() →
        start_turn() → reset_turn() in sequence.
        
        EXPECTED OUTCOME: Test PASSES - confirms sequence executes correctly.
        """
        # Set initial phase to COMBAT
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        
        # Track sequence execution order
        execution_order = []
        
        # Spy on methods to track execution order
        original_mirror_phase = game_state.mirror_phase
        original_cleanup = shop_controller.cleanup_dead_cards
        original_start_turn = game_state.start_turn
        original_reset_turn = game_state.reset_turn
        
        def spy_mirror_phase(phase):
            execution_order.append('mirror_phase')
            return original_mirror_phase(phase)
        
        def spy_cleanup():
            execution_order.append('cleanup_dead_cards')
            return original_cleanup()
        
        def spy_start_turn():
            execution_order.append('start_turn')
            return original_start_turn()
        
        def spy_reset_turn():
            execution_order.append('reset_turn')
            return original_reset_turn()
        
        game_state.mirror_phase = spy_mirror_phase
        shop_controller.cleanup_dead_cards = spy_cleanup
        game_state.start_turn = spy_start_turn
        game_state.reset_turn = spy_reset_turn
        
        # Execute phase transition
        result = shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Verify sequence executed in correct order
        expected_order = ['mirror_phase', 'cleanup_dead_cards', 'start_turn', 'reset_turn']
        assert execution_order == expected_order, (
            f"Phase transition sequence should execute in order: {expected_order}. "
            f"Got: {execution_order}"
        )
        
        # Verify result is ShopControllerResult
        assert result is not None, "Phase transition should return ShopControllerResult"
        assert hasattr(result, 'state'), "Result should have state attribute"
        assert hasattr(result, 'removed_coords'), "Result should have removed_coords attribute"
        
        # Restore original methods
        game_state.mirror_phase = original_mirror_phase
        shop_controller.cleanup_dead_cards = original_cleanup
        game_state.start_turn = original_start_turn
        game_state.reset_turn = original_reset_turn
    
    def test_phase_state_updated_correctly_after_transition(self, shop_controller, game_state):
        """
        Test 2: Phase state updated correctly after transition.
        
        Requirement 3.11: When phase transitions are successful, the system SHALL
        CONTINUE TO update game state correctly.
        
        EXPECTED OUTCOME: Test PASSES - confirms phase state updates correctly.
        """
        # Set initial phase to COMBAT
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        assert initial_phase == "STATE_COMBAT", "Initial phase should be STATE_COMBAT"
        
        # Execute phase transition to PREPARATION
        result = shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Verify phase changed to PREPARATION
        current_phase = game_state._store.phase
        assert current_phase == "STATE_PREPARATION", (
            f"Phase should be updated to STATE_PREPARATION after transition. "
            f"Got: {current_phase}"
        )
        
        # Verify result contains updated state
        assert result.state.phase == "STATE_PREPARATION", (
            f"Result state should reflect new phase. "
            f"Got: {result.state.phase}"
        )
    
    def test_state_combat_transition_executes_correctly(self, shop_controller, game_state):
        """
        Test 3: STATE_COMBAT transition executes correctly.
        
        Requirement 3.10: When phase transitions complete successfully, the system
        SHALL CONTINUE TO execute the appropriate sequence for each phase.
        
        EXPECTED OUTCOME: Test PASSES - confirms COMBAT transition works correctly.
        """
        # Set initial phase to PREPARATION
        game_state._store.phase = "STATE_PREPARATION"
        
        # Track if trigger_combat was called
        combat_triggered = False
        
        # Spy on trigger_combat
        original_trigger_combat = shop_controller.trigger_combat
        def spy_trigger_combat():
            nonlocal combat_triggered
            combat_triggered = True
            return original_trigger_combat()
        
        shop_controller.trigger_combat = spy_trigger_combat
        
        # Execute phase transition to COMBAT
        result = shop_controller.handle_phase_change("STATE_COMBAT")
        
        # Verify phase changed to COMBAT
        assert game_state._store.phase == "STATE_COMBAT", (
            "Phase should be updated to STATE_COMBAT"
        )
        
        # Verify trigger_combat was called
        assert combat_triggered, (
            "trigger_combat should be called during STATE_COMBAT transition"
        )
        
        # Verify result contains combat_logs
        assert hasattr(result, 'combat_logs'), (
            "Result should have combat_logs attribute for COMBAT phase"
        )
        
        # Restore original method
        shop_controller.trigger_combat = original_trigger_combat
    
    def test_state_endgame_transition_executes_correctly(self, shop_controller, game_state):
        """
        Test 4: STATE_ENDGAME transition executes correctly.
        
        Requirement 3.10: When phase transitions complete successfully, the system
        SHALL CONTINUE TO execute the appropriate sequence for each phase.
        
        EXPECTED OUTCOME: Test PASSES - confirms ENDGAME transition works correctly.
        """
        # Set initial phase to COMBAT
        game_state._store.phase = "STATE_COMBAT"
        
        # Execute phase transition to ENDGAME
        result = shop_controller.handle_phase_change("STATE_ENDGAME")
        
        # Verify phase changed to ENDGAME
        assert game_state._store.phase == "STATE_ENDGAME", (
            "Phase should be updated to STATE_ENDGAME"
        )
        
        # Verify result contains endgame_stats
        assert hasattr(result, 'endgame_stats'), (
            "Result should have endgame_stats attribute for ENDGAME phase"
        )
    
    def test_other_shop_controller_methods_work_correctly(self, shop_controller, game_state):
        """
        Test 5: Other ShopController methods work correctly.
        
        Requirement 3.12: When other ShopController methods are called, the system
        SHALL CONTINUE TO function as currently implemented.
        
        EXPECTED OUTCOME: Test PASSES - confirms other methods work correctly.
        """
        # Test refresh_public_state
        state = shop_controller.refresh_public_state()
        assert state is not None, "refresh_public_state should return PublicState"
        assert hasattr(state, 'phase'), "PublicState should have phase attribute"
        
        # Test get_turn
        turn = shop_controller.get_turn()
        assert isinstance(turn, int), "get_turn should return integer"
        assert turn >= 1, "Turn should be >= 1"
        
        # Test cleanup_dead_cards
        cleanup_result = shop_controller.cleanup_dead_cards()
        assert cleanup_result is not None, "cleanup_dead_cards should return result"
        assert hasattr(cleanup_result, 'state'), "Result should have state attribute"
        assert hasattr(cleanup_result, 'removed_coords'), "Result should have removed_coords"
        
        # Test trigger_combat (should not raise exception)
        try:
            shop_controller.trigger_combat()
            combat_works = True
        except Exception as e:
            combat_works = False
            pytest.fail(f"trigger_combat should not raise exception: {e}")
        
        assert combat_works, "trigger_combat should execute without errors"
    
    def test_multiple_phase_transitions_work_correctly(self, shop_controller, game_state):
        """
        Test 6: Multiple phase transitions work correctly in sequence.
        
        Requirement 3.11: When phase transitions are successful, the system SHALL
        CONTINUE TO update game state correctly through multiple transitions.
        
        EXPECTED OUTCOME: Test PASSES - confirms multiple transitions work correctly.
        """
        # Start in PREPARATION phase
        game_state._store.phase = "STATE_PREPARATION"
        
        # Transition 1: PREPARATION → COMBAT
        result1 = shop_controller.handle_phase_change("STATE_COMBAT")
        assert game_state._store.phase == "STATE_COMBAT", (
            "First transition should update phase to COMBAT"
        )
        # Note: PublicState phase may be cached, so we verify StateStore.phase instead
        
        # Transition 2: COMBAT → PREPARATION
        result2 = shop_controller.handle_phase_change("STATE_PREPARATION")
        assert game_state._store.phase == "STATE_PREPARATION", (
            "Second transition should update phase to PREPARATION"
        )
        # Note: PublicState phase may be cached, so we verify StateStore.phase instead
        
        # Transition 3: PREPARATION → ENDGAME
        result3 = shop_controller.handle_phase_change("STATE_ENDGAME")
        assert game_state._store.phase == "STATE_ENDGAME", (
            "Third transition should update phase to ENDGAME"
        )
        # Note: PublicState phase may be cached, so we verify StateStore.phase instead
        # This is the observed baseline behavior - phase updates in StateStore but
        # PublicState may reflect cached value until next invalidation
    
    def test_phase_transition_returns_correct_result_structure(self, shop_controller, game_state):
        """
        Test 7: Phase transition returns correct ShopControllerResult structure.
        
        Requirement 3.11: When phase transitions are successful, the system SHALL
        CONTINUE TO return properly structured results.
        
        EXPECTED OUTCOME: Test PASSES - confirms result structure is correct.
        """
        # Test PREPARATION phase result structure
        game_state._store.phase = "STATE_COMBAT"
        result_prep = shop_controller.handle_phase_change("STATE_PREPARATION")
        
        assert hasattr(result_prep, 'state'), "Result should have state"
        assert hasattr(result_prep, 'removed_coords'), "PREPARATION result should have removed_coords"
        assert isinstance(result_prep.removed_coords, tuple), "removed_coords should be tuple"
        
        # Test COMBAT phase result structure
        game_state._store.phase = "STATE_PREPARATION"
        result_combat = shop_controller.handle_phase_change("STATE_COMBAT")
        
        assert hasattr(result_combat, 'state'), "Result should have state"
        assert hasattr(result_combat, 'combat_logs'), "COMBAT result should have combat_logs"
        assert isinstance(result_combat.combat_logs, tuple), "combat_logs should be tuple"
        
        # Test ENDGAME phase result structure
        game_state._store.phase = "STATE_COMBAT"
        result_endgame = shop_controller.handle_phase_change("STATE_ENDGAME")
        
        assert hasattr(result_endgame, 'state'), "Result should have state"
        assert hasattr(result_endgame, 'endgame_stats'), "ENDGAME result should have endgame_stats"
        assert isinstance(result_endgame.endgame_stats, tuple), "endgame_stats should be tuple"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
