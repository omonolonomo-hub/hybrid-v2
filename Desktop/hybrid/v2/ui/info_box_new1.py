"""
InfoBox — Kart Detay Paneli
============================
Hover kart önizlemesi. Mantıksal boyut (self.rect) ekranda konum için sabit;
içerik isteğe bağlı daha yüksek çözünürlükte çizilip ölçeklenir (keskinlik).

Kullanım:
    box = InfoBox(rect, render_scale=2)
    box.set_card(card_data_or_none)
    box.render(surface)
"""

from __future__ import annotations

import math
import pygame
from v2.ui import font_cache, icon_loader
from v2.core.card_database import CardData
from v2.constants import Colors

_PHI = 1.618033988749895
_DEFAULT_RENDER_SCALE = 2

# Renkler
_BORDER = (58, 68, 98)
_DIVIDER_MID = (88, 96, 120)
_DIVIDER_EDGE = (42, 48, 62)

# Opaklık
_BG_ALPHA = 170
_BORDER_ALPHA = 255

_PASSIVE_COLORS: dict[str, tuple[int, int, int]] = {
    "SYNERGY FIELD": (80, 180, 255),
    "COMBAT":        (255, 100,  80),
    "COMBO":         (255, 200,  50),
    "COPY":          (140, 220, 140),
    "SURVIVAL":      (200,  80, 200),
    "ECONOMY":       (255, 210,  60),
}

# Stat ikonları — kategori ikonlarından ayrı tutulur (ANKH/ATOM/STAR vb. kategoride)
STAT_ICON: dict[str, str] = {
    "Power": "FIST",        # Güç - Yumruk ikonu
    "Durability": "SHIELD",
    "Size": "EXPAND",       # Boyut - Genişleme ikonu
    "Speed": "BOLT",
    "Meaning": "BOOK",
    "Secret": "LOCK",
    "Intelligence": "GEAR",
    "Trace": "FOOTPRINT",   # İz - Ayak izi ikonu
    "Gravity": "MAGNET",    # Çekim - Mıknatıs ikonu
    "Harmony": "MUSIC",
    "Spread": "BROADCAST",  # Yayılma - Yayın ikonu (dalga yerine)
    "Prestige": "GEM",      # Prestij - Mücevher ikonu
}

_STAT_ROW_ORDER: tuple[str, ...] = (
    "Power", "Durability", "Size", "Speed",
    "Meaning", "Secret", "Intelligence", "Trace",
    "Gravity", "Harmony", "Spread", "Prestige",
)


def _category_icon_key(category: str) -> str:
    """Kategori metni → font_cache.ICONS (Mitoloji/ Sanat/ Doğa/ Kozmos/ Bilim/ Tarih)."""
    u = category.upper()
    if "MYTH" in u or "GOD" in u:
        return "ANKH"
    if "ART" in u or "CULTURE" in u:
        return "PALETTE"
    if "NATUR" in u or "BIOLOGY" in u or "CREATURE" in u:
        return "SEEDLING"
    if "COSMO" in u or "SPACE" in u:
        return "STAR"
    if "SCIEN" in u or "TECH" in u:
        return "ATOM"
    if "HIST" in u or "CIVIL" in u:
        return "LANDMARK"
    return "AWARD"


