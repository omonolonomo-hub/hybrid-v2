"""
hex_math.py — Pure axial hex coordinate math functions.

Extracted from hex_grid.py to keep rendering concerns separate from
coordinate math. These functions have no pygame dependency and are
straightforward to unit-test in isolation.
"""

import math
from v2.constants import GridMath, CameraState


def axial_to_pixel(q: int, r: int, camera: CameraState) -> tuple[float, float]:
    """Convert axial hex coordinates to center pixel position with camera support."""
    zoom = camera.zoom
    off_x = camera.offset_x
    off_y = camera.offset_y

    base_x = GridMath.HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3) / 2 * r)
    base_y = GridMath.HEX_SIZE * (3 / 2 * r)

    x = (base_x * zoom) + GridMath.ORIGIN_X + off_x
    y = (base_y * zoom) + GridMath.ORIGIN_Y + off_y

    return x, y


def pixel_to_axial(px: float, py: float, camera: CameraState) -> tuple[int, int]:
    """Convert a pixel position to the nearest axial hex coordinate with camera support."""
    zoom = camera.zoom
    off_x = camera.offset_x
    off_y = camera.offset_y

    px -= (GridMath.ORIGIN_X + off_x)
    py -= (GridMath.ORIGIN_Y + off_y)

    px /= zoom
    py /= zoom

    q_f = (math.sqrt(3) / 3 * px - 1 / 3 * py) / GridMath.HEX_SIZE
    r_f = (2 / 3 * py) / GridMath.HEX_SIZE

    return _hex_round(q_f, r_f)


def hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Return the hex grid distance between two axial coordinates."""
    aq, ar = a
    bq, br = b
    as_ = -aq - ar
    bs = -bq - br
    return max(abs(aq - bq), abs(ar - br), abs(as_ - bs))


def _hex_round(q_f: float, r_f: float) -> tuple[int, int]:
    """Round fractional axial coordinates to the nearest hex."""
    s_f = -q_f - r_f
    q, r, s = round(q_f), round(r_f), round(s_f)
    dq, dr, ds = abs(q - q_f), abs(r - r_f), abs(s - s_f)
    if dq > dr and dq > ds:
        q = -r - s
    elif dr > ds:
        r = -q - s
    return q, r
