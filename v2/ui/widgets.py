"""
v2/ui/widgets.py
================
Ortak UI ilkel sınıfları.

FloatingText        — 3 fazlı animasyonlu yüzen metin:
                      RISE (yüksel) → HOLD (bekle) → FADE (sön)
FloatingTextManager — vagon kuyruğu ile spawn yönetimi.
                      Aynı coord_key'e gelen metinler sırayla tetiklenir,
                      her biri bir öncekinin peşinden gelir.
"""
from __future__ import annotations
import pygame
from v2.constants import Timing


# ══════════════════════════════════════════════════════════════════════════
#  FLOATING TEXT  —  RISE → HOLD → FADE
# ══════════════════════════════════════════════════════════════════════════

class FloatingText:
    """
    3 fazlı animasyonlu metin:

      RISE  : spawn_y'den target_y'ye (spawn_y - max_rise_px) doğru yükselir.
              Süre = max_rise_px / rise_pxs * 1000 ms
      HOLD  : target_y'de sabit kalır, tam görünür.
              Süre = hold_ms
      FADE  : target_y'de sabit, yavaşça söner (alpha 255 → 0).
              Süre = fade_ms

    Görsel katmanlar (alttan üste):
      1. Pill halo  — %35 × alfa koyu arka plan
      2. Gölge      — 1 px sağ-aşağı, %60 × alfa
      3. Ana metin  — tam renk × alfa
    """

    def __init__(
        self,
        text:        str,
        x:           float,
        y:           float,
        color:       tuple,
        font_size:   int           = 14,
        font_type:   str           = "bold",   # "bold" | "mono" | "regular"
        max_rise_px: float | None  = None,
        hold_ms:     float | None  = None,
        fade_ms:     float | None  = None,
        rise_px_s:   float | None  = None,
    ):
        self.text      = text
        self.x         = float(x)
        self.y         = float(y)
        self.color     = color
        self.font_size = font_size
        self.font_type = font_type

        self._max_rise = float(max_rise_px if max_rise_px is not None
                               else Timing.FLOAT_TEXT_MAX_RISE_PX)
        self._hold_ms  = float(hold_ms  if hold_ms  is not None
                               else Timing.FLOAT_TEXT_HOLD_MS)
        self._fade_ms  = float(fade_ms  if fade_ms  is not None
                               else Timing.FLOAT_TEXT_FADE_MS)
        self._rise_pxs = float(rise_px_s if rise_px_s is not None
                               else Timing.FLOAT_TEXT_RISE_PX_S)

        self._elapsed  = 0.0
        self._target_y = float(y) - self._max_rise   # yükselme bitiş noktası

    # ── Hesaplanan süreler ───────────────────────────────────────────────

    @property
    def _rise_dur(self) -> float:
        """RISE fazının milisaniye cinsinden süresi."""
        return (self._max_rise / max(0.1, self._rise_pxs)) * 1000.0

    @property
    def _total_lifetime(self) -> float:
        return self._rise_dur + self._hold_ms + self._fade_ms

    # ── Güncelleme ───────────────────────────────────────────────────────

    def update(self, dt_ms: float) -> bool:
        """Her frame çağrılır. True döndürürse metin hâlâ canlı."""
        self._elapsed += dt_ms

        if self._elapsed <= self._rise_dur:
            # RISE: yukarı hareket et, target_y'yi aşma
            self.y = max(self._target_y,
                         self.y - self._rise_pxs * dt_ms / 1000.0)
        else:
            # HOLD / FADE: target_y'de sabit kal
            self.y = self._target_y

        return self._elapsed < self._total_lifetime

    # ── Alfa ─────────────────────────────────────────────────────────────

    @property
    def alpha(self) -> int:
        hold_end = self._rise_dur + self._hold_ms

        if self._elapsed <= hold_end:
            # RISE ve HOLD fazı: tamamen görünür
            return 255

        # FADE fazı: lineer azalma
        fade_elapsed = self._elapsed - hold_end
        ratio = 1.0 - fade_elapsed / max(1.0, self._fade_ms)
        return max(0, int(255 * ratio))

    # ── Render ───────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        a = self.alpha
        if a <= 0:
            return

        from v2.ui import font_cache
        fnt = {
            "bold":    font_cache.bold,
            "mono":    font_cache.mono,
            "regular": font_cache.regular,
        }.get(self.font_type, font_cache.bold)(self.font_size)

        try:
            text_surf = fnt.render(self.text, True, self.color)
        except pygame.error:
            return

        tw, th = text_surf.get_size()
        x = int(self.x - tw / 2)
        y = int(self.y - th / 2)

        # ── Katman 1: Pill halo ──────────────────────────────────────
        pad    = 5
        halo_w = tw + pad * 2
        halo_h = th + pad * 2
        halo_a = int(89 * a / 255)      # 255 × 0.35 ≈ 89
        if halo_a > 0:
            halo = pygame.Surface((halo_w, halo_h), pygame.SRCALPHA)
            pygame.draw.rect(
                halo,
                (0, 0, 0, halo_a),
                pygame.Rect(0, 0, halo_w, halo_h),
                border_radius=halo_h // 2,
            )
            surface.blit(halo, (x - pad, y - pad))

        # ── Katman 2: Gölge ──────────────────────────────────────────
        shadow_a = min(255, int(a * 0.6))
        if shadow_a > 0:
            try:
                shadow = fnt.render(self.text, True, (0, 0, 0))
                shadow.set_alpha(shadow_a)
                surface.blit(shadow, (x + 1, y + 1))
            except pygame.error:
                pass

        # ── Katman 3: Ana metin ──────────────────────────────────────
        text_surf.set_alpha(a)
        surface.blit(text_surf, (x, y))


