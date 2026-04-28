"""
MenuScene - İlk açılış ekranı
Gereksinim 2: Menü Ekranı Görüntüleme
"""

import pygame
from pathlib import Path
from v2.core.scene_manager import Scene, SceneManager
from v2.constants import Screen, Colors

# Renkler - Synergy gruplarından ilham alınmış
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_DARK = (12, 12, 18)  # Koyu arka plan
BG_GRADIENT_TOP = (20, 25, 40)  # Gradient üst
BG_GRADIENT_BOTTOM = (35, 15, 45)  # Gradient alt (mor ton)

# Altın Oran (Golden Ratio)
GOLDEN_RATIO = 1.618

# Kategori renkleri (card_meta.py'den)
CATEGORY_COLORS = {
    "Mythology & Gods": (248, 222, 34),   # Sarı
    "Art & Culture": (209, 32, 82),       # Kırmızı
    "Nature & Creatures": (35, 114, 39),  # Yeşil
    "Cosmos": (80, 50, 180),              # Mor
    "Science": (3, 174, 210),             # Cyan
    "History & Civilizations": (244, 91, 38),  # Turuncu
}


class MenuScene(Scene):
    """
    İlk açılış ekranı. "AUTOCHESS HYBRID" başlığı ve "YENİ OYUN" butonu gösterir.
    
    Gereksinim 2.5, 7.1: Fontlar lazy init ile yüklenir (pygame başlamadan önce değil)
    """
    
    def __init__(self):
        """
        Constructor'da font alanlarını None olarak initialize et.
        Gereksinim 2.5, 7.1
        """
        super().__init__()
        self._font_title: pygame.font.Font | None = None
        self._font_button: pygame.font.Font | None = None
        self._btn_rect: pygame.Rect | None = None
        # Performance: Cache background to avoid redrawing every frame
        self._background_cache: pygame.Surface | None = None
        # Interactive button state
        self._btn_hovered: bool = False
        self._btn_pressed: bool = False
        self._btn_scale: float = 1.0  # Scale animation

    def update(self, dt_ms: float) -> None:
        """Update button animations."""
        # Check mouse position for hover effect
        mouse_pos = pygame.mouse.get_pos()
        if self._btn_rect is not None:
            self._btn_hovered = self._btn_rect.collidepoint(mouse_pos)
        
        # Smooth scale animation
        target_scale = 1.08 if self._btn_hovered else 1.0
        if self._btn_pressed:
            target_scale = 0.95
        
        # Lerp towards target scale
        lerp_speed = 0.3
        self._btn_scale += (target_scale - self._btn_scale) * lerp_speed
    
    def _init_fonts(self) -> None:
        """
        Fontları lazy init ile yükle.
        Idempotent: Zaten yüklenmişse tekrar yükleme yapma.
        Gereksinim 7.2, 7.3, 7.4
        """
        if self._font_title is None:
            # Ana başlık: BitcountGridDoubleInk
            font_dir = Path("v2/assets/fonts")
            self._font_title = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 72)
            # Buton yazısı: BitcountGridDoubleInk
            self._font_button = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 36)

    def _render_background(self) -> pygame.Surface:
        """Render background once and cache it for performance."""
        bg = pygame.Surface((Screen.W, Screen.H))
        
        # Gradient arka plan (üstten alta)
        for y in range(Screen.H):
            ratio = y / Screen.H
            r = int(BG_GRADIENT_TOP[0] * (1 - ratio) + BG_GRADIENT_BOTTOM[0] * ratio)
            g = int(BG_GRADIENT_TOP[1] * (1 - ratio) + BG_GRADIENT_BOTTOM[1] * ratio)
            b = int(BG_GRADIENT_TOP[2] * (1 - ratio) + BG_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (Screen.W, y))
        
        # Dekoratif kategori renk çizgileri (üstte)
        category_colors = list(CATEGORY_COLORS.values())
        stripe_height = 4
        stripe_y = 0
        for i, color in enumerate(category_colors):
            x_start = (Screen.W // len(category_colors)) * i
            x_end = (Screen.W // len(category_colors)) * (i + 1)
            pygame.draw.rect(bg, color, (x_start, stripe_y, x_end - x_start, stripe_height))
        
        # Dekoratif hex pattern (arka planda)
        import math
        hex_size = 30
        hex_alpha = 15
        for row in range(0, Screen.H // hex_size + 2):
            for col in range(0, Screen.W // hex_size + 2):
                x = col * hex_size * 1.5
                y = row * hex_size * math.sqrt(3) + (hex_size * math.sqrt(3) / 2 if col % 2 else 0)
                
                # Hex çizimi
                points = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    px = x + hex_size * 0.5 * math.cos(angle)
                    py = y + hex_size * 0.5 * math.sin(angle)
                    points.append((px, py))
                
                # Sadece border çiz (fill değil)
                if len(points) >= 3:
                    hex_surf = pygame.Surface((hex_size * 2, hex_size * 2), pygame.SRCALPHA)
                    offset_points = [(px - x + hex_size, py - y + hex_size) for px, py in points]
                    pygame.draw.polygon(hex_surf, (*Colors.MIND, hex_alpha), offset_points, width=1)
                    bg.blit(hex_surf, (x - hex_size, y - hex_size))
        
        return bg

    def draw(self, surface: pygame.Surface) -> None:
        """
        Menü ekranını render et.
        Gereksinim 2.1, 2.2, 2.3, 2.4
        """
        # Fontları yükle (lazy init)
        self._init_fonts()
        
        # Use cached background or render it once
        if self._background_cache is None:
            self._background_cache = self._render_background()
        
        # Blit cached background (much faster than redrawing)
        surface.blit(self._background_cache, (0, 0))
        
        # "AUTOCHESS HYBRID" başlığını Altın Oran konumunda render et
        # Başlığa glow efekti ekle
        title_text = "AUTOCHESS HYBRID"
        # Golden Ratio: başlık ekranın 1/φ * H'sine yerleştirilir
        title_y = int(Screen.H * (1 / GOLDEN_RATIO))
        
        # Glow efekti (3 katman)
        for offset in [4, 2, 0]:
            alpha = 80 if offset > 0 else 255
            glow_color = (*Colors.MIND[:3], alpha) if offset > 0 else WHITE
            title_surf = self._font_title.render(title_text, True, glow_color if offset == 0 else Colors.MIND)
            title_rect = title_surf.get_rect(center=(Screen.W // 2, title_y + offset))
            if offset > 0:
                title_surf.set_alpha(alpha)
            surface.blit(title_surf, title_rect)
        
        # Alt başlık - synergy gruplarını göster
        # Merkeze hizalanan, simetrik layout
        subtitle_font = pygame.font.Font(str(Path("v2/assets/fonts") / "minimap_category_names.ttf"), 24)
        subtitle_parts = [
            ("MIND", Colors.MIND),
            (" • ", WHITE),
            ("CONNECTION", Colors.CONNECTION),
            (" • ", WHITE),
            ("EXISTENCE", Colors.EXISTENCE)
        ]
        
        # Subtitle'ı merkeze hizala
        subtitle_surfaces = []
        total_width = 0
        for text, color in subtitle_parts:
            surf = subtitle_font.render(text, True, color)
            subtitle_surfaces.append(surf)
            total_width += surf.get_width()
        
        # Merkeze hizalanan x pozisyonu
        subtitle_y = title_y + int(Screen.H * 0.05)
        subtitle_x = Screen.W // 2 - total_width // 2
        
        for surf in subtitle_surfaces:
            surface.blit(surf, (subtitle_x, subtitle_y))
            subtitle_x += surf.get_width()
        
        # "YENİ OYUN" butonunu merkeze hizala
        # Buton: 240x60 boyutunda, border_radius=8
        btn_w, btn_h = 240, 60
        btn_x = Screen.W // 2 - btn_w // 2  # Merkeze hizala
        btn_y = int(Screen.H * 0.75)  # Buton daha aşağıda
        self._btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        # Apply scale animation
        scaled_w = int(btn_w * self._btn_scale)
        scaled_h = int(btn_h * self._btn_scale)
        scaled_rect = pygame.Rect(
            btn_x + (btn_w - scaled_w) // 2,
            btn_y + (btn_h - scaled_h) // 2,
            scaled_w,
            scaled_h
        )
        
        # Buton glow efekti (daha güçlü hover'da)
        glow_intensity = 1.5 if self._btn_hovered else 1.0
        for i in range(3):
            glow_inflate = int((12 - i * 4) * glow_intensity)
            glow_rect = scaled_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = int((40 + i * 20) * glow_intensity)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*Colors.MIND, min(glow_alpha, 255)), 
                           glow_surf.get_rect(), border_radius=12)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Buton rengi (hover'da daha parlak)
        btn_color = WHITE if not self._btn_hovered else (255, 255, 255)
        if self._btn_hovered:
            # Hafif mavi tint hover'da
            btn_color = (240, 245, 255)
        
        # Beyaz buton çiz
        pygame.draw.rect(surface, btn_color, scaled_rect, border_radius=8)
        
        # İnce border (hover'da daha kalın ve parlak)
        border_width = 3 if self._btn_hovered else 2
        if self._btn_hovered:
            border_color = (min(Colors.MIND[0] + 30, 255), min(Colors.MIND[1] + 30, 255), min(Colors.MIND[2] + 50, 255))
        else:
            border_color = Colors.MIND
        pygame.draw.rect(surface, border_color, scaled_rect, width=border_width, border_radius=8)
        
        # Buton metnini çiz (koyu mavi metin)
        btn_text_surf = self._font_button.render("YENİ OYUN", True, Colors.MIND)
        btn_text_rect = btn_text_surf.get_rect(center=scaled_rect.center)
        surface.blit(btn_text_surf, btn_text_rect)
        
        # Alt bilgi metni (ShopScene tarzı küçük detay)
        # Golden Ratio ile konumlandırıl (ekranın en altından φ mesafede)
        info_font = pygame.font.Font(str(Path("v2/assets/fonts") / "BitcountGridDoubleInk.ttf"), 14)
        info_text = "Press ESC to exit"
        info_surf = info_font.render(info_text, True, (120, 120, 140))
        info_rect = info_surf.get_rect(center=(Screen.W // 2, int(Screen.H * 0.95)))
        surface.blit(info_surf, info_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Kullanıcı input'unu işle.
        "YENİ OYUN" butonuna sol fare butonu ile tıklandığında LobbyScene'e geçiş yap.
        Gereksinim 3.1, 3.2, 11.1, 11.2, 11.3, 11.4
        """
        # Mouse button down - start press animation
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                self._btn_pressed = True
        
        # Mouse button up - trigger transition
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._btn_pressed = False
            # Guard clause: _btn_rect None ise (draw() henüz çağrılmadıysa) tıklamayı yoksay
            # Gereksinim 10.3, 11.1, 11.2, 11.3
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                # Lazy import ile LobbyScene'i import et (circular dependency önleme)
                from v2.scenes.lobby import LobbyScene
                # LobbyScene'e fade geçişi başlat (Gereksinim 3.1)
                SceneManager.get().transition_to(LobbyScene())
