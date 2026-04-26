"""
Unit tests for ParameterizedAI parameter resolution.

Tests the three-tier priority system:
1. Manual overrides > JSON file > hardcoded defaults
2. Crash-proof file loading
3. Partial parameter merging

Feature: strategy-params-hot-reload
"""

import json
import pytest
from pathlib import Path
from engine_core.ai import ParameterizedAI, TRAINED_PARAMS, load_strategy_params


class TestLoadStrategyParams:
    """Test the load_strategy_params() helper function."""
    
    def test_missing_file_returns_empty_dict(self):
        """Test that missing file returns empty dict without crashing."""
        # Temporarily rename the file if it exists
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            result = load_strategy_params()
            assert result == {}
        finally:
            if file_existed:
                backup_file.rename(params_file)
    
    def test_invalid_json_returns_empty_dict(self):
        """Test that invalid JSON returns empty dict without crashing."""
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        # Backup existing file
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            # Create invalid JSON
            params_file.write_text("{ invalid json }")
            result = load_strategy_params()
            assert result == {}
        finally:
            # Restore
            params_file.unlink(missing_ok=True)
            if file_existed:
                backup_file.rename(params_file)
    
    def test_valid_json_loads_economist_params(self):
        """Test that valid JSON file loads economist parameters correctly."""
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        # Backup existing file
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            # Create test file
            test_params = {
                "economist": {
                    "thresh_high": 30.0,
                    "greed_turn_end": 10.0
                }
            }
            params_file.write_text(json.dumps(test_params))
            
            result = load_strategy_params()
            assert result == test_params["economist"]
        finally:
            # Restore
            params_file.unlink(missing_ok=True)
            if file_existed:
                backup_file.rename(params_file)


class TestParameterizedAIInit:
    """Test ParameterizedAI.__init__() parameter resolution."""
    
    def test_defaults_only_when_no_file_no_params(self):
        """Test that defaults are used when no file and no params provided."""
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        # Backup and remove file
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            ai = ParameterizedAI(strategy="economist")
            # Should use TRAINED_PARAMS defaults
            assert ai.p == TRAINED_PARAMS["economist"]
        finally:
            if file_existed:
                backup_file.rename(params_file)
    
    def test_manual_params_override_defaults(self):
        """Test that manual params override defaults (Requirement 4.1)."""
        manual_params = {
            "thresh_high": 99.0,
            "greed_turn_end": 20.0
        }
        
        ai = ParameterizedAI(strategy="economist", params=manual_params)
        
        # Manual params should override
        assert ai.p["thresh_high"] == 99.0
        assert ai.p["greed_turn_end"] == 20.0
        
        # Other defaults should still be present
        assert "spike_turn_end" in ai.p
        assert ai.p["spike_turn_end"] == TRAINED_PARAMS["economist"]["spike_turn_end"]
    
    def test_partial_params_merge_with_defaults(self):
        """Test that partial params merge correctly (Requirement 4.4)."""
        partial_params = {
            "thresh_high": 50.0
        }
        
        ai = ParameterizedAI(strategy="economist", params=partial_params)
        
        # Provided param should be present
        assert ai.p["thresh_high"] == 50.0
        
        # Missing params should have defaults
        assert "greed_turn_end" in ai.p
        assert "spike_turn_end" in ai.p
        assert ai.p["greed_turn_end"] == TRAINED_PARAMS["economist"]["greed_turn_end"]
    
    def test_file_params_override_defaults(self):
        """Test that file params override defaults (Requirement 4.2)."""
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        # Backup existing file
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            # Create test file
            file_params = {
                "economist": {
                    "thresh_high": 35.0,
                    "greed_turn_end": 12.0
                }
            }
            params_file.write_text(json.dumps(file_params))
            
            ai = ParameterizedAI(strategy="economist")
            
            # File params should override defaults
            assert ai.p["thresh_high"] == 35.0
            assert ai.p["greed_turn_end"] == 12.0
            
            # Other defaults should still be present
            assert "spike_turn_end" in ai.p
        finally:
            # Restore
            params_file.unlink(missing_ok=True)
            if file_existed:
                backup_file.rename(params_file)
    
    def test_manual_params_override_file_params(self):
        """Test priority: manual > file > defaults (Requirement 4.1)."""
        project_root = Path(__file__).parent.parent.parent
        params_file = project_root / "trained_params.json"
        backup_file = project_root / "trained_params.json.backup"
        
        # Backup existing file
        file_existed = params_file.exists()
        if file_existed:
            params_file.rename(backup_file)
        
        try:
            # Create test file
            file_params = {
                "economist": {
                    "thresh_high": 35.0,
                    "greed_turn_end": 12.0
                }
            }
            params_file.write_text(json.dumps(file_params))
            
            # Provide manual override
            manual_params = {
                "thresh_high": 100.0
            }
            
            ai = ParameterizedAI(strategy="economist", params=manual_params)
            
            # Manual should win
            assert ai.p["thresh_high"] == 100.0
            
            # File param should be used for non-overridden keys
            assert ai.p["greed_turn_end"] == 12.0
        finally:
            # Restore
            params_file.unlink(missing_ok=True)
            if file_existed:
                backup_file.rename(params_file)
    
    def test_strategy_attribute_set(self):
        """Test that strategy attribute is set correctly."""
        ai = ParameterizedAI(strategy="economist")
        assert ai.strategy == "economist"
    
    def test_parameters_cached_in_self_p(self):
        """Test that resolved parameters are cached in self.p (Requirement 3.4)."""
        ai = ParameterizedAI(strategy="economist")
        assert hasattr(ai, 'p')
        assert isinstance(ai.p, dict)
        assert len(ai.p) > 0


class TestParameterizedAIIntegration:
    """Integration tests for ParameterizedAI with AI class."""
    
    def test_has_buy_cards_method(self):
        """Test that ParameterizedAI has buy_cards method."""
        ai = ParameterizedAI(strategy="economist")
        assert hasattr(ai, 'buy_cards')
        assert callable(ai.buy_cards)
    
    def test_has_place_cards_method(self):
        """Test that ParameterizedAI has place_cards method."""
        ai = ParameterizedAI(strategy="economist")
        assert hasattr(ai, 'place_cards')
        assert callable(ai.place_cards)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
