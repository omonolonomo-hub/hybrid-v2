import pytest
import math
from v2.constants import Layout, GridMath, Screen
from v2.ui.hex_grid import axial_to_pixel, VALID_HEX_COORDS

def test_hexgrid_fully_fits_inside_center_panel_no_overlaps():
    """Hexagonal Grid'in ekranda taşmadığını ve UI panelleriyle çakışmadığını garanti eder."""
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    hex_w = math.sqrt(3) * GridMath.HEX_SIZE
    hex_h_radius = GridMath.HEX_SIZE

    for q, r in VALID_HEX_COORDS:
        px, py = axial_to_pixel(q, r)
        
        left_edge = px - hex_w / 2
        right_edge = px + hex_w / 2
        top_edge = py - hex_h_radius
        bottom_edge = py + hex_h_radius
        
        min_x = min(min_x, left_edge)
        max_x = max(max_x, right_edge)
        min_y = min(min_y, top_edge)
        max_y = max(max_y, bottom_edge)

    # 1. X EKSENİ KONTROLÜ (Solid UI panellerine taşmamalı)
    assert min_x >= Layout.LEFT_PANEL_W, f"Hex grid LEFT panele giriyor! En sol nokta: {min_x}"
    
    right_limit = Screen.W - Layout.RIGHT_PANEL_W
    assert max_x <= right_limit, f"Hex grid RIGHT panele giriyor! En sağ nokta: {max_x} limit: {right_limit}"

    # 2. Y EKSENİ KONTROLÜ (Ortadaki paneller)
    shop_bottom = Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H
    hand_top = Layout.HAND_PANEL_Y

    assert min_y >= shop_bottom, f"Hex grid SHOP panelin içine taşıyor! Üst tepe: {min_y}, Dükkan altı: {shop_bottom}"
    assert max_y <= hand_top, f"Hex grid HAND panelin içine taşıyor! Alt taban: {max_y}, Hand üstü: {hand_top}"
