import pygame

class UIUtils:
    @staticmethod
    def create_gradient_panel(width: int, height: int, color_top: tuple, color_bottom: tuple, border_radius: int = 0, border_color: tuple | None = None) -> pygame.Surface:
        """
        Yukarıdan aşağıya renk geçişi (gradient) yapar ve 3B hacimli görünmesi için 
        üst/alt kenarlarına highlight ve gölge ekler. border_radius ile köşeler yumuşatılabilir.
        """
        width = int(width)
        height = int(height)
        
        # 1. 1 Boyutlu Degrade Kalıbı Yarat (Sadece Y ekseni)
        # Bu yöntem pikselleri X,Y çift loop ile çizmekten yüzlerce kat daha performanslıdır.
        gradient_1d = pygame.Surface((1, height), pygame.SRCALPHA)
        
        r1, g1, b1 = color_top[:3]
        a1 = color_top[3] if len(color_top) == 4 else 255
        
        r2, g2, b2 = color_bottom[:3]
        a2 = color_bottom[3] if len(color_bottom) == 4 else 255
        
        for y in range(height):
            # Float/int karışıklığını tamamen sıfırlamak için kesin oransal iterasyon uyguluyoruz
            ratio = y / max(1, (height - 1))
            
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            a = int(a1 + (a2 - a1) * ratio)
            
            # Sınırlara tam oturduğundan (clamping) emin ol
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            a = max(0, min(255, a))
            
            gradient_1d.set_at((0, y), (r, g, b, a))
            
        # 2. Kalıbı yatayda gerdirerek ana Surface'i oluştur
        raw = pygame.transform.scale(gradient_1d, (width, height))
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.blit(raw, (0, 0))
        
        # 3. 3B Hacim (Bevel) - sadece radius yoksa
        if border_radius == 0:
            pygame.draw.line(surface, (255, 255, 255, 60), (0, 0), (width - 1, 0), 1)
            pygame.draw.line(surface, (255, 255, 255, 20), (0, 1), (width - 1, 1), 1)
            pygame.draw.line(surface, (0, 0, 0, 140), (0, height - 1), (width - 1, height - 1), 1)
            pygame.draw.line(surface, (0, 0, 0, 70),  (0, height - 2), (width - 1, height - 2), 1)
            pygame.draw.line(surface, (0, 0, 0, 40), (0, 1), (0, height - 2), 1)
            pygame.draw.line(surface, (0, 0, 0, 40), (width - 1, 1), (width - 1, height - 2), 1)
        
        # 4. Köşe Maskeleme (rounded clip)
        if border_radius > 0:
            mask = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
            surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 5. Kenarlık
        if border_color is not None:
            pygame.draw.rect(surface, border_color, surface.get_rect(), width=1, border_radius=border_radius)
        elif border_radius > 0:
            pygame.draw.rect(surface, (0, 0, 0, 160), surface.get_rect(), width=1, border_radius=border_radius)
        
        return surface

    @staticmethod
    def create_glow(radius: int, color: tuple) -> pygame.Surface:
        """
        Merkezden dışarıya doğru yumuşayarak kaybolan parıltı (glow) efekti.
        Ağır matematik içerir ancak sadece önbellekleme sırasında (1 kez) çalışmalıdır.
        """
        size = int(radius * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (radius, radius)
        
        r, g, b = color[:3]
        max_alpha = color[3] if len(color) == 4 else 120
        
        # En dışarıdan merkeze doğru iç içe daireler çizerek glow yarat
        for i in range(radius, 0, -1):
            ratio = i / radius
            # Dışarıya doğru erime formülü (quadratic falloff)
            alpha = int(max_alpha * ((1.0 - ratio) ** 1.5))
            pygame.draw.circle(surf, (r, g, b, alpha), center, i)
            
        return surf
