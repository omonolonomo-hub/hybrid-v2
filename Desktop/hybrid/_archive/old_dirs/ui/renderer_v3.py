"""
Renderer V3 - Clean Tarot-Style UI
Board and Shop UI Cleanup v3 implementation

This is a clean implementation without legacy code.
"""

import pygame
import math
from typing import Tuple, Optional

# ── Colors ────────────────────────────────────────────────────
C_BG = (12, 15, 28)
C_PANEL = (18, 22, 38)
C_PANEL_2 = (22, 26, 42)
C_WHITE = (245, 245, 255)
C_GOLD = (255, 215, 0)
C_BRONZE = (205, 127, 50)

# Group colors
GROUP_COLORS = {
    "EXISTENCE": (255, 60, 50),
    "MIND": (50, 130, 255),
    "CONNECTION": (40, 230, 130),
}

# Rarity colors
RARITY_COLORS = {
    "1": (160, 160, 160),
    "2": (50, 255, 120),
    "3": (0, 180, 255),
    "4": (255, 0, 255),
    "5": (255, 215, 0),
    "E": (255, 255, 255),
}

# Stat to group mapping
STAT_TO_GROUP = {
    "Power": "EXISTENCE",
    "Durability": "EXISTENCE",
    "Size": "EXISTENCE",
    "Speed": "EXISTENCE",
    "Meaning": "MIND",
    "Secret": "MIND",
    "Intelligence": "MIND",
    "Trace": "MIND",
    "Gravity": "CONNECTION",
    "Harmony": "CONNECTION",
    "Spread": "CONNECTION",
    "Prestige": "CONNECTION",
}

STAT_SHORT = {
    "Power": "PW", "Durability": "DU", "Size": "SZ", "Speed": "SP",
    "Meaning": "MN", "Secret": "SC", "Intelligence": "IN", "Trace": "TR",
    "Gravity": "GR", "Harmony": "HR", "Spread": "SR", "Prestige": "PR",
}

# Constants
HEX_SIZE = 85
EDGE_LABEL_INSET = 12


# ── Helper Functions ──────────────────────────────────────────
def _hex_corners(cx, cy, r):
    """Calculate hex corner positions."""
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.radians(angle_deg)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        corners.append((x, y))
    return corners


def _edge_midpoint(corners, index):
    """Get midpoint of hex edge."""
    ax, ay = corners[index]
    bx, by = corners[(index + 1) % 6]
    return ((ax + bx) / 2, (ay + by) / 2)


def _toward_center(px, py, cx, cy, inset):
    """Move point toward center by inset amount."""
    dx = cx - px
    dy = cy - py
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.01:
        return (px, py)
    ratio = inset / dist
    return (px + dx * ratio, py + dy * ratio)


def _darken(color, factor):
    """Darken a color by factor (0-1)."""
    return tuple(max(0, int(c * factor)) for c in color[:3])


def _rarity_color(rarity):
    """Get color for rarity."""
    return RARITY_COLORS.get(str(rarity), (160, 160, 160))


def _safe_rarity_int(rarity):
    """Convert rarity to int (E -> 6)."""
    if str(rarity).upper() == "E":
        return 6
    try:
        return int(rarity)
    except:
        return 1


def _truncate_to_width(font, text, max_width, suffix="..."):
    """Truncate text to fit width."""
    if font.size(text)[0] <= max_width:
        return text
    for i in range(len(text), 0, -1):
        truncated = text[:i] + suffix
        if font.size(truncated)[0] <= max_width:
            return truncated
    return suffix


