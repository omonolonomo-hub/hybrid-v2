"""
AI module public API.

This module maintains backward compatibility by re-exporting all public symbols.
All existing imports like `from engine_core.ai import AI, ParameterizedAI` continue to work.
"""

from engine_core.ai.base import AI, STRATEGY_MAP
from engine_core.ai.parameterized import ParameterizedAI
from engine_core.ai.config import (
    TRAINED_PARAMS,
    load_all_strategy_params,
    load_strategy_params,
    AIConfigError
)
from engine_core.ai.strategies.builder import BuilderSynergyMatrix

__all__ = [
    "AI",
    "ParameterizedAI",
    "TRAINED_PARAMS",
    "load_all_strategy_params",
    "load_strategy_params",
    "AIConfigError",
    "BuilderSynergyMatrix",
    "STRATEGY_MAP",
]
