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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Module-level counter for unique card IDs
_card_id_counter = 0


def _next_card_uid() -> int:
    """Generate unique ID for cards to avoid memory address collisions."""
    global _card_id_counter
    _card_id_counter += 1
    return _card_id_counter

# Import constants needed by Card class
try:
    from .constants import STAT_TO_GROUP, _LEGACY_RARITY_TO_ID, RARITY_TAVAN, EVOLVED_TAVAN
except ImportError:
    from constants import STAT_TO_GROUP, _LEGACY_RARITY_TO_ID, RARITY_TAVAN, EVOLVED_TAVAN


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def _normalize_rarity(rarity: str) -> str:
    return _LEGACY_RARITY_TO_ID.get(rarity, rarity)


def _load_card_entry(entry: dict) -> Tuple[Dict[str, int], str, str]:
    """Load card data from JSON (now in English)."""
    stats = entry.get("stats", {})
    category = entry.get("category", "")
    passive_type = entry.get("passive_type", "none")
    return stats, category, passive_type


# ===================================================================
# CARD CLASS
# ===================================================================

@dataclass(slots=True)
class Card:
    name:         str
    category:     str
    rarity:       str
    stats:        Dict[str, int]   # 6 stats: name -> value
    passive_type: str = "none"

    # Computed at runtime
    edges: List[Tuple[str, int]] = field(default_factory=list)
    uid: int = field(default=0)  # Unique ID to avoid memory address collisions

    # Rotation: 0-5 (steps of 60°, clockwise). Affects which physical edge
    # each stat faces. rotation=0 → edge[0] faces direction 0 (N), etc.
    # rotation=1 → edge[0] faces direction 1 (NE), etc.
    rotation: int = field(default=0)

    def __post_init__(self):
        # Assign stats to six edge slots in order
        self.edges = list(self.stats.items())   # [(stat_name, value), ...] len=6
        # Assign unique ID if not already set (e.g., from clone)
        if self.uid == 0:
            self.uid = _next_card_uid()

    # -- Rotation --

    def rotate(self, steps: int = 1):
        """Rotate card by `steps` * 60° clockwise. Wraps around at 6."""
        self.rotation = (self.rotation + steps) % 6

    def rotated_edges(self) -> List[Tuple[str, int]]:
        """Return edges list shifted by rotation so edge[i] faces direction i.
        
        With rotation=0: edges[0] → dir 0, edges[1] → dir 1, ...
        With rotation=1: edges[0] → dir 1, edges[1] → dir 2, ...
        i.e., the stat that was at slot 0 now faces direction `rotation`.
        
        For combat/rendering: rotated_edges()[direction] gives the stat at that direction.
        """
        n = len(self.edges)
        if n == 0:
            return []
        r = self.rotation % n
        if r == 0:
            return self.edges[:]
        # Shift: rotated_edges[d] = edges[(d - r) % n]
        return [self.edges[(i - r) % n] for i in range(n)]

    # -- Edge queries --

    def edge_val(self, d: int) -> int:
        """Value at direction d (accounts for rotation)."""
        edges = self.rotated_edges()
        return edges[d][1] if d < len(edges) else 0

    def edge_group(self, d: int) -> Optional[str]:
        """Group at direction d (accounts for rotation)."""
        edges = self.rotated_edges()
        if d < len(edges) and edges[d][1] > 0:
            return STAT_TO_GROUP.get(edges[d][0])
        return None

    def dominant_group(self) -> str:
        """Group with the most active stats on this card."""
        cnt = defaultdict(int)
        for s, v in self.stats.items():
            if v <= 0:
                continue
            group_name = STAT_TO_GROUP.get(s)
            if group_name:
                cnt[group_name] += 1
        return max(cnt, key=cnt.get) if cnt else "EXISTENCE"

    def total_power(self) -> int:
        # Exclude internal keys (e.g. _narwhal_buff, _sf_pc) from combat totals
        total = 0
        for k, v in self.stats.items():
            if not str(k).startswith("_"):
                total += v
        return total

    def get_group_composition(self) -> Dict[str, int]:
        """Return this card's spread across groups."""
        result: Dict[str, int] = {}
        for stat_name, val in self.stats.items():
            if val > 0:
                group = STAT_TO_GROUP.get(stat_name)
                if group:
                    result[group] = result.get(group, 0) + 1
        return result

    # -- Elimination check --

    def is_eliminated(self) -> bool:
        """
        Card is eliminated if every stat in some group on this card is 0.
        OR if all primary stats are 0 (Total Power check).
        """
        # 1. Total Power Check (Eğer tüm kenarlar 0 ise kart yok olmuştur)
        if all(v <= 0 for k, v in self.stats.items() if not str(k).startswith("_")):
            return True

        # 2. Group Wipe Check (Grup bazlı yok oluş kuralı)
        group_vals: Dict[str, List[int]] = {}
        for s, v in self.stats.items():
            g = STAT_TO_GROUP.get(s)
            if g:
                if g not in group_vals:
                    group_vals[g] = []
                group_vals[g].append(v)
        for vals in group_vals.values():
            if len(vals) >= 2 and all(v == 0 for v in vals):
                return True
        return False

    # -- Damage / edge loss --

    def lose_highest_edge(self):
        """On combat loss, zero the highest-value edge (rotation-aware)."""
        if not self.edges:
            return
        idx = max(range(len(self.edges)), key=lambda i: self.edges[i][1])
        stat_name, _ = self.edges[idx]
        self.edges[idx] = (stat_name, 0)
        self.stats[stat_name] = 0

    def apply_edge_debuff(self, d: int, amount: int = 1):
        """Apply debuff to physical direction d (rotation-aware)."""
        # d is the physical direction; map back to base edge index
        n = len(self.edges)
        if n == 0:
            return
        base_idx = (d - self.rotation) % n
        stat_name, val = self.edges[base_idx]
        new_val = max(0, val - amount)
        self.edges[base_idx] = (stat_name, new_val)
        self.stats[stat_name] = new_val

    # -- Copy strengthening --

    def strengthen(self, copy_num: int):
        """Copy milestone: +2 to highest edge (2nd copy) or +3 (3rd copy)."""
        bonus = 2 if copy_num == 2 else 3
        if not self.edges:
            return
        idx = max(range(len(self.edges)), key=lambda i: self.edges[i][1])
        stat_name, val = self.edges[idx]
        self.edges[idx] = (stat_name, val + bonus)
        self.stats[stat_name] = val + bonus

    def clone(self) -> "Card":
        c = Card(
            name=self.name, category=self.category,
            rarity=self.rarity, stats=self.stats.copy(),
            passive_type=self.passive_type,
        )
        c.edges = self.edges[:]
        c.rotation = self.rotation
        c.uid = _next_card_uid()  # Assign new unique ID for clone
        return c

    def __repr__(self):
        return f"Card({self.name} {self.rarity} pwr={self.total_power()} rot={self.rotation})"


