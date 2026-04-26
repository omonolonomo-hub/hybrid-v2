from typing import Optional, Callable

class PhaseMachine:
    """
    Manages game phase transitions and ensures engine/UI synchronization.
    Transitions: PREPARATION -> VERSUS -> COMBAT -> ENDGAME
    """
    def __init__(self):
        self._current_phase = "STATE_PREPARATION"
        self._on_phase_change: Optional[Callable[[str], None]] = None

    @property
    def current_phase(self) -> str:
        return self._current_phase

    def set_callback(self, callback: Callable[[str], None]):
        self._on_phase_change = callback

    def transition_to(self, new_phase: str):
        if self._current_phase == new_phase:
            return
        
        # Validations can be added here
        self._current_phase = new_phase
        if self._on_phase_change:
            self._on_phase_change(new_phase)

    def next_phase(self, alive_count: int):
        if self._current_phase == "STATE_PREPARATION":
            self.transition_to("STATE_VERSUS")
        elif self._current_phase == "STATE_VERSUS":
            self.transition_to("STATE_COMBAT")
        elif self._current_phase == "STATE_COMBAT":
            if alive_count <= 1:
                self.transition_to("STATE_ENDGAME")
            else:
                self.transition_to("STATE_PREPARATION")
        elif self._current_phase == "STATE_ENDGAME":
            self.transition_to("STATE_PREPARATION")
