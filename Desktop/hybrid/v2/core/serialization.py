"""
v2/core/serialization.py
═══════════════════════════════════════════════════════════════════
JSON Serialization Layer for PublicState and ActionLog.

Zero network code — pure data transformation.
Converts immutable dataclass snapshots to/from JSON-compatible dicts.

Constraints:
- Standard library only (json, dataclasses)
- Tuple coords (q, r) → list in JSON, restored to tuple on read
- Card references → card.name string only
- Lossless round-trip: from_dict(to_dict(state)) == state
═══════════════════════════════════════════════════════════════════
"""

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from v2.core.public_state import (
    PublicState,
    ActivePlayerViewState,
    ShopViewState,
    HandViewState,
    PlayerHudViewState,
    CombatViewState,
    SynergyViewState,
    SynergyGroupViewState,
    PassiveFeedEntryViewState,
    EffectViewState,
)


# ═══════════════════════════════════════════════════════════════════
# PublicState Serialization
# ═══════════════════════════════════════════════════════════════════


def to_dict(state: PublicState) -> Dict[str, Any]:
    """Convert PublicState to JSON-compatible dict.
    
    Handles:
    - Tuple coords → list
    - Nested dataclasses → nested dicts
    - MappingProxyType → dict (via asdict)
    
    Returns:
        Dict ready for json.dumps()
    """
    data = asdict(state)
    
    # Convert tuple coords in board_cards keys to string representation
    # JSON doesn't support tuple keys, so we use "q,r" format
    active = data["active_player"]
    if "board_cards" in active:
        board_cards_serialized = {
            f"{q},{r}": card_data
            for (q, r), card_data in _deserialize_coord_keys(active["board_cards"]).items()
        }
        active["board_cards"] = board_cards_serialized
    
    if "board_rotations" in active:
        board_rotations_serialized = {
            f"{q},{r}": rotation
            for (q, r), rotation in _deserialize_coord_keys(active["board_rotations"]).items()
        }
        active["board_rotations"] = board_rotations_serialized
    
    if "board_card_info" in active:
        board_card_info_serialized = {
            f"{q},{r}": card_info
            for (q, r), card_info in _deserialize_coord_keys(active["board_card_info"]).items()
        }
        active["board_card_info"] = board_card_info_serialized
    
    # Convert eliminated_coords tuples to lists
    if "eliminated_coords" in active:
        active["eliminated_coords"] = [list(coord) for coord in active["eliminated_coords"]]
    
    # Convert adjacency_pairs nested tuples to nested lists
    if "adjacency_pairs" in active:
        active["adjacency_pairs"] = [
            [list(item) if isinstance(item, tuple) else item for item in pair]
            for pair in active["adjacency_pairs"]
        ]
    
    return data


