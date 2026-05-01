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

# AI stratejilerine özel renkler (oyundaki diğer renklerle çakışmayan özel palet)
STRATEGY_COLORS = {
    "random": (140, 140, 140),      # Açık gri - nötr
    "warrior": (220, 60, 60),       # Parlak kırmızı - saldırgan
    "builder": (80, 180, 100),      # Açık yeşil - bağlantı kurucu
    "evolver": (160, 90, 220),      # Parlak mor - evrimleşen
    "economist": (255, 200, 50),    # Parlak altın - ekonomi
    "balancer": (100, 150, 255),    # Açık mavi - dengeli
    "rare_hunter": (200, 160, 255), # Açık mor/pembe - nadir avcısı
}

# Strateji açıklamaları (tooltip için)
STRATEGY_DESCRIPTIONS = {
    "random": "Random card purchases",
    "warrior": "Aggressive combat focus",
    "builder": "Synergy building strategy",
    "evolver": "Evolution-focused gameplay",
    "economist": "Gold optimization",
    "balancer": "Balanced approach",
    "rare_hunter": "Targets rare cards"
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
        # AI strategies list (7 players) - each AI's selected strategy
        self._ai_strategies = [
            "random",
            "warrior", 
            "builder",
            "evolver",
            "economist",
            "balancer",
            "rare_hunter"
        ]
        
        # All available strategies for dropdown
        self._available_strategies = [
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
        self._font_dropdown = None  # Dropdown font
        
        # Button rect - lazy initialization
        self._btn_rect = None
        
        # Dropdown state
        self._active_dropdown = None  # Which AI's dropdown is open (0-6 or None)
        self._dropdown_rects = []     # Rect for each strategy button (clickable area)
        self._dropdown_item_rects = []  # Rects for dropdown items
        self._hovered_strategy_btn = None  # Which strategy button is hovered (0-6 or None)
        self._hovered_dropdown_item = None  # Which dropdown item is hovered (index or None)
        
        # Audio loader - kept for compatibility with existing audio cleanup logic
        self._audio_loader = None
        
        # Performance: Cache background to avoid redrawing every frame
        self._background_cache = None
        
        # Interactive button state
        self._btn_hovered = False
        self._btn_pressed = False
        self._btn_scale = 1.0  # Scale animation
    
    def update(self, dt_ms: float) -> None:
        """Update button animations and hover states."""
        # Check mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()
        
        # Update start button hover
        if self._btn_rect is not None:
            self._btn_hovered = self._btn_rect.collidepoint(mouse_pos)
        
        # Update strategy button hover
        self._hovered_strategy_btn = None
        for i, rect in enumerate(self._dropdown_rects):
            if rect.collidepoint(mouse_pos):
                self._hovered_strategy_btn = i
                break
        
        # Update dropdown item hover
        self._hovered_dropdown_item = None
        if self._active_dropdown is not None:
            for i, rect in enumerate(self._dropdown_item_rects):
                if rect.collidepoint(mouse_pos):
                    self._hovered_dropdown_item = i
                    break
        
        # Smooth scale animation for start button
        target_scale = 1.06 if self._btn_hovered else 1.0
        if self._btn_pressed:
            target_scale = 0.96
        
        # Lerp towards target scale
        lerp_speed = 0.3
        self._btn_scale += (target_scale - self._btn_scale) * lerp_speed
    
    def _init_fonts(self) -> None:
        """Initialize fonts lazily (only after pygame.init() is called).
        
        This method is idempotent - it only creates fonts if they haven't been
        created yet. This ensures fonts are only initialized after pygame is ready.
        
        Font sizes:
        - Title font: 48pt (for "LOBBY" heading) - BitcountGridDoubleInk
        - Row font: 24pt (for player list rows) - broken-strings.regular
        - Button font: 32pt (for "OYUNA BAŞLA" button) - minimap_category_names
        - Dropdown font: 20pt (for dropdown items) - broken-strings.regular
        
        Validates: Requirements 7.2, 7.3
        """
        if self._font_title is None:
            # Ana başlık: BitcountGridDoubleInk
            font_dir = Path("v2/assets/fonts")
            self._font_title = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 48)
            # Oyuncu listesi: broken-strings.regular (biraz daha büyük)
            self._font_row = pygame.font.Font(str(font_dir / "broken-strings.regular.ttf"), 26)
            # Buton yazısı: minimap_category_names
            self._font_button = pygame.font.Font(str(font_dir / "minimap_category_names.ttf"), 32)
            # Dropdown yazısı: broken-strings.regular
            self._font_dropdown = pygame.font.Font(str(font_dir / "broken-strings.regular.ttf"), 22)
    
    def on_exit(self) -> None:
        """Cleanup resources when exiting the scene.
        
        Nulls out references to allow GC to reclaim memory.
        Validates: Requirement 9.1
        """
        self._audio_loader = None
    
    def _draw_dropdown(self, surface: pygame.Surface, content_padding: int, content_width: int, y_start: int, row_height: int) -> None:
        """Draw the strategy dropdown menu for the active AI.
        
        Args:
            surface: Surface to draw on
            content_padding: Left padding for content
            content_width: Width of content area
            y_start: Y position of first AI row
            row_height: Height of each row
        """
        ai_index = self._active_dropdown
        if ai_index is None or ai_index < 0 or ai_index >= len(self._ai_strategies):
            return
        
        # Calculate dropdown position (below the strategy button)
        row_y = y_start + ai_index * row_height
        dropdown_x = content_padding + 160 - 6  # 150 → 160 (strateji pozisyonuyla aynı)
        dropdown_y = row_y + 38  # 35 → 38 (biraz daha aşağı)
        
        # Dropdown dimensions - broken-strings fontu için ayarlandı
        dropdown_w = 250  # 240 → 250 (biraz daha geniş)
        item_h = 36  # 34 → 36 (biraz daha yüksek)
        dropdown_h = len(self._available_strategies) * item_h + 8  # 8px padding
        
        # Draw dropdown shadow (multiple layers for depth - yumuşak köşeler)
        for i in range(3):
            shadow_offset = 4 + i * 2
            shadow_alpha = 50 - i * 12
            shadow_surf = pygame.Surface((dropdown_w + shadow_offset, dropdown_h + shadow_offset), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, shadow_alpha), shadow_surf.get_rect(), border_radius=16)  # 16px yumuşak köşe
            surface.blit(shadow_surf, (dropdown_x + i * 2, dropdown_y + i * 2))
        
        # Draw dropdown background (yumuşak köşeler)
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_w, dropdown_h)
        pygame.draw.rect(surface, (25, 30, 45), dropdown_rect, border_radius=14)  # 14px yumuşak köşe
        pygame.draw.rect(surface, (100, 150, 255), dropdown_rect, width=2, border_radius=14)  # 14px yumuşak köşe  # Açık mavi border
        
        # Draw dropdown items
        self._dropdown_item_rects = []
        current_strategy = self._ai_strategies[ai_index]
        
        for i, strategy in enumerate(self._available_strategies):
            item_y = dropdown_y + 4 + i * item_h
            item_rect = pygame.Rect(dropdown_x + 4, item_y, dropdown_w - 8, item_h)
            self._dropdown_item_rects.append(item_rect)
            
            # Hover effect (yumuşak köşeler)
            if self._hovered_dropdown_item == i:
                hover_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                strategy_color = STRATEGY_COLORS.get(strategy, GRAY)
                pygame.draw.rect(hover_surf, (*strategy_color, 50), hover_surf.get_rect(), border_radius=10)  # 10px yumuşak köşe
                surface.blit(hover_surf, item_rect.topleft)
            
            # Selected indicator (checkmark)
            if strategy == current_strategy:
                check_surf = self._font_dropdown.render("✓", True, (100, 255, 150))  # Açık yeşil check
                surface.blit(check_surf, (item_rect.x + 10, item_rect.y + 6))  # 5 → 6 (biraz daha aşağı)
            
            # Strategy name
            strategy_color = STRATEGY_COLORS.get(strategy, GRAY)
            strategy_text = strategy.upper()
            strategy_surf = self._font_dropdown.render(strategy_text, True, strategy_color)
            text_x = item_rect.x + 38 if strategy == current_strategy else item_rect.x + 16  # 35/15 → 38/16
            surface.blit(strategy_surf, (text_x, item_rect.y + 8))  # 7 → 8 (biraz daha aşağı)
    
    def _render_background(self) -> pygame.Surface:
        """Render background once and cache it for performance."""
        W = Screen.W
        H = Screen.H
        bg = pygame.Surface((W, H))
        
        # Gradient arka plan (üstten alta)
        for y in range(H):
            ratio = y / H
            r = int(BG_GRADIENT_TOP[0] * (1 - ratio) + BG_GRADIENT_BOTTOM[0] * ratio)
            g = int(BG_GRADIENT_TOP[1] * (1 - ratio) + BG_GRADIENT_BOTTOM[1] * ratio)
            b = int(BG_GRADIENT_TOP[2] * (1 - ratio) + BG_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (W, y))
        
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
                    bg.blit(hex_surf, (x - hex_size, y - hex_size))
        
        # Dekoratif synergy renk çizgileri (solda)
        stripe_width = 6
        synergy_colors = [Colors.MIND, Colors.CONNECTION, Colors.EXISTENCE]
        for i, color in enumerate(synergy_colors):
            y_start = (H // len(synergy_colors)) * i
            y_end = (H // len(synergy_colors)) * (i + 1)
            pygame.draw.rect(bg, color, (0, y_start, stripe_width, y_end - y_start))
        
        return bg
    
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
        
        # Use cached background or render it once
        if self._background_cache is None:
            self._background_cache = self._render_background()
        
        # Blit cached background (much faster than redrawing)
        surface.blit(self._background_cache, (0, 0))
        
        # Draw 7 AI player rows with strategy-specific colors
        # Merkezi layout: satırlar ekranın ortasında, simetrik padding
        content_padding = int(W * 0.08)  # Soldan ve sağdan %8 padding
        content_width = W - 2 * content_padding  # Kullanılabilir genişlik
        row_start_x = content_padding  # Satırların başlangıç x'i
        
        # Draw title "LOBBY" - satırlarla aynı hizada (sol tarafta)
        title_text = "LOBBY"
        title_x = row_start_x + 20  # Satırlarla aynı hizalama (AI numarası ile aynı)
        title_y = 50  # Üstten 50px
        # Glow efekti (ShopScene tarzı çok katmanlı)
        for offset in [4, 2, 0]:
            alpha = 100 if offset > 0 else 255
            glow_color = Colors.MIND if offset > 0 else WHITE
            title_surf = self._font_title.render(title_text, True, glow_color)
            if offset > 0:
                title_surf.set_alpha(alpha)
            surface.blit(title_surf, (title_x + offset, title_y + offset))
        
        # Alt başlık - oyuncu sayısı (başlığın altında, aynı hizada)
        subtitle_font = pygame.font.Font(str(Path("v2/assets/fonts") / "broken-strings.regular.ttf"), 16)
        subtitle_text = "8 Players • 7 AI Strategies"
        subtitle_surf = subtitle_font.render(subtitle_text, True, (150, 150, 170))
        surface.blit(subtitle_surf, (title_x, title_y + 55))  # Başlıktan 55px aşağı
        
        # Satır konumları ve aralıkları
        y_start = title_y + 100  # Başlıktan 100px aşağı (alt başlıktan 45px sonra)
        row_height = 55  # Her satır için sabit yükseklik (daha geniş aralık)
        
        # Clear dropdown rects for this frame
        self._dropdown_rects = []
        
        for i, strategy in enumerate(self._ai_strategies):
            # Format: "AI {i+1} — {strategy}"
            ai_num = f"AI {i+1}"
            strategy_name = strategy.upper()
            row_y = y_start + i * row_height
            
            # Satır arka planı - broken-strings fontu için ayarlandı (yumuşak köşeler)
            row_bg_height = 44  # Biraz daha yüksek (font daha büyük)
            row_bg_y = row_y - 6  # Yazıların biraz daha üstünden başla
            row_rect = pygame.Rect(row_start_x, row_bg_y, content_width, row_bg_height)
            pygame.draw.rect(surface, (20, 25, 35, 80), row_rect, border_radius=12)  # 12px yumuşak köşe
            
            # AI numarası (gri) - daha sola hizalı
            num_surf = self._font_row.render(ai_num, True, GRAY)
            surface.blit(num_surf, (row_start_x + 20, row_y))
            
            # Ayırıcı - AI numarasından sonra
            sep_surf = self._font_row.render("—", True, GRAY)
            surface.blit(sep_surf, (row_start_x + 105, row_y))  # 100 → 105 (biraz daha sağda)
            
            # Strateji butonu (tıklanabilir dropdown trigger)
            strategy_color = STRATEGY_COLORS.get(strategy, GRAY)
            strategy_surf = self._font_row.render(strategy_name, True, strategy_color)
            strategy_x = row_start_x + 160  # 150 → 160 (biraz daha sağda)
            strategy_y = row_y
            
            # Dropdown button rect (clickable area) - font boyutuna göre ayarlandı
            dropdown_btn_w = strategy_surf.get_width() + 45  # 40 → 45 (biraz daha geniş)
            dropdown_btn_h = strategy_surf.get_height() + 6  # 4 → 6 (biraz daha yüksek)
            dropdown_btn_rect = pygame.Rect(strategy_x - 6, strategy_y - 3, dropdown_btn_w, dropdown_btn_h)
            self._dropdown_rects.append(dropdown_btn_rect)
            
            # Hover effect on strategy button (yumuşak köşeler) - broken-strings fontu için
            if self._hovered_strategy_btn == i:
                hover_surf = pygame.Surface((dropdown_btn_w, dropdown_btn_h), pygame.SRCALPHA)
                pygame.draw.rect(hover_surf, (*strategy_color, 35), hover_surf.get_rect(), border_radius=10)  # 30 → 35 alpha, 8 → 10 radius
                surface.blit(hover_surf, dropdown_btn_rect.topleft)
            
            # Draw strategy name
            surface.blit(strategy_surf, (strategy_x, strategy_y))
            
            # Draw dropdown arrow (▼)
            arrow_color = strategy_color if self._hovered_strategy_btn == i else GRAY
            arrow_surf = self._font_row.render("▼", True, arrow_color)
            arrow_surf = pygame.transform.scale(arrow_surf, (int(arrow_surf.get_width() * 0.6), int(arrow_surf.get_height() * 0.6)))
            surface.blit(arrow_surf, (strategy_x + strategy_surf.get_width() + 8, strategy_y + 4))
        
        # Draw human player row (8th row) with special styling - BEFORE dropdown
        human_y = y_start + 7 * row_height
        
        # Oyuncu satırı için arka plan highlight - broken-strings fontu için ayarlandı
        human_bg_height = 48  # 44 → 48 (biraz daha yüksek)
        human_bg_y = human_y - 8  # 6 → 8 (biraz daha üstten)
        highlight_rect = pygame.Rect(row_start_x, human_bg_y, content_width, human_bg_height)
        
        # Glow katmanları (yumuşak köşeler)
        for i in range(2):
            glow_inflate = 6 - i * 3
            glow_rect = highlight_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = 30 + i * 20
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*CYAN, glow_alpha), 
                           glow_surf.get_rect(), border_radius=16)  # 16px yumuşak köşe
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Ana arka plan (yumuşak köşeler)
        pygame.draw.rect(surface, (30, 40, 60), highlight_rect, border_radius=14)  # 14px yumuşak köşe
        pygame.draw.rect(surface, CYAN, highlight_rect, width=2, border_radius=14)  # 14px yumuşak köşe
        
        # "► SEN — HUMAN" kısmı - broken-strings fontu için ayarlandı
        arrow_surf = self._font_row.render("►", True, CYAN)
        surface.blit(arrow_surf, (row_start_x + 20, human_y))
        
        sen_surf = self._font_row.render("SEN", True, CYAN)
        surface.blit(sen_surf, (row_start_x + 60, human_y))  # 55 → 60 (biraz daha sağda)
        
        # Ayırıcı
        sep_surf = self._font_row.render("—", True, GRAY)  # CYAN → GRAY (daha az vurgulu)
        surface.blit(sep_surf, (row_start_x + 125, human_y))  # 115 → 125 (biraz daha sağda)
        
        # İnsan oyuncu adı
        human_surf = self._font_row.render(self._human_name, True, WHITE)
        surface.blit(human_surf, (row_start_x + 175, human_y))  # 160 → 175 (biraz daha sağda)
        
        # Draw active dropdown AFTER human row (so it appears on top)
        if self._active_dropdown is not None:
            self._draw_dropdown(surface, content_padding, content_width, y_start, row_height)
        
        # Draw "OYUNA BAŞLA" button at bottom with centered layout
        # Buton merkeze ve simetrik layout ile konumlandırıl (satırlardan sonra)
        btn_w = 280
        btn_h = 70
        btn_x = W // 2 - btn_w // 2  # Merkeze hizala
        btn_y = int(H * 0.88)  # Ekranın %88'sinde (daha aşağı)
        
        # Update button rect for click detection
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
        
        # Buton glow efekti (daha güçlü hover'da - yumuşak köşeler)
        glow_intensity = 1.6 if self._btn_hovered else 1.0
        for i in range(3):
            glow_inflate = int((12 - i * 4) * glow_intensity)
            glow_rect = scaled_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = int((40 + i * 20) * glow_intensity)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*Colors.CONNECTION, min(glow_alpha, 255)), 
                           glow_surf.get_rect(), border_radius=18)  # 18px yumuşak köşe
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Buton arka planı (gradient - daha parlak hover'da)
        btn_surf = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)
        brightness_boost = 1.2 if self._btn_hovered else 1.0
        for y in range(scaled_h):
            ratio = y / scaled_h
            r = int(Colors.CONNECTION[0] * (1 - ratio * 0.3) * brightness_boost)
            g = int(Colors.CONNECTION[1] * (1 - ratio * 0.3) * brightness_boost)
            b = int(Colors.CONNECTION[2] * (1 - ratio * 0.3) * brightness_boost)
            pygame.draw.line(btn_surf, (min(r, 255), min(g, 255), min(b, 255)), (0, y), (scaled_w, y))
        
        # Buton border (hover'da daha kalın - yumuşak köşeler)
        border_width = 4 if self._btn_hovered else 3
        border_color = (255, 255, 255) if self._btn_hovered else WHITE
        pygame.draw.rect(btn_surf, border_color, btn_surf.get_rect(), width=border_width, border_radius=16)  # 16px yumuşak köşe
        surface.blit(btn_surf, scaled_rect.topleft)
        
        # Buton metni (beyaz, kalın)
        btn_text_surf = self._font_button.render("OYUNA BAŞLA", True, WHITE)
        btn_text_rect = btn_text_surf.get_rect(center=scaled_rect.center)
        surface.blit(btn_text_surf, btn_text_rect)
        
        # Alt bilgi metni (ShopScene tarzı küçük detay)
        # Golden Ratio ile konumlandırıl (ekranın en altında)
        info_font = pygame.font.Font(str(Path("v2/assets/fonts") / "broken-strings.regular.ttf"), 13)
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
        
        Handles:
        - Strategy dropdown clicks (open/close dropdown, select strategy)
        - Start button clicks (initialize game and transition to ShopScene)
        
        When the user clicks the "OYUNA BAŞLA" button with the left mouse button:
        1. Calls _bootstrap() to initialize the game engine and create GameState
        2. Transitions to ShopScene with the GameState
        
        Uses lazy imports for both _bootstrap and ShopScene to avoid circular
        dependencies. This is the critical point where heavy engine initialization
        happens (lazy loading pattern).
        
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
        """
        # Mouse button down - start press animation
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if start button was clicked
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                self._btn_pressed = True
                return
            
            # PRIORITY 1: Check if a dropdown item was clicked (highest priority)
            if self._active_dropdown is not None:
                for i, rect in enumerate(self._dropdown_item_rects):
                    if rect.collidepoint(event.pos):
                        # Update the AI's strategy
                        self._ai_strategies[self._active_dropdown] = self._available_strategies[i]
                        # Close dropdown
                        self._active_dropdown = None
                        return
                
                # Click outside dropdown - close it
                self._active_dropdown = None
                return
            
            # PRIORITY 2: Check if a strategy button was clicked (toggle dropdown)
            for i, rect in enumerate(self._dropdown_rects):
                if rect.collidepoint(event.pos):
                    # Toggle dropdown for this AI
                    if self._active_dropdown == i:
                        self._active_dropdown = None  # Close if already open
                    else:
                        self._active_dropdown = i  # Open dropdown
                    return
        
        # Mouse button up - trigger transition
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._btn_pressed = False
            # Guard clause: ensure button rect is initialized
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                # Lazy import to avoid circular dependencies
                from v2.main import _bootstrap
                
                # Initialize game engine and create GameState
                # Pass the selected AI strategies to bootstrap
                gs = _bootstrap(ai_strategies=self._ai_strategies)
                
                # Lazy import ShopScene
                from v2.scenes.shop import ShopScene
                
                # Transition to ShopScene with GameState
                from v2.core.scene_manager import SceneManager
                SceneManager.get().transition_to(ShopScene(gs))
