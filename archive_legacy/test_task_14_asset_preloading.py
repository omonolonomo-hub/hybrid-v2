"""
Test for Task 14: Asset pre-loading system

Verifies:
- _preload_all_assets() collects unique card names and loads assets
- _create_corrupted_visual() creates glitch-style visuals
- _validate_card_data() validates card integrity
- _create_fallback_card() creates safe default cards
"""

import pytest
import pygame
from unittest.mock import Mock, patch
from scenes.combat_scene import CombatScene, AssetManager
from core.core_game_state import CoreGameState
from engine_core.card import Card


@pytest.fixture
def mock_game_state():
    """Create a mock CoreGameState with players and cards."""
    pygame.init()
    
    # Create mock game
    mock_game = Mock()
    
    # Create mock player with board and hand
    mock_player = Mock()
    mock_player.pid = 1
    mock_player.hp = 100
    mock_player.gold = 50
    mock_player.win_streak = 0
    mock_player.stats = {}
    mock_player.strategy = "test_strategy"
    
    # Create mock board with grid
    mock_board = Mock()
    
    # Create test cards
    test_card_1 = Card(
        name="TestCard1",
        category="test",
        rarity="1",
        stats={"strength": 5, "agility": 4, "intelligence": 3, "vitality": 2, "luck": 1, "charisma": 6}
    )
    
    test_card_2 = Card(
        name="TestCard2",
        category="test",
        rarity="2",
        stats={"strength": 7, "agility": 6, "intelligence": 5, "vitality": 4, "luck": 3, "charisma": 8}
    )
    
    # Set up board grid with cards
    mock_board.grid = {
        (0, 0): test_card_1,
        (1, 0): test_card_2,
        (0, 1): None,
    }
    
    mock_player.board = mock_board
    mock_player.hand = [test_card_1]
    mock_player.copies = {"TestCard1": 2, "TestCard2": 1}
    
    mock_game.players = [mock_player]
    
    return CoreGameState(mock_game)


def test_preload_all_assets(mock_game_state):
    """Test _preload_all_assets() collects and loads unique card names."""
    scene = CombatScene(mock_game_state)
    scene.on_enter()
    
    # Verify assets were loaded for unique cards
    assert "TestCard1" in [key.split("_")[0] for key in scene.asset_manager.card_images.keys()]
    assert "TestCard2" in [key.split("_")[0] for key in scene.asset_manager.card_images.keys()]
    
    # Verify both front and back were loaded
    assert "TestCard1_front" in scene.asset_manager.card_images
    assert "TestCard1_back" in scene.asset_manager.card_images
    assert "TestCard2_front" in scene.asset_manager.card_images
    assert "TestCard2_back" in scene.asset_manager.card_images


def test_create_corrupted_visual():
    """Test _create_corrupted_visual() creates glitch-style visual."""
    asset_manager = AssetManager()
    
    # Create corrupted visual
    surface = asset_manager._create_corrupted_visual("test_label", 200, 280)
    
    # Verify surface was created
    assert surface is not None
    assert isinstance(surface, pygame.Surface)
    assert surface.get_width() == 200
    assert surface.get_height() == 280


def test_validate_card_data_valid():
    """Test _validate_card_data() returns True for valid card."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_game.players[0].board = Mock()
    mock_game.players[0].board.grid = {}
    mock_game.players[0].hand = []
    mock_game.players[0].copies = {}
    mock_game.players[0].hp = 100
    mock_game.players[0].gold = 50
    mock_game.players[0].win_streak = 0
    mock_game.players[0].stats = {}
    mock_game.players[0].strategy = "test"
    mock_game.players[0].pid = 1
    
    game_state = CoreGameState(mock_game)
    scene = CombatScene(game_state)
    
    # Create valid card
    valid_card = Card(
        name="ValidCard",
        category="test",
        rarity="1",
        stats={"strength": 5, "agility": 4, "intelligence": 3, "vitality": 2, "luck": 1, "charisma": 6}
    )
    
    # Validate card
    assert scene._validate_card_data(valid_card) == True


def test_validate_card_data_missing_name():
    """Test _validate_card_data() returns False for card missing name."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_game.players[0].board = Mock()
    mock_game.players[0].board.grid = {}
    mock_game.players[0].hand = []
    mock_game.players[0].copies = {}
    mock_game.players[0].hp = 100
    mock_game.players[0].gold = 50
    mock_game.players[0].win_streak = 0
    mock_game.players[0].stats = {}
    mock_game.players[0].strategy = "test"
    mock_game.players[0].pid = 1
    
    game_state = CoreGameState(mock_game)
    scene = CombatScene(game_state)
    
    # Create card without name
    invalid_card = Mock()
    delattr(invalid_card, 'name')
    invalid_card.stats = {"strength": 5}
    
    # Validate card
    assert scene._validate_card_data(invalid_card) == False


def test_validate_card_data_invalid_stat_value():
    """Test _validate_card_data() returns False for invalid stat value."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_game.players[0].board = Mock()
    mock_game.players[0].board.grid = {}
    mock_game.players[0].hand = []
    mock_game.players[0].copies = {}
    mock_game.players[0].hp = 100
    mock_game.players[0].gold = 50
    mock_game.players[0].win_streak = 0
    mock_game.players[0].stats = {}
    mock_game.players[0].strategy = "test"
    mock_game.players[0].pid = 1
    
    game_state = CoreGameState(mock_game)
    scene = CombatScene(game_state)
    
    # Create card with invalid stat value (out of range)
    invalid_card = Card(
        name="InvalidCard",
        category="test",
        rarity="1",
        stats={"strength": 150, "agility": 4}  # 150 is out of range (0-99)
    )
    
    # Validate card
    assert scene._validate_card_data(invalid_card) == False


def test_create_fallback_card():
    """Test _create_fallback_card() creates card with safe defaults."""
    mock_game = Mock()
    mock_game.players = [Mock()]
    mock_game.players[0].board = Mock()
    mock_game.players[0].board.grid = {}
    mock_game.players[0].hand = []
    mock_game.players[0].copies = {}
    mock_game.players[0].hp = 100
    mock_game.players[0].gold = 50
    mock_game.players[0].win_streak = 0
    mock_game.players[0].stats = {}
    mock_game.players[0].strategy = "test"
    mock_game.players[0].pid = 1
    
    game_state = CoreGameState(mock_game)
    scene = CombatScene(game_state)
    
    # Create fallback card
    hex_coord = (2, 3)
    fallback_card = scene._create_fallback_card(hex_coord)
    
    # Verify fallback card properties
    assert fallback_card is not None
    assert fallback_card.name == "Fallback_2_3"
    assert fallback_card.category == "fallback"
    assert fallback_card.rarity == "1"
    
    # Verify all stats are set to 1
    for stat_value in fallback_card.stats.values():
        assert stat_value == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
