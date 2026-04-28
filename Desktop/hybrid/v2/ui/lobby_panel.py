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

# ── Rank Badge İkonları ve Renkleri ─────────────────────────────────────────
RANK_ICON_NAMES = {
    1: "CROWN",   # Font Awesome taç ikonu
    2: "MEDAL",   # Font Awesome madalya ikonu
    3: "AWARD",   # Font Awesome ödül ikonu
}

RANK_BG_COLORS = {
    1: (65, 45, 5, 220),    # Altın arka plan
    2: (50, 50, 60, 220),   # Gümüş arka plan
    3: (55, 28, 8, 220),    # Bronz arka plan
}

RANK_TEXT_COLORS = {
    1: (255, 215, 0),       # Altın text
    2: (192, 192, 192),     # Gümüş text
    3: (205, 127, 50),      # Bronz text
}

class LobbyPanel:
    def __init__(self, player_count: int = 8):
        self.rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)

        # ── Altın Oran ile Oyuncu Satırları ────────────────────────────────────
        self.player_count = player_count
        
        # Row height: 70px (tam değer, çarpan yok)
        self.row_h = Layout.LOBBY_ROW_H  # 70px
        
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
        
        # Margin: Maksimum genişlik için margin'i minimize et
        # AAA Style için çok daha geniş row (%10-12 artış)
        margin_offset = int(self.rect.w * 0.005)  # %0.5 margin (neredeyse yok)
        self.margin_x = self.rect.x + margin_offset
        self.row_w    = self.rect.w - 2 * margin_offset  # Maksimum genişlik

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
            # AAA Kalite Layout - Altın oran ile dengeli yerleşim
            content_padding = int(draw_rect.w * 0.012)  # %1.2 iç padding
            usable_w = draw_rect.w - 2 * content_padding
            
            # Sol: Avatar (yuvarlak badge) - 70px row için
            avatar_size = int(self.row_h * 0.66)  # %66 (70px için ~46px) - biraz küçültüldü
            avatar_left_pad = int(self.row_h * 0.06)  # Sol padding
            avatar_x = draw_rect.x + content_padding + avatar_left_pad
            
            # Orta: İçerik (isim + HP bar + categories)
            # Avatar'dan sonra altın oran ile gap
            content_left_margin = avatar_x + avatar_size + int(self.row_h * 0.14)  # %14 gap
            
            # Sağ: HP sayısı - dengeli alan
            hp_num_w = int(usable_w * 0.18)  # %18 (123/150 için yeterli)
            hp_right_pad = int(self.row_h * 0.08)  # Sağ padding
            content_w = draw_rect.right - content_padding - hp_num_w - hp_right_pad - content_left_margin
            hp_num_x = content_left_margin + content_w + int(self.row_h * 0.06)  # HP'den gap
            
            # ── 5. Avatar Badge (Yuvarlak) - AAA Style ────────────────────
            # Yüksek çözünürlükte çiz, sonra scale et (keskin görünüm için)
            scale_factor = 2  # 2x çözünürlük
            avatar_size_hd = avatar_size * scale_factor
            avatar_surf_hd = pygame.Surface((avatar_size_hd, avatar_size_hd), pygame.SRCALPHA)
            center_hd = avatar_size_hd // 2
            
            # Outer glow (rank renginde)
            rank_col = RANK_TEXT_COLORS.get(rank, (200, 200, 210))
            for i in range(2, 0, -1):
                glow_alpha = 50 * i
                glow_color = (*rank_col, glow_alpha)
                pygame.draw.circle(avatar_surf_hd, glow_color, (center_hd, center_hd), center_hd + i * 4)
            
            # Ana daire (rank rengine göre gradient background)
            bg_color = RANK_BG_COLORS.get(rank, (30, 30, 40, 255))
            pygame.draw.circle(avatar_surf_hd, bg_color, (center_hd, center_hd), center_hd)
            
            # Border (2 katmanlı - depth için) - daha kalın HD'de
            border_color = RANK_TEXT_COLORS.get(rank, (80, 80, 90))
            pygame.draw.circle(avatar_surf_hd, border_color, (center_hd, center_hd), center_hd, width=4)
            pygame.draw.circle(avatar_surf_hd, (*border_color[:3], 100), (center_hd, center_hd), center_hd - 4, width=2)
            
            # İçerik: Top 3 için ikon + numara, diğerleri için sadece numara
            if rank in RANK_ICON_NAMES:
                # İkon (üstte) - HD boyutta
                icon_name = RANK_ICON_NAMES[rank]
                icon_char = font_cache.ICONS.get(icon_name, "?")
                icon_size_hd = int(avatar_size_hd * 0.32)
                icon_font = font_cache.icons(icon_size_hd)
                icon_surf = icon_font.render(icon_char, True, rank_col)
                icon_rect = icon_surf.get_rect(center=(center_hd, int(center_hd * 0.68)))
                avatar_surf_hd.blit(icon_surf, icon_rect)
                
                # Numara (altta) - HD boyutta
                num_font = font_cache.bold(int(avatar_size_hd * 0.26))
                num_surf = num_font.render(str(rank), True, rank_col)
                num_rect = num_surf.get_rect(center=(center_hd, int(center_hd * 1.38)))
                avatar_surf_hd.blit(num_surf, num_rect)
            else:
                # Sadece numara (ortalanmış) - HD boyutta
                num_font = font_cache.bold(int(avatar_size_hd * 0.42))
                num_surf = num_font.render(f"#{rank}", True, rank_col)
                num_rect = num_surf.get_rect(center=(center_hd, center_hd))
                avatar_surf_hd.blit(num_surf, num_rect)
            
            # HD'den normal boyuta scale et (smoothscale = anti-aliasing)
            avatar_surf = pygame.transform.smoothscale(avatar_surf_hd, (avatar_size, avatar_size))
            
            # Avatar'ı yerleştir (dikey ortalanmış)
            avatar_y = draw_rect.centery - avatar_size // 2
            surface.blit(avatar_surf, (avatar_x, avatar_y))
            
            # ── 6. İçerik Bölgesi - AAA Style ─────────────────────────────
            # Dikey yerleşim: İsim + HP Bar + Category Strips
            # Altın oran ile dengeli spacing
            content_top = draw_rect.y + int(self.row_h * 0.10)  # Üst padding
            content_bottom = draw_rect.bottom - int(self.row_h * 0.08)  # Alt padding
            content_h = content_bottom - content_top
            
            # Altın oran ile katmanlar (φ⁻¹ ≈ 0.618)
            # İsim: %24, HP Bar: %42, Gap: %8, Category: %26
            name_h = int(content_h * 0.24)
            bar_h_allocation = int(content_h * 0.42)
            gap_after_bar = int(content_h * 0.08)
            cat_h_allocation = content_h - name_h - bar_h_allocation - gap_after_bar
            
            # İsim (üstte)
            name_y = content_top
            name_color = (0, 242, 255) if is_self else (240, 245, 255)
            name_font_size = 13 if is_self else 12
            font_cache.render_text(surface, player.get("name", "---"), 
                                   font_cache.bold(name_font_size), name_color, 
                                   pygame.Rect(content_left_margin, name_y, content_w, name_h),
                                   v_align="center")
            
            # HP Bar (ortada, kalın ve segmentli)
            bar_y = name_y + name_h
            bar_h_px = int(self.row_h * 0.24)  # Bar yüksekliği (%24 of row)
            bar_w = content_w
            
            # HP Bar Background (koyu, depth için)
            bar_bg_rect = pygame.Rect(content_left_margin, bar_y, bar_w, bar_h_px)
            pygame.draw.rect(surface, (10, 12, 18), bar_bg_rect, border_radius=int(bar_h_px * 0.25))
            
            # HP Bar Fill (renkli, gradient)
            if hp > 0:
                fill_w = int(bar_w * ratio)
                if fill_w > 0:
                    # HP rengine göre gradient
                    if ratio > 0.6:
                        fill_start = (0, 255, 120)
                        fill_end = (0, 200, 90)
                    elif ratio > 0.35:
                        fill_start = (255, 200, 60)
                        fill_end = (220, 160, 40)
                    else:
                        fill_start = (255, 60, 60)
                        fill_end = (200, 30, 30)
                    
                    # Gradient fill
                    fill_surf = pygame.Surface((fill_w, bar_h_px), pygame.SRCALPHA)
                    for i in range(bar_h_px):
                        t = i / bar_h_px
                        color = (
                            int(fill_start[0] * (1 - t) + fill_end[0] * t),
                            int(fill_start[1] * (1 - t) + fill_end[1] * t),
                            int(fill_start[2] * (1 - t) + fill_end[2] * t)
                        )
                        pygame.draw.line(fill_surf, color, (0, i), (fill_w, i))
                    
                    # Clip to rounded rect
                    fill_rect = pygame.Rect(content_left_margin, bar_y, fill_w, bar_h_px)
                    pygame.draw.rect(surface, (255, 255, 255), fill_rect, border_radius=int(bar_h_px * 0.25))
                    surface.blit(fill_surf, (content_left_margin, bar_y), special_flags=pygame.BLEND_RGBA_MIN)
                    pygame.draw.rect(surface, fill_start, fill_rect, border_radius=int(bar_h_px * 0.25))
                    
                    # Top highlight (shine effect)
                    shine_h = max(2, bar_h_px // 4)
                    shine_rect = pygame.Rect(content_left_margin, bar_y, fill_w, shine_h)
                    shine_surf = pygame.Surface((fill_w, shine_h), pygame.SRCALPHA)
                    shine_surf.fill((255, 255, 255, 60))
                    surface.blit(shine_surf, shine_rect.topleft)
                    
                    # Segmentation lines (her 10 HP'de bir)
                    segment_size = max_hp // 10
                    if segment_size > 0:
                        segments = max_hp // segment_size
                        for i in range(1, segments):
                            seg_x = content_left_margin + int((i * segment_size / max_hp) * bar_w)
                            if seg_x < content_left_margin + fill_w:
                                pygame.draw.line(surface, (0, 0, 0, 120), 
                                               (seg_x, bar_y), (seg_x, bar_y + bar_h_px), 2)
            
            # HP Bar Border (ince, parlak)
            pygame.draw.rect(surface, (60, 70, 90, 180), bar_bg_rect, width=1, border_radius=int(bar_h_px * 0.25))
            
            # Low HP pulse effect
            if ratio < 0.35 and hp > 0:
                pulse_intensity = 0.5 + 0.5 * math.sin(time_ms * 0.008)
                pulse_alpha = int(40 + 60 * pulse_intensity)
                glow_rect = bar_bg_rect.inflate(6, 6)
                pygame.draw.rect(surface, (255, 50, 50, pulse_alpha), glow_rect, 
                               width=2, border_radius=int(bar_h_px * 0.25))
            
            # Category Strips (altta, renkli çizgiler)
            cat_y = bar_y + bar_h_px + gap_after_bar
            cat_stats = player.get("categories", {})
            if cat_stats:
                total_units = sum(cat_stats.values())
                if total_units > 0:
                    # Category strip yüksekliği - allocation içinde ortalanmış
                    strip_h = max(5, int(self.row_h * 0.11))
                    strip_y = cat_y + (cat_h_allocation - strip_h) // 2  # Dikey ortalama
                    gap = 2
                    usable_cat_w = bar_w - (len(cat_stats) - 1) * gap
                    curr_x = content_left_margin
                    
                    for cat, count in cat_stats.items():
                        color = _CAT_COLORS.get(cat, (150, 150, 150))
                        seg_w = (count / total_units) * usable_cat_w
                        if seg_w > 0:
                            cat_rect = pygame.Rect(int(curr_x), strip_y, int(seg_w), strip_h)
                            pygame.draw.rect(surface, color, cat_rect, border_radius=2)
                            # Glow effect
                            glow_color = (*color, 80)
                            pygame.draw.rect(surface, glow_color, cat_rect.inflate(2, 2), 
                                           width=1, border_radius=2)
                            curr_x += seg_w + gap
            
            # ── 7. HP Sayı (Sağ) - AAA Style ──────────────────────────────
            # HP sayısı + max HP (123/150 formatında) - dengeli yerleşim
            hp_color = self._get_hp_color(ratio)
            hp_main_font = font_cache.bold(14)
            hp_max_font = font_cache.regular(9)
            
            # Ana HP sayısı
            hp_text = f"{hp}"
            hp_surf = hp_main_font.render(hp_text, True, hp_color)
            
            # Max HP (gri, küçük)
            max_text = f"/{max_hp}"
            max_surf = hp_max_font.render(max_text, True, (120, 130, 140))
            
            # Toplam genişlik hesapla
            total_w = hp_surf.get_width() + max_surf.get_width() + 2
            
            # Sağa hizala - hp_num_w alanı içinde ortalanmış
            hp_area_x = draw_rect.right - content_padding - hp_num_w - hp_right_pad
            hp_x = hp_area_x + (hp_num_w - total_w) // 2  # Ortalanmış
            hp_y = draw_rect.centery - hp_surf.get_height() // 2
            
            # Glow effect (düşük HP'de)
            if ratio < 0.35 and hp > 0:
                pulse_intensity = 0.5 + 0.5 * math.sin(time_ms * 0.008)
                glow_alpha = int(60 + 80 * pulse_intensity)
                glow_surf = hp_main_font.render(hp_text, True, (*hp_color, glow_alpha))
                for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    surface.blit(glow_surf, (hp_x + dx, hp_y + dy))
            
            # Ana HP
            surface.blit(hp_surf, (hp_x, hp_y))
            
            # Max HP (sağda, biraz aşağıda)
            max_x = hp_x + hp_surf.get_width() + 2
            max_y = hp_y + hp_surf.get_height() - max_surf.get_height()
            surface.blit(max_surf, (max_x, max_y))

            # ── 8. Dead State - AAA Style ──────────────────────────────
            if hp <= 0:
                # Koyu overlay
                dead_overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                dead_overlay.fill((15, 5, 10, 235))
                surface.blit(dead_overlay, draw_rect.topleft)
                
                # "ELIMINATED" text (büyük, kırmızı, glow ile)
                elim_font = font_cache.bold(16)
                elim_text = "ELIMINATED"
                elim_color = (255, 60, 60)
                
                # Glow effect
                for offset in range(3, 0, -1):
                    glow_alpha = 40 * offset
                    glow_surf = elim_font.render(elim_text, True, (*elim_color, glow_alpha))
                    glow_rect = glow_surf.get_rect(center=draw_rect.center)
                    for dx, dy in [(-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]:
                        surface.blit(glow_surf, (glow_rect.x + dx, glow_rect.y + dy))
                
                # Ana text
                font_cache.render_text(surface, elim_text, elim_font, elim_color, 
                                      draw_rect, align="center", v_align="center")
        
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
