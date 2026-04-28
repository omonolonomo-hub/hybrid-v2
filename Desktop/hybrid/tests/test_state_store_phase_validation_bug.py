"""
Bug Condition Exploration Test: StateStore.phase Validation Missing

This test demonstrates Bug 3 from ACIL/IMMEDIATE fixes (OMNISCIENT AUDIT V7).

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Bug Condition:
    When StateStore.phase is set to an invalid string (not in VALID_PHASES),
    the setter accepts it silently without validation, causing phase guards
    to fail silently downstream.

Expected Behavior (after fix):
    When StateStore.phase is set to an invalid string, the setter SHALL raise
    ValueError with a clear error message listing valid phases.

Test Strategy:
    Test concrete failing cases that demonstrate silent acceptance of invalid phases:
    - "STATE_GARBAGE" (completely invalid)
    - "STATE_PREPARTION" (typo)
    - "" (empty string)

EXPECTED OUTCOME ON UNFIXED CODE:
    All tests FAIL because invalid phases are accepted silently (no ValueError raised).
    This is CORRECT - it proves the bug exists.

Requirements: 1.7, 1.8
"""

import pytest
from v2.core.state_store import StateStore


class TestStateStorePhaseValidationBug:
    """
    Bug Condition Exploration: Invalid Phase Silently Accepted
    
    These tests encode the EXPECTED BEHAVIOR (ValueError raised for invalid phases).
    On UNFIXED code, they will FAIL (invalid phases accepted silently).
    On FIXED code, they will PASS (ValueError raised as expected).
    """

    def test_invalid_phase_garbage_should_raise_error(self):
        """
        Test Case 1: Completely invalid phase string
        
        Bug Condition: StateStore.phase = "STATE_GARBAGE" is accepted silently
        Expected Behavior: ValueError raised with clear error message
        
        EXPECTED ON UNFIXED CODE: FAILS (no ValueError raised)
        EXPECTED ON FIXED CODE: PASSES (ValueError raised)
        """
        store = StateStore()
        
        # On unfixed code: this will NOT raise ValueError (bug exists)
        # On fixed code: this WILL raise ValueError (bug fixed)
        with pytest.raises(ValueError) as exc_info:
            store.phase = "STATE_GARBAGE"
        
        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "Invalid phase" in error_msg
        assert "STATE_GARBAGE" in error_msg
        assert "STATE_PREPARATION" in error_msg
        assert "STATE_VERSUS" in error_msg
        assert "STATE_COMBAT" in error_msg
        assert "STATE_ENDGAME" in error_msg

    def test_invalid_phase_typo_should_raise_error(self):
        """
        Test Case 2: Typo in valid phase name
        
        Bug Condition: StateStore.phase = "STATE_PREPARTION" (typo) is accepted silently
        Expected Behavior: ValueError raised with clear error message
        
        EXPECTED ON UNFIXED CODE: FAILS (no ValueError raised)
        EXPECTED ON FIXED CODE: PASSES (ValueError raised)
        """
        store = StateStore()
        
        # On unfixed code: this will NOT raise ValueError (bug exists)
        # On fixed code: this WILL raise ValueError (bug fixed)
        with pytest.raises(ValueError) as exc_info:
            store.phase = "STATE_PREPARTION"  # Typo: missing 'A'
        
        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "Invalid phase" in error_msg
        assert "STATE_PREPARTION" in error_msg

    def test_invalid_phase_empty_string_should_raise_error(self):
        """
        Test Case 3: Empty string phase
        
        Bug Condition: StateStore.phase = "" is accepted silently
        Expected Behavior: ValueError raised with clear error message
        
        EXPECTED ON UNFIXED CODE: FAILS (no ValueError raised)
        EXPECTED ON FIXED CODE: PASSES (ValueError raised)
        """
        store = StateStore()
        
        # On unfixed code: this will NOT raise ValueError (bug exists)
        # On fixed code: this WILL raise ValueError (bug fixed)
        with pytest.raises(ValueError) as exc_info:
            store.phase = ""
        
        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "Invalid phase" in error_msg

    def test_multiple_invalid_phases_all_rejected(self):
        """
        Test Case 4: Multiple invalid phase strings
        
        Bug Condition: All invalid phases are accepted silently
        Expected Behavior: All invalid phases raise ValueError
        
        EXPECTED ON UNFIXED CODE: FAILS (no ValueError raised for any)
        EXPECTED ON FIXED CODE: PASSES (ValueError raised for all)
        """
        store = StateStore()
        
        invalid_phases = [
            "INVALID",
            "STATE_INVALID",
            "state_preparation",  # lowercase
            "STATE_PREP",  # abbreviated
            "STATE_COMBAT_PHASE",  # extra suffix
            "None",
            "null",
        ]
        
        for invalid_phase in invalid_phases:
            # On unfixed code: this will NOT raise ValueError (bug exists)
            # On fixed code: this WILL raise ValueError (bug fixed)
            with pytest.raises(ValueError) as exc_info:
                store.phase = invalid_phase
            
            # Verify error message mentions the invalid value
            error_msg = str(exc_info.value)
            assert "Invalid phase" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