def from_dict(data: Dict[str, Any]) -> PublicState:
    """Reconstruct PublicState from JSON dict.
    
    Handles:
    - list → tuple for coords
    - String coord keys "q,r" → tuple (q, r)
    - Nested dicts → nested dataclasses
    
    Args:
        data: Dict from json.loads()
    
    Returns:
        PublicState instance
    """
    # Deep copy to avoid mutating input
    data = dict(data)
    
    # Reconstruct active_player
    active_data = data["active_player"]
    
    # Convert string coord keys back to tuples
    if "board_cards" in active_data:
        active_data["board_cards"] = {
            _parse_coord(key): card_data
            for key, card_data in active_data["board_cards"].items()
        }
    
    if "board_rotations" in active_data:
        active_data["board_rotations"] = {
            _parse_coord(key): rotation
            for key, rotation in active_data["board_rotations"].items()
        }
    
    if "board_card_info" in active_data:
        active_data["board_card_info"] = {
            _parse_coord(key): card_info
            for key, card_info in active_data["board_card_info"].items()
        }
    
    # Convert eliminated_coords lists to tuples
    if "eliminated_coords" in active_data:
        active_data["eliminated_coords"] = tuple(
            tuple(coord) for coord in active_data["eliminated_coords"]
        )
    
    # Convert adjacency_pairs nested lists to nested tuples
    if "adjacency_pairs" in active_data:
        active_data["adjacency_pairs"] = tuple(
            tuple(tuple(item) if isinstance(item, list) else item for item in pair)
            for pair in active_data["adjacency_pairs"]
        )
    
    # Reconstruct nested dataclasses
    active_data["shop"] = ShopViewState(**_tuplify_slots(active_data["shop"]))
    active_data["hand"] = HandViewState(**_tuplify_slots(active_data["hand"]))
    active_data["hud"] = PlayerHudViewState(**active_data["hud"])
    
    # Combat
    combat_data = active_data["combat"]
    combat_data["last_results"] = tuple(combat_data["last_results"])
    combat_data["logs"] = tuple(combat_data["logs"])
    combat_data["passive_feed"] = tuple(combat_data["passive_feed"])
    active_data["combat"] = CombatViewState(**combat_data)
    
    # Synergy
    synergy_data = active_data["synergy"]
    synergy_data["groups"] = tuple(
        SynergyGroupViewState(**_tuplify_color(group))
        for group in synergy_data["groups"]
    )
    synergy_data["passive_feed"] = tuple(
        PassiveFeedEntryViewState(**_tuplify_color(entry))
        for entry in synergy_data["passive_feed"]
    )
    synergy_data["active_effects"] = tuple(
        EffectViewState(**_tuplify_color(effect))
        for effect in synergy_data["active_effects"]
    )
    active_data["synergy"] = SynergyViewState(**synergy_data)
    
    # Copy milestones
    active_data["copy_milestones"] = tuple(active_data["copy_milestones"])
    
    # Reconstruct ActivePlayerViewState
    data["active_player"] = ActivePlayerViewState(**active_data)
    
    # Convert top-level tuples
    data["alive_pids"] = tuple(data["alive_pids"])
    data["pairings"] = tuple(tuple(pair) for pair in data["pairings"])
    data["lobby_players"] = tuple(data["lobby_players"])
    data["endgame_stats"] = tuple(data["endgame_stats"])
    
    return PublicState(**data)


# ═══════════════════════════════════════════════════════════════════
# ActionLog Record Serialization
# ═══════════════════════════════════════════════════════════════════


def action_to_dict(record: Any) -> Dict[str, Any]:
    """Convert a single ActionEntry to JSON-compatible dict.
    
    Args:
        record: ActionEntry instance from engine_core.action_log
    
    Returns:
        Dict ready for json.dumps()
    """
    params = dict(record.params)
    
    # Convert tuple coords to lists for JSON serialization
    if "coord" in params and isinstance(params["coord"], tuple):
        params["coord"] = list(params["coord"])
    
    return {
        "action_type": record.action_type,
        "params": params,
        "turn": record.turn,
        "sub_turn": record.sub_turn,
    }


def action_from_dict(data: Dict[str, Any]) -> Any:
    """Reconstruct ActionEntry from JSON dict.
    
    Args:
        data: Dict from json.loads()
    
    Returns:
        ActionEntry instance
    """
    from engine_core.action_log import ActionEntry
    
    params = dict(data["params"])
    
    # Convert coord lists back to tuples
    if "coord" in params and isinstance(params["coord"], list):
        params["coord"] = tuple(params["coord"])
    
    return ActionEntry(
        action_type=data["action_type"],
        params=params,
        turn=data["turn"],
        sub_turn=data["sub_turn"],
    )


# ═══════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════


def _parse_coord(key: str) -> Tuple[int, int]:
    """Parse "q,r" string to (q, r) tuple."""
    q, r = key.split(",")
    return (int(q), int(r))


def _deserialize_coord_keys(data: Dict[Any, Any]) -> Dict[Tuple[int, int], Any]:
    """Handle both string keys "q,r" and tuple keys (q, r) during serialization.
    
    This is needed because asdict() may preserve tuple keys in some cases.
    """
    result = {}
    for key, value in data.items():
        if isinstance(key, str):
            result[_parse_coord(key)] = value
        elif isinstance(key, tuple):
            result[key] = value
        else:
            # Fallback: try to convert to tuple
            result[tuple(key)] = value
    return result


def _tuplify_slots(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert 'slots' list to tuple."""
    data = dict(data)
    if "slots" in data:
        data["slots"] = tuple(data["slots"])
    return data


def _tuplify_color(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert 'color' list to tuple."""
    data = dict(data)
    if "color" in data:
        data["color"] = tuple(data["color"])
    return data
