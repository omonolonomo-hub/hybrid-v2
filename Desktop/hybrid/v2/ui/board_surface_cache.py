from __future__ import annotations

import math
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

import pygame

from v2.constants import CameraState, Colors, GridMath, Layout

Coord = Tuple[int, int]


class BoardSurfaceCache:
    """
    Hex grid ve synergy geometry'si için lazy surface cache.

    Cache katmanları:
      - _grid_surface: hex fill + border (animasyonsuz, statik)
      - _synergy_geom: synergy adjacency pair'leri için pixel koordinatları (statik geometry)

    Dirty flag'ler:
      - _board_dirty: board içeriği değişince
      - _camera_dirty: kamera zoom/offset değişince
    """

    __slots__ = (
        "_grid_surface",
        "_synergy_geom",
        "_hex_points_cache",
        "_board_dirty",
        "_camera_dirty",
        "_last_board_key",
        "_last_cam_key",
        "_surf_w",
        "_surf_h",
    )

    def __init__(self, width: int, height: int) -> None:
        self._surf_w = width
        self._surf_h = height

        self._grid_surface: Optional[pygame.Surface] = None
        # [(x1,y1,x2,y2,r,g,b,max_conn), ...]
        self._synergy_geom: List[Tuple[float, float, float, float, int, int, int, int]] = []
        # Per-hex cached geometry for cheap animated overlays:
        # {coord: (cx, cy, outer_pts, inner_pts)}
        self._hex_points_cache: Dict[
            Coord, Tuple[float, float, List[Tuple[int, int]], List[Tuple[int, int]]]
        ] = {}

        self._board_dirty = True
        self._camera_dirty = True
        self._last_board_key: Optional[frozenset[Coord]] = None
        self._last_cam_key: Optional[Tuple[float, float, float]] = None

    # ── Dirty markers ────────────────────────────────────────────────────────

    def mark_board_dirty(self) -> None:
        self._board_dirty = True

    def mark_camera_dirty(self) -> None:
        self._camera_dirty = True

    # ── Public API ───────────────────────────────────────────────────────────

    def get_grid(
        self,
        board_cards: Dict[Coord, object],
        camera: CameraState,
        valid_coords: Iterable[Coord] | FrozenSet[Coord],
    ) -> pygame.Surface:
        cam_key = self._cam_key(camera)
        board_key = frozenset(board_cards.keys())

        need_rebuild = (
            self._board_dirty
            or self._camera_dirty
            or cam_key != self._last_cam_key
            or board_key != self._last_board_key
            or self._grid_surface is None
        )

        if need_rebuild:
            self._rebuild_grid(board_cards, camera, valid_coords)
            self._last_board_key = board_key
            self._last_cam_key = cam_key
            self._board_dirty = False
            self._camera_dirty = False

        # _grid_surface set edildi
        return self._grid_surface  # type: ignore[return-value]

    def get_hex_points_cache(
        self,
        board_cards: Dict[Coord, object],
        camera: CameraState,
        valid_coords: Iterable[Coord] | FrozenSet[Coord],
    ) -> Dict[Coord, Tuple[float, float, List[Tuple[int, int]], List[Tuple[int, int]]]]:
        """
        Animated overlay'ler için hex noktalarını döndürür.
        Grid rebuild ile beraber güncellenir, bu yüzden grid'i lazily garanti eder.
        """
        _ = self.get_grid(board_cards, camera, valid_coords)
        return self._hex_points_cache

    def get_synergy_geom(
        self,
        adjacency_pairs: List[Tuple],
        camera: CameraState,
        board_cards: Dict[Coord, object],
    ) -> List[Tuple[float, float, float, float, int, int, int, int]]:
        cam_key = self._cam_key(camera)
        board_key = frozenset(board_cards.keys())

        if (
            cam_key != self._last_cam_key
            or board_key != self._last_board_key
            or self._board_dirty
            or self._camera_dirty
        ):
            self._rebuild_synergy_geom(adjacency_pairs, camera)
            # geom rebuild, ama grid'i mutlaka rebuild etmek zorunda değiliz;
            # yine de key'leri güncel tutalım ki bir sonraki çağrıda thrash olmasın.
            self._last_cam_key = cam_key
            self._last_board_key = board_key

        return self._synergy_geom

    # ── Rebuild: Grid ─────────────────────────────────────────────────────────

    def _rebuild_grid(
        self,
        board_cards: Dict[Coord, object],
        camera: CameraState,
        valid_coords: Iterable[Coord] | FrozenSet[Coord],
    ) -> None:
        """
        Tüm hex'leri animasyonsuz olarak _grid_surface'e çizer.

        Not: Breathing ve hover bu layer'da yok; hover per-frame overlay.
        """
        surf = pygame.Surface((self._surf_w, self._surf_h), pygame.SRCALPHA).convert_alpha()
        surf.fill((0, 0, 0, 0))

        zoom = camera.zoom
        base_r = GridMath.HEX_SIZE * zoom
        clip_rect = self._clip_rect()

        points_cache: Dict[Coord, Tuple[float, float, List[Tuple[int, int]], List[Tuple[int, int]]]] = {}

        for coord in valid_coords:
            cx, cy = _axial_to_pixel(coord[0], coord[1], camera)

            if not self._in_clip(cx, cy, base_r, clip_rect):
                continue

            is_filled = coord in board_cards

            outer = self._hex_points(cx, cy, base_r)
            inner = self._hex_points(cx, cy, base_r * 0.85)
            points_cache[coord] = (cx, cy, outer, inner)

            body_a = 140 if is_filled else 30
            pygame.draw.polygon(surf, (16, 13, 20, body_a), outer)

            inner_a = 80 if is_filled else 20
            pygame.draw.polygon(surf, (25, 21, 31, inner_a), inner)

            border_col = (50, 41, 61, 100)
            border_w = max(1, int(2 * zoom))
            pygame.draw.polygon(surf, border_col, outer, border_w)

            if is_filled:
                pygame.draw.polygon(surf, (145, 120, 175, 100), inner, 1)

        self._grid_surface = surf
        self._hex_points_cache = points_cache

    # ── Rebuild: Synergy geometry ─────────────────────────────────────────────

    def _rebuild_synergy_geom(self, adjacency_pairs: List[Tuple], camera: CameraState) -> None:
        GROUP_COL = {
            "EXISTENCE": Colors.EXISTENCE,
            "MIND": Colors.MIND,
            "CONNECTION": Colors.CONNECTION,
        }

        conn_count: Dict[Coord, int] = {}
        for ca, cb, ga, gb in adjacency_pairs:
            if ga == gb:
                conn_count[ca] = conn_count.get(ca, 0) + 1
                conn_count[cb] = conn_count.get(cb, 0) + 1

        geom: List[Tuple[float, float, float, float, int, int, int, int]] = []
        for coord_a, coord_b, group_a, group_b in adjacency_pairs:
            if group_a != group_b:
                continue
            col = GROUP_COL.get(group_a, (180, 180, 180))
            max_conn = max(conn_count.get(coord_a, 1), conn_count.get(coord_b, 1))

            x1, y1 = _axial_to_pixel(coord_a[0], coord_a[1], camera)
            x2, y2 = _axial_to_pixel(coord_b[0], coord_b[1], camera)

            geom.append((x1, y1, x2, y2, int(col[0]), int(col[1]), int(col[2]), int(max_conn)))

        self._synergy_geom = geom

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cam_key(camera: CameraState) -> Tuple[float, float, float]:
        return (
            round(camera.zoom, 3),
            round(camera.offset_x, 1),
            round(camera.offset_y, 1),
        )

    @staticmethod
    def _hex_points(cx: float, cy: float, r: float) -> List[Tuple[int, int]]:
        pts: List[Tuple[int, int]] = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        return pts

    @staticmethod
    def _clip_rect() -> pygame.Rect:
        return pygame.Rect(
            Layout.CENTER_ORIGIN_X,
            Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 5,
            Layout.CENTER_W,
            Layout.HAND_PANEL_Y - (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H) - 10,
        )

    @staticmethod
    def _in_clip(cx: float, cy: float, r: float, clip: pygame.Rect) -> bool:
        return clip.collidepoint(cx, cy) or clip.collidepoint(cx + r, cy) or clip.collidepoint(cx - r, cy)


def _axial_to_pixel(q: int, r: int, camera: CameraState) -> Tuple[float, float]:
    """
    `v2.ui.hex_grid.axial_to_pixel` ile aynı matematik, ama import/cycle riskini önlemek için kopya.
    """
    zoom = camera.zoom
    base_x = GridMath.HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3) / 2 * r)
    base_y = GridMath.HEX_SIZE * (3 / 2 * r)
    x = (base_x * zoom) + GridMath.ORIGIN_X + camera.offset_x
    y = (base_y * zoom) + GridMath.ORIGIN_Y + camera.offset_y
    return x, y

