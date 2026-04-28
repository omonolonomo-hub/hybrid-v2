"""
Preservation Unit Tests: Signal.emit() Normal Behavior
═══════════════════════════════════════════════════════════════════

Property 2: Preservation - Normal Signal Notification Behavior

IMPORTANT: Follow observation-first methodology
- Observe behavior on UNFIXED code for normal emit() calls (no disconnections)
- Write unit tests capturing observed behavior patterns

Test Coverage:
- Test 1: Observers notified in same order when no disconnections occur
- Test 2: Observers receive same arguments as before
- Test 3: connect() and disconnect() outside of emit() work correctly

EXPECTED OUTCOME: Tests PASS on unfixed code (confirms baseline behavior to preserve)

Requirements: 3.1, 3.2, 3.3
═══════════════════════════════════════════════════════════════════
"""

import pytest
from engine_core.signals import Signal


class TestSignalEmitPreservation:
    """
    Preservation Tests: Normal Signal behavior that must remain unchanged
    
    These tests capture the baseline behavior on UNFIXED code to ensure
    the fix doesn't introduce regressions in normal usage patterns.
    """
    
    def test_observers_notified_in_connection_order(self):
        """
        Test 1: Observers notified in same order when no disconnections occur
        
        Preservation Requirement 3.1: WHEN Signal.emit() is called AND no observers
        disconnect during notification THEN the system SHALL CONTINUE TO notify all
        observers in the original order
        
        This test verifies that observer notification order matches connection order.
        """
        signal = Signal()
        call_log = []
        
        def observer_1(**kwargs):
            call_log.append("observer_1")
        
        def observer_2(**kwargs):
            call_log.append("observer_2")
        
        def observer_3(**kwargs):
            call_log.append("observer_3")
        
        # Connect observers in specific order
        signal.connect(observer_1)
        signal.connect(observer_2)
        signal.connect(observer_3)
        
        # Emit signal
        signal.emit()
        
        # Verify observers were called in connection order
        assert call_log == ["observer_1", "observer_2", "observer_3"], \
            "Observers should be notified in connection order"
        
        # Emit again to verify consistent behavior
        call_log.clear()
        signal.emit()
        
        assert call_log == ["observer_1", "observer_2", "observer_3"], \
            "Observer order should be consistent across multiple emits"
    
    def test_observers_receive_correct_arguments(self):
        """
        Test 2: Observers receive same arguments as before
        
        Preservation Requirement 3.2: WHEN Signal.emit() is called with arguments
        THEN the system SHALL CONTINUE TO pass those arguments to all observer callbacks
        
        This test verifies that all observers receive the exact arguments passed to emit().
        """
        signal = Signal()
        received_args = []
        
        def observer_1(**kwargs):
            received_args.append(("observer_1", kwargs.copy()))
        
        def observer_2(**kwargs):
            received_args.append(("observer_2", kwargs.copy()))
        
        def observer_3(**kwargs):
            received_args.append(("observer_3", kwargs.copy()))
        
        # Connect observers
        signal.connect(observer_1)
        signal.connect(observer_2)
        signal.connect(observer_3)
        
        # Emit with specific arguments
        test_args = {"player_id": 42, "action": "buy", "card_name": "Einstein"}
        signal.emit(**test_args)
        
        # Verify all observers received the same arguments
        assert len(received_args) == 3, "All three observers should have been called"
        
        for observer_name, kwargs in received_args:
            assert kwargs == test_args, \
                f"{observer_name} should receive exact arguments passed to emit()"
        
        # Test with different arguments
        received_args.clear()
        test_args_2 = {"event": "combat_finished", "winner": "player_1", "damage": 15}
        signal.emit(**test_args_2)
        
        assert len(received_args) == 3, "All three observers should have been called again"
        
        for observer_name, kwargs in received_args:
            assert kwargs == test_args_2, \
                f"{observer_name} should receive new arguments on second emit()"
    
    def test_connect_disconnect_outside_emit_works_correctly(self):
        """
        Test 3: connect() and disconnect() outside of emit() work correctly
        
        Preservation Requirement 3.3: WHEN observers are connected or disconnected
        outside of emit() THEN the system SHALL CONTINUE TO manage the observer
        list correctly
        
        This test verifies that connect/disconnect operations work correctly when
        not called during emit().
        """
        signal = Signal()
        call_log = []
        
        def observer_1(**kwargs):
            call_log.append("observer_1")
        
        def observer_2(**kwargs):
            call_log.append("observer_2")
        
        def observer_3(**kwargs):
            call_log.append("observer_3")
        
        # Test: Connect and emit
        signal.connect(observer_1)
        signal.connect(observer_2)
        signal.emit()
        
        assert call_log == ["observer_1", "observer_2"], \
            "Only connected observers should be notified"
        
        # Test: Disconnect and emit
        call_log.clear()
        signal.disconnect(observer_1)
        signal.emit()
        
        assert call_log == ["observer_2"], \
            "Disconnected observer should not be notified"
        
        # Test: Connect new observer and emit
        call_log.clear()
        signal.connect(observer_3)
        signal.emit()
        
        assert call_log == ["observer_2", "observer_3"], \
            "Newly connected observer should be notified"
        
        # Test: Disconnect all and emit
        call_log.clear()
        signal.disconnect(observer_2)
        signal.disconnect(observer_3)
        signal.emit()
        
        assert call_log == [], \
            "No observers should be notified when all are disconnected"
    
    def test_duplicate_connect_ignored(self):
        """
        Additional Preservation Test: Duplicate connect() calls are ignored
        
        This test verifies that connecting the same observer multiple times
        doesn't result in duplicate notifications.
        """
        signal = Signal()
        call_count = []
        
        def observer(**kwargs):
            call_count.append(1)
        
        # Connect same observer multiple times
        signal.connect(observer)
        signal.connect(observer)
        signal.connect(observer)
        
        # Emit signal
        signal.emit()
        
        # Verify observer was only called once
        assert len(call_count) == 1, \
            "Observer should only be called once even if connected multiple times"
    
    def test_disconnect_nonexistent_observer_safe(self):
        """
        Additional Preservation Test: Disconnecting non-existent observer is safe
        
        This test verifies that disconnecting an observer that was never connected
        or already disconnected doesn't cause errors.
        """
        signal = Signal()
        call_log = []
        
        def observer_1(**kwargs):
            call_log.append("observer_1")
        
        def observer_2(**kwargs):
            call_log.append("observer_2")
        
        # Connect only observer_1
        signal.connect(observer_1)
        
        # Try to disconnect observer_2 (never connected)
        signal.disconnect(observer_2)  # Should not raise error
        
        # Emit and verify observer_1 still works
        signal.emit()
        assert call_log == ["observer_1"], \
            "Connected observer should still work after disconnecting non-existent observer"
        
        # Disconnect observer_1 twice
        signal.disconnect(observer_1)
        signal.disconnect(observer_1)  # Should not raise error
        
        # Emit and verify no observers are called
        call_log.clear()
        signal.emit()
        assert call_log == [], \
            "No observers should be called after disconnection"
    
    def test_empty_signal_emit_safe(self):
        """
        Additional Preservation Test: Emitting signal with no observers is safe
        
        This test verifies that calling emit() on a signal with no connected
        observers doesn't cause errors.
        """
        signal = Signal()
        
        # Emit with no observers connected
        signal.emit()  # Should not raise error
        signal.emit(data="test")  # Should not raise error with arguments
        
        # This test passes if no exceptions are raised
        assert True, "Emitting signal with no observers should be safe"
    
    def test_observer_can_emit_another_signal(self):
        """
        Additional Preservation Test: Observer can emit another signal
        
        This test verifies that an observer callback can safely emit a different
        signal (nested emit calls on different signals).
        """
        signal_1 = Signal()
        signal_2 = Signal()
        call_log = []
        
        def observer_2(**kwargs):
            call_log.append("observer_2")
        
        def observer_1(**kwargs):
            call_log.append("observer_1")
            # Observer 1 emits signal_2 during its callback
            signal_2.emit()
        
        # Connect observers
        signal_1.connect(observer_1)
        signal_2.connect(observer_2)
        
        # Emit signal_1, which will trigger signal_2
        signal_1.emit()
        
        # Verify both observers were called
        assert call_log == ["observer_1", "observer_2"], \
            "Nested signal emits should work correctly"


if __name__ == "__main__":
    # Run tests to verify baseline behavior
    pytest.main([__file__, "-v", "-s"])
