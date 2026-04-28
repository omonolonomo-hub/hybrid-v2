"""
Preservation Unit Tests: StateStore.phase Valid Phase Assignment

This test validates that the fix for Bug 3 (StateStore.phase validation)
preserves all existing behavior for valid phase assignments.

Property 2: Preservation - Valid Phase Assignment
    For any attempt to set StateStore.phase to a valid phase string
    (in VALID_PHASES), the fixed setter SHALL accept and store the value
    exactly as the original setter did, preserving all existing phase
    transition logic.

Test Strategy:
    1. Observe behavior on UNFIXED code for valid phase assignments
    2. Write unit tests capturing observed behavior patterns
    3. Run tests on UNFIXED code - EXPECTED OUTCOME: Tests PASS
    4. After fix is applied, re-run tests - EXPECTED OUTCOME: Tests still PASS

Requirements Validated: 3.7, 3.8, 3.9
"""

import pytest
from v2.core.state_store import StateStore


class TestStateStorePhasePreservation:
    """
    Preservation Tests: Valid Phase Assignment
    
    These tests verify that valid phase assignments continue to work
    correctly after the validation fix is applied.
    
    EXPECTED ON UNFIXED CODE: ALL TESTS PASS (baseline behavior)
    EXPECTED ON FIXED CODE: ALL TESTS PASS (no regressions)
    """
    
    def test_all_valid_phases_accepted(self):
        """
        Test 1: All four valid phases are accepted and stored correctly
        
        Preservation Requirement 3.7: Valid phase strings from the defined
        set SHALL CONTINUE TO be accepted and stored.
        
        EXPECTED ON UNFIXED CODE: PASSES
        EXPECTED ON FIXED CODE: PASSES (no regression)
        """
        store = StateStore()
        
        # Test all four valid phases
        valid_phases = [
            "STATE_PREPARATION",
            "STATE_VERSUS",
            "STATE_COMBAT",
            "STATE_ENDGAME"
        ]
        
        for phase in valid_phases:
            # Should accept without error
            store.phase = phase
            
            # Should store correctly
            assert store.phase == phase, \
                f"Phase '{phase}' should be stored correctly"
    
    def test_phase_transitions_work_correctly(self):
        """
        Test 2: Phase transitions work correctly
        
        Preservation Requirement 3.8: Phase transitions SHALL CONTINUE TO
        function as currently implemented.
        
        This test simulates a typical game flow through all phases.
        
        EXPECTED ON UNFIXED CODE: PASSES
        EXPECTED ON FIXED CODE: PASSES (no regression)
        """
        store = StateStore()
        
        # Initial phase should be STATE_PREPARATION
        assert store.phase == "STATE_PREPARATION", \
            "Initial phase should be STATE_PREPARATION"
        
        # Transition to STATE_VERSUS (after ready button)
        store.phase = "STATE_VERSUS"
        assert store.phase == "STATE_VERSUS", \
            "Should transition to STATE_VERSUS"
        
        # Transition to STATE_COMBAT (after versus overlay)
        store.phase = "STATE_COMBAT"
        assert store.phase == "STATE_COMBAT", \
            "Should transition to STATE_COMBAT"
        
        # Transition to STATE_PREPARATION (next turn)
        store.phase = "STATE_PREPARATION"
        assert store.phase == "STATE_PREPARATION", \
            "Should transition back to STATE_PREPARATION"
        
        # Transition to STATE_ENDGAME (game over)
        store.phase = "STATE_ENDGAME"
        assert store.phase == "STATE_ENDGAME", \
            "Should transition to STATE_ENDGAME"
    
    def test_phase_guards_work_correctly(self):
        """
        Test 3: Phase guards (e.g., `if phase == "STATE_PREPARATION"`) work correctly
        
        Preservation Requirement 3.9: Phase guards SHALL CONTINUE TO return
        the stored phase value for comparison.
        
        This test verifies that phase comparisons (guards) work as expected.
        
        EXPECTED ON UNFIXED CODE: PASSES
        EXPECTED ON FIXED CODE: PASSES (no regression)
        """
        store = StateStore()
        
        # Test STATE_PREPARATION guard
        store.phase = "STATE_PREPARATION"
        assert store.phase == "STATE_PREPARATION", \
            "Phase guard for STATE_PREPARATION should work"
        assert store.phase != "STATE_VERSUS", \
            "Phase guard should distinguish STATE_PREPARATION from STATE_VERSUS"
        
        # Test STATE_VERSUS guard
        store.phase = "STATE_VERSUS"
        assert store.phase == "STATE_VERSUS", \
            "Phase guard for STATE_VERSUS should work"
        assert store.phase != "STATE_COMBAT", \
            "Phase guard should distinguish STATE_VERSUS from STATE_COMBAT"
        
        # Test STATE_COMBAT guard
        store.phase = "STATE_COMBAT"
        assert store.phase == "STATE_COMBAT", \
            "Phase guard for STATE_COMBAT should work"
        assert store.phase != "STATE_ENDGAME", \
            "Phase guard should distinguish STATE_COMBAT from STATE_ENDGAME"
        
        # Test STATE_ENDGAME guard
        store.phase = "STATE_ENDGAME"
        assert store.phase == "STATE_ENDGAME", \
            "Phase guard for STATE_ENDGAME should work"
        assert store.phase != "STATE_PREPARATION", \
            "Phase guard should distinguish STATE_ENDGAME from STATE_PREPARATION"
    
    def test_multiple_phase_assignments(self):
        """
        Test 4: Multiple phase assignments work correctly
        
        This test verifies that the phase property can be set multiple times
        without issues, which is common in game loops.
        
        EXPECTED ON UNFIXED CODE: PASSES
        EXPECTED ON FIXED CODE: PASSES (no regression)
        """
        store = StateStore()
        
        # Simulate multiple turns
        for _ in range(3):
            store.phase = "STATE_PREPARATION"
            assert store.phase == "STATE_PREPARATION"
            
            store.phase = "STATE_VERSUS"
            assert store.phase == "STATE_VERSUS"
            
            store.phase = "STATE_COMBAT"
            assert store.phase == "STATE_COMBAT"
        
        # Simulate game over
        store.phase = "STATE_ENDGAME"
        assert store.phase == "STATE_ENDGAME"
    
    def test_phase_property_getter(self):
        """
        Test 5: Phase property getter works correctly
        
        This test verifies that the phase getter returns the correct value
        after assignment.
        
        EXPECTED ON UNFIXED CODE: PASSES
        EXPECTED ON FIXED CODE: PASSES (no regression)
        """
        store = StateStore()
        
        # Test getter for each valid phase
        for phase in ["STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"]:
            store.phase = phase
            retrieved_phase = store.phase
            
            assert retrieved_phase == phase, \
                f"Getter should return '{phase}' after assignment"
            assert isinstance(retrieved_phase, str), \
                "Getter should return a string"
