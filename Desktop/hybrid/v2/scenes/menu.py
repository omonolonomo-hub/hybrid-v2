"""
MenuScene - İlk açılış ekranı
Gereksinim 2: Menü Ekranı Görüntüleme

Gelişmiş görsel efektler:
- Parçacık sistemi
- Animasyonlu arka plan
- Geometrik şekiller ve glow efektleri
"""

import pygame
import math
import random
from pathlib import Path
from v2.core.scene_manager import Scene, SceneManager
from v2.constants import Screen, Colors

# Renkler - Synergy gruplarından ilham alınmış
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_DARK = (12, 12, 18)
BG_GRADIENT_TOP = (20, 25, 40)
BG_GRADIENT_BOTTOM = (35, 15, 45)

# Altın Oran (Golden Ratio)
GOLDEN_RATIO = 1.618

# Kategori renkleri
CATEGORY_COLORS = {
    "Mythology & Gods": (248, 222, 34),
    "Art & Culture": (209, 32, 82),
    "Nature & Creatures": (35, 114, 39),
    "Cosmos": (80, 50, 180),
    "Science": (3, 174, 210),
    "History & Civilizations": (244, 91, 38),
}


class Particle:
    """Arka plan parçacık efekti için basit parçacık sınıfı."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, color: tuple[int, int, int], size: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.alpha = random.randint(30, 120)
        self.life = random.uniform(0.5, 1.0)
    
    def update(self, dt: float) -> bool:
        """Parçacığı güncelle. False dönerse parçacık ölmüştür."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt * 0.2
        return self.life > 0
    
    def draw(self, surface: pygame.Surface) -> None:
        """Parçacığı çiz."""
        if self.life <= 0:
            return
        alpha = int(self.alpha * self.life)
        if alpha < 5:
            return
        
        # Glow efekti için 3 katman
        for i in range(3):
            radius = self.size * (1 + i * 0.5)
            glow_alpha = alpha // (i + 1)
            if glow_alpha < 5:
                continue
            
            glow_surf = pygame.Surface((int(radius * 4), int(radius * 4)), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (*self.color, glow_alpha),
                (int(radius * 2), int(radius * 2)),
                int(radius)
            )
            surface.blit(glow_surf, (int(self.x - radius * 2), int(self.y - radius * 2)))


