from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Mapping, Tuple


def _normalize_stat_value(stat_name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Stat '{stat_name}' must be an int, got {type(value).__name__}")
    return max(0, value)


class EffectPriority(IntEnum):
    COMBAT_DEBUFF = 100
    DEFAULT = 150
    COMBAT_BUFF = 200


@dataclass(frozen=True)
class Effect:
    source: str
    stat_name: str
    delta: int
    duration: int = -1
    applied_turn: int = 0
    priority: int = int(EffectPriority.DEFAULT)
    stacking: str = "additive"


class EffectPipeline:
    def __init__(self, base_stats: Mapping[str, int]):
        self._base_stats: Dict[str, int] = {
            stat_name: _normalize_stat_value(stat_name, value)
            for stat_name, value in dict(base_stats).items()
        }
        self._effects: List[Tuple[int, Effect]] = []
        self._next_sequence = 0

    def has_stat(self, stat_name: str) -> bool:
        return stat_name in self._base_stats

    def add_effect(self, effect: Effect) -> None:
        if effect.stat_name not in self._base_stats:
            raise KeyError(f"Unknown stat '{effect.stat_name}'")
        if isinstance(effect.delta, bool) or not isinstance(effect.delta, int):
            raise TypeError(f"Effect delta for '{effect.stat_name}' must be an int")
        if isinstance(effect.priority, bool) or not isinstance(effect.priority, int):
            raise TypeError("Effect priority must be an int")
        if effect.stacking != "additive":
            raise ValueError(f"Unsupported effect stacking policy '{effect.stacking}'")
        if isinstance(effect.duration, bool) or not isinstance(effect.duration, int):
            raise TypeError("Effect duration must be an int")
        if isinstance(effect.applied_turn, bool) or not isinstance(effect.applied_turn, int):
            raise TypeError("Effect applied_turn must be an int")

        self._effects.append((self._next_sequence, effect))
        self._next_sequence += 1

    def get_active_effects(self) -> List[Effect]:
        return [
            effect
            for _, effect in sorted(
                self._effects,
                key=lambda entry: (entry[1].priority, entry[0]),
            )
        ]

    def get_current_stats(self) -> Dict[str, int]:
        current = self._base_stats.copy()
        for effect in self.get_active_effects():
            current[effect.stat_name] = max(0, current[effect.stat_name] + effect.delta)
        return current

    def get_base_stats(self) -> Dict[str, int]:
        return self._base_stats.copy()

    def get_base_stat(self, stat_name: str) -> int:
        if stat_name not in self._base_stats:
            raise KeyError(f"Unknown stat '{stat_name}'")
        return self._base_stats[stat_name]

    def set_base_stat(self, stat_name: str, new_value: int) -> None:
        if stat_name not in self._base_stats:
            raise KeyError(f"Unknown stat '{stat_name}'")
        self._base_stats[stat_name] = _normalize_stat_value(stat_name, new_value)

    def add_base_stat(self, stat_name: str, delta: int) -> None:
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise TypeError(f"Delta for '{stat_name}' must be an int")
        self.set_base_stat(stat_name, self.get_base_stat(stat_name) + delta)

    def clear_expired(self, current_turn: int) -> None:
        self._effects = [
            entry
            for entry in self._effects
            if entry[1].duration < 0 or current_turn < entry[1].applied_turn + entry[1].duration
        ]
