import pygame
import math
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache

# ── Altın Oran Sabitleri ────────────────────────────────────────────────────
PHI = 1.618  # Altın oran
PHI_INV = 0.618  # 1/φ

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

        # ── Altın Oran ile Oyuncu Satırları ────────────────────────────────────
        self.player_count = player_count
        
        # Altın oran ile satır yüksekliği ve boşluk hesaplama
        # Row height: φ tabanlı oran (70 → ~72 için yuvarlanmış)
        self.row_h = int(Layout.LOBBY_ROW_H * 1.03)  # Hafif artış
        
        # Spacing: row_h / φ² ≈ row_h * 0.382
        row_spacing = int(self.row_h * 0.382)
        
        self.total_h  = player_count * (self.row_h + row_spacing) - row_spacing
        
        # ── DİKEY ÇAKIŞMA ÖNLEME ────────────────────────────────────────────
        # ShopPanel: y=0, h=210 (bottom=210)
        # HandPanel: y=870, h=210 (top=870)
        # Güvenli alan: 210 ile 870 arası (660px)
        
        safe_top = Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 20  # 230px (20px padding)
        safe_bottom = Layout.HAND_PANEL_Y - 20  # 850px (20px padding)
        safe_height = safe_bottom - safe_top  # 620px
        
        # Eğer total_h güvenli alana sığmıyorsa, ortalama
        if self.total_h <= safe_height:
            self.start_y = safe_top + (safe_height - self.total_h) // 2
        else:
            # Çok uzunsa, güvenli alanın başından başla
            self.start_y = safe_top
            # Row spacing'i azalt
            available_h = safe_height
            row_spacing = max(8, (available_h - player_count * self.row_h) // (player_count - 1))
            self.total_h = player_count * (self.row_h + row_spacing) - row_spacing
        
        # Margin: panel genişliğinin φ⁻¹'i (altın oran ile kenar boşluğu)
        # DÜZELTME: Margin'i panel içinde tutmak için daha küçük oran kullan
        margin_offset = int(self.rect.w * 0.05)  # %5 margin (daha güvenli)
        self.margin_x = self.rect.x + margin_offset
        self.row_w    = self.rect.w - 2 * margin_offset  # Panel içinde kal

        self.player_rects: list[pygame.Rect] = []
        for i in range(player_count):
            ry = self.start_y + i * (self.row_h + row_spacing)
            # Rect'leri panel sınırları içinde tut
            self.player_rects.append(pygame.Rect(self.margin_x, ry, self.row_w, self.row_h))

        # Hover state
        self.hover_index = None

        # Arkaplan Önbelleği (DCI Style) — altın oran ile border radius
        from v2.ui.ui_utils import UIUtils
        border_radius = int(self.row_h * 0.12)  # ~8-9px, orantılı
        c_brd = (42, 58, 92, 180)
        
        self.bg_mine = UIUtils.create_gradient_panel(self.row_w, self.row_h, (30, 45, 65, 255), (10, 15, 25, 255), border_radius=border_radius, border_color=c_brd)
        self.bg_norm = UIUtils.create_gradient_panel(self.row_w, self.row_h, (35, 38, 48, 255), (12, 14, 20, 255), border_radius=border_radius, border_color=c_brd)
        # Top 3 Gradients (Special Colors)
        self.bg_top1 = UIUtils.create_gradient_panel(self.row_w, self.row_h, (65, 55, 20, 255), (25, 15,  5, 255), border_radius=border_radius, border_color=(200, 180, 50, 180))
        self.bg_top2 = UIUtils.create_gradient_panel(self.row_w, self.row_h, (50, 50, 60, 255), (15, 15, 20, 255), border_radius=border_radius, border_color=(150, 160, 180, 180))
        self.bg_top3 = UIUtils.create_gradient_panel(self.row_w, self.row_h, (55, 30, 20, 255), (20, 10,  5, 255), border_radius=border_radius, border_color=(180, 100, 50, 180))
        
        self.border_radius = border_radius

    def update(self, mouse_pos: tuple[int, int]):
        """Hover tespit motoru."""
        self.hover_index = None
        for i, r in enumerate(self.player_rects):
            if r.collidepoint(mouse_pos):
                self.hover_index = i
                break

    def render(self, surface: pygame.Surface, players: list = None) -> None:
        if players is None: players = []
        
        # Clipping: Sadece sağ sidebar alanına çiz (taşmayı önle)
        clip_rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)
        original_clip = surface.get_clip()
        surface.set_clip(clip_rect)
            
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
            scale = 1.04 if is_hovered else 1.0
            draw_rect = p_rect.inflate(int(p_rect.w * (scale - 1)), int(p_rect.h * (scale - 1)))
            
            # ── 2. Threat Color ────────────────────────────────────────
            danger = 1.0 - ratio
            border_col = (
                int(50 + 200 * danger),
                int(160 - 110 * danger),
                int(210 - 160 * danger)
            )
            
            # ── 3. Background ──────────────────────────────────────────
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
            
            if scale > 1.0:
                s_surf = pygame.transform.smoothscale(surf, draw_rect.size)
            else:
                s_surf = surf
                
            surface.blit(s_surf, draw_rect.topleft)

            # Hover Glow
            if is_hovered:
                glow_surf = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                glow_surf.fill((0, 200, 255, 35))
                surface.blit(glow_surf, draw_rect.topleft)

            # Border
            pygame.draw.rect(surface, border_col, draw_rect, width=1, border_radius=self.border_radius)
            if is_self:
                pygame.draw.rect(surface, (0, 255, 255), draw_rect, width=2, border_radius=self.border_radius)

            # ── 4. ALTIN ORAN İÇERİK YERLEŞİMİ ─────────────────────────
            # Kutu içini altın oran ile 3 yatay bölgeye ayır:
            # Sol: Rank badge (φ⁻²)
            # Orta: İçerik (φ⁻¹) 
            # Sağ: HP sayı (φ⁻²)
            
            content_padding = int(draw_rect.w * 0.04)  # %4 iç padding
            usable_w = draw_rect.w - 2 * content_padding
            
            # Altın oran bölümleme
            rank_zone_w = int(usable_w * 0.12)  # Rank badge için
            hp_num_zone_w = int(usable_w * 0.15)  # HP sayı için
            content_zone_w = usable_w - rank_zone_w - hp_num_zone_w
            
            rank_x = draw_rect.x + content_padding
            content_x = rank_x + rank_zone_w
            hp_num_x = content_x + content_zone_w
            
            # ── 5. Rank Badge (Sol) ────────────────────────────────────
            rank_col = (255, 255, 255)
            if rank == 1: rank_col = (255, 215, 0)
            elif rank == 2: rank_col = (192, 192, 192)
            elif rank == 3: rank_col = (205, 127, 50)
            
            rank_y = draw_rect.y + int(self.row_h * 0.18)
            font_cache.render_text(surface, f"#{rank}", font_cache.bold(12), rank_col, 
                                   pygame.Rect(rank_x, rank_y, rank_zone_w, 20), 
                                   align="center")
            
            # ── 6. İçerik Bölgesi (Orta) ───────────────────────────────
            # Dikey olarak altın oran ile 3 katmana ayır:
            # Üst: İsim (φ⁻¹)
            # Orta: HP Bar (φ⁻²)
            # Alt: Category strips (φ⁻³)
            
            content_h = self.row_h - 2 * int(self.row_h * 0.08)  # Üst-alt padding
            
            name_h = int(content_h * PHI_INV)  # ~0.618
            bar_h = int(content_h * (1 - PHI_INV) * PHI_INV)  # ~0.236
            cat_h = content_h - name_h - bar_h  # Kalan
            
            name_y = draw_rect.y + int(self.row_h * 0.08)
            bar_y = name_y + name_h
            cat_y = bar_y + bar_h
            
            # İsim
            name_color = (0, 242, 255) if is_self else (220, 230, 255)
            font_cache.render_text(surface, player.get("name", "---"), 
                                   font_cache.bold(13), name_color, 
                                   pygame.Rect(content_x, name_y, content_zone_w, name_h),
                                   v_align="center")
            
            # HP Bar
            bar_w = content_zone_w - 4
            bar_h_px = max(8, int(bar_h * 0.6))  # Bar yüksekliği
            bar_y_centered = bar_y + (bar_h - bar_h_px) // 2
            
            # HP Pulse & Glow
            if ratio < 0.35 and hp > 0:
                pulse_intensity = 0.5 + 0.5 * math.sin(time_ms * 0.008)
                pulse_alpha = int(60 + 80 * pulse_intensity)
                glow_size = int(4 * pulse_intensity)
                glow_col = (255, 50, 50, pulse_alpha)
                glow_rect = (content_x - glow_size, bar_y_centered - glow_size, 
                            bar_w + glow_size * 2, bar_h_px + glow_size * 2)
                pygame.draw.rect(surface, glow_col, glow_rect, border_radius=5)
            
            self._draw_enhanced_health_bar(surface, content_x, bar_y_centered, 
                                          bar_w, bar_h_px, hp, max_hp, ratio, time_ms)
            
            # Category Strips
            cat_stats = player.get("categories", {})
            if cat_stats:
                total_units = sum(cat_stats.values())
                if total_units > 0:
                    gap = 2
                    strip_h = max(3, int(cat_h * 0.5))
                    strip_y = cat_y + (cat_h - strip_h) // 2
                    usable_cat_w = bar_w - (len(cat_stats) - 1) * gap
                    curr_x = content_x
                    
                    for cat, count in cat_stats.items():
                        color = _CAT_COLORS.get(cat, (150, 150, 150))
                        seg_w = (count / total_units) * usable_cat_w
                        if seg_w > 0:
                            pygame.draw.rect(surface, color, 
                                           (int(curr_x), strip_y, int(seg_w), strip_h), 
                                           border_radius=1)
                            curr_x += seg_w + gap
            
            # ── 7. HP Sayı (Sağ) ───────────────────────────────────────
            hp_text = f"{hp}"
            hp_color = self._get_hp_color(ratio)
            hp_y = draw_rect.y + int(self.row_h * 0.5) - 8
            font_cache.render_text(surface, hp_text, font_cache.bold(14), hp_color, 
                                   pygame.Rect(hp_num_x, hp_y, hp_num_zone_w, 16), 
                                   align="center", v_align="center")

            # ── 8. Dead State ──────────────────────────────────────────
            if hp <= 0:
                dead_overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                dead_overlay.fill((30, 5, 5, 220))
                surface.blit(dead_overlay, draw_rect.topleft)
                font_cache.render_text(surface, "ELIMINATED", font_cache.bold(14), 
                                      (255, 60, 60), draw_rect, 
                                      align="center", v_align="center")
        
        # Clipping'i geri yükle
        surface.set_clip(original_clip)

    def _get_hp_color(self, ratio: float) -> tuple[int, int, int]:
        """HP oranına göre renk döndürür (gradient)."""
        if ratio > 0.6:
            return (100, 255, 150)  # Yeşil
        elif ratio > 0.35:
            return (255, 200, 80)   # Sarı
        else:
            return (255, 80, 80)    # Kırmızı

    def _draw_enhanced_health_bar(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, 
                                  hp: int, max_hp: int, ratio: float, time_ms: int) -> None:
        """Geliştirilmiş can barı - gradient, shine ve segmentli görünüm."""
        # Background (dark)
        bg_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (15, 20, 30), bg_rect, border_radius=3)
        
        if hp <= 0: 
            return
        
        # HP color based on ratio
        if ratio > 0.6:
            fill_start = (0, 255, 120)
            fill_end = (0, 200, 90)
        elif ratio > 0.35:
            fill_start = (255, 200, 60)
            fill_end = (220, 160, 40)
        else:
            fill_start = (255, 60, 60)
            fill_end = (200, 30, 30)
        
        # Filled portion
        fill_w = int(w * ratio)
        if fill_w > 0:
            # Gradient fill
            fill_surf = pygame.Surface((fill_w, h), pygame.SRCALPHA)
            for i in range(h):
                t = i / h
                color = (
                    int(fill_start[0] * (1 - t) + fill_end[0] * t),
                    int(fill_start[1] * (1 - t) + fill_end[1] * t),
                    int(fill_start[2] * (1 - t) + fill_end[2] * t)
                )
                pygame.draw.line(fill_surf, color, (0, i), (fill_w, i))
            
            surface.blit(fill_surf, (x, y))
            
            # Shine effect (top highlight)
            shine_h = max(1, h // 3)
            shine_surf = pygame.Surface((fill_w, shine_h), pygame.SRCALPHA)
            shine_surf.fill((255, 255, 255, 40))
            surface.blit(shine_surf, (x, y))
            
            # Segmentation lines (subtle)
            segment_size = max_hp // 10  # 10 HP per segment
            if segment_size > 0:
                segments = max_hp // segment_size
                for i in range(1, segments):
                    seg_x = x + int((i * segment_size / max_hp) * w)
                    if seg_x < x + fill_w:
                        pygame.draw.line(surface, (0, 0, 0, 100), (seg_x, y), (seg_x, y + h), 1)
        
        # Border
        pygame.draw.rect(surface, (60, 70, 90), bg_rect, width=1, border_radius=3)
        
        # Animated flow effect for low HP
        if ratio < 0.35 and hp > 0:
            flow_offset = (time_ms // 50) % 20
            for i in range(0, fill_w, 20):
                flow_x = x + i + flow_offset
                if flow_x < x + fill_w:
                    pygame.draw.line(surface, (255, 255, 255, 30), 
                                   (flow_x, y), (flow_x, y + h), 1)

    def _draw_segmented_health_bar(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, hp: int, max_hp: int) -> None:
        """Legacy segmented health bar - kept for compatibility."""
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
