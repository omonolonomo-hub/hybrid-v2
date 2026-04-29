"""
Architectural Defect Exploration Tests for AI Strategy Decoupling

Property 1: Bug Condition - Monolithic Architecture Defects

CRITICAL: These tests MUST PASS on unfixed code - passing confirms the architectural defects exist.
DO NOT attempt to fix the tests or the code when they pass.

These tests encode the expected modular architecture - they will validate the refactoring
when they fail after implementation.

GOAL: Confirm the architectural defects exist in the current codebase.

Expected Outcome: Tests PASS (this is correct - it proves the architectural defects exist)
"""

import os
import sys
import importlib
import inspect
import pytest
from pathlib import Path


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_all_strategies_in_single_monolithic_file():
    """
    Bug Condition 1.1: All 8 AI strategies exist in a single monolithic file.
    
    This test confirms that all strategy implementations are coupled in engine_core/ai.py.
    When this test PASSES, it proves the architectural defect exists.
    When this test FAILS (after refactoring), it proves strategies are decoupled.
    
    Validates Requirements: 1.1, 2.1
    """
    ai_file_path = Path("engine_core/ai.py")
    
    # Confirm the monolithic file exists
    assert ai_file_path.exists(), "engine_core/ai.py should exist (monolithic structure)"
    
    # Read the file content
    content = ai_file_path.read_text(encoding='utf-8')
    
    # All 8 strategy classes should be defined in this single file
    expected_strategies = [
        "class RandomStrategy",
        "class WarriorStrategy",
        "class EconomistStrategy",
        "class BuilderStrategy",
        "class EvolverStrategy",
        "class BalancerStrategy",
        "class RareHunterStrategy",
        "class TempoStrategy",
    ]
    
    for strategy_class in expected_strategies:
        assert strategy_class in content, (
            f"{strategy_class} should be defined in engine_core/ai.py (monolithic structure). "
            f"If this fails, the strategy has been decoupled (expected after refactoring)."
        )
    
    # Confirm that no separate strategy modules exist yet
    strategies_dir = Path("engine_core/ai/strategies")
    assert not strategies_dir.exists(), (
        "engine_core/ai/strategies/ directory should NOT exist yet (monolithic structure). "
        "If this fails, the refactoring has already been applied."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_monolithic_file_size_confirms_coupling():
    """
    Bug Condition 1.1: The engine_core/ai.py file is >= 55KB, confirming monolithic structure.
    
    This test confirms that all strategies, utilities, and configuration are coupled
    in a single large file.
    
    When this test PASSES, it proves the monolithic structure exists.
    When this test FAILS (after refactoring), it proves the code has been decoupled.
    
    Validates Requirements: 1.1, 1.4
    """
    ai_file_path = Path("engine_core/ai.py")
    
    assert ai_file_path.exists(), "engine_core/ai.py should exist"
    
    file_size_bytes = ai_file_path.stat().st_size
    file_size_kb = file_size_bytes / 1024
    
    # The monolithic file should be >= 55KB
    assert file_size_kb >= 55.0, (
        f"engine_core/ai.py should be >= 55KB (monolithic structure), "
        f"but found {file_size_kb:.2f}KB. "
        f"If this fails, the file has been split (expected after refactoring)."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_importing_ai_loads_builder_synergy_matrix_eagerly():
    """
    Bug Condition 1.3: Importing AI loads BuilderSynergyMatrix even when not using builder strategy.
    
    This test confirms eager loading of all dependencies regardless of which strategy is used.
    
    When this test PASSES, it proves eager loading exists (architectural defect).
    When this test FAILS (after refactoring), it proves lazy loading is implemented.
    
    Validates Requirements: 1.3, 2.3
    """
    # Clear any cached imports
    if 'engine_core.ai' in sys.modules:
        del sys.modules['engine_core.ai']
    
    # Import the AI module
    import engine_core.ai as ai_module
    
    # Check if BuilderSynergyMatrix is defined in the same module
    assert hasattr(ai_module, 'BuilderSynergyMatrix'), (
        "BuilderSynergyMatrix should be defined in engine_core.ai (eager loading). "
        "If this fails, BuilderSynergyMatrix has been moved to a separate module (expected after refactoring)."
    )
    
    # Verify it's a class defined in the ai module, not imported from elsewhere
    builder_synergy_class = getattr(ai_module, 'BuilderSynergyMatrix')
    assert inspect.isclass(builder_synergy_class), "BuilderSynergyMatrix should be a class"
    
    # Check that it's defined in the ai.py file itself (not imported)
    source_file = inspect.getfile(builder_synergy_class)
    assert source_file.endswith('ai.py'), (
        f"BuilderSynergyMatrix should be defined in ai.py (eager loading), "
        f"but found in {source_file}. "
        f"If this fails, it has been moved to a separate module (expected after refactoring)."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_adding_new_strategy_requires_modifying_existing_file():
    """
    Bug Condition 1.2: Adding a new strategy requires modifying engine_core/ai.py.
    
    This test confirms violation of the Open/Closed Principle - the system is not
    open for extension without modification.
    
    When this test PASSES, it proves the Open/Closed violation exists.
    When this test FAILS (after refactoring), it proves strategies can be added
    without modifying existing files.
    
    Validates Requirements: 1.2, 2.2
    """
    ai_file_path = Path("engine_core/ai.py")
    
    # The monolithic file should exist
    assert ai_file_path.exists(), "engine_core/ai.py should exist (monolithic structure)"
    
    content = ai_file_path.read_text(encoding='utf-8')
    
    # STRATEGY_MAP should be defined in the same file as all strategy implementations
    assert "STRATEGY_MAP" in content, (
        "STRATEGY_MAP should be defined in engine_core/ai.py (monolithic structure). "
        "If this fails, STRATEGY_MAP has been moved to a separate module."
    )
    
    # All strategy registrations should be in the same file
    # This means adding a new strategy requires editing this file
    assert '"random":' in content or "'random':" in content, (
        "Strategy registration should be in engine_core/ai.py (Open/Closed violation)"
    )
    
    # Confirm that there's no separate strategies directory where new strategies
    # could be added without modifying existing files
    strategies_dir = Path("engine_core/ai/strategies")
    assert not strategies_dir.exists(), (
        "engine_core/ai/strategies/ should NOT exist (Open/Closed violation). "
        "If this fails, the modular architecture has been implemented."
    )
    
    # Confirm that there's no base.py module that could handle strategy registration
    base_module_path = Path("engine_core/ai/base.py")
    assert not base_module_path.exists(), (
        "engine_core/ai/base.py should NOT exist (monolithic structure). "
        "If this fails, the refactoring has been applied."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_shared_utilities_buried_in_monolithic_class():
    """
    Bug Condition 1.5: Shared helper functions are buried in the monolithic AI class.
    
    This test confirms that utilities like _economy_phase_controls cannot be easily
    reused without importing the entire AI module.
    
    When this test PASSES, it proves poor code organization exists.
    When this test FAILS (after refactoring), it proves utilities are properly extracted.
    
    Validates Requirements: 1.5, 2.5
    """
    ai_file_path = Path("engine_core/ai.py")
    
    assert ai_file_path.exists(), "engine_core/ai.py should exist"
    
    content = ai_file_path.read_text(encoding='utf-8')
    
    # _economy_phase_controls should be defined in the monolithic file
    assert "_economy_phase_controls" in content, (
        "_economy_phase_controls should be defined in engine_core/ai.py (poor organization). "
        "If this fails, it has been extracted to a utils module."
    )
    
    # There should be no separate utils.py module yet
    utils_module_path = Path("engine_core/ai/utils.py")
    assert not utils_module_path.exists(), (
        "engine_core/ai/utils.py should NOT exist yet (monolithic structure). "
        "If this fails, utilities have been extracted (expected after refactoring)."
    )
    
    # _get_param_with_fallback should also be in the monolithic file
    assert "_get_param_with_fallback" in content, (
        "_get_param_with_fallback should be defined in engine_core/ai.py (poor organization). "
        "If this fails, it has been extracted to a utils module."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_configuration_mixed_with_strategy_implementations():
    """
    Bug Condition: Configuration loading is mixed with strategy implementations.
    
    This test confirms that TRAINED_PARAMS and load_all_strategy_params are defined
    in the same file as all strategy implementations, violating separation of concerns.
    
    When this test PASSES, it proves poor separation of concerns exists.
    When this test FAILS (after refactoring), it proves configuration is isolated.
    
    Validates Requirements: 1.1, 2.1
    """
    ai_file_path = Path("engine_core/ai.py")
    
    assert ai_file_path.exists(), "engine_core/ai.py should exist"
    
    content = ai_file_path.read_text(encoding='utf-8')
    
    # TRAINED_PARAMS should be defined in the monolithic file
    assert "TRAINED_PARAMS" in content, (
        "TRAINED_PARAMS should be defined in engine_core/ai.py (poor separation). "
        "If this fails, it has been moved to a config module."
    )
    
    # load_all_strategy_params should be in the same file
    assert "def load_all_strategy_params" in content, (
        "load_all_strategy_params should be defined in engine_core/ai.py (poor separation). "
        "If this fails, it has been moved to a config module."
    )
    
    # There should be no separate config.py module yet
    config_module_path = Path("engine_core/ai/config.py")
    assert not config_module_path.exists(), (
        "engine_core/ai/config.py should NOT exist yet (monolithic structure). "
        "If this fails, configuration has been extracted (expected after refactoring)."
    )


@pytest.mark.xfail(
    reason="AI architecture was refactored — defects no longer exist. "
           "These tests document the OLD state and are expected to fail.",
    strict=False
)
def test_no_modular_directory_structure_exists():
    """
    Bug Condition: No modular directory structure exists for AI strategies.
    
    This test confirms that the engine_core/ai/ directory structure does not exist,
    proving that all code is in a single file.
    
    When this test PASSES, it proves the monolithic structure exists.
    When this test FAILS (after refactoring), it proves the modular structure is in place.
    
    Validates Requirements: 1.1, 2.1
    """
    # The ai/ directory should not exist as a package yet
    ai_dir = Path("engine_core/ai")
    
    if ai_dir.exists():
        # If it exists, it should not have an __init__.py (not a package yet)
        init_file = ai_dir / "__init__.py"
        assert not init_file.exists(), (
            "engine_core/ai/__init__.py should NOT exist yet (monolithic structure). "
            "If this fails, the modular package structure has been created."
        )
    
    # Key modular files should not exist
    expected_modular_files = [
        "engine_core/ai/__init__.py",
        "engine_core/ai/base.py",
        "engine_core/ai/config.py",
        "engine_core/ai/utils.py",
        "engine_core/ai/parameterized.py",
        "engine_core/ai/strategies/__init__.py",
        "engine_core/ai/strategies/random.py",
        "engine_core/ai/strategies/warrior.py",
        "engine_core/ai/strategies/economist.py",
        "engine_core/ai/strategies/builder.py",
    ]
    
    for file_path_str in expected_modular_files:
        file_path = Path(file_path_str)
        assert not file_path.exists(), (
            f"{file_path_str} should NOT exist yet (monolithic structure). "
            f"If this fails, the modular structure has been created (expected after refactoring)."
        )


if __name__ == "__main__":
    """
    Run these tests to confirm the architectural defects exist.
    
    Expected outcome: ALL TESTS PASS
    
    This proves:
    - All strategies are in a single 55KB+ file
    - BuilderSynergyMatrix is loaded eagerly
    - Adding new strategies requires modifying existing code
    - Shared utilities are buried in the monolithic class
    - Configuration is mixed with implementations
    - No modular directory structure exists
    
    After refactoring, these same tests should FAIL, proving the defects are fixed.
    """
    import pytest
    pytest.main([__file__, "-v"])
