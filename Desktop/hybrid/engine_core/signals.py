"""
engine_core/signals.py
═══════════════════════════════════════════════════════════════════
Simple Signal/Event Bus for engine-internal communication.

Allows decoupling of state mutation (engine) and state observation (UI/Cache).
═══════════════════════════════════════════════════════════════════
"""

from typing import Callable, Dict, List, Any

class Signal:
    def __init__(self):
        self._observers: List[Callable] = []

    def connect(self, observer: Callable):
        if observer not in self._observers:
            self._observers.append(observer)

    def disconnect(self, observer: Callable):
        if observer in self._observers:
            self._observers.remove(observer)

    def emit(self, **kwargs):
        for observer in self._observers:
            observer(**kwargs)

class SignalBus:
    def __init__(self):
        # Global engine signals
        self.board_mutated = Signal()
        self.economy_changed = Signal()
        self.inventory_changed = Signal()
        self.turn_started = Signal()
        self.combat_finished = Signal()

# Global bus instance for the engine
engine_signals = SignalBus()
