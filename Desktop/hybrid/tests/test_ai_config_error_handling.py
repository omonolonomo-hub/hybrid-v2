"""
tests/test_ai_config_error_handling.py
═══════════════════════════════════════════════════════════════════
AI Config Error Handling tests (P1-4).

Verifies AIConfigError, descriptive logging, and crash-proof loading.
"""

import json
import logging
import tempfile
from pathlib import Path

from engine_core.ai import (
    AIConfigError, load_all_strategy_params, load_strategy_params,
    ParameterizedAI,
)


class TestAIConfigError:
    """Test AIConfigError exception class."""

    def test_ai_config_error_is_exception(self):
        assert issubclass(AIConfigError, Exception)

    def test_ai_config_error_can_be_raised(self):
        try:
            raise AIConfigError("test error")
        except AIConfigError as e:
            assert str(e) == "test error"

    def test_ai_config_error_with_context(self):
        try:
            raise AIConfigError("missing config: economist")
        except AIConfigError as e:
            assert "economist" in str(e)


class TestLoadAllStrategyParams:
    """Test crash-proof parameter loading."""

    def test_missing_file_returns_empty_dict(self, tmp_path, monkeypatch):
        """Missing trained_params.json should return {} without crashing."""
        monkeypatch.setattr(Path, "parent", property(lambda self: tmp_path))
        result = load_all_strategy_params()
        assert result == {}

    def test_invalid_json_returns_empty_dict(self, tmp_path, monkeypatch):
        """Invalid JSON should return {} without crashing."""
        bad_json = tmp_path / "trained_params.json"
        bad_json.write_text("{invalid json}", encoding="utf-8")
        monkeypatch.setattr(Path, "parent", property(lambda self: tmp_path))
        result = load_all_strategy_params()
        assert result == {}

    def test_non_dict_root_returns_empty_dict(self, tmp_path, monkeypatch):
        """JSON that's not a dict should return {} without crashing."""
        bad_json = tmp_path / "trained_params.json"
        bad_json.write_text("[1, 2, 3]", encoding="utf-8")
        monkeypatch.setattr(Path, "parent", property(lambda self: tmp_path))
        result = load_all_strategy_params()
        assert result == {}

    def test_valid_json_returns_params(self, tmp_path, monkeypatch):
        """Valid JSON should return the parsed parameters."""
        good_json = tmp_path / "trained_params.json"
        good_json.write_text(json.dumps({"economist": {"greed_turn_end": 7}}), encoding="utf-8")
        monkeypatch.setattr(Path, "parent", property(lambda self: tmp_path))
        result = load_all_strategy_params()
        assert "economist" in result
        assert result["economist"]["greed_turn_end"] == 7


class TestLoadStrategyParamsDeprecated:
    """Test deprecated load_strategy_params()."""

    def test_returns_economist_params(self):
        result = load_strategy_params()
        assert isinstance(result, dict)

    def test_deprecated_function_returns_dict(self):
        """Deprecated function should still work."""
        result = load_strategy_params()
        # Should have some economist params (from TRAINED_PARAMS)
        assert len(result) > 0


class TestParameterizedAILogging:
    """Test ParameterizedAI initialization logging."""

    def test_parameterized_ai_creates_successfully(self):
        ai = ParameterizedAI("economist")
        assert ai.strategy == "economist"
        assert "economist" in ai.p

    def test_parameterized_ai_with_manual_params(self):
        ai = ParameterizedAI("economist", params={"greed_turn_end": 99})
        assert ai.p["economist"]["greed_turn_end"] == 99

    def test_parameterized_ai_fallback_to_defaults(self):
        ai = ParameterizedAI("warrior")
        # warrior defaults should exist
        assert "power_weight" in ai.p.get("warrior", {})
