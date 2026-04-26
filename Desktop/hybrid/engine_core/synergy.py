"""
engine_core/synergy.py
═══════════════════════════════════════════════════════════════════
Synergy BFS hesaplaması için TEK KAYNAK (Single Source of Truth).

Daha önce aynı BFS üç yerde kopyalanmıştı:
  ✗  engine_core/board.py            → calculate_group_synergy_bonus
  ✗  v2/core/ui_adapter.py           → _build_synergy_view (inline BFS)
  ✗  v2/core/synergy_calculator.py   → SynergyCalculator.compute()

Artık bu modül tek yetkili kaynaktır.
board.py ve synergy_calculator.py yalnızca bu modülü çağırır.

Kural: Başka bir yerde synergy BFS kodu görürseniz silin.
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Set, Tuple

from engine_core.constants import (
    HEX_DIRS, OPP_DIR, STAT_TO_GROUP,
    SYNERGY_TIER_SMALL, SYNERGY_TIER_MED, SYNERGY_TIER_LARGE,
    SYNERGY_TIER_HUGE, SYNERGY_TIER_INCREMENT,
)

Coord = Tuple[int, int]

# Grup sabitleri
GROUPS: Tuple[str, ...] = ("MIND", "CONNECTION", "EXISTENCE")


# ──────────────────────────────────────────────────────────────────
# Çıktı veri yapısı
# ──────────────────────────────────────────────────────────────────

class SynergyResult:
    """compute_synergy() çıktısı."""

    __slots__ = ("group_counts", "group_bonuses", "total", "adjacency_pairs")

    def __init__(
        self,
        group_counts: Dict[str, int],
        group_bonuses: Dict[str, int],
        total: int,
        adjacency_pairs: List[Tuple],
    ):
        self.group_counts = group_counts
        self.group_bonuses = group_bonuses
        self.total = total
        self.adjacency_pairs = adjacency_pairs

    @staticmethod
    def empty() -> "SynergyResult":
        return SynergyResult(
            group_counts  = {g: 0 for g in GROUPS},
            group_bonuses = {g: 0 for g in GROUPS},
            total         = 0,
            adjacency_pairs = [],
        )


# ──────────────────────────────────────────────────────────────────
# Çekirdek hesaplama — edge-group lookup callback ile genel
# ──────────────────────────────────────────────────────────────────

def compute_synergy(
    coords: List[Coord],
    get_edge_group: Callable[[Coord, int], Optional[str]],
    get_neighbor: Callable[[Coord, int], Optional[Coord]],
) -> SynergyResult:
    """
    Genel synergy BFS hesaplayıcısı.

    Parametreler
    ─────────────
    coords : tahtadaki tüm kart koordinatları
    get_edge_group : (coord, dir_idx) → grup adı veya None
    get_neighbor : (coord, dir_idx) → komşu koordinat veya None
                   None = bu yönde komşu yok

    Dönüş
    ─────
    SynergyResult (group_counts, group_bonuses, total, adjacency_pairs)
    """
    if not coords:
        return SynergyResult.empty()

    coord_set: Set[Coord] = set(coords)
    group_counts:  Dict[str, int]  = {g: 0 for g in GROUPS}
    group_bonuses: Dict[str, int]  = {g: 0 for g in GROUPS}

    for group in GROUPS:
        visited: Set[Coord] = set()
        for coord in coord_set:
            if coord in visited:
                continue
            cluster, matches = _bfs_cluster(
                coord, group, coord_set, get_edge_group, get_neighbor
            )
            visited.update(cluster)
            n = len(cluster)
            if n >= 2:
                group_counts[group]  = max(group_counts[group], n)
                group_bonuses[group] += tier_bonus(n) + matches * 2

    total = sum(group_bonuses.values())
    adj   = _all_adjacency_pairs(coord_set, get_edge_group, get_neighbor)

    return SynergyResult(
        group_counts    = group_counts,
        group_bonuses   = group_bonuses,
        total           = total,
        adjacency_pairs = adj,
    )


# ──────────────────────────────────────────────────────────────────
# Board-özgü convenience fonksiyon
# ──────────────────────────────────────────────────────────────────

def compute_board_synergy(board) -> int:
    """
    Board objesi alan convenience wrapper.
    combat_engine ve eski calculate_group_synergy_bonus call-site'ları
    bunu kullanır.

    Dönüş: toplam synergy puanı (int)
    """
    grid = board.grid
    if not grid:
        return 0

    coord_list = list(grid.keys())
    coord_set  = set(coord_list)

    def _get_edge_group(coord: Coord, dir_idx: int) -> Optional[str]:
        card = grid.get(coord)
        if card is None:
            return None
        edges = card.rotated_edges()
        if dir_idx >= len(edges):
            return None
        stat_name, _ = edges[dir_idx]
        return STAT_TO_GROUP.get(stat_name)

    def _get_neighbor(coord: Coord, dir_idx: int) -> Optional[Coord]:
        dq, dr = HEX_DIRS[dir_idx]
        nb = (coord[0] + dq, coord[1] + dr)
        return nb if nb in coord_set else None

    result = compute_synergy(coord_list, _get_edge_group, _get_neighbor)
    return result.total


# ──────────────────────────────────────────────────────────────────
# İç yardımcılar
# ──────────────────────────────────────────────────────────────────

def _bfs_cluster(
    start: Coord,
    group: str,
    coord_set: Set[Coord],
    get_edge_group: Callable[[Coord, int], Optional[str]],
    get_neighbor: Callable[[Coord, int], Optional[Coord]],
) -> Tuple[Set[Coord], int]:
    """
    'start' noktasından BFS ile 'group' tipinde bağlı cluster'ı bulur.
    Dönüş: (cluster koordinat seti, eşleşen kenar çifti sayısı)
    """
    cluster: Set[Coord]       = {start}
    queue:   List[Coord]      = [start]
    seen:    Set[Coord]       = {start}
    matches                   = 0
    matched_pairs: Set[Tuple] = set()

    while queue:
        curr = queue.pop(0)
        for dir_idx in range(6):
            nb = get_neighbor(curr, dir_idx)
            if nb is None:
                continue

            g_a = get_edge_group(curr, dir_idx)
            g_b = get_edge_group(nb, OPP_DIR[dir_idx])

            if g_a == group and g_b == group:
                pair = (min(curr, nb), max(curr, nb))
                if pair not in matched_pairs:
                    matches += 1
                    matched_pairs.add(pair)
                if nb not in seen:
                    seen.add(nb)
                    cluster.add(nb)
                    queue.append(nb)

    return cluster, matches


def _all_adjacency_pairs(
    coord_set: Set[Coord],
    get_edge_group: Callable[[Coord, int], Optional[str]],
    get_neighbor: Callable[[Coord, int], Optional[Coord]],
) -> List[Tuple]:
    """
    Tahtadaki TÜM komşu kart çiftlerini döndürür (her çift bir kez).
    Format: (coord_a, coord_b, group_a_edge, group_b_edge)
    """
    pairs: List[Tuple] = []
    seen:  Set[Tuple]  = set()

    for coord in coord_set:
        for dir_idx in range(6):
            nb = get_neighbor(coord, dir_idx)
            if nb is None:
                continue
            pair_key = (min(coord, nb), max(coord, nb))
            if pair_key in seen:
                continue
            seen.add(pair_key)

            g_a = get_edge_group(coord, dir_idx) or ""
            g_b = get_edge_group(nb, OPP_DIR[dir_idx]) or ""
            pairs.append((coord, nb, g_a, g_b))

    return pairs


def tier_bonus(n: int) -> int:
    """
    Cluster size-based tiered bonus points.

    N=2 -> 3  |  N=3 -> 9  |  N=4-5 -> 16  |  N=6+ -> 25 + (N-6)*3

    Values sourced from engine_core/constants.py (SYNERGY_TIER_*).
    """
    if n == 2:    return SYNERGY_TIER_SMALL
    if n == 3:    return SYNERGY_TIER_MED
    if n <= 5:    return SYNERGY_TIER_LARGE
    return SYNERGY_TIER_HUGE + (n - 6) * SYNERGY_TIER_INCREMENT
