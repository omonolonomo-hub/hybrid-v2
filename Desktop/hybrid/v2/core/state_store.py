from typing import Dict, List, Tuple, Any, Optional

_VALID_PHASES = frozenset({"STATE_PREPARATION", "STATE_VERSUS", "STATE_COMBAT", "STATE_ENDGAME"})

class StateStore:
    """
    Reactive-style store for UI-facing state.
    Provides read-only snapshots and caches values to minimize engine polling.

    Board cache kaldırıldı (H3-5) — artık PublicState.active_player üzerinden erişiliyor.
    """
    def __init__(self):
        self._phase: str = "STATE_PREPARATION"
        self._view_index: int = 0
        self._place_locked: bool = False
        self._pairings_cache: List[Tuple[int, int]] = []

    @property
    def phase(self) -> str: return self._phase
    @phase.setter
    def phase(self, value: str):
        if value not in _VALID_PHASES:
            raise ValueError(
                f"Invalid phase: '{value}'. Valid phases: STATE_PREPARATION, STATE_VERSUS, STATE_COMBAT, STATE_ENDGAME"
            )
        self._phase = value

    @property
    def view_index(self) -> int: return self._view_index
    @view_index.setter
    def view_index(self, value: int): self._view_index = value

    @property
    def place_locked(self) -> bool: return self._place_locked
    @place_locked.setter
    def place_locked(self, value: bool): self._place_locked = value

    def update_pairings(self, pairs: List[Any]):
        """Update the pairings cache. Robustly handles both Player objects and PID integers."""
        new_cache = []
        for a, b in pairs:
            pid_a = getattr(a, "pid", a) if not isinstance(a, int) else a
            pid_b = getattr(b, "pid", b) if not isinstance(b, int) else b
            new_cache.append((int(pid_a), int(pid_b)))
        self._pairings_cache = new_cache

    def get_pairings(self) -> List[Tuple[int, int]]:
        return self._pairings_cache
