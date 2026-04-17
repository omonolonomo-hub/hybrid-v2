import pygame
import math
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache

# ── Kategori Renkleri (Minimap ve Sidebar ile senkron) ──────────────────────
_CAT_COLORS = {
    "MYTHOLOGY": (248, 222, 34),
    "ART":       (240, 60, 110),
    "NATURE":    (60, 255, 80),
    "COSMOS":    (140, 80, 255),
    "SCIENCE":   (3, 190, 240),
    "HISTORY":   (255, 120, 40),
}

class LobbyPanel:
    def __init__(self, player_count: int = 8):
        self.rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)

        # Oyuncu satırları — dikey ortala
        self.player_count = player_count
        row_spacing = 8
        self.total_h  = player_count * (Layout.LOBBY_ROW_H + row_spacing) - row_spacing
        self.start_y  = (Screen.H - self.total_h) // 2
        self.margin_x = self.rect.x + 10
        self.row_w    = self.rect.w - 20

        self.player_rects: list[pygame.Rect] = []
        for i in range(player_count):
            ry = self.start_y + i * (Layout.LOBBY_ROW_H + row_spacing)
            self.player_rects.append(pygame.Rect(self.margin_x, ry, self.row_w, Layout.LOBBY_ROW_H))

        # Hover state
        self.hover_index = None

        # Arkaplan Önbelleği (DCI Style)
        from v2.ui.ui_utils import UIUtils
        c_brd = (42, 58, 92, 180)
        self.bg_mine = UIUtils.create_gradient_panel(self.row_w, Layout.LOBBY_ROW_H, (30, 45, 65, 255), (10, 15, 25, 255), border_radius=8, border_color=c_brd)
        self.bg_norm = UIUtils.create_gradient_panel(self.row_w, Layout.LOBBY_ROW_H, (35, 38, 48, 255), (12, 14, 20, 255), border_radius=8, border_color=c_brd)
        # Top 3 Gradients (Special Colors)
        self.bg_top1 = UIUtils.create_gradient_panel(self.row_w, Layout.LOBBY_ROW_H, (65, 55, 20, 255), (25, 15,  5, 255), border_radius=8, border_color=(200, 180, 50, 180))
        self.bg_top2 = UIUtils.create_gradient_panel(self.row_w, Layout.LOBBY_ROW_H, (50, 50, 60, 255), (15, 15, 20, 255), border_radius=8, border_color=(150, 160, 180, 180))
        self.bg_top3 = UIUtils.create_gradient_panel(self.row_w, Layout.LOBBY_ROW_H, (55, 30, 20, 255), (20, 10,  5, 255), border_radius=8, border_color=(180, 100, 50, 180))

    def update(self, mouse_pos: tuple[int, int]):
        """Hover tespit motoru."""
        self.hover_index = None
        for i, r in enumerate(self.player_rects):
            if r.collidepoint(mouse_pos):
                self.hover_index = i
                break

    def render(self, surface: pygame.Surface, players: list = None) -> None:
        if players is None: players = []
            
        time_ms = pygame.time.get_ticks()

        for i, p_rect in enumerate(self.player_rects):
            player  = players[i] if i < len(players) else {}
            is_self = player.get("index") == 0 or player.get("name") == "YOU"
            hp      = player.get("hp", 150)
            max_hp  = player.get("max_hp", 150)
            rank    = player.get("rank", i + 1)
            ratio   = max(0.0, min(1.0, hp / max_hp))
            
            # ── 1. Scale & Hover Logic ─────────────────────────────────
            is_hovered = (i == self.hover_index)
            scale = 1.03 if is_hovered else 1.0
            
            # Inflate rect for rendering
            draw_rect = p_rect.inflate(int(p_rect.w * (scale - 1)), int(p_rect.h * (scale - 1)))
            
            # ── 2. Threat Color (Danger Lerp) ─────────────────────────
            # HP düştükçe bordür rengini maviden kırmızıya kaydır
            danger = 1.0 - ratio
            border_col = (
                int(50 + 200 * danger),
                int(160 - 110 * danger),
                int(210 - 160 * danger)
            )
            
            # ── 3. Background Drawing ──────────────────────────────────
            if is_self:
                surf = self.bg_mine
            elif rank == 1:
                surf = self.bg_top1
            elif rank == 2:
                surf = self.bg_top2
            elif rank == 3:
                surf = self.bg_top3
            else:
                surf = self.bg_norm
            
            # Eğer hover ediliyorsa veya scale edilmişse surf'ü scale etmemiz gerekebilir (smoothscale)
            # Ama performans için p_rect boyunda blit edip draw_rect ile border çiziyoruz.
            # Gerçek bir scale hissi için surf'ü de inflate edebiliriz:
            if scale > 1.0:
                s_surf = pygame.transform.smoothscale(surf, draw_rect.size)
            else:
                s_surf = surf
                
            surface.blit(s_surf, draw_rect.topleft)

            # Hover Highlight Glow
            if is_hovered:
                glow_surf = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                glow_surf.fill((0, 200, 255, 30))
                surface.blit(glow_surf, draw_rect.topleft)

            # Border
            pygame.draw.rect(surface, border_col, draw_rect, width=1, border_radius=8)
            if is_self:
                pygame.draw.rect(surface, (0, 255, 255), draw_rect, width=2, border_radius=8)

            # ── 4. HP Bar & Pulse ──────────────────────────────────────
            bar_x = draw_rect.x + 40
            bar_y = draw_rect.y + 26
            bar_w = draw_rect.w - 50
            bar_h = 7
            
            # HP Pulse (Low HP only)
            if ratio < 0.3 and hp > 0:
                pulse = int(40 + 40 * math.sin(time_ms * 0.006))
                glow_col = (255, 50, 50, pulse)
                pygame.draw.rect(surface, glow_col, (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=4)
            
            self._draw_segmented_health_bar(surface, bar_x, bar_y, bar_w, bar_h, hp, max_hp)

            # ── 5. Category Strips (Global Hint) ──────────────────────
            # Çakışmayı önlemek için HP barının hemen altına (y+3) orantılı yerleştir
            cat_stats = player.get("categories", {})
            if cat_stats:
                total_units = sum(cat_stats.values())
                if total_units > 0:
                    gap = 2
                    usable_w = bar_w - (len(cat_stats) - 1) * gap
                    curr_x = bar_x
                    cy = bar_y + bar_h + 3
                    
                    for cat, count in cat_stats.items():
                        color = _CAT_COLORS.get(cat, (150, 150, 150))
                        # Orantılı genişlik
                        seg_w = (count / total_units) * usable_w
                        if seg_w > 0:
                            pygame.draw.rect(surface, color, (int(curr_x), cy, int(seg_w), 3), border_radius=1)
                            curr_x += seg_w + gap

            # ── 6. Text & Badge ────────────────────────────────────────
            # Rank
            rank_col = (255, 255, 255)
            if rank == 1: rank_col = (255, 215, 0)
            font_cache.render_text(surface, f"#{rank}", font_cache.bold(10), rank_col, 
                                   pygame.Rect(draw_rect.x + 8, draw_rect.y + 12, 24, 20), align="center")
            
            # Name
            name_color = (0, 242, 255) if is_self else (220, 230, 255)
            font_cache.render_text(surface, player.get("name", "---"), font_cache.bold(11), 
                                   name_color, pygame.Rect(draw_rect.x + 40, draw_rect.y + 6, 120, 18))
            
            # HP Num
            font_cache.render_text(surface, f"{hp}", font_cache.mono(9), (255, 255, 255), 
                                   pygame.Rect(draw_rect.right - 40, draw_rect.y + 6, 30, 16), align="right")

            # ── 7. Dead State ─────────────────────────────────────────
            if hp <= 0:
                dead_overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                dead_overlay.fill((30, 5, 5, 210))
                surface.blit(dead_overlay, draw_rect.topleft)
                font_cache.render_text(surface, "ELIMINATED", font_cache.bold(12), (255, 60, 60), draw_rect, align="center", v_align="center")

    def _draw_segmented_health_bar(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, hp: int, max_hp: int) -> None:
        pygame.draw.rect(surface, (15, 20, 30), (x, y, w, h), border_radius=2)
        if hp <= 0: return
        ratio = max(0.0, min(1.0, hp / max_hp))
        fill_color = (0, 255, 120) if ratio > 0.4 else (255, 60, 60)
        
        blp = 5 
        total_blocks = max_hp // blp
        padding = 1
        block_w = (w - (total_blocks - 1) * padding) / total_blocks
        blocks_to_draw = int(total_blocks * ratio)
        if blocks_to_draw == 0 and hp > 0: blocks_to_draw = 1
            
        for i in range(blocks_to_draw):
            bx = x + i * (block_w + padding)
            pygame.draw.rect(surface, fill_color, (int(bx), y, int(block_w), h), border_radius=1)

    def handle_event(self, event: pygame.event.Event, players: list = None) -> int | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if players is None: return None
            for i, p_rect in enumerate(self.player_rects):
                if p_rect.collidepoint(event.pos):
                    if i < len(players):
                        return players[i].get("index", i)
        return None
