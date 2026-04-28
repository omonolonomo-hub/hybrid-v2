"""
Bug Condition Exploration Test: UIAdapter.build_public_state() Performance Leak

This test explores Bug 1 from Phase 2 (CRITICAL) fixes:
- Cache invalidation triggers expensive full BFS + DB + triple-iteration on every frame
- economy_changed, inventory_changed, turn_started signals trigger BFS despite board unchanged

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS with BFS running for non-board signals (this proves the bug).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from v2.core.game_state import GameState
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
        signal._observers = self._callbacks[name]  # For compatibility
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


@pytest.fixture
def game_state():
    """Create a GameState with mocked engine."""
    gs = GameState()
    engine = MockEngine()
    gs.hook_engine(engine)
    return gs


class TestBug1CacheInvalidationPerformanceLeak:
    """
    Bug Condition Exploration: Unnecessary BFS on Non-Board Signals
    
    Property 1: Bug Condition - Unnecessary BFS on Non-Board Signals
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Expected Behavior (after fix):
    - economy_changed → NO BFS run (only HUD invalidated)
    - inventory_changed → NO BFS run (only hand invalidated)
    - turn_started → NO BFS run (only shop invalidated)
    - board_mutated → BFS runs (synergy + board invalidated)
    """
    
    def test_economy_changed_triggers_unnecessary_cache_invalidation(self, game_state):
        """
        Test Case 1: economy_changed signal invalidates entire cache despite board unchanged.
        
        EXPECTED OUTCOME: Test FAILS - entire cache invalidated when only HUD should be.
        This proves the bug exists.
        """
        # Build initial state (triggers first build_public_state)
        initial_state = game_state.get_public_state()
        
        # Verify cache is populated
        assert game_state._cached_public_state is not None, "Cache should be populated after get_public_state()"
        
        # Spy on UIAdapter.build_public_state() to count full rebuilds
        ui_adapter = game_state._ui_adapter
        original_build = ui_adapter.build_public_state
        
        build_call_count = 0
        def spy_build(*args, **kwargs):
            nonlocal build_call_count
            build_call_count += 1
            return original_build(*args, **kwargs)
        
        ui_adapter.build_public_state = spy_build
        
        # Trigger economy_changed signal (gold changed, board unchanged)
        engine = game_state._adapter._engine
        engine.players[0].gold = 50
        engine.signals.economy_changed.emit(pid=0)
        
        # Check if cache was invalidated
        cache_invalidated = game_state._cached_public_state is None
        
        # Rebuild state
        updated_state = game_state.get_public_state()
        
        # EXPECTED BEHAVIOR: Cache should NOT be fully invalidated (only HUD component)
        # BUG BEHAVIOR: Entire cache invalidated, causing full rebuild with BFS + DB + triple-iteration
        assert not cache_invalidated, (
            f"BUG DETECTED: economy_changed invalidated entire cache despite board unchanged. "
            f"This triggers expensive full rebuild (BFS + DB + triple-iteration). "
            f"Expected: granular invalidation (only HUD component). "
            f"Got: {build_call_count} full rebuild(s)."
        )
    
    def test_inventory_changed_triggers_unnecessary_cache_invalidation(self, game_state):
        """
        Test Case 2: inventory_changed signal invalidates entire cache despite board unchanged.
        
        EXPECTED OUTCOME: Test FAILS - entire cache invalidated when only hand should be.
        This proves the bug exists.
        """
        # Build initial state
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Trigger inventory_changed signal (hand changed, board unchanged)
        engine = game_state._adapter._engine
        engine.players[0].hand = [Card("TestCard", "common", "test", {})]
        engine.signals.inventory_changed.emit(pid=0)
        
        # Check if cache was invalidated
        cache_invalidated = game_state._cached_public_state is None
        
        # EXPECTED BEHAVIOR: Cache should NOT be fully invalidated (only hand component)
        # BUG BEHAVIOR: Entire cache invalidated
        assert not cache_invalidated, (
            f"BUG DETECTED: inventory_changed invalidated entire cache despite board unchanged. "
            f"Expected: granular invalidation (only hand component)."
        )
    
    def test_turn_started_triggers_unnecessary_cache_invalidation(self, game_state):
        """
        Test Case 3: turn_started signal invalidates entire cache despite board unchanged.
        
        EXPECTED OUTCOME: Test FAILS - entire cache invalidated when only shop should be.
        This proves the bug exists.
        """
        # Build initial state
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Trigger turn_started signal (turn changed, board unchanged)
        engine = game_state._adapter._engine
        engine.turn = 2
        engine.signals.turn_started.emit(turn=2)
        
        # Check if cache was invalidated
        cache_invalidated = game_state._cached_public_state is None
        
        # EXPECTED BEHAVIOR: Cache should NOT be fully invalidated (only shop component)
        # BUG BEHAVIOR: Entire cache invalidated
        assert not cache_invalidated, (
            f"BUG DETECTED: turn_started invalidated entire cache despite board unchanged. "
            f"Expected: granular invalidation (only shop component)."
        )
    
    def test_multiple_signals_trigger_multiple_cache_invalidations(self, game_state):
        """
        Test Case 4: Simulate start_turn with 15-20 signals (AI purchases + income).
        
        This simulates the real-world scenario where start_turn() fires:
        - 7 AI purchases (7x inventory_changed)
        - 8 income signals (8x economy_changed)
        - 1 turn_started signal
        Total: 16 signals, all invalidate entire cache unnecessarily
        
        EXPECTED OUTCOME: Test FAILS - Multiple full cache invalidations detected.
        This proves the performance leak.
        """
        # Build initial state
        initial_state = game_state.get_public_state()
        
        # Spy on UIAdapter.build_public_state() to count full rebuilds
        ui_adapter = game_state._ui_adapter
        original_build = ui_adapter.build_public_state
        
        build_call_count = 0
        def spy_build(*args, **kwargs):
            nonlocal build_call_count
            build_call_count += 1
            return original_build(*args, **kwargs)
        
        ui_adapter.build_public_state = spy_build
        
        engine = game_state._adapter._engine
        
        # Simulate 7 AI purchases (inventory_changed)
        for i in range(7):
            engine.signals.inventory_changed.emit(pid=0)
            # Rebuild state after each signal (simulates frame rendering)
            game_state.get_public_state()
        
        # Simulate 8 income signals (economy_changed)
        for i in range(8):
            engine.signals.economy_changed.emit(pid=0)
            # Rebuild state after each signal
            game_state.get_public_state()
        
        # Simulate turn_started signal
        engine.signals.turn_started.emit(turn=2)
        game_state.get_public_state()
        
        # EXPECTED BEHAVIOR: Should use granular invalidation (minimal rebuilds)
        # BUG BEHAVIOR: 16 full rebuilds (each with BFS + DB + triple-iteration)
        # With 8+ cards, each rebuild takes 5-8ms, approaching 16ms frame budget
        assert build_call_count <= 1, (
            f"BUG DETECTED: {build_call_count} full build_public_state() calls triggered by 16 non-board signals. "
            f"Expected: ≤1 rebuild with granular invalidation. "
            f"This causes frame rate drops (5-8ms per rebuild with 8+ cards)."
        )
    
    def test_board_mutated_should_invalidate_cache(self, game_state):
        """
        Test Case 5: board_mutated signal SHOULD invalidate cache (this is correct behavior).
        
        This test verifies that board_mutated correctly invalidates cache.
        This should PASS even on unfixed code.
        """
        # Build initial state
        initial_state = game_state.get_public_state()
        assert game_state._cached_public_state is not None
        
        # Trigger board_mutated signal (board changed)
        engine = game_state._adapter._engine
        engine.players[0].board.place((0, 0), Card("TestCard", "common", "test", {}))
        engine.signals.board_mutated.emit(pid=0)
        
        # Check if cache was invalidated
        cache_invalidated = game_state._cached_public_state is None
        
        # EXPECTED BEHAVIOR: Cache SHOULD be invalidated (board changed)
        assert cache_invalidated, (
            f"board_mutated should invalidate cache when board changes."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