def _ordered_stat_pairs(stats: dict[str, int]) -> list[tuple[str, int]]:
    """Sabit sıra + tanınmayan anahtarlar sonda; en fazla 6 gösterim."""
    out: list[tuple[str, int]] = []
    seen: set[str] = set()
    for key in _STAT_ROW_ORDER:
        if key in stats:
            out.append((key, stats[key]))
            seen.add(key)
    for key, val in stats.items():
        if key not in seen:
            out.append((key, val))
            seen.add(key)
    return out[:6]


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _blend_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _soft_horizontal_rule(
    surf: pygame.Surface,
    y: int,
    x0: int,
    x1: int,
    mid_rgb: tuple[int, int, int],
    edge_rgb: tuple[int, int, int],
    alpha_center: int,
    thickness: int,
) -> None:
    """Yatay ayırıcı: ortada belirgin, yumuşak kenar (birkaç ton geçiş)."""
    half = max(1, thickness // 2)
    for dy in range(-half, half + 1):
        dist = abs(dy) / max(1, half)
        rgb = _blend_rgb(mid_rgb, edge_rgb, dist * 0.85)
        fa = int(alpha_center * (1.0 - 0.45 * dist))
        yy = y + dy
        if 0 <= yy < surf.get_height():
            pygame.draw.line(surf, (*rgb, fa), (x0, yy), (x1, yy), 1)


class InfoBox:
    def __init__(self, rect: pygame.Rect, render_scale: int = _DEFAULT_RENDER_SCALE) -> None:
        self.rect = pygame.Rect(rect)
        self._render_scale = max(1, int(render_scale))
        self._card: CardData | None = None

        self._alpha = 0.0
        self._time = 0.0
        self._anim_time = 0.0
        self._last_tick = pygame.time.get_ticks()

        self._hi_surf: pygame.Surface | None = None

    def set_anchor_at_mouse(
        self,
        mx: int,
        my: int,
        screen_w: int,
        screen_h: int,
        pad: int = 16,
    ) -> None:
        w, h = self.rect.w, self.rect.h
        sw, sh = max(1, screen_w), max(1, screen_h)
        x = mx + pad
        y = my + pad
        if x + w > sw:
            x = mx - w - pad
        if y + h > sh:
            y = my - h - pad
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))
        self.rect.x = int(x)
        self.rect.y = int(y)

    def set_card(self, card: CardData | None) -> None:
        is_same_card = (
            self._card is not None and
            card is not None and
            self._card.name == card.name
        )

        if not is_same_card:
            self._card = card
            if card:
                self._alpha = 0.0
                self._time = 0.0
                self._anim_time = 0.0
            else:
                self._alpha = 0.0
                self._anim_time = 0.0
                if self._hi_surf is not None:
                    self._hi_surf.fill((0, 0, 0, 0))
        else:
            self._card = card

    def _ensure_hi(self, rw: int, rh: int) -> pygame.Surface:
        s = self._render_scale
        W, H = rw * s, rh * s
        if self._hi_surf is None or self._hi_surf.get_size() != (W, H):
            self._hi_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        return self._hi_surf

    # ------------------------------------------------------------------ #
    # CYBER-SYNTHWAVE DETAY KATMANLARI
    # ------------------------------------------------------------------ #
    
    def _draw_inner_glow(self, surf: pygame.Surface, w: int, h: int, accent: tuple[int, int, int], alpha: float, border_radius: int, s: int) -> None:
        """İç kenar ışığı - inner glow gradient effect (daha opak)."""
        fill_thickness = max(10, int(18 * s))
        for i in range(fill_thickness):
            t = 1.0 - (i / fill_thickness)
            a = int(14 * t * t * alpha)
            if a < 2:
                continue
            r = pygame.Rect(i, i, w - 2 * i, h - 2 * i)
            if r.w <= 0 or r.h <= 0:
                break
            pygame.draw.rect(
                surf,
                (*accent, a),
                r,
                width=0,
                border_radius=max(1, border_radius - i // 2),
            )

        # Glow kalınlığı artırıldı: daha geniş alan kaplayacak
        glow_thickness = max(20, int(32 * s))  # 18 -> 32
        
        # Accent rengini kullan
        for i in range(glow_thickness):
            # Dıştan içe doğru azalan alpha
            t = 1.0 - (i / glow_thickness)
            # Opaklık çok daha yüksek: max %50 opaklık (önceden %14)
            glow_alpha = int(128 * t * t * alpha)  # 35 -> 128
            
            if glow_alpha < 5:  # Çok düşük alpha'yı atla
                continue
            
            glow_color = (*accent, glow_alpha)
            
            # İç kenar çerçevesi çiz
            glow_rect = pygame.Rect(i, i, w - 2 * i, h - 2 * i)
            pygame.draw.rect(
                surf,
                glow_color,
                glow_rect,
                width=1,
                border_radius=max(1, border_radius - i // 2)
            )
    
    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        dt = (now - self._last_tick) / 1000.0
        self._last_tick = now

        self._time += dt

        ANIMATION_DURATION = 0.25

        # Kart yoksa hızla kapat
        if self._card is None:
            self._anim_time = max(0.0, self._anim_time - dt * 3.0)
        else:
            self._anim_time = min(ANIMATION_DURATION, self._anim_time + dt)

        # Animasyon tamamen bittiyse hiçbir şey çizme
        if self._anim_time <= 0.0:
            self._alpha = 0.0
            if self._hi_surf is not None:
                self._hi_surf.fill((0, 0, 0, 0))
            return

        t = self._anim_time / ANIMATION_DURATION
        eased_t = 1.0 - (1.0 - t) ** 3
        self._alpha = eased_t
        current_scale = 0.8 + (0.2 * eased_t)

        rw, rh = self.rect.w, self.rect.h

        anim_w = int(rw * current_scale)
        anim_h = int(rh * current_scale)
        offset_x = (rw - anim_w) // 2
        offset_y = (rh - anim_h) // 2
        final_x = self.rect.x + offset_x
        final_y = self.rect.y + offset_y

        if self._alpha > 0.1 and anim_w > 0 and anim_h > 0:
            bg_rect = pygame.Rect(final_x, final_y, anim_w, anim_h)
            if surface.get_rect().contains(bg_rect):
                backdrop = surface.subsurface(bg_rect).copy()
                blur_factor = max(2, int(8 * eased_t))
                small_w = max(1, anim_w // blur_factor)
                small_h = max(1, anim_h // blur_factor)
                small_bg = pygame.transform.smoothscale(backdrop, (small_w, small_h))
                blurred_bg = pygame.transform.smoothscale(small_bg, (anim_w, anim_h))
                darken = pygame.Surface((anim_w, anim_h))
                darken.set_alpha(int(100 * eased_t))
                blurred_bg.blit(darken, (0, 0))
                surface.blit(blurred_bg, (final_x, final_y))

        s = self._render_scale
        hi = self._ensure_hi(rw, rh)
        hi.fill((0, 0, 0, 0))
        self._paint_hi_res(hi, rw, rh, s)

        if anim_w > 0 and anim_h > 0:
            anim_surf = pygame.transform.smoothscale(hi, (anim_w, anim_h))
            surface.blit(anim_surf, (final_x, final_y))

    def _paint_hi_res(self, hi: pygame.Surface, rw: int, rh: int, s: int) -> None:
        """Tüm çizim hi-res piksel uzayında (genişlik rw*s, yükseklik rh*s)."""
        W, H = rw * s, rh * s
        draw_rect = pygame.Rect(0, 0, W, H)
        a = self._alpha
        base_rgb = (12, 14, 20)
        br = max(8, int(10 * s))

        # Arka plan - opaklık artırıldı
        pygame.draw.rect(hi, (*base_rgb, int(_BG_ALPHA * a)), draw_rect, border_radius=br)

        # ═══════════════════════════════════════════════════════════════
        # CYBER-SYNTHWAVE DETAY KATMANLARI
        # ═══════════════════════════════════════════════════════════════
        
        # INNER GLOW - Kenar ışığı
        if self._card:
            c_accent = _get_cat_color(self._card.category)
            self._draw_inner_glow(hi, W, H, c_accent, a, br, s)
        
        # ═══════════════════════════════════════════════════════════════

        rim_col = (210, 225, 245) if not self._card else _get_cat_color(self._card.category)
        rim_in = max(6, int(7 * s))
        pygame.draw.line(hi, rim_col, (rim_in, 2 * s), (W - rim_in, 2 * s), max(1, s // 2))
        pygame.draw.line(hi, rim_col, (rim_in, H - 1 - 2 * s), (W - rim_in, H - 1 - 2 * s), max(1, s // 2))

        # Ana çerçeve - genişletildi ve opaklık artırıldı
        pygame.draw.rect(
            hi,
            (*_BORDER, int(_BORDER_ALPHA * a)),
            draw_rect,
            width=max(2, int(s * 1.5)),  # Çerçeve kalınlığı artırıldı
            border_radius=br,
        )

        if self._card is not None:
            pulse = int(50 + 38 * math.sin(self._time * 2.8))
            # Kategori rengi vurgusu - daha kalın ve parlak
            pygame.draw.rect(
                hi,
                (*rim_col, min(255, int((pulse + 60) * a))),  # Daha parlak
                draw_rect,
                width=max(2, int(s * 1.8)),  # Daha kalın
                border_radius=br,
            )

        logical = pygame.Rect(0, 0, rw, rh)
        if self._card is None:
            self._render_placeholder_hi(hi, logical, s)
        else:
            self._render_card_hi(hi, self._card, logical, s)

    # ------------------------------------------------------------------ #
    def _render_placeholder_hi(self, surface: pygame.Surface, rect: pygame.Rect, s: int) -> None:
        if self._alpha < 0.3:
            return
        r = pygame.Rect(rect.x * s, rect.y * s, rect.w * s, rect.h * s)
        font_cache.render_text(
            surface,
            "HOVER A CARD",
            font_cache.regular(max(8, int(10 * s))),
            (90, 95, 115, int(255 * self._alpha)),
            r,
            align="center",
            v_align="center",
        )

    # ------------------------------------------------------------------ #
    def _render_card_hi(self, surface: pygame.Surface, card: CardData, rect: pygame.Rect, s: int) -> None:
        """rect = mantıksal (0,0,rw,rh); çizim koordinatları * s."""
        rw, rh = rect.w, rect.h
        # İç kenar boşlukları - üst padding azaltıldı
        pad_x = max(10, min(16, int(rw * 0.035)))
        pad_y = max(4, min(8, int(rh * 0.015)))  # Üst padding daha az (0.028 -> 0.015)
        px, py = pad_x * s, pad_y * s
        iw, ih = (rw - pad_x * 2) * s, (rh - pad_y * 2) * s
        inner = pygame.Rect(px, py, iw, ih)

        gap = max(5, min(10, int(rh * 0.022))) * s
        # İstatistik bandı (~2× görsel): satır yüksekliği / punto ile orantılı — iç yüksekliğin ~%42’sine kadar
        h_stats = max(125 * s, int(130 * s))  # Stat alanı büyütüldü (110->125, 115->130)
        remaining = max(inner.h - h_stats - gap, 36 * s)
        h_identity = int(remaining / (1 + _PHI * 1.2))

        line_h = max(24 * s, int(26 * s))
        a_int = int(255 * self._alpha)
        cat_color = _get_cat_color(card.category)

        y = inner.y
        
        # Kart ismi - wrap edilebilir (uzun isimler için 2 satır)
        # Commodore Angled için daha büyük punto ve satır aralığı
        name_font_size = max(16, int(22 * s))  # 19 -> 22 (daha büyük)
        name_font = font_cache.card_name(name_font_size)
        name_lines = _wrap_text(card.name, name_font, inner.w)
        name_lines = name_lines[:2]  # Maksimum 2 satır
        
        name_line_h = max(26 * s, int(30 * s))  # 24 -> 30 (daha geniş satır aralığı)
        for i, name_line in enumerate(name_lines):
            name_r = pygame.Rect(inner.x, y + i * name_line_h, inner.w, name_line_h)
            font_cache.render_text(
                surface,
                name_line,
                name_font,
                (*cat_color, a_int),
                name_r,
                v_align="center",  # Dikey ortalama ekle
            )
        
        name_total_h = len(name_lines) * name_line_h
        accent_y = y + name_total_h - max(1, s // 2)
        
        # Kategori rengi vurgusu - daha kalın ve parlak
        pygame.draw.line(
            surface,
            (*cat_color, min(255, int(255 * self._alpha))),  # Tam opaklık
            (inner.x, accent_y),
            (inner.right, accent_y),
            max(2, 3 * s),  # Daha kalın çizgi
        )
        
        y = accent_y + max(4 * s, int(gap / (_PHI + 0.1)))  # Biraz daha fazla boşluk

        tag_h = max(24 * s, int(26 * s))
        tag_r = pygame.Rect(inner.x, y, inner.w, tag_h)
        # Kategori tag rengi - daha parlak
        tag_cat_color = [max(0, min(255, c + 60)) for c in cat_color]  # +40 -> +60
        tag_cat_color = (*tag_cat_color, min(255, int(255 * self._alpha)))  # Tam opaklık
        passive_color = _PASSIVE_COLORS.get(card.passive_label, (190, 190, 200))

        tag_fs = max(11, int(13 * s))
        cat_icon_key = _category_icon_key(card.category)
        cat_icon_sz = max(20, int(22 * s))  # 16'dan 20'ye, 14'ten 22'ye artırıldı
        icy = y + (tag_h - cat_icon_sz) // 2
        
        # PNG ikon çiz
        icon_surf = icon_loader.get_icon(card.category, cat_icon_sz, is_category=True)
        if icon_surf:
            icon_surf = icon_surf.copy()
            icon_surf.set_alpha(int(255 * self._alpha))
            # Gölge
            shadow_surf = icon_surf.copy()
            shadow_surf.fill((0, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow_surf, (inner.x + 1, icy + 1))
            # Ana ikon
            surface.blit(icon_surf, (inner.x, icy))
        else:
            # Fallback: Font Awesome ikonu
            try:
                icon_font = font_cache.icons(cat_icon_sz)
                icon_char = font_cache.ICONS.get(cat_icon_key, "?")
                shadow_surf = icon_font.render(icon_char, True, (0, 0, 0))
                shadow_surf.set_alpha(int(255 * self._alpha))
                surface.blit(shadow_surf, (inner.x + 1, icy + 1))
                icon_surf = icon_font.render(icon_char, True, cat_color)
                icon_surf.set_alpha(int(255 * self._alpha))
                surface.blit(icon_surf, (inner.x, icy))
            except pygame.error:
                pass

        cat_text_x = inner.x + cat_icon_sz + int(6 * s)
        # Synergy group kaldırıldı - sadece kategori göster
        cat_lbl_r = pygame.Rect(cat_text_x, y, max(1, inner.w - (cat_text_x - inner.x)), tag_h)
        font_cache.render_text(
            surface,
            f"[{card.category}]",
            font_cache.other_texts(tag_fs),
            tag_cat_color,
            cat_lbl_r,
            align="left",
            v_align="center",
        )

        identity_used = (y + tag_h) - inner.y
        if identity_used > h_identity:
            h_identity = identity_used

        top_divider_y = inner.y + h_identity
        div_a = min(255, int(225 * self._alpha))
        _soft_horizontal_rule(
            surface,
            top_divider_y,
            px,
            rw * s - px,
            _DIVIDER_MID,
            _DIVIDER_EDGE,
            div_a,
            max(3 * s, 4),
        )

        passive_top = top_divider_y + max(2 * s, gap // 3)
        stats_top = inner.bottom - h_stats
        bottom_divider_y = stats_top - max(1 * s, gap // 6)  # Boşluk azaltıldı (2*s -> 1*s, gap//3 -> gap//6)

        # Passive effect alanına kategori rengi hafif sızması - opaklık artırıldı
        passive_bg_tint = (*[int(c * 0.12) for c in cat_color], int(235 * self._alpha))  # 200 -> 235
        passive_h = bottom_divider_y - passive_top
        passive_bg_rect = pygame.Rect(inner.x, passive_top, inner.w, passive_h)
        
        # Passive alan border shadow (küçük, elit görünüm)
        shadow_offset = max(1, int(2 * s))
        shadow_rect = passive_bg_rect.inflate(shadow_offset * 2, shadow_offset * 2)
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, int(60 * self._alpha)), shadow_surf.get_rect(), border_radius=max(5, int(7 * s)))
        surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
        
        pygame.draw.rect(surface, passive_bg_tint, passive_bg_rect, border_radius=max(4, int(6 * s)))

        p_font = font_cache.stat_passive(max(15, int(17 * s)))  # Passive text büyütüldü (11->15, 13.5->17)
        text_indent = int(8 * s)
        text_width = inner.w - text_indent
        
        lines = _wrap_text(card.passive_effect, p_font, text_width)
        max_lines = 6 if rh >= 350 else 4
        lines = lines[:max_lines]

        line_gap = max(13 * s, int(14 * s))
        label_h = max(16 * s, int(18 * s))
        content_h = label_h + len(lines) * line_gap
        avail_h = max(0, bottom_divider_y - passive_top)
        # Ortalamak yerine üstten başlat — orta alan “tok” dolar; taşarsa yukarı yapışır
        mid_start_y = passive_top + min(int(2 * s), max(0, (avail_h - content_h) // 4))

        passive_lbl_r = pygame.Rect(inner.x, mid_start_y, inner.w, label_h)
        label = f"◈ {card.passive_label}"
        lbl_fs = max(16, int(18 * s))  # Passive label büyütüldü (12->16, 14.5->18)
        font_cache.render_text(surface, label, font_cache.stat_passive(lbl_fs), passive_color, passive_lbl_r)

        text_y = mid_start_y + label_h + int(1.5 * s)
        
        for line in lines:
            # Satırlar indent ile başlar
            lr = pygame.Rect(inner.x + text_indent, text_y, inner.w - text_indent, line_gap)
            font_cache.render_text(surface, line, p_font, (228, 230, 242), lr)
            text_y += line_gap

        stat_sep_a = min(255, int(200 * self._alpha))
        _soft_horizontal_rule(
            surface,
            bottom_divider_y,
            px,
            rw * s - px,
            _DIVIDER_MID,
            _DIVIDER_EDGE,
            stat_sep_a,
            max(3 * s, 4),
        )

        stats_start_y = stats_top + int(2 * s)  # Padding azaltıldı (3*s -> 2*s)
        
        # Stat alanına kategori rengi hafif sızması (arka plan tonu) - opaklık artırıldı
        cat_color_stat = _get_cat_color(card.category)
        stat_bg_tint = (*[int(c * 0.15) for c in cat_color_stat], int(220 * self._alpha))  # 180 -> 220
        stat_bg_rect = pygame.Rect(inner.x, stats_start_y - int(2 * s), inner.w, h_stats + int(4 * s))
        
        # Stat alan border shadow (küçük, elit görünüm)
        shadow_offset = max(1, int(2 * s))
        shadow_rect = stat_bg_rect.inflate(shadow_offset * 2, shadow_offset * 2)
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, int(60 * self._alpha)), shadow_surf.get_rect(), border_radius=max(5, int(7 * s)))
        surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
        
        pygame.draw.rect(surface, stat_bg_tint, stat_bg_rect, border_radius=max(4, int(6 * s)))
        
        # Stat görünümü - 2 kolon, tam hizalı ve dengeli
        stat_row_h = max(int(38 * s), int(42 * s))  # Satır yüksekliği artırıldı (32->38, 36->42)
        icon_sz = max(int(28 * s), int(30 * s))  # İkon boyutu daha da artırıldı (22->28, 24->30)
        
        # Sabit padding ve boşluklar - tutarlı yerleşim için
        edge_pad = int(8 * s)  # Kenar boşluğu
        icon_gap = int(6 * s)  # İkon-label arası boşluk (azaltıldı)
        label_val_gap = int(10 * s)  # Label-değer arası boşluk
        
        # İki kolon için eşit genişlik - tam orta ayraç
        col_w = inner.w // 2
        
        # Değer kolonu genişliği - sabit ve dengeli
        val_col_w = int(45 * s)  # Sabit genişlik, 2-3 haneli sayılar için yeterli

        # Ayraç rengi - kategori rengine göre
        stat_line_mid = tuple(int(c * 0.35 + 72 * 0.65) for c in cat_color_stat)  # Kategori + gri karışımı
        stat_line_edge = tuple(int(c * 0.25 + 48 * 0.75) for c in cat_color_stat)  # Daha az kategori rengi
        for i in range(3):
            y_line = stats_start_y + i * stat_row_h
            _soft_horizontal_rule(
                surface,
                y_line,
                inner.x,
                inner.right,
                stat_line_mid,
                stat_line_edge,
                min(255, int(185 * self._alpha)),
                max(2 * s, 3),
            )

        stats_pairs = _ordered_stat_pairs(dict(card.stats))
        mono_sz = max(int(20 * s), int(22 * s))  # Label font büyütüldü (16->20, 18->22)
        val_sz = max(int(24 * s), int(26 * s))  # Değer font büyütüldü (18->24, 20->26)

        for i, (stat_name, val) in enumerate(stats_pairs):
            col = i % 2
            row = i // 2
            
            # Her kolonun başlangıç noktası - tam eşit bölünmüş
            sx = inner.x + col * col_w
            sy = stats_start_y + row * stat_row_h
            
            val_color = _stat_color(stat_name, val)
            icon_key = STAT_ICON.get(stat_name, "GEAR")

            # İkon - kenardan sabit mesafede, dikey ortalanmış
            ix = sx + edge_pad
            iy = sy + (stat_row_h - icon_sz) // 2
            
            # PNG ikon çiz (stat ikonları için)
            icon_surf = icon_loader.get_icon(icon_key, icon_sz, is_category=False)
            if icon_surf:
                icon_surf = icon_surf.copy()
                icon_surf.set_alpha(int(255 * self._alpha))
                # Gölge
                shadow_surf = icon_surf.copy()
                shadow_surf.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(shadow_surf, (ix + 1, iy + 1))
                # Ana ikon
                surface.blit(icon_surf, (ix, iy))
            else:
                # Fallback: Font Awesome ikonu
                try:
                    icon_font = font_cache.icons(icon_sz)
                    icon_char = font_cache.ICONS.get(icon_key, "?")
                    shadow_surf = icon_font.render(icon_char, True, (0, 0, 0))
                    shadow_surf.set_alpha(int(180 * self._alpha))
                    surface.blit(shadow_surf, (ix + 1, iy + 1))
                    icon_surf = icon_font.render(icon_char, True, val_color)
                    icon_surf.set_alpha(int(255 * self._alpha))
                    surface.blit(icon_surf, (ix, iy))
                except pygame.error:
                    pass

            # Label - ikondan sonra sabit boşlukla
            lbl_left = ix + icon_sz + icon_gap
            
            # Değer - kolonun sonundan sabit mesafede (sağa hizalı)
            val_right = sx + col_w - edge_pad
            val_left = val_right - val_col_w
            
            # Label alanı - değer kolonuna kadar uzanır
            lbl_width = max(1, val_left - lbl_left - label_val_gap)
            
            lbl_rect = pygame.Rect(lbl_left, sy, lbl_width, stat_row_h)
            lbl = f"{stat_name[:3].upper()}:"
            font_cache.render_text(
                surface,
                lbl,
                font_cache.stat_passive(mono_sz),  # 99_percent_OCCUPY fontu
                (185, 192, 205),
                lbl_rect,
                align="left",
                v_align="center",
            )

            # Value - sağa hizalı, sabit genişlikte
            val_rect = pygame.Rect(val_left, sy, val_col_w, stat_row_h)
            font_cache.render_text(
                surface,
                str(int(val)),
                font_cache.stat_passive(val_sz),  # 99_percent_OCCUPY fontu
                val_color,
                val_rect,
                align="right",
                v_align="center",
            )


def _stat_color(stat_name: str, val: int) -> tuple[int, int, int]:
    if stat_name in ("Secret", "Meaning", "Intelligence", "Trace"):
        c_high = (120, 200, 255)
        c_mid = Colors.MIND
        c_low = (60, 100, 160)
        c_min = (45, 70, 110)
    elif stat_name in ("Power", "Durability", "Size", "Speed"):
        c_high = (255, 80, 80)
        c_mid = Colors.EXISTENCE
        c_low = (150, 60, 60)
        c_min = (110, 45, 45)
    else:
        c_high = (100, 255, 150)
        c_mid = Colors.CONNECTION
        c_low = (60, 140, 80)
        c_min = (45, 100, 60)

    if val >= 8:
        return c_high
    if val >= 6:
        return c_mid
    if val >= 4:
        return c_low
    return c_min


def _get_cat_color(category: str) -> tuple[int, int, int]:
    _MAP = {
        "Mythology & Gods": (248, 222, 34),
        "Art & Culture": (240, 60, 110),
        "Nature & Biology": (60, 255, 80),
        "Nature & Creatures": (60, 255, 80),
        "Cosmos & Space": (140, 80, 255),
        "Science & Technology": (3, 190, 240),
        "History & Civilizations": (255, 120, 40),
    }
    if category in _MAP:
        return _MAP[category]

    cat_upper = category.upper()
    if "MYTH" in cat_upper:
        return (248, 222, 34)
    if "ART" in cat_upper:
        return (240, 60, 110)
    if "NATUR" in cat_upper:
        return (60, 255, 80)
    if "COSMO" in cat_upper:
        return (140, 80, 255)
    if "SCIEN" in cat_upper:
        return (3, 190, 240)
    if "HIST" in cat_upper:
        return (255, 120, 40)

    return (120, 160, 200)
