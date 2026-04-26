"""
================================================================
|         AUTOCHESS HYBRID - Card Module                       |
|  Card class definition and related functionality             |
================================================================

This module contains the Card class which represents a game card,
along with card pool management functions.
"""

import json
import os
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Tuple

from engine_core.constants import STAT_TO_GROUP, _LEGACY_RARITY_TO_ID, EVOLVED_TAVAN, RARITY_TAVAN
from engine_core.effects import Effect, EffectPipeline, EffectPriority
from engine_core.meta_keys import get_meta_scope, is_combat_bonus_key, validate_meta_value


def _normalize_rarity(rarity: str) -> str:
    return _LEGACY_RARITY_TO_ID.get(rarity, rarity)


def _load_card_entry(entry: dict) -> Tuple[Dict[str, int], str, str]:
    """Load card data from JSON (now in English)."""
    stats = entry.get("stats", {})
    category = entry.get("category", "")
    passive_type = entry.get("passive_type", "none")
    return stats, category, passive_type


def _split_card_state(raw_stats: Mapping[str, Any]) -> Tuple[Dict[str, int], Dict[str, Any]]:
    base_stats: Dict[str, int] = {}
    meta: Dict[str, Any] = {}
    for stat_name, value in dict(raw_stats).items():
        if str(stat_name).startswith("_") or isinstance(value, bool):
            meta[stat_name] = validate_meta_value(str(stat_name), value)
        elif isinstance(value, int):
            base_stats[stat_name] = max(0, value)
        else:
            meta[stat_name] = validate_meta_value(str(stat_name), value)
    return base_stats, meta


@dataclass(slots=True)
class Card:
    name: str
    category: str
    rarity: str
    stats: InitVar[Mapping[str, Any]]
    passive_type: str = "none"
    uid: int = field(default=0)
    rotation: int = field(default=0)

    _pipeline: EffectPipeline = field(init=False, repr=False)
    _meta: Dict[str, Any] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self, stats: Mapping[str, Any]) -> None:
        base_stats, meta = _split_card_state(stats)
        self._pipeline = EffectPipeline(base_stats)
        self._meta = meta

    @property
    def stats(self):
        return MappingProxyType(self._pipeline.get_current_stats())

    @property
    def edges(self) -> List[Tuple[str, int]]:
        return list(self._pipeline.get_current_stats().items())

    def get_base_stats(self) -> Dict[str, int]:
        return self._pipeline.get_base_stats()

    def get_base_stat(self, stat_name: str, default: Optional[int] = None) -> Optional[int]:
        if not self._pipeline.has_stat(stat_name):
            return default
        return self._pipeline.get_base_stat(stat_name)

    def has_stat(self, stat_name: str) -> bool:
        return self._pipeline.has_stat(stat_name)

    def set_base_stat(self, stat_name: str, value: int) -> None:
        self._pipeline.set_base_stat(stat_name, value)

    def add_base_stat(self, stat_name: str, delta: int) -> None:
        self._pipeline.add_base_stat(stat_name, delta)

    def get_meta(self, key: str, default=None):
        return self._meta.get(key, default)

    def set_meta(self, key: str, value: Any) -> None:
        if self._pipeline.has_stat(key):
            raise KeyError(f"'{key}' is a gameplay stat, not meta")
        self._meta[key] = validate_meta_value(key, value)

    def inc_meta(self, key: str, delta: int = 1) -> int:
        validate_meta_value(key, 0)
        current = self._meta.get(key, 0)
        if isinstance(current, bool) or not isinstance(current, int):
            raise TypeError(f"Meta '{key}' must be an int to increment")
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise TypeError(f"Meta delta for '{key}' must be an int")
        new_value = current + delta
        self._meta[key] = new_value
        return new_value

    def clear_meta_scope(self, scope: str) -> None:
        for key in [meta_key for meta_key in self._meta if get_meta_scope(meta_key) == scope]:
            del self._meta[key]

    def add_effect(self, effect: Effect) -> None:
        self._pipeline.add_effect(effect)

    def clear_expired_effects(self, current_turn: int) -> None:
        self._pipeline.clear_expired(current_turn)

    def get_combat_bonus_total(self) -> int:
        return sum(
            value
            for key, value in self._meta.items()
            if is_combat_bonus_key(str(key)) and isinstance(value, int) and not isinstance(value, bool)
        )

    def rotate(self, steps: int = 1):
        self.rotation = (self.rotation + steps) % 6

    def rotated_edges(self) -> List[Tuple[str, int]]:
        edges = self.edges
        n = len(edges)
        if n == 0:
            return []
        r = self.rotation % n
        if r == 0:
            return edges
        return [edges[(i - r) % n] for i in range(n)]

    def edge_val(self, d: int) -> int:
        edges = self.rotated_edges()
        return edges[d][1] if d < len(edges) else 0

    def edge_group(self, d: int) -> Optional[str]:
        edges = self.rotated_edges()
        if d < len(edges) and edges[d][1] > 0:
            return STAT_TO_GROUP.get(edges[d][0])
        return None

    def dominant_group(self) -> str:
        cnt = defaultdict(int)
        for stat_name, value in self.stats.items():
            if value <= 0:
                continue
            group_name = STAT_TO_GROUP.get(stat_name)
            if group_name:
                cnt[group_name] += 1
        return max(cnt, key=cnt.get) if cnt else "EXISTENCE"

    def total_power(self) -> int:
        return sum(self.stats.values())

    def is_eliminated(self) -> bool:
        resolved = dict(self.stats)
        if all(value <= 0 for value in resolved.values()):
            return True

        group_vals: Dict[str, List[int]] = {}
        for stat_name, value in resolved.items():
            group_name = STAT_TO_GROUP.get(stat_name)
            if group_name:
                group_vals.setdefault(group_name, []).append(value)
        for values in group_vals.values():
            if len(values) >= 2 and all(value == 0 for value in values):
                return True
        return False

    def lose_highest_edge(self):
        """On combat loss, zero the highest-value edge permanently."""
        edges = self.edges
        if not edges:
            return
        idx = max(range(len(edges)), key=lambda i: edges[i][1])
        stat_name, _ = edges[idx]
        self.set_base_stat(stat_name, 0)

    def apply_edge_debuff(self, d: int, amount: int = 1, *, source: str = "debuff", duration: int = -1, applied_turn: int = 0):
        """Apply a temporary or permanent debuff through the effect pipeline."""
        edges = self.edges
        n = len(edges)
        if n == 0:
            return
        base_idx = (d - self.rotation) % n
        stat_name, _ = edges[base_idx]
        self.add_effect(
            Effect(
                source=source,
                stat_name=stat_name,
                delta=-amount,
                duration=duration,
                applied_turn=applied_turn,
                priority=int(EffectPriority.COMBAT_DEBUFF),
            )
        )

    def strengthen(self, copy_num: int):
        """Increase the highest edge permanently."""
        bonus = 2 if copy_num == 2 else 3 if copy_num == 3 else copy_num
        if bonus <= 0:
            return
        edges = self.edges
        if not edges:
            return
        idx = max(range(len(edges)), key=lambda i: edges[i][1])
        stat_name, _ = edges[idx]
        self.add_base_stat(stat_name, bonus)

    def clone(self) -> "Card":
        cloned = Card(
            name=self.name,
            category=self.category,
            rarity=self.rarity,
            stats=self.get_base_stats(),
            passive_type=self.passive_type,
        )
        cloned.rotation = self.rotation
        cloned.uid = self.uid
        return cloned

    def __repr__(self):
        return f"Card({self.name} {self.rarity} pwr={self.total_power()} rot={self.rotation})"


