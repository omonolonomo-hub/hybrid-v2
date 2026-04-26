import pygame
from v2.constants import Layout

class TimerBar:
    def __init__(self, height: int = 8):
        # Timer Bar (Eriyen Çubuk) ShopPanel'in hemen altına, Board Canvas'ın en tepesine yerleşir.
        self.rect = pygame.Rect(
             Layout.CENTER_ORIGIN_X,
             Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H,
             Layout.CENTER_W,
             height
        )

    def render(self, surface: pygame.Surface, ratio: float = 1.0):
        """
        ratio: 0.0 ile 1.0 arasinda eriyen isiyi/sureyi temsil eder.
        """
        # 1. Background track (Koyu gri/siyah zemin)
        pygame.draw.rect(surface, (15, 12, 18), self.rect)
        
        # 2. Eriyen Ates Kismi (Cyber Turuncu)
        # Ratio'nun guvenligini al (tasmamasi icin)
        safe_ratio = max(0.0, min(1.0, ratio))
        fill_w = int(self.rect.width * safe_ratio)
        
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, (255, 100, 30), fill_rect)
            
            # Kucuk neon parlamasi (sari-turuncu ufak cizgi)
            glow_rect = pygame.Rect(self.rect.x, self.rect.y + 2, fill_w, 2)
            pygame.draw.rect(surface, (255, 200, 80), glow_rect)

        # 3. Ust ve Alt ince Cyber Sınır Cizgileri
        pygame.draw.line(surface, (42, 58, 92), (self.rect.x, self.rect.y), (self.rect.right, self.rect.y), 1)
        pygame.draw.line(surface, (42, 58, 92), (self.rect.x, self.rect.bottom), (self.rect.right, self.rect.bottom), 1)
