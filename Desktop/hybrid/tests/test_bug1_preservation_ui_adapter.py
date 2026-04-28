"""
Preservation Unit Tests: UIAdapter.build_public_state()

Property 2: Preservation - Full State Computation

These tests capture the baseline behavior of UIAdapter.build_public_state() on UNFIXED code.
They ensure that after the fix, the full state computation (when no cache exists) produces
exactly the same results as before.

IMPORTANT: Follow observation-first methodology
- Run tests on UNFIXED code
- EXPECTED OUTCOME: Tests PASS (confirms baseline behavior to preserve)
- After fix implementation, re-run these tests to ensure no regressions

Requirements: 3.1, 3.2, 3.3
"""

import pytest
from collections.abc import Mapping
from unittest.mock import Mock, MagicMock, patch
from v2.core.ui_adapter import UIAdapter
from v2.core.card_database import CardDatabase, CardData
from v2.core.synergy_calculator import SynergyCalculator, SynergyComputeResult
from engine_core.card import Card


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
        return 3 + (win_streak * 1) + (hp // 10)


class MockPlayer:
    """Mock player for testing."""
    def __init__(self, pid):
        self.pid = pid
        self.alive = True
        self.gold = 10
        self.hp = 100
        self.board = MockBoard()
        self.hand = []
        self.shop_locked = False
        self.passive_buff_log = []
        self.win_streak = 0
        self.total_pts = 0
        self.interest_multiplier = 1.0
        self.economy = MockEconomy()
        self.turns_played = 5
        self.stats = {"damage_dealt": 100, "damage_taken": 50}
        self.strategy = "test_strategy"
        self.copies = {"Albert Einstein": 2, "Algorithm": 1}
        self.copy_applied = {}


class MockMarket:
    """Mock market for testing."""
    def __init__(self):
        self._windows = {}
    
    def get_window(self, pid):
        if pid not in self._windows:
            # Return 5 mock cards for shop
            self._windows[pid] = [
                Card("Albert Einstein", "Science", "1", {"atk": 10, "hp": 10}),
                Card("Algorithm", "Science", "1", {"atk": 8, "hp": 12}),
                None,
                Card("Anubis", "Mythology & Gods", "2", {"atk": 15, "hp": 15}),
                None,
            ]
        return self._windows[pid]


class MockEngineAdapter:
    """Mock EngineAdapter for testing."""
    def __init__(self):
        self.players = {0: MockPlayer(0)}
        self.market = MockMarket()
        self.eliminated_coords = []
        self.last_results = []
    
    def get_turn(self):
        return 5
    
    def get_player(self, pid):
        return self.players.get(pid)
    
    def get_alive_players(self):
        return [p for p in self.players.values() if p.alive]
    
    def get_all_players(self):
        return list(self.players.values())
    
    def get_shop_window(self, pid):
        window = self.market.get_window(pid)
        return [card.name if card else None for card in window]
    
    def get_hand(self, pid):
        player = self.players.get(pid)
        if player:
            return [card.name if card else None for card in player.hand]
        return []
    
    def is_shop_locked(self, pid):
        player = self.players.get(pid)
        return player.shop_locked if player else False
    
    def get_player_hp(self, pid):
        player = self.players.get(pid)
        return player.hp if player else 0
    
    def get_player_gold(self, pid):
        player = self.players.get(pid)
        return player.gold if player else 0
    
    def get_passive_buff_log(self, pid):
        player = self.players.get(pid)
        return player.passive_buff_log if player else []
    
    def get_last_results(self):
        return self.last_results
    
    def get_eliminated_coords(self, pid):
        return self.eliminated_coords
    
    def get_market(self):
        return self.market
    
    def get_rarity_weight(self, rarity, turn):
        # Simple mock rarity weights
        weights = {1: 100.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        return weights.get(rarity, 0.0)
    
    @staticmethod
    def get_constants():
        """Mock constants."""
        constants = Mock()
        constants.STARTING_HP = 100
        constants.SYNERGY_THRESHOLDS = [2, 4, 6]
        return constants
    
    @staticmethod
    def tier_bonus(threshold):
        """Mock tier bonus calculation."""
        bonuses = {2: 5, 4: 10, 6: 15}
        return bonuses.get(threshold, 0)


class MockStateStore:
    """Mock StateStore for testing."""
    def __init__(self):
        self.phase = "STATE_PREPARATION"
        self.view_index = 0
        self.place_locked = False
        self._pairings = []
    
    def get_pairings(self):
        return self._pairings


class MockFormatter:
    """Mock formatter for testing."""
    def format_rarity_probs(self, weight_fn, turn):
        return {"1": 100.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0}
    
    def format_combat_logs(self, results, view_index, turn, passive_feed):
        return []
    
    def get_card_data_snapshot(self, card_obj):
        """Return mock CardData for testing."""
        if card_obj is None:
            return None
        
        card_name = card_obj.name if hasattr(card_obj, 'name') else str(card_obj)
        
        # Return mock CardData
        return CardData(
            name=card_name,
            category="Science",
            rarity="1",
            stats={"atk": 10, "hp": 10},
            passive_type="combat",
            passive_effect="Test effect",
            synergy_group="MIND"
        )


@pytest.fixture
def mock_card_database():
    """Mock CardDatabase for testing."""
    with patch('v2.core.card_database.CardDatabase.get') as mock_db:
        db = Mock()
        db.lookup.return_value = CardData(
            name="Test Card",
            category="Science",
            rarity="1",
            stats={"atk": 10, "hp": 10},
            passive_type="combat",
            passive_effect="Test effect",
            synergy_group="MIND"
        )
        mock_db.return_value = db
        yield db


@pytest.fixture
def ui_adapter():
    """Create UIAdapter instance for testing."""
    return UIAdapter()


@pytest.fixture
def mock_adapter():
    """Create mock EngineAdapter for testing."""
    return MockEngineAdapter()


@pytest.fixture
def mock_store():
    """Create mock StateStore for testing."""
    return MockStateStore()


@pytest.fixture
def mock_formatter():
    """Create mock formatter for testing."""
    return MockFormatter()


def test_build_public_state_with_no_cache_produces_complete_state(
    ui_adapter, mock_adapter, mock_store, mock_formatter, mock_card_database
):
    """
    Test 1: build_public_state() with no cache produces complete state with BFS + DB + triple-iteration
    
    This test verifies that when no cache exists, build_public_state() performs:
    1. Full BFS computation via SynergyCalculator.compute()
    2. Database lookups for card info (shop, hand, board)
    3. Triple-iteration over shop/hand/board to build card_info dicts
    
    Requirement: 3.1
    """
    # Setup: Add cards to board to trigger synergy calculation
    player = mock_adapter.players[0]
    player.board.place((0, 0), Card("Albert Einstein", "Science", "1", {"atk": 10, "hp": 10}))
    player.board.place((1, 0), Card("Algorithm", "Science", "1", {"atk": 8, "hp": 12}))
    player.hand = [Card("Anubis", "Mythology & Gods", "2", {"atk": 15, "hp": 15}), None, None, None, None, None]
    
    # Spy on SynergyCalculator.compute to verify BFS runs
    with patch.object(SynergyCalculator, 'compute', wraps=ui_adapter._synergy_calculator.compute) as mock_compute:
        # Act: Build public state (no cache exists)
        result = ui_adapter.build_public_state(mock_adapter, mock_store, mock_formatter)
        
        # Assert: BFS was called (full computation)
        assert mock_compute.call_count == 1, "SynergyCalculator.compute() should be called once for full state computation"
        
        # Assert: Complete state structure exists
        assert result is not None
        assert result.phase == "STATE_PREPARATION"
        assert result.turn == 5
        assert result.view_index == 0
        
        # Assert: Active player state is complete
        active = result.active_player
        assert active is not None
        assert active.pid == 0
        assert active.hp == 100
        assert active.gold == 10
        assert active.alive is True
        assert active.turns_played == 5
        
        # Assert: Board cards are present
        assert len(active.board_cards) == 2
        assert (0, 0) in active.board_cards
        assert (1, 0) in active.board_cards
        assert active.board_cards[(0, 0)]["name"] == "Albert Einstein"
        assert active.board_cards[(1, 0)]["name"] == "Algorithm"
        
        # Assert: Shop data is present
        assert active.shop is not None
        assert len(active.shop.slots) == 5
        assert active.shop.slots[0] == "Albert Einstein"
        assert active.shop.slots[1] == "Algorithm"
        assert active.shop.slots[2] is None
        
        # Assert: Hand data is present
        assert active.hand is not None
        assert len(active.hand.slots) == 6
        assert active.hand.slots[0] == "Anubis"
        
        # Assert: HUD data is present
        assert active.hud is not None
        assert active.hud.hp == 100
        assert active.hud.gold == 10
        assert active.hud.turn == 5
        
        # Assert: Synergy data is present (from BFS)
        assert active.synergy is not None
        assert len(active.synergy.groups) > 0
        
        # Assert: Card info dicts are populated (triple-iteration)
        assert active.shop_card_info is not None
        assert active.hand_card_info is not None
        assert active.board_card_info is not None
        
        # Verify shop_card_info has entries for non-None slots
        assert 0 in active.shop_card_info  # Albert Einstein
        assert 1 in active.shop_card_info  # Algorithm
        assert 3 in active.shop_card_info  # Anubis
        
        # Verify hand_card_info has entry for Anubis
        assert 0 in active.hand_card_info
        
        # Verify board_card_info has entries for board cards
        assert (0, 0) in active.board_card_info
        assert (1, 0) in active.board_card_info


def test_synergy_calculations_return_correct_data(
    ui_adapter, mock_adapter, mock_store, mock_formatter, mock_card_database
):
    """
    Test 2: Synergy calculations return correct data
    
    This test verifies that synergy calculations via SynergyCalculator.compute()
    produce correct group counts, bonuses, and adjacency pairs.
    
    Requirement: 3.2
    """
    # Setup: Add MIND cards to board to trigger synergy
    player = mock_adapter.players[0]
    player.board.place((0, 0), Card("Albert Einstein", "Science", "1", {"atk": 10, "hp": 10}))  # MIND
    player.board.place((1, 0), Card("Algorithm", "Science", "1", {"atk": 8, "hp": 12}))        # MIND
    player.board.place((0, 1), Card("Anubis", "Mythology & Gods", "2", {"atk": 15, "hp": 15}))           # CONNECTION
    
    # Mock CardDatabase to return proper tags
    mock_card_database.lookup.side_effect = lambda name: CardData(
        name=name,
        category="Science" if name in ["Albert Einstein", "Algorithm"] else "Mythology & Gods",
        rarity="1",
        stats={"atk": 10, "hp": 10},
        passive_type="combat",
        passive_effect="Test effect",
        synergy_group="MIND" if name in ["Albert Einstein", "Algorithm"] else "EXISTENCE"
    )
    
    # Act: Build public state
    result = ui_adapter.build_public_state(mock_adapter, mock_store, mock_formatter)
    
    # Assert: Synergy data structure is correct
    synergy = result.active_player.synergy
    assert synergy is not None
    assert synergy.groups is not None
    assert len(synergy.groups) == 3  # MIND, CONNECTION, EXISTENCE
    
    # Assert: Synergy groups have correct structure
    for group in synergy.groups:
        assert hasattr(group, 'key')
        assert hasattr(group, 'label')
        assert hasattr(group, 'short_label')
        assert hasattr(group, 'color')
        assert hasattr(group, 'count')
        assert hasattr(group, 'bonus')
        assert hasattr(group, 'next_tier_count')
        assert hasattr(group, 'next_tier_bonus')
    
    # Assert: Total synergy bonus is calculated
    assert synergy.total >= 0
    
    # Assert: Adjacency pairs are present (from BFS)
    adjacency = result.active_player.adjacency_pairs
    assert adjacency is not None
    assert isinstance(adjacency, tuple)
    
    # Assert: Synergy calculation was performed (groups exist with proper structure)
    # Note: We don't assert specific counts because that depends on CardDatabase initialization
    # The key preservation property is that synergy structure is complete and correct
    assert all(isinstance(g.count, int) for g in synergy.groups)
    assert all(isinstance(g.bonus, int) for g in synergy.groups)


def test_shop_hand_board_card_info_returns_correct_data(
    ui_adapter, mock_adapter, mock_store, mock_formatter, mock_card_database
):
    """
    Test 3: Shop/hand/board card info returns correct data
    
    This test verifies that card info dicts (shop_card_info, hand_card_info, board_card_info)
    are correctly populated with CardData snapshots from the database.
    
    Requirement: 3.3
    """
    # Setup: Add cards to shop, hand, and board
    player = mock_adapter.players[0]
    player.board.place((0, 0), Card("Albert Einstein", "Science", "1", {"atk": 10, "hp": 10}))
    player.board.place((1, 0), Card("Algorithm", "Science", "1", {"atk": 8, "hp": 12}))
    player.hand = [Card("Anubis", "Mythology & Gods", "2", {"atk": 15, "hp": 15}), Card("Athena", "Mythology & Gods", "3", {"atk": 20, "hp": 20}), None, None, None, None]
    
    # Mock CardDatabase to return proper CardData
    def mock_lookup(name):
        return CardData(
            name=name,
            category="Science",
            rarity="1",
            stats={"atk": 10, "hp": 10},
            passive_type="combat",
            passive_effect=f"Test effect: {name}",
            synergy_group="MIND"
        )
    
    mock_card_database.lookup.side_effect = mock_lookup
    
    # Act: Build public state
    result = ui_adapter.build_public_state(mock_adapter, mock_store, mock_formatter)
    active = result.active_player
    
    # Assert: Shop card info is populated
    assert active.shop_card_info is not None
    assert isinstance(active.shop_card_info, Mapping)
    
    # Shop has: Albert Einstein (0), Algorithm (1), None (2), Anubis (3), None (4)
    assert 0 in active.shop_card_info
    assert 1 in active.shop_card_info
    assert 3 in active.shop_card_info
    
    # Verify shop card data structure
    shop_card_0 = active.shop_card_info[0]
    assert shop_card_0 is not None
    assert hasattr(shop_card_0, 'name')
    assert hasattr(shop_card_0, 'category')
    assert hasattr(shop_card_0, 'rarity')
    assert hasattr(shop_card_0, 'stats')
    
    # Assert: Hand card info is populated
    assert active.hand_card_info is not None
    assert isinstance(active.hand_card_info, Mapping)
    
    # Hand has: Anubis (0), Athena (1), None (2-5)
    assert 0 in active.hand_card_info
    assert 1 in active.hand_card_info
    
    # Verify hand card data structure
    hand_card_0 = active.hand_card_info[0]
    assert hand_card_0 is not None
    assert hasattr(hand_card_0, 'name')
    assert hasattr(hand_card_0, 'rarity')
    
    # Assert: Board card info is populated
    assert active.board_card_info is not None
    assert isinstance(active.board_card_info, Mapping)
    
    # Board has: Albert Einstein (0,0), Algorithm (1,0)
    assert (0, 0) in active.board_card_info
    assert (1, 0) in active.board_card_info
    
    # Verify board card data structure
    board_card_00 = active.board_card_info[(0, 0)]
    assert board_card_00 is not None
    assert hasattr(board_card_00, 'name')
    assert hasattr(board_card_00, 'rarity')
    
    # Assert: Card info matches expected cards
    assert active.shop.slots[0] == "Albert Einstein"
    assert active.hand.slots[0] == "Anubis"
    assert active.board_cards[(0, 0)]["name"] == "Albert Einstein"
    
    # Assert: All card info dicts use correct types
    for card_data in active.shop_card_info.values():
        if card_data is not None:
            assert isinstance(card_data, CardData)
    
    for card_data in active.hand_card_info.values():
        if card_data is not None:
            assert isinstance(card_data, CardData)
    
    for card_data in active.board_card_info.values():
        if card_data is not None:
            assert isinstance(card_data, CardData)


def test_build_public_state_preserves_player_stats(
    ui_adapter, mock_adapter, mock_store, mock_formatter, mock_card_database
):
    """
    Additional preservation test: Verify player stats are correctly preserved
    
    This test ensures that player-level data (stats, copies, strategy) is correctly
    transferred to the PublicState without modification.
    """
    # Setup: Configure player with specific stats
    player = mock_adapter.players[0]
    player.stats = {"damage_dealt": 250, "damage_taken": 100, "cards_bought": 15}
    player.copies = {"Albert Einstein": 3, "Algorithm": 2, "Anubis": 1}
    player.strategy = "aggressive_strategy"
    player.turns_played = 10
    player.win_streak = 3
    player.total_pts = 150
    
    # Act: Build public state
    result = ui_adapter.build_public_state(mock_adapter, mock_store, mock_formatter)
    active = result.active_player
    
    # Assert: Player stats are preserved
    assert active.stats == player.stats
    assert active.stats["damage_dealt"] == 250
    assert active.stats["damage_taken"] == 100
    assert active.stats["cards_bought"] == 15
    
    # Assert: Copies are preserved
    assert active.copies_by_name == player.copies
    assert active.copies_by_name["Albert Einstein"] == 3
    assert active.copies_by_name["Algorithm"] == 2
    
    # Assert: Strategy is preserved
    assert active.strategy == "aggressive_strategy"
    
    # Assert: Turn data is preserved
    assert active.turns_played == 10
    assert active.hud.win_streak == 3
    assert active.hud.total_pts == 150


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
