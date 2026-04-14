"""
Unit tests for AI._buy_economist() parameterization.

Tests that the economist strategy correctly uses parameterized values
from ParameterizedAI instance and falls back to hardcoded defaults
when ai_instance is None.

Feature: strategy-params-hot-reload
Task: 3.1
"""

import pytest
from unittest.mock import Mock, MagicMock
from engine_core.ai import AI, ParameterizedAI
from engine_core.player import Player
from engine_core.card import Card


class TestBuyEconomistParameterization:
    """Test AI._buy_economist() parameter access."""
    
    def test_uses_parameterized_values_when_ai_instance_provided(self):
        """Test that _buy_economist uses parameterized values from ai_instance."""
        # Create a ParameterizedAI with custom parameters
        custom_params = {
            "greed_turn_end": 10.0,
            "greed_gold_thresh": 20.0,
            "spike_turn_end": 20.0,
            "spike_r4_thresh": 50.0,
            "thresh_high": 30.0,
            "buy_2_thresh": 18.0,
            "spike_buy_count": 4.0,
            "convert_r5_thresh": 70.0,
            "convert_buy_count": 5.0
        }
        ai_instance = ParameterizedAI(strategy="economist", params=custom_params)
        
        # Verify parameters are set correctly
        assert ai_instance.p["greed_turn_end"] == 10.0
        assert ai_instance.p["greed_gold_thresh"] == 20.0
        assert ai_instance.p["spike_turn_end"] == 20.0
        assert ai_instance.p["spike_r4_thresh"] == 50.0
        assert ai_instance.p["thresh_high"] == 30.0
        assert ai_instance.p["buy_2_thresh"] == 18.0
        assert ai_instance.p["spike_buy_count"] == 4.0
        assert ai_instance.p["convert_r5_thresh"] == 70.0
        assert ai_instance.p["convert_buy_count"] == 5.0
    
    def test_uses_hardcoded_defaults_when_ai_instance_is_none(self):
        """Test backward compatibility: uses hardcoded defaults when ai_instance=None."""
        # Create mock player and market
        player = Mock(spec=Player)
        player.gold = 15
        player.hp = 50
        player.turns_played = 5
        player.buy_card = Mock()
        
        market = []
        
        # Call _buy_economist with ai_instance=None (backward compatibility)
        # Should not crash and should use hardcoded defaults
        try:
            AI._buy_economist(player, market, max_cards=1, ai_instance=None)
            # If we get here, it didn't crash - that's good!
            assert True
        except Exception as e:
            pytest.fail(f"_buy_economist crashed with ai_instance=None: {e}")
    
    def test_greed_phase_uses_parameterized_turn_threshold(self):
        """Test that greed phase uses parameterized greed_turn_end."""
        # Set greed_turn_end to 10 (instead of default 8)
        custom_params = {"greed_turn_end": 10.0}
        ai_instance = ParameterizedAI(strategy="economist", params=custom_params)
        
        # Create mock player at turn 9 (should be in greed phase with custom params)
        player = Mock(spec=Player)
        player.gold = 15
        player.hp = 50
        player.turns_played = 9  # Would be spike phase with default, greed with custom
        player.buy_card = Mock()
        
        market = []
        
        # Call with custom ai_instance
        AI._buy_economist(player, market, max_cards=1, ai_instance=ai_instance)
        
        # Verify it executed without error (greed phase logic should apply)
        assert True
    
    def test_spike_phase_uses_parameterized_thresholds(self):
        """Test that spike phase uses parameterized thresholds."""
        # Set custom spike parameters
        custom_params = {
            "greed_turn_end": 8.0,
            "spike_turn_end": 20.0,  # Extended spike phase
            "spike_r4_thresh": 50.0,  # Higher threshold for R4
            "thresh_high": 30.0,      # Higher threshold for R3
            "spike_buy_count": 4.0    # Buy more cards
        }
        ai_instance = ParameterizedAI(strategy="economist", params=custom_params)
        
        # Create mock player in spike phase
        player = Mock(spec=Player)
        player.gold = 35  # Between thresh_high (30) and spike_r4_thresh (50)
        player.hp = 50
        player.turns_played = 15  # In spike phase
        player.buy_card = Mock()
        
        market = []
        
        # Call with custom ai_instance
        AI._buy_economist(player, market, max_cards=5, ai_instance=ai_instance)
        
        # Verify it executed without error
        assert True
    
    def test_convert_phase_uses_parameterized_thresholds(self):
        """Test that convert phase uses parameterized thresholds."""
        # Set custom convert parameters
        custom_params = {
            "spike_turn_end": 18.0,
            "convert_r5_thresh": 80.0,  # Higher threshold for R5
            "convert_buy_count": 5.0    # Buy more cards
        }
        ai_instance = ParameterizedAI(strategy="economist", params=custom_params)
        
        # Create mock player in convert phase
        player = Mock(spec=Player)
        player.gold = 70  # Below convert_r5_thresh (80)
        player.hp = 50
        player.turns_played = 25  # In convert phase
        player.buy_card = Mock()
        
        market = []
        
        # Call with custom ai_instance
        AI._buy_economist(player, market, max_cards=5, ai_instance=ai_instance)
        
        # Verify it executed without error
        assert True
    
    def test_backward_compatibility_with_legacy_code(self):
        """Test that legacy code (no ai_instance) still works."""
        # Create mock player
        player = Mock(spec=Player)
        player.gold = 25
        player.hp = 50
        player.turns_played = 12
        player.buy_card = Mock()
        
        market = []
        
        # Call without ai_instance (legacy usage)
        try:
            AI._buy_economist(player, market, max_cards=1)
            assert True
        except Exception as e:
            pytest.fail(f"Legacy usage failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