_card_pool_cache: Optional[List[Card]] = None


def get_card_pool() -> List[Card]:
    global _card_pool_cache
    if _card_pool_cache is None:
        pool = build_card_pool()
        apply_micro_buff_to_weak_cards(pool)
        _card_pool_cache = pool
    return _card_pool_cache


def build_card_pool() -> List[Card]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "..", "assets", "data", "cards.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards: List[Card] = []
    for entry in data:
        stats, category, passive_type = _load_card_entry(entry)
        cards.append(
            Card(
                name=entry["name"],
                category=category,
                rarity=_normalize_rarity(entry["rarity"]),
                stats=stats,
                passive_type=passive_type,
            )
        )
    return cards


def apply_micro_buff_to_weak_cards(cards: List[Card]) -> int:
    total_stats = 0
    total_count = 0
    for card in cards:
        for stat_name, value in card.get_base_stats().items():
            total_stats += value
            total_count += 1

    if total_count == 0:
        return 0

    global_avg = total_stats / total_count
    threshold = global_avg - 1

    buffed_count = 0
    for card in cards:
        card_stats = list(card.get_base_stats().items())
        if not card_stats:
            continue
        card_avg = sum(value for _, value in card_stats) / len(card_stats)
        if card_avg < threshold:
            lowest_stat_name = min(card_stats, key=lambda item: item[1])[0]
            card.add_base_stat(lowest_stat_name, 1)
            buffed_count += 1
    return buffed_count


def evolve_card(base_card: Card) -> Card:
    base_stats = base_card.get_base_stats()
    base_total = sum(base_stats.values())
    target_total = EVOLVED_TAVAN.get(base_card.rarity, RARITY_TAVAN["E"])
    scale = target_total / base_total if base_total > 0 else 1.0

    new_stats: Dict[str, int] = {}
    for stat_name, value in base_stats.items():
        new_stats[stat_name] = max(1, round(value * scale))

    actual_total = sum(new_stats.values())
    diff = target_total - actual_total
    if diff != 0 and new_stats:
        top_stat = max(new_stats, key=new_stats.get)
        new_stats[top_stat] = max(1, new_stats[top_stat] + diff)

    return Card(
        name=f"Evolved {base_card.name}",
        category=base_card.category,
        rarity="E",
        stats=new_stats,
        passive_type=base_card.passive_type,
    )