class FloatingShape:
    """Arka planda yüzen geometrik şekiller."""
    
    def __init__(self):
        self.x = random.uniform(0, Screen.W)
        self.y = random.uniform(0, Screen.H)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-15, 15)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-30, 30)
        self.size = random.uniform(20, 60)
        self.shape_type = random.choice(['hex', 'triangle', 'square'])
        colors = list(CATEGORY_COLORS.values())
        self.color = random.choice(colors)
        self.alpha = random.randint(15, 40)
    
    def update(self, dt: float) -> None:
        """Şekli güncelle."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        
        # Ekran sınırlarında zıpla
        if self.x < -self.size or self.x > Screen.W + self.size:
            self.vx *= -1
        if self.y < -self.size or self.y > Screen.H + self.size:
            self.vy *= -1
    
    def draw(self, surface: pygame.Surface) -> None:
        """Şekli çiz."""
        shape_surf = pygame.Surface((int(self.size * 3), int(self.size * 3)), pygame.SRCALPHA)
        center = (int(self.size * 1.5), int(self.size * 1.5))
        
        if self.shape_type == 'hex':
            points = []
            for i in range(6):
                angle = math.radians(60 * i + self.rotation)
                px = center[0] + self.size * math.cos(angle)
                py = center[1] + self.size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(shape_surf, (*self.color, self.alpha), points, width=2)
        
        elif self.shape_type == 'triangle':
            points = []
            for i in range(3):
                angle = math.radians(120 * i + self.rotation)
                px = center[0] + self.size * math.cos(angle)
                py = center[1] + self.size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(shape_surf, (*self.color, self.alpha), points, width=2)
        
        elif self.shape_type == 'square':
            angle_rad = math.radians(self.rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            half = self.size
            corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
            points = []
            for cx, cy in corners:
                rx = cx * cos_a - cy * sin_a + center[0]
                ry = cx * sin_a + cy * cos_a + center[1]
                points.append((rx, ry))
            pygame.draw.polygon(shape_surf, (*self.color, self.alpha), points, width=2)
        
        surface.blit(shape_surf, (int(self.x - self.size * 1.5), int(self.y - self.size * 1.5)))


class MenuScene(Scene):
    """
    Opening screen. Shows the "AUTOCHESS HYBRID" title and "NEW GAME" button.
    
    Gelişmiş görsel efektler ile zenginleştirilmiş.
    """
    
    def __init__(self):
        """Constructor."""
        super().__init__()
        self._font_title: pygame.font.Font | None = None
        self._font_button: pygame.font.Font | None = None
        self._btn_rect: pygame.Rect | None = None
        self._background_cache: pygame.Surface | None = None
        self._btn_hovered: bool = False
        self._btn_pressed: bool = False
        self._btn_scale: float = 1.0
        
        # Animasyon zamanı
        self._time: float = 0.0
        
        # Parçacık sistemi
        self._particles: list[Particle] = []
        self._particle_spawn_timer: float = 0.0
        
        # Yüzen şekiller
        self._shapes: list[FloatingShape] = []
        for _ in range(8):
            self._shapes.append(FloatingShape())
        
        # Buton ripple efekti
        self._ripples: list[tuple[float, float, float]] = []  # (x, y, time)

    def update(self, dt_ms: float) -> None:
        """Update animasyonları ve efektleri."""
        dt = dt_ms / 1000.0
        self._time += dt
        
        # Mouse pozisyonu ve hover kontrolü
        mouse_pos = pygame.mouse.get_pos()
        if self._btn_rect is not None:
            self._btn_hovered = self._btn_rect.collidepoint(mouse_pos)
        
        # Buton scale animasyonu
        target_scale = 1.08 if self._btn_hovered else 1.0
        if self._btn_pressed:
            target_scale = 0.95
        lerp_speed = 0.3
        self._btn_scale += (target_scale - self._btn_scale) * lerp_speed
        
        # Parçacık spawn
        self._particle_spawn_timer += dt
        if self._particle_spawn_timer > 0.1:
            self._particle_spawn_timer = 0.0
            if len(self._particles) < 100:
                x = random.uniform(0, Screen.W)
                y = Screen.H + 10
                vx = random.uniform(-20, 20)
                vy = random.uniform(-80, -40)
                colors = list(CATEGORY_COLORS.values())
                color = random.choice(colors)
                size = random.uniform(1, 3)
                self._particles.append(Particle(x, y, vx, vy, color, size))
        
        # Parçacık güncelleme
        self._particles = [p for p in self._particles if p.update(dt)]
        
        # Şekil güncelleme
        for shape in self._shapes:
            shape.update(dt)
        
        # Ripple güncelleme
        self._ripples = [(x, y, t + dt) for x, y, t in self._ripples if t < 1.0]
    
    def _init_fonts(self) -> None:
        """Fontları lazy init ile yükle."""
        if self._font_title is None:
            font_dir = Path("v2/assets/fonts")
            self._font_title = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 72)
            self._font_button = pygame.font.Font(str(font_dir / "BitcountGridDoubleInk.ttf"), 36)

    def _render_background(self) -> pygame.Surface:
        """Statik arka plan render et (cache için)."""
        bg = pygame.Surface((Screen.W, Screen.H))
        
        # Gradient arka plan
        for y in range(Screen.H):
            ratio = y / Screen.H
            r = int(BG_GRADIENT_TOP[0] * (1 - ratio) + BG_GRADIENT_BOTTOM[0] * ratio)
            g = int(BG_GRADIENT_TOP[1] * (1 - ratio) + BG_GRADIENT_BOTTOM[1] * ratio)
            b = int(BG_GRADIENT_TOP[2] * (1 - ratio) + BG_GRADIENT_BOTTOM[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (Screen.W, y))
        
        # Dekoratif kategori renk çizgileri
        category_colors = list(CATEGORY_COLORS.values())
        stripe_height = 4
        stripe_y = 0
        for i, color in enumerate(category_colors):
            x_start = (Screen.W // len(category_colors)) * i
            x_end = (Screen.W // len(category_colors)) * (i + 1)
            pygame.draw.rect(bg, color, (x_start, stripe_y, x_end - x_start, stripe_height))
        
        return bg
    
    def _draw_animated_waves(self, surface: pygame.Surface) -> None:
        """Animasyonlu dalga efektleri çiz."""
        wave_count = 3
        for i in range(wave_count):
            wave_y = Screen.H * 0.3 + i * 80
            wave_amplitude = 30 + i * 10
            wave_frequency = 0.01 + i * 0.005
            wave_speed = 0.5 + i * 0.2
            
            points = []
            for x in range(0, Screen.W + 10, 10):
                y = wave_y + math.sin((x * wave_frequency) + (self._time * wave_speed)) * wave_amplitude
                points.append((x, y))
            
            if len(points) > 1:
                wave_surf = pygame.Surface((Screen.W, Screen.H), pygame.SRCALPHA)
                alpha = 15 + i * 5
                color = (*Colors.MIND, alpha)
                pygame.draw.lines(wave_surf, color, False, points, 2)
                surface.blit(wave_surf, (0, 0))

    def draw(self, surface: pygame.Surface) -> None:
        """Menü ekranını render et."""
        self._init_fonts()
        
        # Cached background
        if self._background_cache is None:
            self._background_cache = self._render_background()
        surface.blit(self._background_cache, (0, 0))
        
        # Yüzen şekiller
        for shape in self._shapes:
            shape.draw(surface)
        
        # Animasyonlu dalgalar
        self._draw_animated_waves(surface)
        
        # Parçacıklar
        for particle in self._particles:
            particle.draw(surface)
        
        # Başlık - pulse efekti ile
        title_text = "AUTOCHESS HYBRID"
        title_y = int(Screen.H * (1 / GOLDEN_RATIO))
        
        # Pulse efekti
        pulse = 1.0 + math.sin(self._time * 2.0) * 0.05
        title_scale = int(72 * pulse)
        title_font = pygame.font.Font(str(Path("v2/assets/fonts") / "BitcountGridDoubleInk.ttf"), title_scale)
        
        # Glow efekti (daha güçlü)
        for offset in [6, 4, 2, 0]:
            if offset > 0:
                alpha = 60 + int(20 * math.sin(self._time * 3.0))
                glow_color = (*Colors.MIND[:3], alpha)
                title_surf = title_font.render(title_text, True, glow_color)
                title_surf.set_alpha(alpha)
            else:
                title_surf = title_font.render(title_text, True, WHITE)
            
            title_rect = title_surf.get_rect(center=(Screen.W // 2, title_y + offset))
            surface.blit(title_surf, title_rect)
        
        # Alt başlık
        subtitle_font = pygame.font.Font(str(Path("v2/assets/fonts") / "minimap_category_names.ttf"), 24)
        subtitle_parts = [
            ("MIND", Colors.MIND),
            (" • ", WHITE),
            ("CONNECTION", Colors.CONNECTION),
            (" • ", WHITE),
            ("EXISTENCE", Colors.EXISTENCE)
        ]
        
        subtitle_surfaces = []
        total_width = 0
        for text, color in subtitle_parts:
            surf = subtitle_font.render(text, True, color)
            subtitle_surfaces.append(surf)
            total_width += surf.get_width()
        
        subtitle_y = title_y + int(Screen.H * 0.05)
        subtitle_x = Screen.W // 2 - total_width // 2
        
        for surf in subtitle_surfaces:
            surface.blit(surf, (subtitle_x, subtitle_y))
            subtitle_x += surf.get_width()
        
        # Buton
        btn_w, btn_h = 240, 60
        btn_x = Screen.W // 2 - btn_w // 2
        btn_y = int(Screen.H * 0.75)
        self._btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        # Scale animasyonu
        scaled_w = int(btn_w * self._btn_scale)
        scaled_h = int(btn_h * self._btn_scale)
        scaled_rect = pygame.Rect(
            btn_x + (btn_w - scaled_w) // 2,
            btn_y + (btn_h - scaled_h) // 2,
            scaled_w,
            scaled_h
        )
        
        # Ripple efektleri
        for rx, ry, rt in self._ripples:
            ripple_radius = int(rt * 150)
            ripple_alpha = int((1.0 - rt) * 100)
            if ripple_alpha > 5:
                ripple_surf = pygame.Surface((ripple_radius * 2, ripple_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    ripple_surf,
                    (*Colors.MIND, ripple_alpha),
                    (ripple_radius, ripple_radius),
                    ripple_radius,
                    width=3
                )
                surface.blit(ripple_surf, (int(rx - ripple_radius), int(ry - ripple_radius)))
        
        # Buton glow
        glow_intensity = 1.5 if self._btn_hovered else 1.0
        for i in range(4):
            glow_inflate = int((16 - i * 4) * glow_intensity)
            glow_rect = scaled_rect.inflate(glow_inflate, glow_inflate)
            glow_alpha = int((30 + i * 15) * glow_intensity)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*Colors.MIND, min(glow_alpha, 255)), 
                           glow_surf.get_rect(), border_radius=12)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Buton rengi
        btn_color = (240, 245, 255) if self._btn_hovered else WHITE
        pygame.draw.rect(surface, btn_color, scaled_rect, border_radius=8)
        
        # Border
        border_width = 3 if self._btn_hovered else 2
        border_color = Colors.MIND
        if self._btn_hovered:
            border_color = (min(Colors.MIND[0] + 30, 255), min(Colors.MIND[1] + 30, 255), min(Colors.MIND[2] + 50, 255))
        pygame.draw.rect(surface, border_color, scaled_rect, width=border_width, border_radius=8)
        
        # Buton metni
        btn_text_surf = self._font_button.render("NEW GAME", True, Colors.MIND)
        btn_text_rect = btn_text_surf.get_rect(center=scaled_rect.center)
        surface.blit(btn_text_surf, btn_text_rect)
        
        # Alt bilgi
        info_font = pygame.font.Font(str(Path("v2/assets/fonts") / "BitcountGridDoubleInk.ttf"), 14)
        info_text = "Press ESC to exit"
        info_surf = info_font.render(info_text, True, (120, 120, 140))
        info_rect = info_surf.get_rect(center=(Screen.W // 2, int(Screen.H * 0.95)))
        surface.blit(info_surf, info_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Kullanıcı input'unu işle."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                self._btn_pressed = True
                # Ripple efekti ekle
                self._ripples.append((event.pos[0], event.pos[1], 0.0))
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._btn_pressed = False
            if self._btn_rect is not None and self._btn_rect.collidepoint(event.pos):
                from v2.scenes.lobby import LobbyScene
                SceneManager.get().set_scene(LobbyScene())
