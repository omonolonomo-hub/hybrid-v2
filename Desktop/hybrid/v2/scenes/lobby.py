"""
LobbyScene: Displays 7 AI players with their strategies and 1 human player.
Validates: Requirements 4.7, 7.1
"""

import pygame
from pathlib import Path
from v2.core.scene_manager import Scene
from v2.constants import Screen, Colors

# Color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
CYAN = (0, 255, 255)
BG_DARK = (12, 12, 18)
BG_GRADIENT_TOP = (25, 20, 35)
BG_GRADIENT_BOTTOM = (15, 25, 40)

# Altın Oran (Golden Ratio)
GOLDEN_RATIO = 1.618

# AI stratejilerine özel renkler (synergy gruplarından)
STRATEGY_COLORS = {
    "random": (150, 150, 150),      # Gri - nötr
    "warrior": Colors.EXISTENCE,     # Kırmızı - saldırgan
    "builder": Colors.CONNECTION,    # Yeşil - bağlantı kurucu
    "evolver": (180, 100, 255),     # Mor - evrimleşen
    "economist": Colors.GOLD_TEXT,   # Altın - ekonomi
    "balancer": Colors.MIND,         # Mavi - dengeli
    "rare_hunter": Colors.PLATINUM,  # Platin - nadir avcısı
}


