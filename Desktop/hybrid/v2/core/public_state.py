from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from v2.core.card_database import CardData


Coord = Tuple[int, int]


@dataclass(frozen=True)
class ShopViewState:
    slots: Tuple[Optional[str], ...]
    is_locked: bool
    rarity_probabilities: Dict[str, float]


@dataclass(frozen=True)
class HandViewState:
    slots: Tuple[Optional[str], ...]


@dataclass(frozen=True)
class PlayerHudViewState:
    hp: int
    gold: int
    win_streak: int
    total_pts: int
    turn: int
    next_gold: int
    interest_multiplier: float


@dataclass(frozen=True)
class SynergyGroupViewState:
    key: str
    label: str
    short_label: str
    color: Tuple[int, int, int]
    count: int
    bonus: int
    next_tier_count: Optional[int] = None
    next_tier_bonus: Optional[int] = None


@dataclass(frozen=True)
class PassiveFeedEntryViewState:
    trigger: str
    card: str
    delta: int
    res: int
    color: Tuple[int, int, int]
    icon_key: str


@dataclass(frozen=True)
class EffectViewState:
    label: str
    value: str = ""
    color: Tuple[int, int, int] = (160, 165, 195)
    icon_key: str = "GEAR"


@dataclass(frozen=True)
class CombatViewState:
    last_results: Tuple[Dict[str, Any], ...]
    logs: Tuple[str, ...]
    passive_feed: Tuple[Dict[str, Any], ...]


@dataclass(frozen=True)
class SynergyViewState:
    groups: Tuple[SynergyGroupViewState, ...]
    total: int
    passive_feed: Tuple[PassiveFeedEntryViewState, ...]
    active_effects: Tuple[EffectViewState, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ActivePlayerViewState:
    index: int
    pid: int
    display_name: str
    strategy: str
    hp: int
    gold: int
    alive: bool
    turns_played: int
    stats: Dict[str, Any]
    has_catalyst: bool
    has_eclipse: bool
    board_cards: Dict[Coord, Dict[str, Any]]
    board_rotations: Dict[Coord, int]
    adjacency_pairs: Tuple[Tuple[Any, ...], ...]
    eliminated_coords: Tuple[Coord, ...]
    shop: ShopViewState
    hand: HandViewState
    hud: PlayerHudViewState
    combat: CombatViewState
    synergy: SynergyViewState
    copies_by_name: Dict[str, int]
    copy_milestones: Tuple[Dict[str, Any], ...]
    prefix_bonus: int
    shop_card_info: Dict[int, Optional[CardData]] = field(default_factory=dict)
    hand_card_info: Dict[int, Optional[CardData]] = field(default_factory=dict)
    board_card_info: Dict[Coord, Optional[CardData]] = field(default_factory=dict)

    def get_card_info(self, source: str, key: Any) -> Optional[CardData]:
        if source == "shop":
            return self.shop_card_info.get(int(key))
        if source == "hand":
            return self.hand_card_info.get(int(key))
        if source == "board":
            return self.board_card_info.get(key)
        return None


@dataclass(frozen=True)
class PublicState:
    phase: str
    turn: int
    view_index: int
    place_locked: bool
    alive_pids: Tuple[int, ...]
    pairings: Tuple[Tuple[int, int], ...]
    active_player: ActivePlayerViewState
    lobby_players: Tuple[Dict[str, Any], ...]
    endgame_stats: Tuple[Dict[str, Any], ...]
