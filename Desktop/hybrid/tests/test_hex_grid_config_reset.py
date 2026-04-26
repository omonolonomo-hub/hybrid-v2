"""
Test suite for HexGridConfig reset functionality.

Verifies that reset_default_config() properly clears the singleton
and allows test isolation with different BOARD_RADIUS values.
"""

import pytest
from v2.ui.hex_grid_config import HexGridConfig, get_default_config, reset_default_config


def test_reset_default_config_clears_singleton():
    """Test that reset_default_config clears the singleton instance."""
    # First call creates singleton
    config1 = get_default_config()
    assert config1 is not None
    
    # Reset clears it
    reset_default_config()
    
    # Next call creates new instance
    config2 = get_default_config()
    assert config2 is not None
    
    # They should be different instances (not the same object)
    assert config1 is not config2


def test_get_default_config_returns_same_instance_before_reset():
    """Test that get_default_config returns the same instance when called multiple times."""
    reset_default_config()  # Start fresh
    
    config1 = get_default_config()
    config2 = get_default_config()
    
    # Should be the same instance (singleton pattern)
    assert config1 is config2


def test_hex_grid_config_has_valid_coords():
    """Test that HexGridConfig properly initializes with valid coordinates."""
    reset_default_config()
    config = get_default_config()
    
    assert hasattr(config, 'valid_coords')
    assert hasattr(config, 'board_radius')
    assert len(config.valid_coords) > 0
    assert isinstance(config.valid_coords, frozenset)


def test_from_custom_creates_independent_instance():
    """Test that from_custom creates an independent config instance."""
    base_config = get_default_config()
    
    # Create custom config with modified coordinates
    disabled_hex = (1, 2)
    new_coords = base_config.valid_coords - {disabled_hex}
    custom_config = HexGridConfig.from_custom(base_config.board_radius, new_coords)
    
    # Custom config should be different instance
    assert custom_config is not base_config
    
    # Custom config should have fewer coordinates
    assert len(custom_config.valid_coords) == len(base_config.valid_coords) - 1
    assert disabled_hex not in custom_config.valid_coords
    assert disabled_hex in base_config.valid_coords


def test_reset_allows_test_isolation():
    """Test that reset enables test isolation for different configurations."""
    # Simulate test 1 with default config
    reset_default_config()
    config1 = get_default_config()
    original_radius = config1.board_radius
    
    # Simulate test 2 with reset (would have different engine state in real scenario)
    reset_default_config()
    config2 = get_default_config()
    
    # In same process, configs should be different instances
    assert config1 is not config2
    
    # But should have same values (since engine state is same in this test)
    assert config2.board_radius == original_radius


def test_shop_scene_uses_instance_config():
    """Test that ShopScene properly initializes with instance-based config."""
    from v2.scenes.shop import ShopScene
    from v2.core.game_state import GameState
    
    # Create a minimal GameState for testing
    game_state = GameState()
    scene = ShopScene(game_state)
    
    # Should have _hex_config attribute
    assert hasattr(scene, '_hex_config')
    assert scene._hex_config is not None
    assert isinstance(scene._hex_config, HexGridConfig)


def test_minimap_hud_uses_instance_config():
    """Test that MinimapHUD properly initializes with instance-based config."""
    from v2.ui.minimap_hud import MinimapHUD
    
    minimap = MinimapHUD()
    
    # Should have _hex_config attribute
    assert hasattr(minimap, '_hex_config')
    assert minimap._hex_config is not None
    assert isinstance(minimap._hex_config, HexGridConfig)


def test_backward_compatibility_with_module_level_import():
    """Test that old-style module-level imports still work via __getattr__."""
    from v2.ui.hex_grid import VALID_HEX_COORDS, BOARD_RADIUS
    
    # Should work through backward compatibility layer
    assert VALID_HEX_COORDS is not None
    assert isinstance(VALID_HEX_COORDS, frozenset)
    assert len(VALID_HEX_COORDS) > 0
    
    assert BOARD_RADIUS is not None
    assert isinstance(BOARD_RADIUS, int)
    assert BOARD_RADIUS > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
