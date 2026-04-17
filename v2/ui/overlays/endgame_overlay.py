import pygame
from v2.constants import Screen, Colors
from v2.ui import font_cache

class EndgameOverlay:
    def __init__(self, player_stats: list[dict]):
        """
        player_stats: Sona kalan ve elenen oyuncuların sıraya dizilmiş stat verisi
        [ {"name": "...", "strategy": "...", "hp": ..., "total_pts": ..., "rank": 1}, ... ]
        """
        self.player_stats = player_stats
        self.restart_clicked = False
        
        # Ekranın tam ortasında 800x600 bir Panel
        self.bg_rect = pygame.Rect(0, 0, 800, 600)
        self.bg_rect.center = (Screen.W // 2, Screen.H // 2)

        # Restart butonu panelin en altında
        self.restart_rect = pygame.Rect(0, 0, 200, 50)
        self.restart_rect.center = (self.bg_rect.centerx, self.bg_rect.bottom - 40)

        # Karartma Arkaplanı
        self.overlay_surf = pygame.Surface((Screen.W, Screen.H), pygame.SRCALPHA)
        self.overlay_surf.fill((0, 0, 0, 180))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_rect.collidepoint(event.pos):
                self.restart_clicked = True
                return True
            # Panel dışına tıklanınca blokla ama bi şey yapma
            return True
        return False

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface):
        surface.blit(self.overlay_surf, (0, 0))
        
        # Panel
        pygame.draw.rect(surface, (20, 25, 30), self.bg_rect)
        pygame.draw.rect(surface, (42, 58, 92), self.bg_rect, width=2)

        font_title = font_cache.bold(32)
        font_header = font_cache.bold(18)
        font_row = font_cache.mono(15)
        font_btn = font_cache.bold(22)

        # 1. Başlık
        title_rect = pygame.Rect(self.bg_rect.x, self.bg_rect.y + 25, self.bg_rect.w, 50)
        font_cache.render_text(surface, "OPERASYON SONU - RAPOR", font_title, Colors.GOLD_TEXT, title_rect, align="center")

        # 2. Tablo Başlıkları (Mutlak Hizalama)
        y_cursor = self.bg_rect.y + 100
        COLS = {
            "RANK": 40,
            "NAME": 110,
            "STRAT": 360,
            "SCORE": 520,
            "STATE": 680
        }
        
        headers = [
            ("SIRA", COLS["RANK"], 60),
            ("OYUNCU", COLS["NAME"], 240),
            ("STRATEJİ", COLS["STRAT"], 150),
            ("STR. SKORU", COLS["SCORE"], 140),
            ("DURUM", COLS["STATE"], 80)
        ]

        for text, x_off, w in headers:
            h_rect = pygame.Rect(self.bg_rect.x + x_off, y_cursor, w, 30)
            font_cache.render_text(surface, text, font_header, (100, 140, 220), h_rect, align="left")
        
        y_cursor += 40
        pygame.draw.line(surface, (42, 58, 92, 100), (self.bg_rect.x + 40, y_cursor - 5), (self.bg_rect.right - 40, y_cursor - 5), 1)

        # 3. Oyuncu Verileri
        for stat in self.player_stats:
            rank = stat.get("rank", "-")
            name = str(stat.get("name", "Unknown"))[:20]
            strt = str(stat.get("strategy", "-"))[:15]
            pts  = stat.get("total_pts", 0)
            hp   = stat.get("hp", 0)
            
            durum = "ELENDİ" if hp <= 0 else f"{hp} HP"
            
            c = Colors.GOLD_TEXT if rank == 1 else Colors.PLATINUM
            if hp <= 0: c = Colors.DISABLED

            # Render Columns
            row_data = [
                (f"#{rank}", COLS["RANK"], 60),
                (name, COLS["NAME"], 240),
                (strt, COLS["STRAT"], 150),
                (str(pts), COLS["SCORE"], 140),
                (durum, COLS["STATE"], 80)
            ]

            for text, x_off, w in row_data:
                r_rect = pygame.Rect(self.bg_rect.x + x_off, y_cursor, w, 28)
                font_cache.render_text(surface, text, font_row, c, r_rect, align="left")
            
            y_cursor += 32

        # 4. Yeniden Başlat Butonu
        is_hover = self.restart_rect.collidepoint(pygame.mouse.get_pos())
        btn_col = (42, 58, 92) if not is_hover else (60, 80, 140)
        pygame.draw.rect(surface, btn_col, self.restart_rect, border_radius=4)
        pygame.draw.rect(surface, (100, 150, 255), self.restart_rect, width=1, border_radius=4)
        font_cache.render_text(surface, "YENİDEN BAŞLAT", font_btn, (255, 255, 255), self.restart_rect, align="center")
