import pygame
import pygame.gfxdraw
import math
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache
from dataclasses import dataclass, field
from typing import Dict

# ── Tasarım Sabitleri (Konfor Odaklı) ──────────────────────────────────────
ROW_PADDING = 12      # Kutunun iç kenar boşluğu
CORNER_CUT = 12       # Modern DCI kesiği
ACCENT_WIDTH = 6      # Sol vurgu çizgisi kalınlığı

_CAT_COLORS = {
    "MYTHOLOGY": (248, 222, 34),
    "ART":       (240, 60, 110),
    "NATURE":    (60, 255, 80),
    "COSMOS":    (140, 80, 255),
    "SCIENCE":   (3, 190, 240),
    "HISTORY":   (255, 120, 40),
}

@dataclass(frozen=True)
class LobbyPlayerDTO:
    index: int = -1
    name: str = "---"
    hp: int = 150
    max_hp: int = 150
    rank: int = 99
    level: int = 1
    streak: int = 0
    ai_strategy: str = ""
    categories: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'LobbyPlayerDTO':
        return cls(
            index=data.get("index", -1),
            name=data.get("name", "---"),
            hp=data.get("hp", 150),
            max_hp=data.get("max_hp", 150),
            rank=data.get("rank", 99),
            level=data.get("level", 1),
            streak=data.get("streak", 0),
            ai_strategy=data.get("ai_strategy", ""),
            categories=data.get("categories", {})
        )

