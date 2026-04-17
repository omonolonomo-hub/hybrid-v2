import pygame
import math
from v2.constants import Screen, Colors, Layout
from v2.ui import font_cache
from v2.core.game_state import GameState

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
    def __init__(self, screen_w=1920, screen_h=1080):
        # 🎯 Size & Scale - SynergyHud'un altındaki kalan alanı tam kullan
        # SynergyHud: y=150, h=470 (groups 204 + feed 240 + padding)
        # Minimap başlangıç: 150 + 470 = 620
        # Kalan alan: 1080 - 620 = 460px (80px daha fazla alan!)
        self.base_w = Layout.SIDEBAR_LEFT_W  # 340px (sidebar genişliği)
        self.base_h = Screen.H - 620         # 460px (kalan dikey alan)
        
        # 📍 Anchor: SynergyHud'un hemen altı (dikişsiz)
        self.anchor_x = 0 
        self.anchor_y = 620  # 700 -> 620 (80px yukarı)
        
        self.rect = pygame.Rect(self.anchor_x, self.anchor_y, self.base_w, self.base_h)

        # Draw Surface
        self.surface = pygame.Surface((self.base_w, self.base_h), pygame.SRCALPHA)
        self.time = 0.0
        self.category_stats = {}
        self.board_grid = {}
        
        # 🎨 Layout Proportions (Optimized)
        # Hex Grid: Üst 65% (~300px) - Daha büyük alan, hex grid rahat
        # Category Dashboard: Alt 35% (~160px) - Kompakt ama okunabilir
        self.grid_section_h = int(self.base_h * 0.65)
        self.category_section_h = self.base_h - self.grid_section_h

    def update(self, dt_ms, mouse_pos):
        self.time += dt_ms / 1000.0
        self._sync_data()

    def _sync_data(self):
        gs = GameState.get()
        board_data = gs.get_board_cards(0)
        
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
        db = CardDatabase.get()
        
        for coord, info in board_data.items():
            name = info.get("name") if isinstance(info, dict) else info
            card = db.lookup(name)
            if card:
                raw_cat = card.category
                cat = _CAT_MAPPING.get(raw_cat, raw_cat.upper().split(" & ")[0])
                stats[cat] = stats.get(cat, 0) + 1
                self.board_grid[coord] = _CAT_DATA.get(cat, {}).get("color", (255, 255, 255))
        
        self.category_stats = stats

    def render(self, screen):
        self.surface.fill((0, 0, 0, 0))
        
        # 1. Unified Background (SynergyHud ile dikişsiz dikey blok)
        pygame.draw.rect(self.surface, (10, 12, 20, 245), (0, 0, self.base_w, self.base_h))
        # Sol ayırıcı çizgi
        pygame.draw.line(self.surface, (42, 58, 92, 100), (0, 0), (0, self.base_h), 1)
        
        # 2. Header (Tactical Minimap Label)
        header_rect = pygame.Rect(0, 4, self.base_w, 18)
        font_cache.render_text(self.surface, "TACTICAL OVERVIEW", font_cache.bold(10), 
                               (100, 140, 220), header_rect, align="center")
        pygame.draw.line(self.surface, (42, 58, 92, 120), (10, 24), (self.base_w - 10, 24), 1)
        
        # 3. Layer A: Tactical Hex Grid (Optimized Center & Size)
        # Grid merkezi: Genişliğin ortası, grid section'ın ortası
        cx = self.base_w // 2
        cy = 28 + (self.grid_section_h - 28) // 2  # Header altından başla, section ortası
        hex_size = 24  # Daha büyük hexler (22 -> 24, daha fazla alan var)
        self._draw_hex_grid(self.surface, cx, cy, hex_size)
        
        # 4. Separator Line (Grid ve Category arası)
        sep_y = self.grid_section_h
        pygame.draw.line(self.surface, (42, 58, 92, 140), (8, sep_y), (self.base_w - 8, sep_y), 1)
        
        # 5. Layer B: Category Dashboard (Optimized Compact Layout)
        self._draw_category_overlay(self.surface)

        # 6. Final Blit
        screen.blit(self.surface, (self.anchor_x, self.anchor_y))

    def _draw_hex_grid(self, surface, cx, cy, size):
        from v2.ui.hex_grid import VALID_HEX_COORDS
        
        for q, r in VALID_HEX_COORDS:
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
                # Boş hex - Soluk ama görünür
                self._draw_mini_hex(surface, hx, hy, size - 2, (30, 38, 55, 120))
                self._draw_mini_hex(surface, hx, hy, size - 2, (50, 65, 95, 100), width=1)

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
        """Optimized compact category dashboard with perfect alignment."""
        # Category section başlangıcı (separator'ın hemen altı)
        section_start_y = self.grid_section_h + 10
        
        # 6 kategori için 3x2 grid (3 satır, 2 sütun)
        padding = 10
        col_w = (self.base_w - padding * 3) // 2  # 2 sütun
        row_h = (self.category_section_h - padding * 4 - 10) // 3  # 3 satır
        
        idx = 0
        for cat, data in _CAT_DATA.items():
            count = self.category_stats.get(cat, 0)
            color = data["color"]
            abbr  = data["abbr"]
            icon_key = data["icon"]
            
            # Grid pozisyonu (3 satır x 2 sütun)
            row = idx // 2
            col = idx % 2
            px = padding + col * (col_w + padding)
            py = section_start_y + row * (row_h + padding)
            
            # ─ Bant Arkaplanı (Glass) ─
            b_alpha = 90 if count > 0 else 40
            bg_rect = pygame.Rect(px, py, col_w, row_h)
            pygame.draw.rect(surface, (15, 22, 38, b_alpha), bg_rect, border_radius=5)
            
            # Aktif kenarlık
            if count > 0:
                pygame.draw.rect(surface, (*color, 120), bg_rect, width=1, border_radius=5)
            
            # ─ Matematiksel Hizalama Hesaplamaları ─
            # İkon boyutu ve padding
            icon_size = 16
            icon_padding_left = 10
            text_padding_left = 8  # İkon ile metin arası
            
            # Dikey merkez (row_h'nin tam ortası)
            vertical_center = py + (row_h // 2)
            
            # ─ İkon (Sol taraf, dikey ortalanmış) ─
            t_alpha = 255 if count > 0 else 110
            icon_x = px + icon_padding_left
            icon_y = vertical_center - (icon_size // 2)  # İkonun merkezini row merkezine hizala
            font_cache.render_icon(surface, icon_key, icon_size, (*color, t_alpha), (icon_x, icon_y))
            
            # ─ Kısaltma (İkonun yanı, dikey ortalanmış) ─
            # Font yüksekliğini hesapla (yaklaşık 12px bold font için)
            abbr_font = font_cache.bold(12)  # 11 -> 12 (daha kalın görünüm)
            abbr_x = icon_x + icon_size + text_padding_left
            
            # Metni dikey ortala (font yüksekliğine göre)
            abbr_rect = pygame.Rect(abbr_x, py, col_w - abbr_x + px - 70, row_h)
            font_cache.render_text(surface, abbr, abbr_font, (*color, t_alpha), 
                                   abbr_rect, align="left", v_align="center")
            
            # ─ Sayı (Sağ taraf, dikey ortalanmış, kalın) ─
            if count > 0:
                count_rect = pygame.Rect(px, py, col_w - 10, row_h)
                # Sayı fontunu daha kalın yap
                font_cache.render_text(surface, str(count), font_cache.bold(20), color, 
                                       count_rect, align="right", v_align="center")
            
            idx += 1
