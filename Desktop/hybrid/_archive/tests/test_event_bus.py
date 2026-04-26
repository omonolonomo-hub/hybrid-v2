import pytest
from v2.core.event_bus import EventBus, UIEvent

@pytest.fixture(autouse=True)
def reset_event_bus():
    EventBus._instance = None
    yield
    EventBus._instance = None

def test_eventbus_pub_sub_contract():
    bus = EventBus.get()
    payloads_received = []
    def mock_callback(payload):
        payloads_received.append(payload)
    bus.subscribe(UIEvent.GOLD_UPDATED, mock_callback)
    bus.publish(UIEvent.GOLD_UPDATED, 15)
    assert len(payloads_received) == 1
    assert payloads_received[0] == 15

def test_eventbus_unsubscribing_non_existent():
    bus = EventBus.get()
    def fake_callback(payload): pass
    try:
        bus.unsubscribe(UIEvent.PLACE_LOCKED, fake_callback)
    except ValueError:
        pytest.fail("Unsubscribe of non-existent callback should not crash.")

def test_eventbus_multiple_publish_to_empty():
    bus = EventBus.get()
    try:
        bus.publish(UIEvent.PLAYER_ELIMINATED, 4)
    except Exception as e:
        pytest.fail(f"Publish to empty subscriber list failed: {e}")

def test_eventbus_singleton_identity():
    bus1 = EventBus.get()
    bus2 = EventBus.get()
    assert bus1 is bus2

def test_eventbus_publish_resilience_to_crashing_callbacks(capsys, monkeypatch):
    import v2.constants
    monkeypatch.setattr(v2.constants.Config, "DEBUG_MODE", True)

    bus = EventBus.get()
    received = []
    
    def crashing_cb(payload): 
        raise ValueError("Simulated UI Crash!")
    def stable_cb(payload): 
        received.append(payload)

    bus.subscribe(UIEvent.GOLD_UPDATED, crashing_cb)
    bus.subscribe(UIEvent.GOLD_UPDATED, stable_cb)
    bus.publish(UIEvent.GOLD_UPDATED, 100)
    
    assert len(received) == 1
    assert received[0] == 100

    out, err = capsys.readouterr()
    assert "Simulated UI Crash!" in out

def test_eventbus_subscribe_idempotency_prevents_duplicates():
    bus = EventBus.get()
    received = []
    
    def listener(payload):
        received.append(payload)

    bus.subscribe(UIEvent.PLACE_LOCKED, listener)
    bus.subscribe(UIEvent.PLACE_LOCKED, listener)  

    bus.publish(UIEvent.PLACE_LOCKED, None)
    assert len(received) == 1

def test_eventbus_unsubscribe_idempotency_is_safe():
    bus = EventBus.get()
    def listener(payload): pass
    
    bus.subscribe(UIEvent.GOLD_UPDATED, listener)
    bus.unsubscribe(UIEvent.GOLD_UPDATED, listener)
    
    try:
        bus.unsubscribe(UIEvent.GOLD_UPDATED, listener)
    except Exception:
        pytest.fail("Second unsubscribe crashed.")

def test_eventbus_publish_does_not_mutate_state():
    bus = EventBus.get()
    received = []
    def listener(payload):
        received.append(payload)
        
    bus.subscribe(UIEvent.GOLD_UPDATED, listener)
    
    bus.publish(UIEvent.GOLD_UPDATED, 1)
    bus.publish(UIEvent.GOLD_UPDATED, 2)
    bus.publish(UIEvent.GOLD_UPDATED, 3)
    
    assert len(received) == 3
    assert received == [1, 2, 3]

# --- YENI EKLENEN TDD TEST: FIFO DETERMINISM ---
def test_eventbus_listener_ordering_determinism():
    """EventBus her zaman subscribe olma sırasına (FIFO) göre çalışmalıdır."""
    bus = EventBus.get()
    execution_order = []
    
    def cb1(p): execution_order.append(1)
    def cb2(p): execution_order.append(2)
    def cb3(p): execution_order.append(3)
    
    bus.subscribe(UIEvent.GOLD_UPDATED, cb1)
    bus.subscribe(UIEvent.GOLD_UPDATED, cb2)
    bus.subscribe(UIEvent.GOLD_UPDATED, cb3)
    
    bus.publish(UIEvent.GOLD_UPDATED, None)
    
    assert execution_order == [1, 2, 3], "FIFO sıralamasi bozuldu!"