class LobbyScene(Scene):
    """
    Lobby screen showing player list (7 AI + 1 human) and start button.
    
    Fields are initialized as None for lazy loading to avoid pygame initialization
    issues before the display is ready.
    """
    
    def __init__(self):
        """Initialize LobbyScene with lazy-loaded resources.
        
        Requirements:
        - 7 AI strategies: ["random", "warrior", "builder", "evolver", 
                           "economist", "balancer", "rare_hunter"]
        - Human player name: "HUMAN"
        - All fonts initialized as None (lazy init)
        - Button rect initialized as None (lazy init)
        - Audio loader kept for compatibility with existing cleanup logic
        """
        # AI strategies list (7 players)
        self._strategies = [
            "random",
            "warrior", 
            "builder",
            "evolver",
            "economist",
            "balancer",
            "rare_hunter"
        ]
        
        # Human player name
        self._human_name = "HUMAN"
        
        # Font fields - lazy initialization
        self._font_title = None
        self._font_row = None
        self._font_button = None
        
        # Button rect - lazy initialization
        self._btn_rect = None
        
        # Audio loader - kept for compatibility with existing audio cleanup logic
        self._audio_loader = None
    
    def _init_fonts(self) -> None:
        """Initialize fonts lazily (only after pygame.init() is called).
        
        This method is idempotent - it only creates fonts if they haven't been
        created yet. This ensures fonts are only initialized after pygame is ready.
        
        Font sizes:
        - Title font: 48pt (for "LOBİ" heading)
        - Row font: 28pt (for player list rows)
        - Button font: 32pt (for "OYUNA BAŞLA" button)
        
        Validates: Requirements 7.2, 7.3
        """
        if self._font_title is None:
            # Ana başlık: BitcountGridDoubleInk
            font_dir = Path("v2/assets/fonts")
            self._font_title = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 48)
            # Oyuncu listesi: BitcountGridDoubleInk
            self._font_row = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 28)
            # Buton yazısı: minimap_category_names
            self._font_button = pygame.font.Font(str(font_dir / "minimap_category_names.ttf"), 32)
    
    def on_exit(self) -> None:
        """Cleanup resources when exiting the scene.
        
        Nulls out references to allow GC to reclaim memory.
        Validates: Requirement 9.1
        """
        self._audio_loader = None
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the lobby screen with player list and start button.
        
        Layout:
        - Gradient background with hex pattern
        - "LOBİ" title at (40, 30)
        - 7 AI rows: "AI {i+1} — {strategy}" with strategy-specific colors
        - 8th row: "► SEN — {_human_name}" in CYAN
        - "OYUNA BAŞLA" button at bottom-right with glow effect
        - Info text at bottom
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        """
        # Initialize fonts if needed
        self._init_fonts()
        
        # Get screen dimensions
        W = Screen.W
        H = Screen.H
        
        # Gradient arka plan (üstten alta)
        for y in range(H):
            ratio = y / H
            r = int(BG_GRADIENT_TOP[0] * (1 - ratio) + BG_GRADIENT_BOTTOM[0] * ratio)
            g = int(BG_GRADIENT_TOP[1] * (1 - ratio) + BG_GRADIENT_BOTTOM[1] * ratio)
            b = int(BG_GRADIENT_TOP[2] * (1 - ratio) + BG_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (W, y))
        
        # Dekoratif hex pattern (arka planda, ShopScene tarzı)
        import math
        hex_size = 35
        hex_alpha = 12
        for row in range(0, H // hex_size + 2):
            for col in range(0, W // hex_size + 2):
                x = col * hex_size * 1.5
                y = row * hex_size * math.sqrt(3) + (hex_size * math.sqrt(3) / 2 if col % 2 else 0)
                
                # Hex çizimi
                points = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    px = x + hex_size * 0.4 * math.cos(angle)
                    py = y + hex_size * 0.4 * math.sin(angle)
                    points.append((px, py))
                
                # Sadece border çiz
                if len(points) >= 3:
                    hex_surf = pygame.Surface((hex_size * 2, hex_size * 2), pygame.SRCALPHA)
                    offset_points = [(px - x + hex_size, py - y + hex_size) for px, py in points]
                    pygame.draw.polygon(hex_surf, (*Colors.CONNECTION, hex_alpha), offset_points, width=1)
                    surface.blit(hex_surf, (x - hex_size, y - hex_size))
        
        # Dekoratif synergy renk çizgileri (solda)
        stripe_width = 6
        synergy_colors = [Colors.MIND, Colors.CONNECTION, Colors.EXISTENCE]
        for i, color in enumerate(synergy_colors):
            y_start = (H // len(synergy_colors)) * i
            y_end = (H // len(synergy_colors)) * (i + 1)
            pygame.draw.rect(surface, color, (0, y_start, stripe_width, y_end - y_start))
        
        # Draw title "LOBİ" at Golden Ratio position with glow
        title_text = "LOBİ"
        # Golden Ratio: başlık ekranın üst kısmına φ ile konumlandırıl
        title_x = int(Screen.W * (1 - 1 / GOLDEN_RATIO))  # Sağdan φ mesafesi
        title_y = int(Screen.H / GOLDEN_RATIO * 0.15)  # Üstten φ'nin 15%'i
        # Glow efekti (ShopScene tarzı çok katmanlı)
        for offset in [4, 2, 0]:
            alpha = 100 if offset > 0 else 255
            glow_color = Colors.MIND if offset > 0 else WHITE
            title_surf = self._font_title.render(title_text, True, glow_color)
            if offset > 0:
                title_surf.set_alpha(alpha)
            surface.blit(title_surf, (title_x + offset, title_y + offset))
        
        # Alt başlık - oyuncu sayısı
        # Golden Ratio ile konumlandırıl (başlığın altında)
        subtitle_font = pygame.font.Font(str(Path("v2/assets/fonts") / "BitcountGridDoubleInk.ttf"), 18)
        subtitle_text = "8 Players • 7 AI Strategies"
        subtitle_surf = subtitle_font.render(subtitle_text, True, (150, 150, 170))
        surface.blit(subtitle_surf, (title_x, int(title_y + Screen.H / GOLDEN_RATIO * 0.08)))
        
        # Draw 7 AI player rows with strategy-specific colors
        # Merkezi layout: satırlar ekranın ortasında, simetrik padding
        content_padding = int(W * 0.08)  # Soldan ve sağdan %8 padding
        content_width = W - 2 * content_padding  # Kullanılabilir genişlik
        row_start_x = content_padding  # Satırların başlangıç x'i
        
        # Satır konumları ve aralıkları
        y_start = int(title_y + Screen.H * 0.08)  # Başlığın %8 altında
        row_height = int(Screen.H / 11)  # Her satır için aşağı doğru alan
        
        for i, strategy in enumerate(self._strategies):
            # Format: "AI {i+1} — {strategy}"
            ai_num = f"AI {i+1}"
            strategy_name = strategy.upper()
            row_y = y_start + i * row_height
            
            # Satır arka planı (hover efekti için hazır)
            row_rect = pygame.Rect(row_start_x, row_y, content_width, int(row_height * 0.6))
            pygame.draw.rect(surface, (20, 25, 35, 80), row_rect, border_radius=6)
            
            # AI numarası (gri)
            num_surf = self._font_row.render(ai_num, True, GRAY)
            surface.blit(num_surf, (row_start_x + int(content_width * 0.05), row_y))
            
            # Ayırıcı
            sep_surf = self._font_row.render("—", True, GRAY)
            surface.blit(sep_surf, (row_start_x + int(content_width * 0.15), row_y))
            
            # Strateji adı (renkli)
            strategy_color = STRATEGY_COLORS.get(strategy, GRAY)
            strategy_surf = self._font_row.render(strategy_name, True, strategy_color)
            surface.blit(strategy_surf, (row_start_x + int(content_width * 0.25), row_y))
            
            # Strateji ikonları (küçük renkli kareler, ShopScene tarzı)
            icon_x = row_start_x + int(content_width * 0.85)
            icon_y = row_y + int(row_height * 0.12)
            # Outer glow
            glow_rect = pygame.Rect(icon_x - 2, icon_y - 2, 16, 16)
            pygame.draw.rect(surface, (*strategy_color, 60), glow_rect, border_radius=3)
            # Inner square
            pygame.draw.rect(surface, strategy_color, (icon_x, icon_y, 12, 12), border_radius=2)
        
        # Draw human player row (8th row) with special styling
        human_y = y_start + 7 * row_height
        
        # Oyuncu satırı için arka plan highlight (ShopScene tarzı çok katmanlı)
        highlight_rect = pygame.Rect(row_start_x, human_y, content_width, int(row_height * 0.6))
        
        # Glow katmanları
        for i in range(2):
            glow_inflate = 6 - i * 3
            glow_rect = highlight_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = 30 + i * 20
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*CYAN, glow_alpha), 
                           glow_surf.get_rect(), border_radius=10)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Ana arka plan
        pygame.draw.rect(surface, (30, 40, 60), highlight_rect, border_radius=8)
        pygame.draw.rect(surface, CYAN, highlight_rect, width=2, border_radius=8)
        
        # "► SEN" kısmı
        arrow_surf = self._font_row.render("►", True, CYAN)
        surface.blit(arrow_surf, (row_start_x + int(content_width * 0.05), human_y))
        
        sen_surf = self._font_row.render("SEN", True, CYAN)
        surface.blit(sen_surf, (row_start_x + int(content_width * 0.12), human_y))
        
        # Ayırıcı
        sep_surf = self._font_row.render("—", True, CYAN)
        surface.blit(sep_surf, (row_start_x + int(content_width * 0.15), human_y))
        
        # İnsan oyuncu adı
        human_surf = self._font_row.render(self._human_name, True, WHITE)
        surface.blit(human_surf, (row_start_x + int(content_width * 0.25), human_y))
        
        # Draw "OYUNA BAŞLA" button at bottom with centered layout
        # Buton merkeze ve simetrik layout ile konumlandırıl (satırlardan sonra)
        btn_w = 280
        btn_h = 70
        btn_x = W // 2 - btn_w // 2  # Merkeze hizala
        btn_y = int(H * 0.88)  # Ekranın %88'sinde (daha aşağı)
        
        # Update button rect for click detection
        self._btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        # Buton glow efekti (ShopScene tarzı çok katmanlı)
        for i in range(3):
            glow_inflate = 12 - i * 4
            glow_rect = self._btn_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = 40 + i * 20
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*Colors.CONNECTION, glow_alpha), 
                           glow_surf.get_rect(), border_radius=12)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Buton arka planı (gradient)
        btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        for y in range(btn_h):
            ratio = y / btn_h
            r = int(Colors.CONNECTION[0] * (1 - ratio * 0.3))
            g = int(Colors.CONNECTION[1] * (1 - ratio * 0.3))
            b = int(Colors.CONNECTION[2] * (1 - ratio * 0.3))
            pygame.draw.line(btn_surf, (r, g, b), (0, y), (btn_w, y))
        
        # Buton border
        pygame.draw.rect(btn_surf, WHITE, btn_surf.get_rect(), width=3, border_radius=10)
        surface.blit(btn_surf, self._btn_rect.topleft)
        
        # Buton metni (beyaz, kalın)
        btn_text_surf = self._font_button.render("OYUNA BAŞLA", True, WHITE)
        btn_text_rect = btn_text_surf.get_rect(center=self._btn_rect.center)
        surface.blit(btn_text_surf, btn_text_rect)
        
        # Alt bilgi metni (ShopScene tarzı küçük detay)
        # Golden Ratio ile konumlandırıl (ekranın en altında)
        info_font = pygame.font.Font(str(Path("v2/assets/fonts") / "BitcountGridDoubleInk.ttf"), 14)
        info_parts = [
            ("Click ", (120, 120, 140)),
            ("OYUNA BAŞLA", Colors.CONNECTION),
            (" to initialize game engine", (120, 120, 140))
        ]
        
        info_x = 40
        info_y = int(H * 0.95)  # Ekranın %95'i
        for text, color in info_parts:
            info_surf = info_font.render(text, True, color)
            surface.blit(info_surf, (info_x, info_y))
            info_x += info_surf.get_width()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input events for the lobby screen.
        
        When the user clicks the "OYUNA BAŞLA" button with the left mouse button:
        1. Calls _bootstrap() to initialize the game engine and create GameState
        2. Transitions to ShopScene with the GameState
        
        Uses lazy imports for both _bootstrap and ShopScene to avoid circular
        dependencies. This is the critical point where heavy engine initialization
        happens (lazy loading pattern).
        
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
        """
        # Only handle left mouse button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Guard clause: ensure button rect is initialized
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                # Lazy import to avoid circular dependencies
                from v2.main import _bootstrap
                
                # Initialize game engine and create GameState
                gs = _bootstrap()
                
                # Lazy import ShopScene
                from v2.scenes.shop import ShopScene
                
                # Transition to ShopScene with GameState
                from v2.core.scene_manager import SceneManager
                SceneManager.get().transition_to(ShopScene(gs))
