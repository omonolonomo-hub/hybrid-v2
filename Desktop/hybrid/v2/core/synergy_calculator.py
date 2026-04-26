"""
v2/core/synergy_calculator.py
═══════════════════════════════════════════════════════════════════
UI-layer synergy hesaplayıcı — engine_core/synergy.py'ye delegate eder.

BFS mantığının tek kaynağı artık engine_core/synergy.py'dir.
Bu modül, UI adapter tarafından kullanılan veri yapısını
(board_cards dict + CardDatabase) engine_core/synergy.py'nin
callback tabanlı API'sine dönüştürür.

Kural: Başka bir yerde synergy BFS kodu görürseniz silin.
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from v2.constants import ENGINE_HEX_DIRS, OPP_DIR, STAT_TO_GROUP
from engine_core.synergy import compute_synergy, tier_bonus, GROUPS

Coord = Tuple[int, int]


# ──────────────────────────────────────────────────────────────────
# Çıktı veri yapısı (backward-compatible)
# ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SynergyComputeResult:
    """SynergyCalculator.compute() çıktısı."""
    group_counts:    Dict[str, int]   # grup → en büyük cluster boyutu
    group_bonuses:   Dict[str, int]   # grup → toplam bonus puan
    total:           int              # tüm grupların toplamı
    adjacency_pairs: List[Tuple]      # (coord_a, coord_b, grp_a, grp_b)
                                      # – TÜM komşu çiftleri (synergy olsun ya da olmasın)

    @staticmethod
    def empty() -> "SynergyComputeResult":
        return SynergyComputeResult(
            group_counts  = {g: 0 for g in GROUPS},
            group_bonuses = {g: 0 for g in GROUPS},
            total         = 0,
            adjacency_pairs = [],
        )


# ──────────────────────────────────────────────────────────────────
# Ana hesaplayıcı
# ──────────────────────────────────────────────────────────────────

class SynergyCalculator:
    """
    Serialized board_cards dict alıp SynergyComputeResult döndürür.

    board_cards formatı (UIAdapter / GameState'den gelen):
        { (q, r): {"name": str, "stats": {...}, "rotation": int}, ... }

    db: CardDatabase örneği  →  db.lookup(name) → CardData | None

    Hesaplama engine_core/synergy.py::compute_synergy()'ye delegate edilir.

    P1-2: Board-hash based caching avoids redundant BFS recomputation.
    Cache is automatically invalidated when board_cards content changes.
    """

    # Class-level cache (shared across instances since compute is @classmethod)
    _last_board_hash: Optional[int] = None
    _cached_result: Optional[SynergyComputeResult] = None

    @classmethod
    def _compute_board_hash(cls, board_cards: Dict[Coord, Dict]) -> int:
        """Compute a hash from board state for cache invalidation.

        Uses frozenset of (coord, name, rotation) tuples for stable hashing.
        """
        return hash(frozenset(
            (k, v.get("name", ""), v.get("rotation", 0))
            for k, v in board_cards.items()
        ))

    @classmethod
    def invalidate_cache(cls) -> None:
        """Explicitly invalidate the synergy cache.

        Call this when board state changes are known but the hash
        hasn't naturally changed (e.g., external card data mutation).
        """
        cls._last_board_hash = None
        cls._cached_result = None

    @classmethod
    def compute(
        cls,
        board_cards: Dict[Coord, Dict],
        db,
    ) -> SynergyComputeResult:
        if not board_cards:
            return SynergyComputeResult.empty()

        # Cache check: return cached result if board hasn't changed
        board_hash = cls._compute_board_hash(board_cards)
        if board_hash == cls._last_board_hash and cls._cached_result is not None:
            return cls._cached_result

        coord_list = list(board_cards.keys())
        coord_set  = set(coord_list)

        # Board cards dict → callback dönüşümü
        def _get_edge_group(coord: Coord, dir_idx: int) -> Optional[str]:
            item = board_cards.get(coord)
            if not item:
                return None
            card_data = db.lookup(item["name"])
            if not card_data:
                return None
            edges    = list(card_data.stats.items())   # [(stat_name, value), ...]
            rot      = item.get("rotation", 0)
            real_idx = (dir_idx - rot) % 6
            if real_idx >= len(edges):
                return None
            return STAT_TO_GROUP.get(edges[real_idx][0])

        def _get_neighbor(coord: Coord, dir_idx: int) -> Optional[Coord]:
            dq, dr = ENGINE_HEX_DIRS[dir_idx]
            nb = (coord[0] + dq, coord[1] + dr)
            return nb if nb in coord_set else None

        result = compute_synergy(coord_list, _get_edge_group, _get_neighbor)

        computed = SynergyComputeResult(
            group_counts    = result.group_counts,
            group_bonuses   = result.group_bonuses,
            total           = result.total,
            adjacency_pairs = result.adjacency_pairs,
        )

        # Store in cache
        cls._last_board_hash = board_hash
        cls._cached_result = computed

        return computed
