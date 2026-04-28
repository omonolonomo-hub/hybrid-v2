"""
Regression tests for Bug 4: ShopController.handle_phase_change() atomicity.

Encodes expected behavior after the fix:
- On exception during STATE_PREPARATION transition, StateStore._phase is restored
  to the pre-transition value (mirror_phase rollback); exception still propagates.
- Successful transitions still run mirror_phase → cleanup_dead_cards → start_turn → reset_turn.

(Test Case 5 was updated from the original exploration test that asserted the unfixed bug.)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
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
        """Mock start_turn - can be patched to raise exception."""
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


class TestBug4NonAtomicPhaseTransition:
    """
    Bug Condition Exploration: Phase Inconsistent on Exception
    
    Property 1: Bug Condition - Phase Inconsistent on Exception
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Expected Behavior (after fix):
    - Exception during phase transition → Phase restored to previous value
    - StateStore._phase rolled back on exception
    - Engine-level mutations (board, market) NOT rolled back (idempotent/logged)
    """
    
    def test_cleanup_dead_cards_exception_leaves_phase_inconsistent(self, shop_controller, game_state):
        """
        Test Case 1: mirror_phase() succeeds → cleanup_dead_cards() throws exception
        → Verify phase already mirrored but turn not started (inconsistent state).
        
        EXPECTED OUTCOME: Test FAILS - phase is "STATE_COMBAT" but turn not started.
        This proves the bug exists.
        """
        # Set initial phase to COMBAT, then transition to PREPARATION
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        assert initial_phase == "STATE_COMBAT", "Initial phase should be STATE_COMBAT"
        
        # Patch cleanup_dead_cards to raise exception
        original_cleanup = shop_controller.cleanup_dead_cards
        def failing_cleanup():
            raise RuntimeError("Simulated cleanup_dead_cards failure")
        
        shop_controller.cleanup_dead_cards = failing_cleanup
        
        # Attempt phase transition (should fail at cleanup_dead_cards)
        with pytest.raises(RuntimeError, match="Simulated cleanup_dead_cards failure"):
            shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Check phase state after exception
        current_phase = game_state._store.phase
        
        # EXPECTED BEHAVIOR: Phase should be restored to initial_phase (rollback)
        # BUG BEHAVIOR: Phase is "STATE_PREPARATION" (already mirrored) but turn not started
        assert current_phase == initial_phase, (
            f"BUG DETECTED: Phase transition not atomic. "
            f"Exception during cleanup_dead_cards left phase in inconsistent state. "
            f"Expected phase: {initial_phase} (rolled back). "
            f"Got phase: {current_phase} (already mirrored but turn not started). "
            f"This proves no rollback mechanism exists."
        )
        
        # Restore original method
        shop_controller.cleanup_dead_cards = original_cleanup
    
    def test_start_turn_exception_leaves_phase_inconsistent(self, shop_controller, game_state):
        """
        Test Case 2: mirror_phase() + cleanup_dead_cards() succeed → start_turn() throws exception
        → Verify phase inconsistent.
        
        EXPECTED OUTCOME: Test FAILS - phase is "STATE_PREPARATION" but turn not started.
        This proves the bug exists.
        """
        # Set initial phase to COMBAT, then transition to PREPARATION
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        
        # Patch start_turn to raise exception
        original_start_turn = game_state.start_turn
        def failing_start_turn():
            raise RuntimeError("Simulated start_turn failure")
        
        game_state.start_turn = failing_start_turn
        
        # Attempt phase transition (should fail at start_turn)
        with pytest.raises(RuntimeError, match="Simulated start_turn failure"):
            shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Check phase state after exception
        current_phase = game_state._store.phase
        
        # EXPECTED BEHAVIOR: Phase should be restored to initial_phase (rollback)
        # BUG BEHAVIOR: Phase is "STATE_PREPARATION" (already mirrored) but turn not started
        assert current_phase == initial_phase, (
            f"BUG DETECTED: Phase transition not atomic. "
            f"Exception during start_turn left phase in inconsistent state. "
            f"Expected phase: {initial_phase} (rolled back). "
            f"Got phase: {current_phase} (already mirrored but turn not started). "
            f"This proves no rollback mechanism exists."
        )
        
        # Restore original method
        game_state.start_turn = original_start_turn
    
    def test_reset_turn_exception_leaves_phase_inconsistent(self, shop_controller, game_state):
        """
        Test Case 3: All steps succeed except reset_turn() → Verify phase inconsistent.
        
        EXPECTED OUTCOME: Test FAILS - phase is "STATE_PREPARATION" but reset incomplete.
        This proves the bug exists.
        """
        # Set initial phase to COMBAT, then transition to PREPARATION
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        
        # Patch reset_turn to raise exception
        original_reset_turn = game_state.reset_turn
        def failing_reset_turn():
            raise RuntimeError("Simulated reset_turn failure")
        
        game_state.reset_turn = failing_reset_turn
        
        # Attempt phase transition (should fail at reset_turn)
        with pytest.raises(RuntimeError, match="Simulated reset_turn failure"):
            shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Check phase state after exception
        current_phase = game_state._store.phase
        
        # EXPECTED BEHAVIOR: Phase should be restored to initial_phase (rollback)
        # BUG BEHAVIOR: Phase is "STATE_PREPARATION" (already mirrored) but reset incomplete
        assert current_phase == initial_phase, (
            f"BUG DETECTED: Phase transition not atomic. "
            f"Exception during reset_turn left phase in inconsistent state. "
            f"Expected phase: {initial_phase} (rolled back). "
            f"Got phase: {current_phase} (already mirrored but reset incomplete). "
            f"This proves no rollback mechanism exists."
        )
        
        # Restore original method
        game_state.reset_turn = original_reset_turn
    
    def test_phase_modified_before_sequence_completes(self, shop_controller, game_state):
        """
        Test Case 4: Verify StateStore._phase is modified before sequence completes.
        
        This test confirms that mirror_phase() modifies StateStore._phase immediately,
        before cleanup_dead_cards(), start_turn(), and reset_turn() complete.
        
        EXPECTED OUTCOME: Test PASSES - confirms phase is modified early.
        This is part of the bug (phase modified before sequence completes).
        """
        # Set initial phase to COMBAT, then transition to PREPARATION
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase
        
        # Track when phase changes
        phase_changed_before_cleanup = False
        
        # Patch cleanup_dead_cards to check phase
        original_cleanup = shop_controller.cleanup_dead_cards
        def spy_cleanup():
            nonlocal phase_changed_before_cleanup
            # Check if phase already changed
            phase_changed_before_cleanup = (game_state._store.phase == "STATE_PREPARATION")
            # Raise exception to stop sequence
            raise RuntimeError("Simulated cleanup_dead_cards failure")
        
        shop_controller.cleanup_dead_cards = spy_cleanup
        
        # Attempt phase transition (should fail at cleanup_dead_cards)
        with pytest.raises(RuntimeError, match="Simulated cleanup_dead_cards failure"):
            shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Verify phase was modified before cleanup_dead_cards completed
        assert phase_changed_before_cleanup, (
            f"Phase should be modified by mirror_phase() before cleanup_dead_cards() runs. "
            f"This confirms the bug: phase is modified early, before sequence completes."
        )
        
        # Restore original method
        shop_controller.cleanup_dead_cards = original_cleanup
    
    def test_rollback_restores_phase_when_exception_propagates(self, shop_controller, game_state):
        """
        Test Case 5: Exception propagates AND StateStore._phase is rolled back.

        Expected behavior (after fix): handle_phase_change() wraps the sequence in
        try/except; on failure it restores phase via mirror_phase(previous_phase)
        and re-raises. Phase must match pre-transition value after the exception.
        """
        game_state._store.phase = "STATE_COMBAT"
        initial_phase = game_state._store.phase

        original_start_turn = game_state.start_turn

        def failing_start_turn():
            raise RuntimeError("Simulated start_turn failure")

        game_state.start_turn = failing_start_turn

        with pytest.raises(RuntimeError, match="Simulated start_turn failure"):
            shop_controller.handle_phase_change("STATE_PREPARATION")

        current_phase = game_state._store.phase
        assert current_phase == initial_phase, (
            "After exception, phase should be restored to the value before "
            f"mirror_phase (expected {initial_phase!r}, got {current_phase!r})."
        )

        game_state.start_turn = original_start_turn
    
    def test_successful_phase_transition_completes_sequence(self, shop_controller, game_state):
        """
        Test Case 6: Verify successful phase transition completes full sequence.
        
        This test verifies that when no exceptions occur, the sequence completes:
        mirror_phase() → cleanup_dead_cards() → start_turn() → reset_turn()
        
        EXPECTED OUTCOME: Test PASSES - confirms successful transitions work.
        This is NOT part of the bug (successful transitions should work).
        """
        # Store initial phase
        initial_phase = game_state._store.phase
        
        # Track sequence execution
        sequence_executed = {
            'mirror_phase': False,
            'cleanup_dead_cards': False,
            'start_turn': False,
            'reset_turn': False,
        }
        
        # Spy on methods to track execution
        original_cleanup = shop_controller.cleanup_dead_cards
        original_start_turn = game_state.start_turn
        original_reset_turn = game_state.reset_turn
        
        def spy_cleanup():
            sequence_executed['cleanup_dead_cards'] = True
            return original_cleanup()
        
        def spy_start_turn():
            sequence_executed['start_turn'] = True
            return original_start_turn()
        
        def spy_reset_turn():
            sequence_executed['reset_turn'] = True
            return original_reset_turn()
        
        shop_controller.cleanup_dead_cards = spy_cleanup
        game_state.start_turn = spy_start_turn
        game_state.reset_turn = spy_reset_turn
        
        # Execute phase transition (should succeed)
        result = shop_controller.handle_phase_change("STATE_PREPARATION")
        
        # Verify phase changed
        sequence_executed['mirror_phase'] = (game_state._store.phase == "STATE_PREPARATION")
        
        # Verify full sequence executed
        assert all(sequence_executed.values()), (
            f"Successful phase transition should execute full sequence. "
            f"Executed: {sequence_executed}"
        )
        
        # Restore original methods
        shop_controller.cleanup_dead_cards = original_cleanup
        game_state.start_turn = original_start_turn
        game_state.reset_turn = original_reset_turn


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
