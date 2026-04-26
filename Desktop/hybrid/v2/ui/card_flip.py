"""
CardFlip — Hover-Flip Animasyon Motoru
=======================================
Bir kart slotuna (hand veya shop) atanır.
Fareyle üzerine gelindiğinde (hover_start çağrısı) flip animasyonu tetiklenir:
  - Faz 1: Kart Y ekseninde sıfıra kadar "kapanır" (back_surface görünür, genişlik 0'a iner)
  - Faz 2: front_surface ortaya çıkar ve tam genişliğe "açılır"
Fare uzaklaşınca (hover_end) tersine döner (front → back).

Hover Fiziği (Katman A):
  - hover_progress 0→1 arası smooth lerp
  - Kart 6px yukarı kayar ve %115 scale-up olur
  - Flip animasyonundan bağımsız, ayrı state makinesi

Kullanım:
    flip = CardFlip(back_surf, front_surf, rect)
    # her frame:
    flip.update(dt_ms)
    flip.render(surface)
    # mouse event:
    flip.hover_start() / flip.hover_end()
"""

import math
import pygame
from v2.ui.ui_utils import UIUtils

class CardFlip:
    FLIP_SPEED  = 6.0   # flip_progress değişim hızı
    HOVER_SPEED = 8.0   # hover_progress değişim hızı (daha hızlı = daha snappy)

    HOVER_LIFT  = 7     # piksel cinsinden yukarı kayma
    HOVER_SCALE = 1.14  # scale faktörü (1.0 = normal, 1.14 = %114)

    def __init__(
        self,
        back_surf: pygame.Surface,
        front_surf: pygame.Surface,
        dest_rect: pygame.Rect,
        evolved: bool = False,
        evolved_color: tuple[int, int, int] | None = None,
    ):
        self.back_surf  = back_surf
        self.front_surf = front_surf
        self.dest_rect  = pygame.Rect(dest_rect)
        self.evolved = evolved
        self.evolved_color = evolved_color or (220, 220, 240)
        self._glow_surf: pygame.Surface | None = None
        
        # Evolved kartlar için glow yüzeyini bir kez oluştur (Performans için)
        if self.evolved:
            glow_color = (*self.evolved_color, 120)
            # Yeterince büyük bir sabit boyutta oluştur (örneğin 256x256)
            # Render sırasında smoothscale ile hedef boyuta çekilecek.
            self._glow_surf = UIUtils.create_glow(128, glow_color)

        # flip_progress: 0.0 = back tam görünür, 1.0 = front tam görünür
        self.flip_progress: float  = 0.0
        self._flip_target: float   = 0.0

        # hover_progress: 0.0 = normal, 1.0 = tam hover (lifted + scaled)
        self.hover_progress: float = 0.0
        self._hover_target: float  = 0.0

        # Caching
        self._cached_surf: pygame.Surface | None = None
        self._cached_glow: pygame.Surface | None = None
        self._last_draw_params: dict = {}

    def hover_start(self) -> None:
        """Fareyle üzerine gelindi → front'a doğru flip + hover lift başlat."""
        self._flip_target  = 1.0
        self._hover_target = 1.0

    def hover_end(self) -> None:
        """Fare uzaklaştı → back'e geri dön + hover lift söndür."""
        self._flip_target  = 0.0
        self._hover_target = 0.0

    def update(self, dt_ms: float) -> None:
        """Her frame çağrılır. dt_ms: milisaniye cinsinden delta time."""
        dt_sec = dt_ms / 1000.0

        # Flip lerp
        diff = self._flip_target - self.flip_progress
        if abs(diff) < 0.002:
            self.flip_progress = self._flip_target
        else:
            self.flip_progress += diff * self.FLIP_SPEED * dt_sec
            self.flip_progress = max(0.0, min(1.0, self.flip_progress))

        # Hover lerp (bağımsız)
        hdiff = self._hover_target - self.hover_progress
        if abs(hdiff) < 0.002:
            self.hover_progress = self._hover_target
        else:
            self.hover_progress += hdiff * self.HOVER_SPEED * dt_sec
            self.hover_progress = max(0.0, min(1.0, self.hover_progress))

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        """
        Flip illüzyonu + Hover Fiziği:
        - Hover: kart yukarı kalkar ve büyür (smooth lerp ile)
        - Flip: progress < 0.5 → back yüzü daralıyor, >= 0.5 → front açılıyor
        """
        p  = self.flip_progress
        hp = self.hover_progress   # 0.0 – 1.0

        # ── Hover Fiziği ────────────────────────────────────────────────
        # Y-lift: hover_progress * HOVER_LIFT piksel yukarı
        y_offset = -int(hp * self.HOVER_LIFT)

        # Scale: 1.0 → HOVER_SCALE arası smooth büyüme
        scale = 1.0 + hp * (self.HOVER_SCALE - 1.0)

        # Hedef boyutlar (scaled)
        base_w = self.dest_rect.width
        base_h = self.dest_rect.height
        scaled_w = int(base_w * scale)
        scaled_h = int(base_h * scale)

        cx = self.dest_rect.centerx
        cy = self.dest_rect.centery + y_offset   # lift uygulandı

        # ── Flip Hesabı ─────────────────────────────────────────────────
        if p < 0.5:
            flip_x = 1.0 - (p * 2)   # 1.0 → 0.0 (back daralıyor)
            src_surf = self.back_surf
        else:
            flip_x = (p - 0.5) * 2   # 0.0 → 1.0 (front açılıyor)
            src_surf = self.front_surf

        # Gerçek çizim genişliği = scaled_w * flip_x
        draw_w = max(1, int(scaled_w * flip_x))

        # ── Cache Check ─────────────────────────────────────────────────
        current_params = {
            "draw_w": draw_w,
            "scaled_h": scaled_h,
            "src_surf_id": id(src_surf),
            "evolved": self.evolved
        }
        
        draw_w_delta = abs(draw_w - self._last_draw_params.get("draw_w", -999))
        scale_delta = abs(scaled_h - self._last_draw_params.get("scaled_h", -999))
        same_src = (id(src_surf) == self._last_draw_params.get("src_surf_id"))
        
        use_cache = False
        if self._cached_surf and same_src:
            if not self.is_animating and self._last_draw_params == current_params:
                use_cache = True
            elif draw_w_delta < 2 and scale_delta < 2:
                # Animasyon sırasında <2px değişimleri yoksayarak CPU tasarrufu (delta threshold)
                use_cache = True

        if use_cache:
            # Cache'teki boyutları kullanarak ufak titremeleri engelliyoruz
            cached_w = self._last_draw_params.get("draw_w", draw_w)
            cached_h = self._last_draw_params.get("scaled_h", scaled_h)
            
            blit_x = cx - cached_w // 2
            blit_y = cy - cached_h // 2
            
            if self.evolved and self._cached_glow:
                glow_w = cached_w + 20
                glow_h = cached_h + 20
                surface.blit(self._cached_glow, (cx - glow_w // 2, cy - glow_h // 2), special_flags=pygame.BLEND_ADD)
                
            surface.blit(self._cached_surf, (blit_x, blit_y))
            
            if self.evolved:
                border_rect = pygame.Rect(blit_x, blit_y, cached_w, cached_h)
                pygame.draw.rect(surface, self.evolved_color, border_rect, width=2, border_radius=8)
            return

        # ── Evolved glow / border (back layer) ─────────────────────────
        if self.evolved and draw_w > 8:
            glow_w = draw_w + 20
            glow_h = scaled_h + 20
            
            # Glow yüzeyini (yoksa oluştur, ama normalde __init__'te oluşur)
            if self._glow_surf is None:
                glow_color = (*self.evolved_color, 120)
                self._glow_surf = UIUtils.create_glow(128, glow_color)
            
            # Mevcut parametrelerle scale edilmiş glow'u cache'le veya yeniden ölçeklendir
            if self._cached_glow is None or self._cached_glow.get_size() != (glow_w, glow_h):
                self._cached_glow = pygame.transform.smoothscale(self._glow_surf, (glow_w, glow_h))
                
            surface.blit(self._cached_glow, (cx - glow_w // 2, cy - glow_h // 2), special_flags=pygame.BLEND_ADD)
        else:
            self._cached_glow = None

        # ── Blit & Cache Update ─────────────────────────────────────────
        self._cached_surf = pygame.transform.smoothscale(src_surf, (draw_w, scaled_h))
        self._last_draw_params = current_params
        
        blit_x = cx - draw_w  // 2
        blit_y = cy - scaled_h // 2
        surface.blit(self._cached_surf, (blit_x, blit_y))

        if self.evolved and draw_w > 8:
            border_rect = pygame.Rect(blit_x, blit_y, draw_w, scaled_h)
            pygame.draw.rect(surface, self.evolved_color, border_rect, width=2, border_radius=8)

    # ------------------------------------------------------------------ #
    # Yardımcılar                                                          #
    # ------------------------------------------------------------------ #
    @property
    def is_showing_front(self) -> bool:
        return self.flip_progress >= 0.5



    @property
    def is_animating(self) -> bool:
        return (abs(self.flip_progress - self._flip_target) > 0.002 or
                abs(self.hover_progress - self._hover_target) > 0.002)


class MockCardBox:
    """Satın alınmış / boş slot için minimal CardFlip uyumu.
    hover_start / hover_end / update / render çağrılarını güvenle yutuyor.
    """
    def __init__(self, dest_rect: pygame.Rect, color: tuple = (5, 7, 12)):
        self.dest_rect = pygame.Rect(dest_rect)
        # Çok koyu, hafif mavi tonlu (deep dark blue/black) zemin
        self.color = color
        self.flip_progress = 0.0
        self.hover_progress = 0.0

    def hover_start(self) -> None: pass
    def hover_end(self)  -> None: pass
    def update(self, dt_ms: float) -> None: pass

    def render(self, surface: pygame.Surface) -> None:
        w, h = self.dest_rect.w, self.dest_rect.h
        cx, cy = self.dest_rect.centerx, self.dest_rect.centery
        radius = h / 2
        
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

        # İç dolgu (Deep Dark Void)
        pygame.draw.polygon(surface, self.color, points)
        
        # Çerçeve (Taktiksel mat ve koyu çizgi)
        pygame.draw.polygon(surface, (25, 30, 45), points, width=1)
        
        # Merkezde şık bir "boşluk" crosshair'i (Çok daha koyu / silik)
        c_size = 12
        pygame.draw.line(surface, (30, 38, 55, 120), (cx - c_size, cy), (cx + c_size, cy), 1)
        pygame.draw.line(surface, (30, 38, 55, 120), (cx, cy - c_size), (cx, cy + c_size), 1)
        
        # Köşe "anchor" noktaları (Orantılı olarak daha koyu)
        pygame.draw.circle(surface, (35, 45, 65, 140), points[2], 2)
        pygame.draw.circle(surface, (35, 45, 65, 140), points[5], 2)