# ══════════════════════════════════════════════════════════════
#  CYBER RENDERER V3
# ══════════════════════════════════════════════════════════════
class CyberRendererV3:
    """Clean tarot-style renderer without legacy code."""
    
    def __init__(self, fonts=None):
        self.fonts = fonts or {}
    
    def _font(self, key, fallback="consolas", size=12, bold=False):
        """Get font from cache or create."""
        if key in self.fonts:
            return self.fonts[key]
        try:
            return pygame.font.SysFont(fallback, size, bold=bold)
        except:
            return pygame.font.Font(None, size)
    
    def _draw_tarot_frame(self, surface, cx, cy, r, rarity_col, rarity_level, highlight=False):
        """Draw tarot-style hex frame with rarity-based geometry.
        
        Level 1: Single thin contour
        Level 2: Corner ticks + double contour
        Level 3: Double thin contour
        Level 4: Double contour + diagonal motif
        Level 5/E: Gold accent ring
        """
        corners = _hex_corners(cx, cy, r)
        border_col = rarity_col if highlight else _darken(rarity_col, 0.15)
        bw = 3 if highlight else 2
        
        # Draw frame based on rarity level
        if rarity_level >= 3:
            # Double contour
            outer = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r)]
            inner = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r - 5)]
            pygame.draw.polygon(surface, border_col, outer, bw)
            pygame.draw.polygon(surface, _darken(border_col, 0.35), inner, 1)
        else:
            # Single contour
            pts = [(int(x), int(y)) for x, y in corners]
            pygame.draw.polygon(surface, border_col, pts, bw if rarity_level == 2 else 1)
        
        # Level 2: Corner ticks
        if rarity_level == 2:
            t = 0.18
            for i in range(6):
                ax, ay = corners[i]
                bx, by = corners[(i + 1) % 6]
                pygame.draw.line(surface, border_col,
                               (int(ax), int(ay)),
                               (int(ax + (bx - ax) * t), int(ay + (by - ay) * t)), 2)
                pygame.draw.line(surface, border_col,
                               (int(bx), int(by)),
                               (int(bx + (ax - bx) * t), int(by + (ay - by) * t)), 2)
        
        # Level 4+: Diagonal motif
        if rarity_level >= 4:
            mids = [_edge_midpoint(corners, i) for i in range(6)]
            mc = _darken(rarity_col, 0.45)
            for i in range(3):
                ax, ay = mids[i]
                bx, by = mids[i + 3]
                pygame.draw.line(surface, mc, (int(ax), int(ay)), (int(bx), int(by)), 1)
        
        # Level 5+: Gold accent ring
        if rarity_level >= 5:
            gold_pts = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r - 8)]
            pygame.draw.polygon(surface, C_GOLD, gold_pts, 1)
        
        # Level 6 (E): Diamond markers at edge midpoints
        if rarity_level == 6:
            mids = [_edge_midpoint(corners, i) for i in range(6)]
            diamond_size = 5
            for mx, my in mids:
                diamond_pts = [
                    (int(mx), int(my - diamond_size)),
                    (int(mx + diamond_size), int(my)),
                    (int(mx), int(my + diamond_size)),
                    (int(mx - diamond_size), int(my))
                ]
                pygame.draw.polygon(surface, C_GOLD, diamond_pts)
                pygame.draw.polygon(surface, border_col, diamond_pts, 1)
    
    def draw_hex_card(self, surface, card, pos, r=68, is_hovered=False, highlighted=False):
        """Draw board card with tarot-style hex frame.
        
        Clean implementation:
        - Hex body fill
        - Tarot frame (rarity-based geometry)
        - Card name at center
        - Edge stats at edge midpoints (no badges)
        - Minimal passive indicator
        """
        x, y = pos
        rarity = str(getattr(card, "rarity", "1"))
        rarity_col = _rarity_color(rarity)
        rarity_level = _safe_rarity_int(rarity)
        highlight = is_hovered or highlighted
        
        # 1. Hex body fill
        body_pts = [(int(px), int(py)) for px, py in _hex_corners(x, y, r - 6)]
        pygame.draw.polygon(surface, C_PANEL_2, body_pts)
        
        # 2. Tarot frame
        self._draw_tarot_frame(surface, x, y, r - 6, rarity_col, rarity_level, highlight)
        
        # 3. Card name at center
        font_name = self._font("xs_bold", "consolas", 11, bold=True)
        name_raw = getattr(card, "name", "")
        name_img = font_name.render(_truncate_to_width(font_name, name_raw[:16].upper(), 78, ""), True, C_WHITE)
        surface.blit(name_img, (x - name_img.get_width() // 2, y - name_img.get_height() // 2))
        
        # 4. Edge stats (no badges, clean text)
        corners = _hex_corners(x, y, r - 6)
        edges = getattr(card, "rotated_edges", lambda: [])()
        font_stat = self._font("xs_bold", "consolas", 12, bold=True)
        
        for index, (stat_name, value) in enumerate(edges[:6]):
            if str(stat_name).startswith("_") or value == 0:
                continue
            
            # Position near edge midpoint
            mp = _edge_midpoint(corners, index)
            lp = _toward_center(mp[0], mp[1], x, y, EDGE_LABEL_INSET)
            
            # Color by upper-group
            stat_group = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            stat_col = GROUP_COLORS.get(stat_group, rarity_col)
            
            # Render with shadow
            val_str = str(value)
            val_img = font_stat.render(val_str, True, stat_col)
            vx = int(lp[0] - val_img.get_width() / 2)
            vy = int(lp[1] - val_img.get_height() / 2)
            
            shadow_img = font_stat.render(val_str, True, (0, 0, 0))
            for sdx, sdy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                surface.blit(shadow_img, (vx + sdx, vy + sdy))
            surface.blit(val_img, (vx, vy))
        
        # 5. Passive indicator (minimal dot)
        if getattr(card, "passive_type", "none") not in ("none", None):
            pygame.draw.circle(surface, rarity_col, (int(x), int(y + 10)), 2)
    
    def draw_shop_card(self, surface, card, rect, hovered=False, bought=False, affordable=True, cost=0, alpha=255):
        """Draw shop card with elegant tarot-style design.
        
        Professional layout:
        - Ornate header with rarity frame
        - Card name with decorative elements
        - Elegant stat display
        - Passive ability section
        - Cost badge
        """
        # Create layer
        layer = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        layer.fill((0, 0, 0, 0))
        
        rarity = str(getattr(card, "rarity", "1"))
        rarity_col = _rarity_color(rarity)
        rarity_level = _safe_rarity_int(rarity)
        
        # Background - elegant gradient effect
        if bought:
            bg_base = (12, 14, 20)
            border_col = (60, 65, 75)
        elif hovered:
            bg_base = (28, 32, 48)
            border_col = rarity_col
        else:
            bg_base = (18, 22, 34)
            border_col = _darken(rarity_col, 0.3)
        
        # Main card background
        pygame.draw.rect(layer, bg_base, layer.get_rect(), border_radius=12)
        
        # Rarity border with corner accents
        pygame.draw.rect(layer, border_col, layer.get_rect(), width=2, border_radius=12)
        
        # Corner ornaments (small diamonds)
        corner_size = 4
        corners = [
            (8, 8), (rect.width - 8, 8),
            (8, rect.height - 8), (rect.width - 8, rect.height - 8)
        ]
        for cx, cy in corners:
            diamond = [
                (cx, cy - corner_size),
                (cx + corner_size, cy),
                (cx, cy + corner_size),
                (cx - corner_size, cy)
            ]
            pygame.draw.polygon(layer, border_col, diamond)
        
        # Layout
        margin = 16
        y_pos = 18
        
        # 1. HEADER - Card name with decorative frame
        font_name = self._font("md_bold", "consolas", 15, bold=True)
        name_str = _truncate_to_width(font_name, getattr(card, "name", "").upper(), rect.width - margin * 2 - 10)
        name_img = font_name.render(name_str, True, C_WHITE if not bought else (120, 125, 135))
        
        # Name background panel
        name_panel_h = 32
        name_panel = pygame.Rect(margin, y_pos, rect.width - margin * 2, name_panel_h)
        pygame.draw.rect(layer, (8, 10, 16, 180), name_panel, border_radius=6)
        pygame.draw.rect(layer, border_col, name_panel, width=1, border_radius=6)
        
        # Rarity accent line at top of name panel
        pygame.draw.rect(layer, rarity_col if not bought else (80, 85, 95),
                        (name_panel.x + 8, name_panel.y + 2, name_panel.width - 16, 2), border_radius=1)
        
        # Center name
        layer.blit(name_img, (rect.width // 2 - name_img.get_width() // 2, y_pos + 12))
        y_pos += name_panel_h + 12
        
        # 2. CATEGORY & RARITY INFO
        category = getattr(card, "category", "Unknown")
        font_cat = self._font("xs", "consolas", 10)
        cat_str = f"{category[:20]} • Rarity {rarity}"
        cat_img = font_cat.render(cat_str, True, (140, 145, 160) if not bought else (90, 95, 105))
        layer.blit(cat_img, (rect.width // 2 - cat_img.get_width() // 2, y_pos))
        y_pos += 20
        
        # 3. DOMINANT GROUP INDICATOR (elegant circle)
        dom = getattr(card, "dominant_group", lambda: "EXISTENCE")()
        dom_col = GROUP_COLORS.get(dom, (120, 120, 120))
        
        circle_y = y_pos + 30
        circle_r = 24
        
        # Outer glow ring
        for i in range(3):
            glow_r = circle_r + 2 + i * 2
            glow_alpha = 40 - i * 10
            glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*dom_col, glow_alpha), (glow_r + 2, glow_r + 2), glow_r, 1)
            layer.blit(glow_surf, (rect.width // 2 - glow_r - 2, circle_y - glow_r - 2))
        
        # Main circle
        pygame.draw.circle(layer, _darken(dom_col, 0.7), (rect.width // 2, circle_y), circle_r)
        pygame.draw.circle(layer, dom_col, (rect.width // 2, circle_y), circle_r, 2)
        
        # Group initial
        font_group = self._font("md_bold", "consolas", 14, bold=True)
        group_initial = dom[0] if dom else "?"
        group_img = font_group.render(group_initial, True, dom_col)
        layer.blit(group_img, (rect.width // 2 - group_img.get_width() // 2, circle_y - group_img.get_height() // 2))
        
        y_pos = circle_y + circle_r + 16
        
        # 4. STATS SECTION - Elegant grid
        stats_panel_h = 85
        stats_panel = pygame.Rect(margin, y_pos, rect.width - margin * 2, stats_panel_h)
        
        # Stats background
        pygame.draw.rect(layer, (10, 12, 18, 200), stats_panel, border_radius=6)
        pygame.draw.rect(layer, (40, 45, 60), stats_panel, width=1, border_radius=6)
        
        # Stats title
        font_stats_title = self._font("xs_bold", "consolas", 10, bold=True)
        stats_title = font_stats_title.render("ATTRIBUTES", True, (120, 130, 150))
        layer.blit(stats_title, (stats_panel.x + 8, stats_panel.y + 6))
        
        # Draw stats grid
        self.draw_shop_stat_grid(layer, card, pygame.Rect(stats_panel.x + 6, stats_panel.y + 22, stats_panel.width - 12, stats_panel.height - 28))
        
        y_pos += stats_panel_h + 10
        
        # 5. PASSIVE ABILITY (if exists)
        passive_type = getattr(card, "passive_type", "none")
        if passive_type and passive_type != "none":
            passive_h = 36
            passive_panel = pygame.Rect(margin, y_pos, rect.width - margin * 2, passive_h)
            
            pygame.draw.rect(layer, (10, 12, 18, 180), passive_panel, border_radius=6)
            pygame.draw.rect(layer, rarity_col if not bought else (70, 75, 85), passive_panel, width=1, border_radius=6)
            
            font_passive = self._font("xs", "consolas", 9)
            passive_str = f"✦ {passive_type[:18]}"
            passive_img = font_passive.render(passive_str, True, rarity_col if not bought else (100, 105, 115))
            layer.blit(passive_img, (passive_panel.x + 8, passive_panel.y + 12))
            
            y_pos += passive_h + 8
        
        # 6. COST BADGE - Bottom right corner
        cost_size = 42
        cost_x = rect.width - margin - cost_size
        cost_y = rect.height - margin - cost_size
        
        # Cost background (hexagonal badge)
        cost_center = (cost_x + cost_size // 2, cost_y + cost_size // 2)
        cost_hex = _hex_corners(cost_center[0], cost_center[1], cost_size // 2)
        cost_pts = [(int(x), int(y)) for x, y in cost_hex]
        
        if affordable and not bought:
            cost_bg = (40, 35, 20)
            cost_border = C_GOLD
        else:
            cost_bg = (25, 25, 30)
            cost_border = (100, 100, 110)
        
        pygame.draw.polygon(layer, cost_bg, cost_pts)
        pygame.draw.polygon(layer, cost_border, cost_pts, 2)
        
        # Cost text
        font_cost = self._font("md_bold", "consolas", 14, bold=True)
        cost_str = str(cost)
        cost_img = font_cost.render(cost_str, True, C_GOLD if (affordable and not bought) else (120, 120, 130))
        layer.blit(cost_img, (cost_center[0] - cost_img.get_width() // 2, cost_center[1] - cost_img.get_height() // 2 - 2))
        
        # "G" label
        font_g = self._font("xs", "consolas", 8)
        g_img = font_g.render("G", True, C_GOLD if (affordable and not bought) else (100, 100, 110))
        layer.blit(g_img, (cost_center[0] - g_img.get_width() // 2, cost_center[1] + 6))
        
        # Blit to surface
        if alpha < 255:
            layer.set_alpha(alpha)
        surface.blit(layer, rect.topleft)
    
    def draw_shop_stat_grid(self, surface, card, rect):
        """Draw elegant stats grid with upper-group colors."""
        # Get real stats (non-zero, non-internal)
        edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
        real_stats = [(name, val) for name, val in edge_source 
                     if val > 0 and not str(name).startswith("_")]
        
        if not real_stats:
            # No stats message
            font = self._font("xs", "consolas", 10)
            no_stats = font.render("No active attributes", True, (100, 105, 120))
            surface.blit(no_stats, (rect.x + rect.width // 2 - no_stats.get_width() // 2, 
                                   rect.y + rect.height // 2 - no_stats.get_height() // 2))
            return
        
        # Grid layout: 2 columns
        cols = 2
        rows = (len(real_stats) + cols - 1) // cols
        cell_w = (rect.width - 8) // cols
        cell_h = max(22, (rect.height - 4) // max(1, rows))
        
        font_stat = self._font("xs_bold", "consolas", 10, bold=True)
        font_val = self._font("sm_bold", "consolas", 12, bold=True)
        
        for idx, (stat_name, value) in enumerate(real_stats):
            col = idx % cols
            row = idx // cols
            
            cell_x = rect.x + col * cell_w + 2
            cell_y = rect.y + row * cell_h + 2
            cell = pygame.Rect(cell_x, cell_y, cell_w - 6, cell_h - 4)
            
            # Color by upper-group
            upper_group = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            group_col = GROUP_COLORS.get(upper_group, (120, 120, 120))
            
            # Elegant cell background with gradient effect
            cell_bg = _darken(group_col, 0.85)
            pygame.draw.rect(surface, cell_bg, cell, border_radius=4)
            
            # Subtle inner glow
            inner_rect = pygame.Rect(cell.x + 1, cell.y + 1, cell.width - 2, cell.height - 2)
            pygame.draw.rect(surface, (*group_col, 30), inner_rect, border_radius=3)
            
            # Border
            pygame.draw.rect(surface, group_col, cell, width=1, border_radius=4)
            
            # Stat short name (left side)
            short_name = STAT_SHORT.get(stat_name, stat_name[:2].upper())
            stat_img = font_stat.render(short_name, True, _darken(group_col, 0.2))
            surface.blit(stat_img, (cell.x + 6, cell.y + cell.height // 2 - stat_img.get_height() // 2))
            
            # Value (right side, larger)
            val_img = font_val.render(str(value), True, group_col)
            surface.blit(val_img, (cell.right - val_img.get_width() - 6, 
                                  cell.y + cell.height // 2 - val_img.get_height() // 2))

    
    def set_fonts(self, fonts):
        """Set fonts dictionary."""
        self.fonts = fonts
    
    def draw_vfx_base(self, surface):
        """Draw base VFX effects (grid, scanlines, etc)."""
        # Simple cyber grid background
        W, H = surface.get_size()
        
        # Horizon grid lines
        for i in range(12):
            y = H - int((i ** 1.6) * 8)
            alpha = max(8, 120 - i * 10)
            pygame.draw.line(surface, (20, 25, 45, alpha), (0, y), (W, y), 1)
        
        # Vertical perspective lines
        horizon_y = 140
        center_x = W // 2
        for lane in range(-8, 9):
            start_x = center_x + lane * 80
            end_x = center_x + lane * 360
            pygame.draw.line(surface, (20, 25, 45, 35), (start_x, horizon_y), (end_x, H), 1)
        
        # Update timer
        if not hasattr(self, 'timer'):
            self.timer = 0.0
        self.timer += 0.016
    
    def draw_priority_popup(self, surface, card, mx, my):
        """Draw priority/stat popup for hovered card."""
        if card is None:
            return
        
        # Simple tooltip with card info
        font = self._font("xs_bold", "consolas", 11, bold=True)
        
        lines = []
        lines.append(f"{getattr(card, 'name', 'Unknown').upper()}")
        lines.append(f"Rarity: {getattr(card, 'rarity', '?')}")
        
        # Show edges
        edges = getattr(card, 'rotated_edges', lambda: [])()
        for i, (stat_name, value) in enumerate(edges[:6]):
            if value > 0 and not str(stat_name).startswith("_"):
                short = STAT_SHORT.get(stat_name, stat_name[:2])
                lines.append(f"{short}: {value}")
        
        # Passive
        passive = getattr(card, 'passive_type', None)
        if passive and passive != "none":
            lines.append(f"✦ {passive}")
        
        # Draw popup
        padding = 8
        line_h = 16
        max_w = max(font.size(line)[0] for line in lines)
        popup_w = max_w + padding * 2
        popup_h = len(lines) * line_h + padding * 2
        
        # Position near mouse
        px = mx + 20
        py = my - popup_h // 2
        
        # Keep on screen
        W, H = surface.get_size()
        if px + popup_w > W - 10:
            px = mx - popup_w - 20
        if py < 10:
            py = 10
        if py + popup_h > H - 10:
            py = H - popup_h - 10
        
        # Draw background
        popup_rect = pygame.Rect(px, py, popup_w, popup_h)
        pygame.draw.rect(surface, (8, 10, 18, 240), popup_rect, border_radius=6)
        pygame.draw.rect(surface, (0, 242, 255), popup_rect, width=1, border_radius=6)
        
        # Draw text
        y = py + padding
        for line in lines:
            text_img = font.render(line, True, C_WHITE)
            surface.blit(text_img, (px + padding, y))
            y += line_h
    
    def draw_clean_tooltip(self, surface, card, mx, my, active=True):
        """Draw clean tooltip (alias for draw_priority_popup)."""
        if active:
            self.draw_priority_popup(surface, card, mx, my)
