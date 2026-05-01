import pygame
import math
from collections.abc import Mapping

from v2.constants import Screen, Colors, Layout
from v2.ui import font_cache, icon_loader
from v2.ui.hex_grid_config import HexGridConfig

# ── Kategori Verileri (Minimap Taktik Renk Paleti & İkonlar) ───────────────────
_CAT_DATA = {
    "MYTHOLOGY": {"color": (248, 222, 34), "abbr": "MYTH", "icon": "ANKH"},
    "ART":       {"color": (240, 60, 110), "abbr": "ARTS", "icon": "PALETTE"},
    "NATURE":    {"color": (60, 255, 80),  "abbr": "NATR", "icon": "SEEDLING"},
    "COSMOS":    {"color": (140, 80, 255), "abbr": "COSM", "icon": "STAR"},
    "SCIENCE":   {"color": (3, 190, 240),  "abbr": "SCIE", "icon": "ATOM"},
    "HISTORY":   {"color": (255, 120, 40), "abbr": "HIST", "icon": "LANDMARK"},
}

class MinimapHUD:
    """
    Tactical Command Minimap (v13 - Optimized Layout & Proportions)
    Sidebar ile bütünleşik, dengeli içerik oranları, net görselleştirme.
    """
    def __init__(self, screen_w=Screen.W, screen_h=Screen.H):
        # 🎯 Size & Scale - SynergyHud'un altındaki kalan alanı tam kullan
        self.base_w = Layout.SIDEBAR_LEFT_W  # 340px (sidebar genişliği)
        self.base_h = Screen.H - (Layout.SYNERGY_HUD_Y + Layout.SYNERGY_HUD_H)
        
        # 📍 Anchor: SynergyHud'un hemen altı (dikişsiz - boşluk daraltıldı)
        self.anchor_x = 0 
        self.anchor_y = Layout.SYNERGY_HUD_Y + Layout.SYNERGY_HUD_H
        
        self.rect = pygame.Rect(self.anchor_x, self.anchor_y, self.base_w, self.base_h)

        # Draw Surface
        self.surface = pygame.Surface((self.base_w, self.base_h), pygame.SRCALPHA)
        self.time = 0.0
        self.category_stats = {}
        self.board_grid = {}
        
        # Hex grid configuration (lazy initialization)
        self._hex_config = HexGridConfig.from_engine()
        
        # 🎨 Layout Proportions (Optimized - hex grid'e daha fazla alan)
        # Hex Grid: Üst 68% (artırıldı) - Hex grid için daha fazla alan
        # Category Dashboard: Alt 32% (azaltıldı) - Kompakt
        self.grid_section_h = int(self.base_h * 0.68)
        self.category_section_h = self.base_h - self.grid_section_h
        
        # ── SynergyHud Stili: Gradient Panel Önbellekleri ──────────────────────
        from v2.ui.ui_utils import UIUtils
        
        # Renk paleti (Karbon-mor tonları - hex grid ile uyumlu)
        self._C_PANEL_TOP = (28, 24, 35, 255)  # Koyu mor-karbon
        self._C_PANEL_BOT = (16, 13, 20, 255)  # Daha koyu mor-karbon
        self._C_BORDER = (50, 41, 61, 180)  # Karbon-mor border
        
        # Grid section için gradient panel (üst padding azaltıldı)
        pad_top = 3  # Üst padding çok azaltıldı (Passives ile boşluk daraldı)
        pad_side = 6
        pad_bottom = 6
        
        grid_inner_w = self.base_w - pad_side * 2
        grid_inner_h = self.grid_section_h - pad_top - pad_bottom
        self._grid_panel = UIUtils.create_gradient_panel(
            grid_inner_w, grid_inner_h, 
            self._C_PANEL_TOP, self._C_PANEL_BOT,
            border_radius=8, border_color=self._C_BORDER
        )
        self.grid_panel_rect = pygame.Rect(pad_side, pad_top, grid_inner_w, grid_inner_h)
        
        # Category section için gradient panel
        cat_inner_w = self.base_w - pad_side * 2
        cat_inner_h = self.category_section_h - pad_side * 2
        self._cat_panel = UIUtils.create_gradient_panel(
            cat_inner_w, cat_inner_h,
            self._C_PANEL_TOP, self._C_PANEL_BOT,
            border_radius=8, border_color=self._C_BORDER
        )
        self.cat_panel_rect = pygame.Rect(pad_side, self.grid_section_h + pad_side, cat_inner_w, cat_inner_h)

    def update(self, dt_ms: float, board_cards: dict, mouse_pos: tuple) -> None:
        """ShopScene board_cards verisini iter — GameState'e dokunmaz."""
        self.time += dt_ms / 1000.0
        self._sync_data(board_cards)

    def _sync_data(self, board_cards: dict) -> None:
        
        _CAT_MAPPING = {
            "Mythology & Gods":     "MYTHOLOGY",
            "Art & Culture":        "ART",
            "Nature & Biology":     "NATURE",
            "Nature & Creatures":   "NATURE",
            "Cosmos & Space":       "COSMOS",
            "Cosmos":               "COSMOS",
            "Science":              "SCIENCE",
            "Science & Technology": "SCIENCE",
            "History":              "HISTORY",
            "History & Civilizations": "HISTORY",
        }

        stats = {k: 0 for k in _CAT_DATA}
        self.board_grid = {}
        
        from v2.core.card_database import CardDatabase
        from v2.core.exceptions import AutochessException
        try:
            db = CardDatabase.get()
        except AutochessException:
            self.category_stats = stats
            return
        
        for coord, info in board_cards.items():
            # board_cards values may be dict or MappingProxyType (frozen PublicState)
            name = info.get("name") if isinstance(info, Mapping) else info
            card = db.lookup(name)
            if card:
                raw_cat = card.category
                cat = _CAT_MAPPING.get(raw_cat, raw_cat.upper().split(" & ")[0])
                stats[cat] = stats.get(cat, 0) + 1
                self.board_grid[coord] = _CAT_DATA.get(cat, {}).get("color", (255, 255, 255))
        
        self.category_stats = stats

    def render(self, screen):
        self.surface.fill((0, 0, 0, 0))
        
        # ── 1. Grid Section Panel (SynergyHud stili) ───────────────────────────
        self.surface.blit(self._grid_panel, self.grid_panel_rect.topleft)
        
        # Header (Grid panel içinde - küçültülmüş)
        header_rect = pygame.Rect(self.grid_panel_rect.x, self.grid_panel_rect.y + 2, 
                                  self.grid_panel_rect.w, 14)
        font_cache.render_text(self.surface, "TACTICAL OVERVIEW", font_cache.bold(9), 
                               (160, 140, 200), header_rect, align="center")  # Mor-gri ton
        
        # ── 2. Hex Grid (Grid panel içinde, clipping ile) ──────────────────────
        # Grid merkezi: Panel içinde ortalanmış, header altında
        header_h = 18  # 28'den 18'e düşürüldü
        available_h = self.grid_panel_rect.h - header_h
        
        cx = self.grid_panel_rect.x + self.grid_panel_rect.w // 2
        cy = self.grid_panel_rect.y + header_h + (available_h // 2)
        
        # Hex boyutu eski haline (24px)
        hex_size = 24
        
        # Clipping: Sadece grid panel içinde çiz (daha az padding)
        old_clip = self.surface.get_clip()
        grid_clip = pygame.Rect(
            self.grid_panel_rect.x + 1,
            self.grid_panel_rect.y + header_h,
            self.grid_panel_rect.w - 2,
            available_h - 2
        )
        self.surface.set_clip(grid_clip)
        
        self._draw_hex_grid(self.surface, cx, cy, hex_size)
        
        # Clipping'i geri yükle
        self.surface.set_clip(old_clip)
        
        # ── 3. Category Section Panel (SynergyHud stili) ───────────────────────
        self.surface.blit(self._cat_panel, self.cat_panel_rect.topleft)
        
        # Category Dashboard (Panel içinde)
        self._draw_category_overlay(self.surface)

        # ── 4. Final Blit ──────────────────────────────────────────────────────
        screen.blit(self.surface, (self.anchor_x, self.anchor_y))

    def _draw_hex_grid(self, surface, cx, cy, size):
        for q, r in self._hex_config.valid_coords:
            dx = size * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
            dy = size * (3/2 * r)
            hx, hy = cx + dx, cy + dy
            
            color = self.board_grid.get((q, r))
            if color:
                # Dolu hex - Doygun ve tok boyama
                # 1. Glow layer (dış parıltı)
                self._draw_mini_hex(surface, hx, hy, size, (*color, 80))
                
                # 2. Ana dolgu (ÇOK DOYGUN, TAM OPAK - alpha yok!)
                # Saturation boost'u daha güçlü yap (1.2 -> 1.4)
                saturated_color = self._boost_saturation(color, 1.4)
                self._draw_mini_hex(surface, hx, hy, size - 1, saturated_color)  # Alpha YOK!
                
                # 3. İç highlight (parlaklık) - daha belirgin
                highlight_color = tuple(min(255, int(c * 1.4)) for c in saturated_color)
                self._draw_mini_hex(surface, hx, hy, size - 3, (*highlight_color, 100))
                
                # 4. Beyaz kenarlık (net sınır) - daha belirgin
                self._draw_mini_hex(surface, hx, hy, size - 1, (255, 255, 255, 200), width=1)
            else:
                # Boş hex - Mor-karbon tonları
                self._draw_mini_hex(surface, hx, hy, size - 2, (35, 30, 42, 120))  # Mor-karbon fill
                self._draw_mini_hex(surface, hx, hy, size - 2, (60, 50, 75, 100), width=1)  # Mor-karbon border

    def _boost_saturation(self, color: tuple, factor: float) -> tuple:
        """Rengin doygunluğunu artırır (RGB -> daha canlı RGB)."""
        r, g, b = color
        # Ortalama parlaklık
        avg = (r + g + b) / 3
        # Her kanalı ortalamadan uzaklaştır (doygunluk artışı)
        r = int(avg + (r - avg) * factor)
        g = int(avg + (g - avg) * factor)
        b = int(avg + (b - avg) * factor)
        # 0-255 aralığında tut
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def _draw_mini_hex(self, surface, x, y, size, color, width=0):
        pts = []
        for i in range(6):
            ang = math.radians(i * 60 - 30)
            pts.append((x + size * math.cos(ang), y + size * math.sin(ang)))
        pygame.draw.polygon(surface, color, pts, width)

    def _draw_category_overlay(self, surface):
        """Category dashboard with SynergyHud-style layout."""
        # Category panel içinde başlangıç (header için yer bırak - küçültülmüş)
        header_h = 16  # 20'den 16'ya düşürüldü
        section_start_y = self.cat_panel_rect.y + header_h
        
        # Header (küçültülmüş)
        header_rect = pygame.Rect(self.cat_panel_rect.x, self.cat_panel_rect.y + 2, 
                                  self.cat_panel_rect.w, 12)
        font_cache.render_text(surface, "CATEGORIES", font_cache.bold(9), 
                               (160, 140, 200), header_rect, align="center")  # Mor-gri ton
        
        # 6 kategori için 3x2 grid (3 satır, 2 sütun) - daha dar boşluklar
        padding = 6  # 8'den 6'ya düşürüldü
        available_w = self.cat_panel_rect.w - padding * 3
        available_h = self.cat_panel_rect.h - header_h - padding * 4
        
        col_w = available_w // 2  # 2 sütun
        row_h = available_h // 3  # 3 satır
        
        idx = 0
        for cat_key, data in _CAT_DATA.items():
            count = self.category_stats.get(cat_key, 0)
            color = data["color"]
            abbr  = data["abbr"]
            icon_key = data["icon"]
            
            # Grid pozisyonu (3 satır x 2 sütun)
            row = idx // 2
            col = idx % 2
            px = self.cat_panel_rect.x + padding + col * (col_w + padding)
            py = section_start_y + row * (row_h + padding)
            
            # ─ Bant Arkaplanı (Karbon-mor glass) - Daha belirgin ─
            b_alpha = 140 if count > 0 else 70  # Opaklık artırıldı (90->140, 40->70)
            bg_rect = pygame.Rect(px, py, col_w, row_h)
            # Arka plan rengi daha belirgin - kategori rengine hafif ton
            if count > 0:
                bg_color = tuple(int(c * 0.15 + 18 * 0.85) for c in color) + (b_alpha,)
            else:
                bg_color = (18, 16, 22, b_alpha)
            pygame.draw.rect(surface, bg_color, bg_rect, border_radius=5)
            
            # Aktif kenarlık - daha kalın ve parlak
            if count > 0:
                pygame.draw.rect(surface, (*color, 180), bg_rect, width=2, border_radius=5)  # width 1->2, alpha 120->180
            
            # ─ İçerik Yerleşimi (Dikey ortalanmış) ─
            icon_size = 28  # İkon büyütüldü (24->28)
            icon_padding = 8
            text_gap = 6  # Boşluk azaltıldı (8->6)
            
            # Dikey merkez
            vertical_center = py + (row_h // 2)
            
            # ─ İkon (Sol taraf, dikey ortalanmış) ─
            t_alpha = 255 if count > 0 else 110
            icon_x = px + icon_padding
            icon_y = vertical_center - (icon_size // 2)
            
            # PNG ikon çiz (kategori için)
            # Kategori adını tam formatta al
            full_cat_name = {
                "MYTHOLOGY": "Mythology & Gods",
                "ART": "Art & Culture",
                "NATURE": "Nature & Creatures",
                "COSMOS": "Cosmos",
                "SCIENCE": "Science",
                "HISTORY": "History & Civilizations",
            }.get(cat_key, cat_key)
            
            icon_surf = icon_loader.get_icon(full_cat_name, icon_size, is_category=True)
            if icon_surf:
                icon_surf = icon_surf.copy()
                icon_surf.set_alpha(t_alpha)
                surface.blit(icon_surf, (icon_x, icon_y))
            else:
                # Fallback: Font Awesome ikonu
                font_cache.render_icon(surface, icon_key, icon_size, (*color, t_alpha), (icon_x, icon_y))
            
            # ─ Kısaltma (İkonun yanında) ─
            abbr_font = font_cache.minimap_cat(16)  # Font büyütüldü (13->16)
            abbr_x = icon_x + icon_size + text_gap
            abbr_w = col_w - (abbr_x - px) - 30  # Sayı için yer bırak
            
            abbr_rect = pygame.Rect(abbr_x, py, abbr_w, row_h)
            # Gölge ekle - daha okunabilir
            shadow_color = (0, 0, 0, int(t_alpha * 0.6))
            shadow_rect = pygame.Rect(abbr_x + 1, py + 1, abbr_w, row_h)
            font_cache.render_text(surface, abbr, abbr_font, shadow_color, 
                                   shadow_rect, align="left", v_align="center")
            font_cache.render_text(surface, abbr, abbr_font, (*color, t_alpha), 
                                   abbr_rect, align="left", v_align="center")
            
            # ─ Sayı (Sağ taraf, dikey ortalanmış) ─
            if count > 0:
                count_rect = pygame.Rect(px, py, col_w - 8, row_h)
                # Gölge ekle
                shadow_rect = pygame.Rect(px + 1, py + 1, col_w - 8, row_h)
                font_cache.render_text(surface, str(count), font_cache.bold(22), (0, 0, 0, 150), 
                                       shadow_rect, align="right", v_align="center")
                font_cache.render_text(surface, str(count), font_cache.bold(22), color, 
                                       count_rect, align="right", v_align="center")  # Font büyütüldü (18->22)
            
            idx += 1
