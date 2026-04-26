"""
engine_core/action_log.py
═══════════════════════════════════════════════════════════════════
ActionLog and Replay Foundation.

Records RNG outcomes and critical state changes to allow for 
deterministic replays of combat and turns.
═══════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

@dataclass
class ActionEntry:
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    turn: int = 0
    sub_turn: int = 0  # For ordering within a turn

@dataclass
class ActionLog:
    seed: Optional[int] = None
    entries: List[ActionEntry] = field(default_factory=list)

    def record(self, action_type: str, params: Dict[str, Any], turn: int = 0):
        entry = ActionEntry(
            action_type=action_type,
            params=params,
            turn=turn,
            sub_turn=len(self.entries)
        )
        self.entries.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "entries": [
                {
                    "type": e.action_type,
                    "params": e.params,
                    "turn": e.turn,
                    "sub_turn": e.sub_turn
                }
                for e in self.entries
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionLog":
        log = cls(seed=data.get("seed"))
        for entry_data in data.get("entries", []):
            log.entries.append(ActionEntry(
                action_type=entry_data["type"],
                params=entry_data["params"],
                turn=entry_data["turn"],
                sub_turn=entry_data["sub_turn"]
            ))
        return log
