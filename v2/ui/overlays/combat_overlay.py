import pygame
from v2.constants import Screen, Layout, Colors
from v2.ui import font_cache

class CombatOverlay:
    def __init__(self, combat_logs: list[str], line_delay_ms: int = 80):
        self.combat_logs = combat_logs
        self.line_delay_ms = line_delay_ms
        self.visible_lines = []
        self.is_finished = False
        
        self._elapsed_ms = 0.0
        self._rendered_count = 0
        self._post_combat_timer = 0.0

        # Termimal Arkaplan Alanı (Ekranın yarısından aşağısı)
        self.bg_rect = pygame.Rect(
            Layout.CENTER_ORIGIN_X + 20,
            Layout.CENTER_ORIGIN_Y + 100,
            Layout.CENTER_W - 40,
            Screen.H - Layout.CENTER_ORIGIN_Y - 200
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Savaş animasyonunu hızlandırmak için click/space yakalanabilir
        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
            if self._rendered_count < len(self.combat_logs):
                # Kalan süreyi ani atla
                self.visible_lines = list(self.combat_logs)
                self._rendered_count = len(self.combat_logs)
            return True
        return False

    def update(self, dt: float):
        if self.is_finished:
            return
            
        # Eğer hepsi gösterildiyse, post-combat bekleme
        if self._rendered_count >= len(self.combat_logs):
            self._post_combat_timer += dt
            if self._post_combat_timer >= 2000.0:
                self.is_finished = True
            return

        if self.line_delay_ms <= 0:
            self.visible_lines = list(self.combat_logs)
            self._rendered_count = len(self.combat_logs)
            return

        self._elapsed_ms += dt
        while self._elapsed_ms >= self.line_delay_ms and self._rendered_count < len(self.combat_logs):
            self._elapsed_ms -= self.line_delay_ms
            self.visible_lines.append(self.combat_logs[self._rendered_count])
            self._rendered_count += 1

    def render(self, surface: pygame.Surface):
        # Arkaplan ve çerçeve
        pygame.draw.rect(surface, Colors.TERMINAL_BG, self.bg_rect)
        pygame.draw.rect(surface, Colors.MIND, self.bg_rect, 2)

        fnt = font_cache.mono(16)
        
        # Terminal gibi alttan yukarıya doğru yazdırma (Auto-scroll effect)
        y_cursor = self.bg_rect.bottom - 40
        line_spacing = 24
        
        for line in reversed(self.visible_lines):
            line_rect = pygame.Rect(self.bg_rect.x + 20, y_cursor, self.bg_rect.w - 40, 20)
            
            color = Colors.TERMINAL_FG
            if "SONUÇ:" in line or "VICTORY" in line:
                color = Colors.GOLD_TEXT
            elif "kazandı" in line or "WIN" in line:
                color = Colors.MIND
            elif "kaybetti" in line or "LOSE" in line or "-1 HP" in line:
                color = Colors.EXISTENCE

            font_cache.render_text(
                surface, line, fnt, color, line_rect, align="left", v_align="center"
            )
            y_cursor -= line_spacing
            
            # Kutu sınırından taşıyorsa üsttekileri kes
            if y_cursor < self.bg_rect.top + 10:
                break