class LobbyPanelRow:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def _draw_modern_card(self, surface: pygame.Surface, rect: pygame.Rect, color: tuple, border: tuple, is_hover: bool):
        """SSAA Canvas üzerinde pürüzsüz kart çizimi"""
        points = [
            (rect.x + CORNER_CUT, rect.y),
            (rect.right, rect.y), # Sağ üst düz (Modern görünüm)
            (rect.right, rect.bottom - CORNER_CUT),
            (rect.right - CORNER_CUT, rect.bottom),
            (rect.left, rect.bottom), # Sol alt düz
            (rect.left, rect.y + CORNER_CUT),
        ]
        
        # 1. Gölge / Glow
        if is_hover:
            glow_rect = rect.inflate(8, 8)
            pygame.draw.rect(surface, (*border[:3], 60), glow_rect, border_radius=8)

        # 2. Ana Dolgu ve AA Kenar
        if color:
            pygame.gfxdraw.filled_polygon(surface, points, color)
        if border:
            pygame.gfxdraw.aapolygon(surface, points, border)
        
        # 3. Üst Işıklandırma (Highlight)
        pygame.draw.line(surface, (255, 255, 255, 40), (rect.x + CORNER_CUT, rect.y + 1), (rect.right - 1, rect.y + 1), 2)
        
        # 4. Sol Vurgu Çizgisi
        pygame.draw.line(surface, border, (rect.x + 4, rect.y + CORNER_CUT + 4), (rect.x + 4, rect.bottom - 4), ACCENT_WIDTH)

    def render(self, surface: pygame.Surface, player: LobbyPlayerDTO, is_hovered: bool, time_ms: int):
        scale = 2
        canvas = pygame.Surface((self.rect.w * scale, self.rect.h * scale), pygame.SRCALPHA)
        draw_rect = pygame.Rect(0, 0, self.rect.w * scale, self.rect.h * scale)
        
        # Eğer hover varsa kartı hafif sola/sağa kaydırarak reaksiyon ver
        if is_hovered:
            draw_rect.x -= 4 * scale

        # Renk Seçimi
        is_self = player.index == 0 or player.name == "YOU"
        base_bg = (35, 38, 48, 240) if not is_self else (45, 60, 85, 240)
        border_col = (100, 110, 140, 180) if not is_self else (0, 220, 255, 200)
        
        if player.rank == 1:
            base_bg = (55, 45, 25, 240)
            border_col = (255, 215, 0, 200)
        elif player.rank == 2:
            border_col = (192, 192, 192, 200)
        elif player.rank == 3:
            border_col = (205, 127, 50, 200)
            
        if is_hovered:
            base_bg = tuple(min(255, c + 25) for c in base_bg[:3]) + (255,)
            border_col = tuple(min(255, c + 50) for c in border_col[:3]) + (255,)

        # 1. Ana Kart Gövdesi
        self._draw_modern_card(canvas, draw_rect, base_bg, border_col, is_hovered)

        # 2. Bölgeleme (Layout Zones)
        # --- Z1: ID ZONE ---
        hex_radius = int(18 * scale)
        hex_cx = ROW_PADDING * scale * 2 + hex_radius
        hex_cy = draw_rect.centery
        
        # Hexagon Badge
        h_pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            h_pts.append((int(hex_cx + hex_radius * math.cos(a)), int(hex_cy + hex_radius * math.sin(a))))
        pygame.gfxdraw.filled_polygon(canvas, h_pts, (20, 20, 25, 255))
        pygame.gfxdraw.aapolygon(canvas, h_pts, border_col)
        
        rank_font = font_cache.bold(int(26 * scale * 0.5))
        r_surf = rank_font.render(str(player.rank), True, (255, 255, 255))
        canvas.blit(r_surf, r_surf.get_rect(center=(hex_cx, hex_cy)))

        # --- Z2: INFO ZONE ---
        info_x = hex_cx + hex_radius + ROW_PADDING * scale * 1.5
        
        # İsim ve Seviye
        name_font = font_cache.bold(int(28 * scale * 0.5))
        n_color = (255, 255, 255) if is_self else (220, 220, 230)
        n_surf = name_font.render(player.name.upper(), True, n_color)
        canvas.blit(n_surf, (info_x, draw_rect.y + ROW_PADDING * scale * 0.8))
        
        lvl_font = font_cache.mono(int(18 * scale * 0.5))
        l_surf = lvl_font.render(f"LVL {player.level}", True, (160, 170, 190))
        canvas.blit(l_surf, (info_x + n_surf.get_width() + 15 * scale, draw_rect.y + ROW_PADDING * scale * 1.0))

        # Sağlıklı HP Bar (Geniş ve Okunaklı)
        bar_w = int(draw_rect.w * 0.60)
        bar_h = int(14 * scale)
        bar_y = draw_rect.bottom - int(ROW_PADDING * scale * 1.8)
        
        hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
        pygame.draw.rect(canvas, (15, 15, 20, 255), (info_x, bar_y, bar_w, bar_h), border_radius=4*scale)
        if hp_ratio > 0:
            hp_color = (60, 255, 120) if hp_ratio > 0.4 else (255, 60, 60)
            pygame.draw.rect(canvas, hp_color, (info_x+2*scale, bar_y+2*scale, int((bar_w-4*scale)*hp_ratio), bar_h-4*scale), border_radius=2*scale)
            
            # Kalkan/Katman efekti
            inner_rect = pygame.Rect(info_x+2*scale, bar_y + bar_h//2, int((bar_w-4*scale)*hp_ratio), bar_h//2 - 2*scale)
            pygame.draw.rect(canvas, (255, 255, 255, 40), inner_rect, border_radius=2*scale)

        # Kategori Şeridi (Board Unit Types)
        cat_y = bar_y + bar_h + 3 * scale
        if player.categories:
            total_units = sum(player.categories.values())
            if total_units > 0:
                curr_x = info_x
                for cat, count in player.categories.items():
                    c_col = _CAT_COLORS.get(cat, (150, 150, 150))
                    seg_w = max(4 * scale, int((count / total_units) * bar_w))
                    pygame.draw.line(canvas, c_col, (curr_x, cat_y), (curr_x + seg_w - 2 * scale, cat_y), 4 * scale)
                    curr_x += seg_w

        # HP Text
        hp_font = font_cache.mono(int(16 * scale * 0.5))
        hp_surf = hp_font.render(f"{player.hp}/{player.max_hp}", True, (255, 255, 255))
        canvas.blit(hp_surf, (info_x + bar_w + 10 * scale, bar_y - 2 * scale))

        # --- Z3: STATUS ZONE (Sağ Taraf) ---
        win_streak = 10 - player.rank # Pseudo streak
        if win_streak > 3:
            s_font = font_cache.bold(int(22 * scale * 0.5))
            i_font = font_cache.icons(int(18 * scale * 0.5))
            
            st_val = s_font.render(str(win_streak), True, (255, 150, 50))
            fire_ico = i_font.render(font_cache.ICONS["FIRE"], True, (255, 100, 50))
            
            grp_w = st_val.get_width() + fire_ico.get_width() + 6 * scale
            grp_x = draw_rect.right - grp_w - ROW_PADDING * scale * 1.5
            grp_y = draw_rect.y + ROW_PADDING * scale * 1.5
            
            canvas.blit(st_val, (grp_x, grp_y))
            canvas.blit(fire_ico, (grp_x + st_val.get_width() + 6 * scale, grp_y + 2 * scale))

        # Dead State Overlay
        if player.hp <= 0:
            dead_overlay = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            dead_overlay.fill((10, 5, 5, 200))
            for dx in range(-draw_rect.h, draw_rect.w, 30 * scale):
                pygame.draw.line(dead_overlay, (255, 0, 0, 15), (dx, 0), (dx + draw_rect.h, draw_rect.h), 4 * scale)
            canvas.blit(dead_overlay, draw_rect.topleft)
            
            elim_font = font_cache.bold(int(36 * scale * 0.5))
            e_surf = elim_font.render("ELIMINATED", True, (255, 50, 50))
            canvas.blit(e_surf, (draw_rect.right - e_surf.get_width() - ROW_PADDING * scale * 2, draw_rect.centery - e_surf.get_height()//2))

        # Final Render
        final_ui = pygame.transform.smoothscale(canvas, self.rect.size)
        surface.blit(final_ui, self.rect.topleft)


class LobbyPanel:
    def __init__(self, player_count: int = 8):
        self.rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)
        
        # Konfor Ayarı: Ekran yüksekliğine göre her oyuncuya "nefes alacak" alan bırak
        margin = 15
        available_w = self.rect.w - (margin * 2)
        
        # Sabit bir oran yerine, optimum yükseklik (Örn: 80-100px arası idealdir)
        row_h = min(90, (Screen.H - 100) // player_count) 
        row_spacing = 12
        
        self.rows = []
        start_y = (Screen.H - (player_count * (row_h + row_spacing))) // 2
        
        for i in range(player_count):
            ry = start_y + i * (row_h + row_spacing)
            self.rows.append(LobbyPanelRow(pygame.Rect(self.rect.x + margin, ry, available_w, row_h)))

        self.hover_index = None

    def update(self, mouse_pos: tuple[int, int]):
        self.hover_index = None
        for i, row in enumerate(self.rows):
            if row.rect.collidepoint(mouse_pos):
                self.hover_index = i
                break

    def render(self, surface: pygame.Surface, players: list = None):
        # Arka planı hafiflet (İçerik parlasın)
        overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        overlay.fill((20, 20, 25, 150))
        surface.blit(overlay, self.rect)
        
        clip_rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)
        original_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        time_ms = pygame.time.get_ticks()
        players = players or []

        for i, row in enumerate(self.rows):
            data = players[i] if players and i < len(players) else {}
            row.render(surface, LobbyPlayerDTO.from_dict(data), i == self.hover_index, time_ms)

        surface.set_clip(original_clip)

    def handle_event(self, event: pygame.event.Event, players: list = None) -> int | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if players is None: return None
            for i, row in enumerate(self.rows):
                if row.rect.collidepoint(event.pos) and i < len(players):
                    return players[i].get("index", i)
        return None
