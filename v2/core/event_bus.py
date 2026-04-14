from enum import Enum
from v2.constants import Config

class UIEvent(Enum):
    GOLD_UPDATED = 1
    PLACE_LOCKED = 2
    PLAYER_ELIMINATED = 3

class EventBus:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event, callback):
        if event not in self._subscribers:
            self._subscribers[event] = []
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)

    def publish(self, event, payload):
        if event in self._subscribers:
            for cb in self._subscribers[event]:
                try:
                    cb(payload)
                except Exception as e:
                    if Config.DEBUG_MODE:
                        print(f"EventBus Error: {e}")

    def unsubscribe(self, event, callback):
        if event in self._subscribers and callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)