# ══════════════════════════════════════════════════════════════════════════
#  FLOATING TEXT MANAGER  —  vagon kuyruğu
# ══════════════════════════════════════════════════════════════════════════

class FloatingTextManager:
    """
    Aktif FloatingText örneklerini yönetir.

    Vagon kuyruğu mekanizması:
    Aynı coord_key'e gelen her yeni metin, bir öncekinden
    WAGON_DELAY_MS ms sonra tetiklenir. Bu sayede metinler
    tren vagonları gibi birbirinin peşi sıra yükselir.

    coord_key verilmezse metin anında aktif olur (kuyruksuz).
    """

    _WAGON_DELAY_MS: int = Timing.FLOAT_TEXT_WAGON_DELAY_MS

    def __init__(self):
        self._active:  list[FloatingText]          = []
        # coord_key → [[remaining_delay_ms, FloatingText], ...]
        self._pending: dict[tuple, list]            = {}

    # ── Spawn ────────────────────────────────────────────────────────────

    def spawn(
        self,
        text:        str,
        x:           float,
        y:           float,
        color:       tuple,
        font_size:   int           = 14,
        font_type:   str           = "bold",
        coord_key:   tuple | None  = None,
        max_rise_px: float | None  = None,
        hold_ms:     float | None  = None,
        fade_ms:     float | None  = None,
    ) -> None:
        """
        Yeni bir FloatingText oluştur.

        coord_key verilirse vagon kuyruğuna eklenir:
          index 0 → 0 ms gecikme (hemen tetiklenir)
          index 1 → 1 × WAGON_DELAY_MS
          index 2 → 2 × WAGON_DELAY_MS
          ...
        """
        ft = FloatingText(
            text=text, x=x, y=y, color=color,
            font_size=font_size, font_type=font_type,
            max_rise_px=max_rise_px, hold_ms=hold_ms, fade_ms=fade_ms,
        )

        if coord_key is None:
            self._active.append(ft)
        else:
            queue = self._pending.setdefault(coord_key, [])
            delay = float(len(queue) * self._WAGON_DELAY_MS)
            queue.append([delay, ft])

    # ── Güncelleme ───────────────────────────────────────────────────────

    def update(self, dt_ms: float) -> None:
        """Kuyruktan aktife al, ölü metinleri temizle."""

        # 1. Bekleyen metinlerin gecikme sayacını düşür
        done_keys = []
        for key, queue in self._pending.items():
            for item in queue:
                item[0] -= dt_ms

            # Gecikme doldu → aktif listeye al
            still_pending = []
            for item in queue:
                if item[0] <= 0:
                    self._active.append(item[1])
                else:
                    still_pending.append(item)
            self._pending[key] = still_pending

            if not still_pending:
                done_keys.append(key)

        for key in done_keys:
            del self._pending[key]

        # 2. Aktif metinleri güncelle, ölenleri çıkar
        self._active = [t for t in self._active if t.update(dt_ms)]

    # ── Render ───────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Tüm aktif metinleri çiz."""
        for t in self._active:
            t.render(surface)

    # ── Yardımcılar ──────────────────────────────────────────────────────

    def clear(self) -> None:
        """Tüm aktif ve bekleyen metinleri sil."""
        self._active.clear()
        self._pending.clear()

    @property
    def active_count(self) -> int:
        """Aktif + kuyrukta bekleyen toplam metin sayısı."""
        pending = sum(len(q) for q in self._pending.values())
        return len(self._active) + pending


# ── Geriye uyumluluk stub'ları ───────────────────────────────────────────
class Button: pass
class Bar:    pass
class Icon:   pass
