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

        # flip_progress: 0.0 = back tam görünür, 1.0 = front tam görünür
        self.flip_progress: float  = 0.0
        self._flip_target: float   = 0.0

        # hover_progress: 0.0 = normal, 1.0 = tam hover (lifted + scaled)
        self.hover_progress: float = 0.0
        self._hover_target: float  = 0.0

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

        # ── Evolved glow / border (back layer) ─────────────────────────
        if self.evolved and draw_w > 8:
            glow_w = draw_w + 20
            glow_h = scaled_h + 20
            if self._glow_surf is None or self._glow_surf.get_size() != (glow_w, glow_h):
                glow_color = (*self.evolved_color, 120)
                self._glow_surf = UIUtils.create_glow(max(glow_w, glow_h) // 2, glow_color)
            glow = pygame.transform.smoothscale(self._glow_surf, (glow_w, glow_h))
            surface.blit(glow, (cx - glow_w // 2, cy - glow_h // 2), special_flags=pygame.BLEND_ADD)

        # ── Blit ────────────────────────────────────────────────────────
        scaled_surf = pygame.transform.smoothscale(src_surf, (draw_w, scaled_h))
        blit_x = cx - draw_w  // 2
        blit_y = cy - scaled_h // 2
        surface.blit(scaled_surf, (blit_x, blit_y))

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
    def __init__(self, dest_rect: pygame.Rect, color: tuple = (25, 28, 40)):
        self.dest_rect = pygame.Rect(dest_rect)
        self.color = color
        self.flip_progress = 0.0
        self.hover_progress = 0.0

    def hover_start(self) -> None: pass
    def hover_end(self)  -> None: pass
    def update(self, dt_ms: float) -> None: pass

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.dest_rect, border_radius=4)
        pygame.draw.rect(surface, (50, 55, 70), self.dest_rect, width=1, border_radius=4)
