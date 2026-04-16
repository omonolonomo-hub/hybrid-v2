import pygame
from v2.constants import Layout, Screen, Colors
from v2.ui import font_cache


class LobbyPanel:
    def __init__(self, player_count: int = 8):
        self.rect = pygame.Rect(Layout.SIDEBAR_RIGHT_X, 0, Layout.SIDEBAR_RIGHT_W, Screen.H)

        # Oyuncu satırları — dikey ortala
        row_spacing = 8
        total_h  = player_count * (Layout.LOBBY_ROW_H + row_spacing) - row_spacing
        start_y  = (Screen.H - total_h) // 2
        margin_x = self.rect.x + 10
        row_w    = self.rect.w - 20

        self.player_rects: list[pygame.Rect] = []
        for i in range(player_count):
            row_y = start_y + i * (Layout.LOBBY_ROW_H + row_spacing)
            self.player_rects.append(pygame.Rect(margin_x, row_y, row_w, Layout.LOBBY_ROW_H))

        # Gradient Arkaplanları Önbelleğe Al (Yumuşak Köşeli)
        from v2.ui.ui_utils import UIUtils
        c_brd = (42, 58, 92, 180) # Unified HUD border
        self.bg_mine = UIUtils.create_gradient_panel(row_w, Layout.LOBBY_ROW_H, (30, 45, 65, 255), (10, 15, 25, 255), border_radius=8, border_color=c_brd)
        self.bg_top1 = UIUtils.create_gradient_panel(row_w, Layout.LOBBY_ROW_H, (65, 55, 20, 255), (25, 15,  5, 255), border_radius=8, border_color=(200, 180, 50, 180))
        self.bg_top2 = UIUtils.create_gradient_panel(row_w, Layout.LOBBY_ROW_H, (50, 50, 60, 255), (15, 15, 20, 255), border_radius=8, border_color=(150, 160, 180, 180))
        self.bg_top3 = UIUtils.create_gradient_panel(row_w, Layout.LOBBY_ROW_H, (55, 30, 20, 255), (20, 10,  5, 255), border_radius=8, border_color=(180, 100, 50, 180))
        self.bg_norm = UIUtils.create_gradient_panel(row_w, Layout.LOBBY_ROW_H, (35, 38, 48, 255), (12, 14, 20, 255), border_radius=8, border_color=c_brd)

        # Glow Yüzeyleri
        self.glow_top1 = UIUtils.create_glow(20, (255, 215, 0, 100))
        self.glow_top2 = UIUtils.create_glow(20, (200, 210, 220, 100))
        self.glow_top3 = UIUtils.create_glow(20, (220, 130, 60, 100))

        # ── Board Capacity Kutusu (8 oyuncu listesinin altında) ────────────
        # Listenin en altından 15px boşluk bırakarak aşağı yerleştir
        list_bottom = max(r.bottom for r in self.player_rects) if self.player_rects else Screen.H // 2
        cap_h = 52
        cap_y = list_bottom + 15
        self.capacity_rect = pygame.Rect(margin_x, cap_y, row_w, cap_h)
        self.cap_surf = UIUtils.create_gradient_panel(
            row_w, cap_h, (38, 44, 64, 255), (18, 24, 44, 255),
            border_radius=8, border_color=c_brd
        )

    # ------------------------------------------------------------------ #
    def _draw_segmented_health_bar(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, hp: int, max_hp: int) -> None:
        """Can barını parçalı küçük fiziksel bloklara bölerek çizer."""
        pygame.draw.rect(surface, (20, 24, 30), (x, y, w, h), border_radius=3)
        
        if hp <= 0: return

        ratio = max(0.0, min(1.0, hp / max_hp))
        fill_color = Colors.HP_FULL if ratio > 0.4 else Colors.HP_LOW
        
        # 5 HP'lik bloklara bölüyoruz (örn 150 can, 30 blok demektir)
        blp = 5 
        total_blocks = max(1, max_hp // blp)
        
        # padding 2px. Width of each block can be calculated
        padding = 1
        # Use exact floating math so it fills the background precisely
        block_w = (w - (total_blocks - 1) * padding) / total_blocks
        
        # Sadece canımız yettiği kadar blok çizeceğiz
        blocks_to_draw = int(total_blocks * ratio)
        if blocks_to_draw == 0 and hp > 0:
            blocks_to_draw = 1 # Çok az canı kaldıysa bile 1 blok görünsün
            
        for i in range(blocks_to_draw):
            bx = x + i * (block_w + padding)
            pygame.draw.rect(surface, fill_color, (int(bx), y, int(block_w), h), border_radius=1)

    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface, players: list = None) -> None:
        if players is None:
            players = []
            
        for i, p_rect in enumerate(self.player_rects):
            player  = players[i] if i < len(players) else {}
            is_self = (i == 0)
            hp      = player.get("hp", 150)
            max_hp  = player.get("max_hp", 150)
            name    = player.get("name", f"P{i+1}")
            rank    = player.get("rank", i + 1)
            ratio   = max(0.0, min(1.0, hp / max_hp))

            # ── Satır Arka Planı (Gradient Yüzey) ──────────────────────
            if is_self:
                surf = self.bg_mine
                border = (0, 210, 255)
            elif rank == 1:
                surf = self.bg_top1
                border = (255, 215, 0)
            elif rank == 2:
                surf = self.bg_top2
                border = (200, 200, 220)
            elif rank == 3:
                surf = self.bg_top3
                border = (205, 127, 50)
            else:
                surf = self.bg_norm
                border = (42, 58, 92)
            
            surface.blit(surf, p_rect.topleft)
            pygame.draw.rect(surface, border, p_rect, width=1, border_radius=8)

            # ── Sıra Numarası Rozeti (Sol - Parıltılı) ─────────────────
            rank_r = pygame.Rect(p_rect.x + 8, p_rect.y + (p_rect.h - 24) // 2, 24, 24)
            # Eğer Top 3 ise Glow ekle
            if rank == 1:
                surface.blit(self.glow_top1, (rank_r.centerx - 20, rank_r.centery - 20))
                pygame.draw.circle(surface, (220, 180, 50), rank_r.center, 12)
                r_c = (20, 20, 20)
            elif rank == 2:
                surface.blit(self.glow_top2, (rank_r.centerx - 20, rank_r.centery - 20))
                pygame.draw.circle(surface, (180, 190, 200), rank_r.center, 12)
                r_c = (20, 20, 20)
            elif rank == 3:
                surface.blit(self.glow_top3, (rank_r.centerx - 20, rank_r.centery - 20))
                pygame.draw.circle(surface, (180, 110, 60), rank_r.center, 12)
                r_c = (20, 20, 20)
            else:
                r_c = (140, 150, 160)
                
            font_cache.render_text(surface, f"#{rank}", font_cache.bold(11), r_c, rank_r, v_align="center", align="center")

            # ── Oyuncu Adı ─────────────────────────────────────────────
            name_r = pygame.Rect(p_rect.x + 40, p_rect.y + 4, p_rect.w - 50, 16)
            name_color = (0, 242, 255) if is_self else Colors.PLATINUM
            font_cache.render_text(surface, name, font_cache.bold(12), name_color, name_r)

            # ── HP Sayısı (Sağ Üst) ────────────────────────────────────
            hp_lbl_r = pygame.Rect(p_rect.x + 40, p_rect.y + 4, p_rect.w - 50, 16)
            hp_color  = Colors.HP_FULL if ratio > 0.4 else Colors.HP_LOW
            font_cache.render_text(surface, f"{hp}", font_cache.mono(10), hp_color, hp_lbl_r, align="right")

            # ── HP Bar (Segmentli Çizim) ───────────────────────────────
            bar_x = p_rect.x + 40
            bar_y = p_rect.y + 24
            bar_w = p_rect.w - 50
            bar_h = 8
            
            self._draw_segmented_health_bar(surface, bar_x, bar_y, bar_w, bar_h, hp, max_hp)

            # ── "DEAD" etiketi (Karartma) ─────────────────────────────
            if hp <= 0:
                dead_r = pygame.Rect(p_rect.x, p_rect.y, p_rect.w, p_rect.h)
                dead_surf = pygame.Surface(p_rect.size, pygame.SRCALPHA)
                dead_surf.fill((10, 5, 5, 180)) # Dramatik yarı saydam karanlık kan kırmızısı
                surface.blit(dead_surf, p_rect.topleft)
                font_cache.render_text(surface, "ELIMINATED", font_cache.bold(12),
                                       (255, 60, 60), dead_r, align="center", v_align="center")

        # ── Board Capacity Göstergesi ─────────────────────────────────
        surface.blit(self.cap_surf, self.capacity_rect.topleft)

        # Kapasite verisini al
        try:
            from v2.core.game_state import GameState
            board    = GameState.get().get_board(player_index=0)
            occupied = sum(1 for c in board if c is not None)
            total    = len(board)
        except Exception:
            occupied, total = 3, 8

        ratio = occupied / float(total) if total > 0 else 0
        if ratio < 0.6:  cap_color = (80, 200, 120)
        elif ratio < 0.9: cap_color = (255, 180, 50)
        else:             cap_color = (255, 80, 80)

        # Başlık
        title_r = pygame.Rect(self.capacity_rect.x, self.capacity_rect.y + 5,
                              self.capacity_rect.w, 14)
        font_cache.render_text(surface, "BOARD CAPACITY", font_cache.bold(10),
                               (100, 140, 220), title_r, align="center")

        # Hexagon nokta barlari
        import math
        hex_r   = 8
        spacing = 5
        total_w = total * (hex_r * 2 + spacing) - spacing
        start_x = self.capacity_rect.x + (self.capacity_rect.w - total_w) // 2
        cy      = self.capacity_rect.y + 37

        for i in range(total):
            cx = start_x + i * (hex_r * 2 + spacing) + hex_r
            pts = []
            for angle in range(0, 360, 60):
                rad = math.radians(angle + 30)
                pts.append((cx + hex_r * math.cos(rad), cy + hex_r * math.sin(rad)))
            if i < occupied:
                pygame.draw.polygon(surface, cap_color, pts)
                pygame.draw.aalines(surface, (255, 255, 255, 60), True, pts)
            else:
                pygame.draw.polygon(surface, (45, 52, 72), pts)
                pygame.draw.polygon(surface, (60, 70, 90), pts, 1)

        # Sayı etiketi sağa
        lbl_text = "FULL" if occupied >= total else f"{occupied}/{total}"
        lbl_r = pygame.Rect(self.capacity_rect.x, self.capacity_rect.y + 4,
                            self.capacity_rect.w - 10, 14)
        font_cache.render_text(surface, lbl_text, font_cache.mono(10),
                               cap_color, lbl_r, align="right", v_align="center")

    def handle_event(self, event: pygame.event.Event, players: list = None) -> int | None:
        """Kullanıcının bir oyuncu satırına tıklayıp tıklamadığını kontrol eder.
        Tıklanan oyuncunun engine index'ini döner (veya None).
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if players is None: return None
            for i, p_rect in enumerate(self.player_rects):
                if p_rect.collidepoint(event.pos):
                    if i < len(players):
                        target_index = players[i].get("index", i)
                        print(f"[DEBUG] Lobby tıklandı: Row={i} Player={players[i].get('name')} Index={target_index}")
                        return target_index
        return None