# ===================================================================
# CARD POOL FUNCTIONS
# ===================================================================

_card_pool_cache: Optional[List[Card]] = None


def get_card_pool() -> List[Card]:
    """Lazy factory for card pool. Builds and caches on first call."""
    global _card_pool_cache
    if _card_pool_cache is None:
        pool = build_card_pool()
        apply_micro_buff_to_weak_cards(pool)
        _card_pool_cache = pool
    return _card_pool_cache


def build_card_pool() -> List[Card]:
    """Load card pool from cards.json next to this module (Turkish fields normalized to English)."""
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
    """
    v0.7 MICRO-BUFF FOR WEAK CARDS
    
    Purpose: Help weak cards survive long enough to use their passives.
    
    Logic:
      1. Calculate global average stat across all cards
      2. For each card, calculate its average stat
      3. If card_avg < global_avg - 1, increase lowest stat by +1
    
    This helps cards with low stats (often passive-focused) survive combat
    without modifying combat logic or hardcoding specific card names.
    
    Example:
      Global avg: 6.5
      Card avg: 5.2 (< 6.5 - 1 = 5.5)
      → Increase lowest stat by +1
    
    Returns:
      Number of cards buffed
    """
    # Calculate global average stat
    total_stats = 0
    total_count = 0
    for card in cards:
        for stat_name, value in card.stats.items():
            if not str(stat_name).startswith("_"):  # Exclude internal stats
                total_stats += value
                total_count += 1
    
    if total_count == 0:
        return 0  # No stats to process
    
    global_avg = total_stats / total_count
    threshold = global_avg - 1  # Buff if below this threshold
    
    # Apply micro-buff to weak cards
    buffed_count = 0
    for card in cards:
        # Calculate card's average stat
        card_stats = [(name, val) for name, val in card.stats.items() 
                      if not str(name).startswith("_")]
        
        if not card_stats:
            continue
        
        card_avg = sum(val for _, val in card_stats) / len(card_stats)
        
        # Check if card needs buff
        if card_avg < threshold:
            # Find lowest stat
            lowest_stat_name = min(card_stats, key=lambda x: x[1])[0]
            
            # Apply +1 buff to lowest stat
            card.stats[lowest_stat_name] += 1
            
            # Update edges (card.edges is list of tuples, need to rebuild)
            card.edges = [(name, card.stats[name]) for name, _ in card.edges]
            
            buffed_count += 1
    
    return buffed_count


# ===================================================================
# EVOLUTION SYSTEM
# ===================================================================

def evolve_card(base_card: Card) -> Card:
    """Create an Evolved (rarity E) card from a base card template.
    Stats are scaled up proportionally based on the base card's rarity.
    Rarity-1 -> 40pts, Rarity-2 -> 48pts, ..., Rarity-5 -> 72pts.
    The passive_type is inherited from the base card."""
    base_total = sum(v for k, v in base_card.stats.items() if not str(k).startswith("_"))
    # Use rarity-based target instead of fixed 72
    target_total = EVOLVED_TAVAN.get(base_card.rarity, RARITY_TAVAN["E"])
    if base_total == 0:
        scale = 1.0
    else:
        scale = target_total / base_total

    new_stats: Dict[str, int] = {}
    for stat_name, val in base_card.stats.items():
        if str(stat_name).startswith("_"):
            continue
        new_stats[stat_name] = max(1, round(val * scale))

    # Fix rounding drift: adjust highest stat so total == target_total exactly
    actual_total = sum(new_stats.values())
    diff = target_total - actual_total
    if diff != 0 and new_stats:
        top_stat = max(new_stats, key=new_stats.get)
        new_stats[top_stat] = max(1, new_stats[top_stat] + diff)

    evolved = Card(
        name=f"Evolved {base_card.name}",
        category=base_card.category,
        rarity="E",
        stats=new_stats,
        passive_type=base_card.passive_type,
    )
    return evolved
