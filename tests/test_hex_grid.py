import pytest
from v2.ui.hex_grid import axial_to_pixel, pixel_to_axial, VALID_HEX_COORDS, HEX_DIRECTION_MAP, _hex_round
from v2.constants import GridMath

# --- 1. CONTRACT ---
def test_hexgrid_has_37_valid_cells():
    assert len(VALID_HEX_COORDS) == 37
    assert (3, 0) in VALID_HEX_COORDS
    assert (0, -3) in VALID_HEX_COORDS
    assert (-3, 3) in VALID_HEX_COORDS

def test_hexgrid_directions_are_6_and_correctly_indexed():
    assert len(HEX_DIRECTION_MAP) == 6
    assert HEX_DIRECTION_MAP[0] == (1, -1)   

# --- 2. EDGE CASE ---
def test_hexgrid_rejects_out_of_bounds_coordinates():
    invalid_coords = [(4, 0), (0, -4), (3, 1), (-2, -2)]
    for coord in invalid_coords:
        assert coord not in VALID_HEX_COORDS

def test_hexgrid_extreme_pixel_click():
    q, r = pixel_to_axial(-10000, 50000)
    assert isinstance(q, int)
    assert isinstance(r, int)

# --- 3. INVARIANT ---
def test_hexgrid_center_is_stable():
    assert pixel_to_axial(GridMath.ORIGIN_X, GridMath.ORIGIN_Y) == (0, 0)
    
def test_hexgrid_roundtrip_stability():
    for q, r in VALID_HEX_COORDS:
        px, py = axial_to_pixel(q, r)
        assert pixel_to_axial(px, py) == (q, r)

# --- 4. PRECISION EDGE CASES (TDD 1) ---
def test_hexgrid_tie_breaker_rounding():
    """Matematiksel eşitlik (tie) durumlarında (Örn: Tam iki hex'in sınırına tıklandığında) motorun rastgele/hatalı bir hex'e kaçmaması, mutlak bir karar vermesi."""
    
    # 1. Tam sınır (Edge): (0,0) ile (1,0) arası. q_f=0.5, r=0.
    # Python 3 round(0.5) = 0 yapar. dq = 0.5, dr = 0, ds = 0.5. dq > ds False döner.
    # Motor bunu sessizce birine yaslamalıdır. Sonucun plane denklemine uymasi lazim (0,0 veya 1,0 olmali).
    
    q, r = _hex_round(0.5, 0.0)
    assert (q, r) in [(0, 0), (1, 0)], f"Tie-breaker failed for 0.5, 0.0. Got {(q, r)}"

    q, r = _hex_round(0.5, 0.5)
    assert (q, r) in [(0, 1), (1, 0)], f"Tie-breaker failed for 0.5, 0.5. Got {(q, r)}"

    # 3-lü Kesişim noktası: (1/3, 1/3). Hex köşesine tam tıklama anı!
    # q=0, r=0, s=0 | q=1, r=0, s=-1 | q=0, r=1, s=-1 arası bir nokta.
    q, r = _hex_round(1/3, 1/3)
    assert (q, r) in [(0, 0), (1, 0), (0, 1)], f"Corner click failed. Got {(q, r)}"
    
    # Eğer motor tie-breaker'i doğru Handle edemiyorsa ve Python'un native round(x.5) -> even davranışına kurban gidiyorsa:
    # 1.5 -> 2 olur. (-1.5) -> -2 olur.
    q, r = _hex_round(1.5, 0.0) # 1.5, 0.0, -1.5
    # Beklenen: (1, 0) veya (2, 0)
    assert (q, r) in [(1, 0), (2, 0)], f"Tie-breaker failed for 1.5, 0.0. Got {(q, r)}"
