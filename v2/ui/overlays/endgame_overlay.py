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
        pygame.draw.rect(surface, Colors.GOLD_TEXT, self.bg_rect, 2)

        font_title = font_cache.bold(36)
        font_header = font_cache.bold(20)
        font_row = font_cache.mono(16)
        font_btn = font_cache.bold(24)

        # Başlık
        title_rect = pygame.Rect(self.bg_rect.x, self.bg_rect.y + 20, self.bg_rect.w, 50)
        font_cache.render_text(surface, "OYUN BİTTİ - KAZANDIN!", font_title, Colors.GOLD_TEXT, title_rect, align="center", v_align="center")

        # Tablo Başlıkları
        y_cursor = self.bg_rect.y + 100
        headers = "Sıra       Oyuncu                 Strateji        Puan     Durum"
        h_rect = pygame.Rect(self.bg_rect.x + 40, y_cursor, self.bg_rect.w - 80, 30)
        font_cache.render_text(surface, headers, font_header, Colors.PLATINUM, h_rect, align="left", v_align="center")
        y_cursor += 40

        # Oyuncular
        for stat in self.player_stats:
            rank = stat.get("rank", "-")
            name = str(stat.get("name", "Unknown"))[:20]
            strt = str(stat.get("strategy", "-"))[:15]
            pts  = stat.get("total_pts", 0)
            hp   = stat.get("hp", 0)
            
            durum = "KEMİK" if hp <= 0 else f"{hp} HP"
            
            # Formatlı satır
            line = f"#{rank:<8} {name:<22} {strt:<15} {pts:<8} {durum}"
            
            c = Colors.GOLD_TEXT if rank == 1 else Colors.PLATINUM
            if hp <= 0:
                c = Colors.DISABLED

            r_rect = pygame.Rect(self.bg_rect.x + 40, y_cursor, self.bg_rect.w - 80, 24)
            font_cache.render_text(surface, line, font_row, c, r_rect, align="left", v_align="center")
            y_cursor += 30

        # Restart Butonu
        pygame.draw.rect(surface, Colors.MIND, self.restart_rect)
        font_cache.render_text(surface, "YENİDEN BAŞLA", font_btn, (0,0,0), self.restart_rect, align="center", v_align="center")
