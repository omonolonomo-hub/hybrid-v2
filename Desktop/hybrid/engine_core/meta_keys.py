from dataclasses import dataclass
from typing import Any, Dict, Literal


MetaScope = Literal["persistent", "combat"]


@dataclass(frozen=True)
class MetaSpec:
    value_type: type
    scope: MetaScope = "persistent"


META_SPECS: Dict[str, MetaSpec] = {
    "_anubis_buff": MetaSpec(int),
    "_combat_bonus": MetaSpec(int),
    "_fib_last_turn": MetaSpec(int),
    "_guernica_count": MetaSpec(int),
    "_guernica_turn": MetaSpec(int),
    "_hammurabi_total_buff": MetaSpec(int),
    "_minotaur_total_buff": MetaSpec(int),
    "_narwhal_buff": MetaSpec(int),
    "_narwhal_last_turn": MetaSpec(int),
    "_prefix_bonus": MetaSpec(int),
    "_pulsar_last_turn": MetaSpec(int),
    "_sf_pc": MetaSpec(int),
    "_sf_stacks": MetaSpec(int),
    "_sirius_buff": MetaSpec(int),
    "_sirius_last_turn": MetaSpec(int),
    "_venus_debuffs": MetaSpec(int),
    "_yggdrasil_bonus": MetaSpec(int),
    "phoenix_used": MetaSpec(bool, scope="combat"),
    "revived_this_combat": MetaSpec(bool, scope="combat"),
}


def is_allowed_meta_key(key: str) -> bool:
    return key in META_SPECS


def get_meta_scope(key: str) -> MetaScope:
    spec = META_SPECS.get(key)
    if spec is None:
        raise KeyError(f"Unknown meta key '{key}'")
    return spec.scope


def validate_meta_value(key: str, value: Any) -> Any:
    spec = META_SPECS.get(key)
    if spec is None:
        raise KeyError(f"Unknown meta key '{key}'")

    if spec.value_type is bool:
        if not isinstance(value, bool):
            raise TypeError(f"Meta '{key}' must be a bool, got {type(value).__name__}")
        return value

    if spec.value_type is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"Meta '{key}' must be an int, got {type(value).__name__}")
        return value

    if not isinstance(value, spec.value_type):
        raise TypeError(f"Meta '{key}' must be a {spec.value_type.__name__}, got {type(value).__name__}")
    return value


def is_combat_bonus_key(key: str) -> bool:
    return key in META_SPECS and key.endswith("_bonus")
