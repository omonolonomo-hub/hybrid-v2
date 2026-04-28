"""
Bug Condition Exploration Test: Signal.emit() Fatal Crash
═══════════════════════════════════════════════════════════════════

Property 1: Bug Condition - Observer Disconnect During Emit

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
DO NOT attempt to fix the test or the code when it fails
NOTE: This test encodes the expected behavior - it will validate the fix when it passes

GOAL: Surface counterexamples that demonstrate the RuntimeError exists

Test implementation details from Bug Condition in design:
- Create Signal instance
- Connect observer that disconnects itself during callback
- Call emit() and verify RuntimeError: "dictionary changed size during iteration"
- Connect observer A that disconnects observer B during callback
- Call emit() and verify RuntimeError occurs

EXPECTED OUTCOME: Test FAILS with RuntimeError (this is correct - it proves the bug exists)

Requirements: 1.1, 1.2
═══════════════════════════════════════════════════════════════════
"""

import pytest
from engine_core.signals import Signal


class TestSignalEmitCrashBugCondition:
    """
    Bug Condition Exploration: Observer disconnects during emit()
    
    These tests demonstrate the bug on UNFIXED code by showing that
    RuntimeError occurs when observers modify the observer list during iteration.
    """
    
    def test_observer_disconnects_self_during_emit(self):
        """
        Test Case 1: Observer disconnects itself during callback
        
        Bug Condition: isBugCondition(input) where
            input.is_emitting == True AND
            input.observer_list_modified_during_iteration == True AND
            input.observer_disconnects_self == True
        
        Expected Behavior (after fix): emit() completes without crash
        Current Behavior (unfixed): RuntimeError: "dictionary changed size during iteration"
        """
        signal = Signal()
        disconnect_called = []
        
        def observer_that_disconnects_self(**kwargs):
            """Observer that disconnects itself during notification"""
            disconnect_called.append(True)
            signal.disconnect(observer_that_disconnects_self)
        
        # Connect the self-disconnecting observer
        signal.connect(observer_that_disconnects_self)
        
        # Call emit() - this should complete without RuntimeError (expected behavior)
        # On UNFIXED code, this will raise RuntimeError
        signal.emit(test_data="value")
        
        # Verify the observer was called and disconnected itself
        assert len(disconnect_called) == 1, "Observer should have been called once"
        assert observer_that_disconnects_self not in signal._observers, \
            "Observer should have disconnected itself"
    
    def test_observer_disconnects_other_during_emit(self):
        """
        Test Case 2: Observer A disconnects Observer B during callback
        
        Bug Condition: isBugCondition(input) where
            input.is_emitting == True AND
            input.observer_list_modified_during_iteration == True AND
            input.observer_disconnects_other == True
        
        Expected Behavior (after fix): emit() completes without crash
        Current Behavior (unfixed): RuntimeError: "dictionary changed size during iteration"
        """
        signal = Signal()
        observer_a_called = []
        observer_b_called = []
        
        def observer_b(**kwargs):
            """Observer B - will be disconnected by Observer A"""
            observer_b_called.append(True)
        
        def observer_a(**kwargs):
            """Observer A - disconnects Observer B during notification"""
            observer_a_called.append(True)
            signal.disconnect(observer_b)
        
        # Connect both observers (A will be called first)
        signal.connect(observer_a)
        signal.connect(observer_b)
        
        # Call emit() - this should complete without RuntimeError (expected behavior)
        # On UNFIXED code, this will raise RuntimeError
        signal.emit(test_data="value")
        
        # Verify Observer A was called and disconnected Observer B
        assert len(observer_a_called) == 1, "Observer A should have been called once"
        assert observer_b not in signal._observers, \
            "Observer B should have been disconnected by Observer A"
    
    def test_multiple_observers_disconnect_during_single_emit(self):
        """
        Test Case 3: Multiple observers disconnect during single emit()
        
        Bug Condition: isBugCondition(input) where
            input.is_emitting == True AND
            input.observer_list_modified_during_iteration == True AND
            input.multiple_disconnections == True
        
        Expected Behavior (after fix): emit() completes without crash
        Current Behavior (unfixed): RuntimeError or unpredictable observer call order
        """
        signal = Signal()
        call_log = []
        
        def observer_1(**kwargs):
            """First observer - disconnects itself"""
            call_log.append("observer_1")
            signal.disconnect(observer_1)
        
        def observer_2(**kwargs):
            """Second observer - disconnects observer_3"""
            call_log.append("observer_2")
            signal.disconnect(observer_3)
        
        def observer_3(**kwargs):
            """Third observer - may or may not be called depending on timing"""
            call_log.append("observer_3")
        
        # Connect all three observers
        signal.connect(observer_1)
        signal.connect(observer_2)
        signal.connect(observer_3)
        
        # Call emit() - this should complete without RuntimeError (expected behavior)
        # On UNFIXED code, this may raise RuntimeError or skip observers unpredictably
        signal.emit(test_data="value")
        
        # Verify observer_1 was called (it's first, so it should always be called)
        assert "observer_1" in call_log, "Observer 1 should have been called"
        
        # The bug manifests as unpredictable behavior:
        # - observer_2 might be skipped if observer_1's disconnect shifts the list
        # - observer_3 might be called even though observer_2 tried to disconnect it
        # This demonstrates the list modification during iteration bug
        
        # Document the actual behavior for counterexample analysis
        print(f"Call log: {call_log}")
        print(f"Remaining observers: {len(signal._observers)}")
        
        # Verify disconnections happened (even if call order was wrong)
        assert observer_1 not in signal._observers, "Observer 1 should be disconnected"
    
    def test_last_observer_disconnects_itself(self):
        """
        Test Case 4: Last observer in list disconnects itself
        
        Edge Case: Last observer disconnects itself during notification
        
        Bug Condition: isBugCondition(input) where
            input.is_emitting == True AND
            input.observer_list_modified_during_iteration == True AND
            input.observer_disconnects_self == True AND
            input.is_last_observer == True
        
        Expected Behavior (after fix): emit() completes without crash
        Current Behavior (unfixed): May or may not crash depending on iteration state
        """
        signal = Signal()
        call_log = []
        
        def observer_1(**kwargs):
            """First observer - normal behavior"""
            call_log.append("observer_1")
        
        def observer_2(**kwargs):
            """Last observer - disconnects itself"""
            call_log.append("observer_2")
            signal.disconnect(observer_2)
        
        # Connect both observers
        signal.connect(observer_1)
        signal.connect(observer_2)
        
        # Call emit() - this should complete without RuntimeError (expected behavior)
        # On UNFIXED code, this may raise RuntimeError
        signal.emit(test_data="value")
        
        # Verify both observers were called
        assert call_log == ["observer_1", "observer_2"], \
            "Both observers should have been called in order"
        
        # Verify observer_2 disconnected itself
        assert observer_2 not in signal._observers, \
            "Observer 2 should have disconnected itself"
        assert observer_1 in signal._observers, \
            "Observer 1 should still be connected"


if __name__ == "__main__":
    # Run tests to demonstrate the bug
    pytest.main([__file__, "-v", "-s"])
