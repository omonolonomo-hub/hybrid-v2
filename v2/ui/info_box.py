"""
InfoBox — Kart Detay Paneli
============================
ShopPanel ve HandPanel'in ortak info_rect'ine çizilen kart inceleyici.
Hover delay sisteminden gelen CardData nesnesiyle beslenirse dolar,
None gönderilirse boş placeholder gösterir.

Kullanım:
    box = InfoBox(rect)
    box.set_card(card_data_or_none)
    box.render(surface)
"""

import pygame
from v2.ui import font_cache
from v2.core.card_database import CardData

# Renk şeması
_BG           = (18, 20, 34)
_BORDER       = (50, 60, 90)
_DIVIDER      = (36, 42, 62)
_PLACEHOLDER  = (50, 55, 75)
_TEXT_DIM     = (90, 95, 115)
_TEXT_WHITE   = (220, 225, 240)

# Passive tip rengi
_PASSIVE_COLORS: dict[str, tuple[int, int, int]] = {
    "SYNERGY FIELD": (80, 180, 255),
    "COMBAT":        (255, 100,  80),
    "COMBO":         (255, 200,  50),
    "COPY":          (140, 220, 140),
    "SURVIVAL":      (200,  80, 200),
    "ECONOMY":       (255, 210,  60),
}


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    """Metni max_w piksel genişliğine sığdırmak için satırlara böl."""
    words  = text.split()
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


class InfoBox:
    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = pygame.Rect(rect)
        self._card: CardData | None = None
        
        # Animasyon Durumu
        self._alpha = 0.0
        self._y_offset = 15.0 # Aşağıdan başlar
        self._time = 0.0      # Pulse için zaman takibi
        self._last_tick = pygame.time.get_ticks()

    def set_card(self, card: CardData | None) -> None:
        # 🧪 Akıllı Güncelleme: Sadece isim değişirse animasyonu sıfırla.
        # Eğer sadece statlar değişmişse (sinerji/prestige) şeffaflığı bozma.
        is_same_card = (
            self._card is not None and 
            card is not None and 
            self._card.name == card.name
        )

        if not is_same_card:
            self._card = card
            if card:
                # Yeni bir kart geldi, giriş animasyonunu başlat
                self._alpha = 0.0
                self._y_offset = 15.0
            else:
                # Kart çekildi, görünmez yap
                self._alpha = 0.0
        else:
            # Aynı kartın güncel (belki statı değişmiş) snapshot'ı gelmiş
            self._card = card

    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        dt  = (now - self._last_tick) / 1000.0
        self._last_tick = now

        # Lerp (150ms hedef)
        lerp_speed = 10.0
        self._alpha    += (1.0 - self._alpha) * lerp_speed * dt
        self._y_offset += (0.0 - self._y_offset) * lerp_speed * dt
        self._time     += dt

        if self._alpha < 0.01:
            return

        # Alpha desteği için geçici surface
        box_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        draw_rect = pygame.Rect(0, 0, self.rect.w, self.rect.h)

        # ── 1. Deep Void Layer (Arka Plan) ──
        # Kart rengini buraya karıştırmıyoruz, panelin 'havada' durması için sabit koyu zemin
        bg_alpha = int(245 * self._alpha) # %95 opaklık
        pygame.draw.rect(box_surf, (10, 12, 18, bg_alpha), draw_rect, border_radius=8)

        # 2. Top-Down Glow (Üstten süzülen hafif kategori rengi)
        if self._card:
            c_accent = _get_cat_color(self._card.category)
            # Üstten aşağıya doğru sönümlenen gradyan (1/3'lük alan)
            grad_h = self.rect.h // 3
            for y_glow in range(grad_h):
                strength = (1.0 - (y_glow / grad_h)) * 0.08 * self._alpha
                glow_col = (*c_accent, int(255 * strength))
                pygame.draw.line(box_surf, glow_col, (2, y_glow + 2), (self.rect.w - 3, y_glow + 2))

        # 3. Rim Lighting (Cam efektini veren keskin hatlar)
        rim_col = (200, 220, 255) if not self._card else _get_cat_color(self._card.category)
        r_alpha = int(120 * self._alpha)
        # Üst kenar (En parlak)
        pygame.draw.line(box_surf, (*rim_col, r_alpha), (10, 1), (self.rect.w - 10, 1), 1)
        # Yan kenarlar (Sönük)
        pygame.draw.line(box_surf, (*rim_col, int(r_alpha * 0.3)), (1, 10), (1, self.rect.h - 10), 1)
        pygame.draw.line(box_surf, (*rim_col, int(r_alpha * 0.3)), (self.rect.w - 1, 10), (self.rect.w - 1, self.rect.h - 10), 1)

        # 4. Dış Çerçeve
        pygame.draw.rect(box_surf, (*_BORDER, int(255 * self._alpha)), draw_rect, width=1, border_radius=8)

        # 🎨 Holografik Pulse (Minimap ile senkron) - Sadece kart varsa parlasın
        if self._card is not None:
            import math
            pulse_alpha = math.sin(self._time * 3) * 30 + 30
            # Kategori rengiyle pulse (rim_col zaten kategoriye göre set edildi)
            pygame.draw.rect(box_surf, (*rim_col, int(pulse_alpha * self._alpha)), draw_rect, width=3, border_radius=8)

        if self._card is None:
            self._render_placeholder(box_surf, draw_rect)
        else:
            self._render_card(box_surf, self._card, draw_rect)

        # Ana yüzeye uygula (y_offset ile)
        surface.blit(box_surf, (self.rect.x, self.rect.y + int(self._y_offset)))

    # ------------------------------------------------------------------ #
    def _render_placeholder(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Kart seçilmemişken gösterilen boş durum."""
        font_cache.render_text(surface, "HOVER A CARD",
                               font_cache.regular(10), (*_TEXT_DIM, int(255 * self._alpha)),
                               rect, align="center", v_align="center")

    # ------------------------------------------------------------------ #
    def _render_card(self, surface: pygame.Surface, card: CardData, rect: pygame.Rect) -> None:
        pad_x  = 12
        pad_y  = 8  # 12 -> 8 (Yatay genişliği koruyup dikeyde yukarı çekiyoruz)
        inner  = pygame.Rect(rect.x + pad_x, rect.y + pad_y,
                             rect.w - pad_x * 2, rect.h - pad_y * 2)
        y      = inner.y
        line_h = 24 
        a_int  = int(255 * self._alpha)
 
        # 🎨 Category Color
        cat_color = _get_cat_color(card.category)
 
        # ── 1. İsim ──────────────────────────────────────────────────
        name_r = pygame.Rect(inner.x, y, inner.w, line_h)
        font_cache.render_text(surface, card.name, font_cache.bold(16), (*cat_color, a_int), name_r)
        
        # 🎨 Category Accent (Çizgiyi isme daha yakın çekiyoruz)
        accent_y = y + line_h - 1 # 2px yukarı kaydı
        pygame.draw.line(surface, (*cat_color, int(180 * self._alpha)), (inner.x, accent_y), (inner.right, accent_y), 2)
        y += line_h + 8 # Spacing daraltıldı
 
        # ── 2. Tagler (Kategori + Pasif Tipi + Sinerji/Independent) ──
        # Bold 9 -> 11 (Daha okunaklı etiketler)
        tag_r = pygame.Rect(inner.x, y, inner.w, 18)
        
        tag_cat_color = [max(0, min(255, c + 40)) for c in cat_color]
        tag_cat_color = (*tag_cat_color, int(180 * self._alpha))
        
        passive_color = _PASSIVE_COLORS.get(card.passive_label, (180, 180, 180))
        
        font_cache.render_text(surface, f"[{card.category}]", font_cache.bold(11), tag_cat_color, tag_r, align="left")
        
        if card.synergy_group:
            from v2.constants import Colors
            grp_color = {"MIND": Colors.MIND, "CONNECTION": Colors.CONNECTION, "EXISTENCE": Colors.EXISTENCE}.get(card.synergy_group, (150, 150, 160))
            font_cache.render_text(surface, f"<{card.synergy_group}>", font_cache.bold(11), grp_color, tag_r, align="right")
        else:
            font_cache.render_text(surface, f"<INDEPENDENT>", font_cache.bold(11), (160, 160, 170), tag_r, align="right")
            
        y += 20 # 24 -> 20 (Header'dan kazanılan 4px)
        top_divider_y = y + 2
        pygame.draw.line(surface, (*_DIVIDER, int(120 * self._alpha)), (self.rect.x + 8, top_divider_y), (self.rect.right - 8, top_divider_y))
        top_y = top_divider_y + 4 # 8 -> 4 (Divider'dan hemen sonra başlasın)
 
        # ── 3. Alt Stat Konumlandırması (Sabit Alt Anchor) ─────────────
        # Stat satırları 20 -> 18px (Daha kompakt)
        stats_h = 54
        stats_start_y = inner.bottom - stats_h
        
        for i in range(3):
            y_line = stats_start_y + i * 18
            pygame.draw.line(surface, (50, 60, 80, int(120 * self._alpha)), (inner.x, y_line), (inner.right, y_line), 1)
        
        bottom_divider_y = stats_start_y - 8
        pygame.draw.line(surface, (*_DIVIDER, int(120 * self._alpha)), (self.rect.x + 8, bottom_divider_y), (self.rect.right - 8, bottom_divider_y))
 
        # ── 4. Orta Pasif Bölümü (Dinamik Ortalama) ────────────────────
        # Regular 12 -> 11 (Kompaktlık için)
        p_font = font_cache.regular(11)
        lines  = _wrap_text(card.passive_effect, p_font, inner.w)
        lines = lines[:3] 
        
        # Başlık 18 -> 14, metin satırları 16 -> 14
        content_h = 16 + (len(lines) * 14)
        avail_h = bottom_divider_y - top_y
        # Hafif yukarı yaslayarak (floor) daha fazla alan kazanıyoruz
        mid_start_y = top_y + max(1, (avail_h - content_h) // 3) 
        
        passive_lbl_r = pygame.Rect(inner.x, mid_start_y, inner.w, 16)
        label = f"◈ {card.passive_label}"
        # Bold 14 -> 12
        font_cache.render_text(surface, label, font_cache.bold(12), passive_color, passive_lbl_r)
        
        text_y = mid_start_y + 18
        for line in lines:
            lr = pygame.Rect(inner.x, text_y, inner.w, 14)
            font_cache.render_text(surface, line, p_font, (220, 225, 235), lr)
            text_y += 14
 
        # ── 5. Stat Verilerini Çizme ───────────────────────────────────
        stats = list(card.stats.items())
        col_w = inner.w // 2
        for i, (stat_name, val) in enumerate(stats[:6]):
            col = i % 2
            sx  = inner.x + col * col_w
            sy  = stats_start_y + (i // 2) * 18
            stat_r = pygame.Rect(sx, sy, col_w, 18)
            
            label  = f"{stat_name[:3].upper()}:"
            font_cache.render_text(surface, label, font_cache.mono(10), (160, 170, 180), stat_r, align="left")
            
            val_r = pygame.Rect(sx + 36, sy, col_w - 36, 18)
            val_color = _stat_color(stat_name, val)
            # Bold 14 -> 12
            font_cache.render_text(surface, str(int(val)), font_cache.bold(12), val_color, val_r, align="left")


def _stat_color(stat_name: str, val: int) -> tuple[int, int, int]:
    """Stat grubuna göre sinerji rengini al ve gücüne göre parlat."""
    from v2.constants import Colors
    
    if stat_name in ("Secret", "Meaning", "Intelligence", "Trace"):
        c_high = (120, 200, 255) # MIND Neon (Cıvıl cıvıl mavi)
        c_mid  = Colors.MIND
        c_low  = ( 30,  60, 120)
        c_min  = ( 15,  30,  60) # MIND Ölü
    elif stat_name in ("Power", "Durability", "Size", "Speed"):
        c_high = (255,  80,  80) # EXISTENCE Neon (Canlı kırmızı)
        c_mid  = Colors.EXISTENCE
        c_low  = (100,  30,  30)
        c_min  = ( 50,  15,  15) # EXISTENCE Ölü
    else:
        c_high = (100, 255, 150) # CONNECTION Neon (Parlak yeşil)
        c_mid  = Colors.CONNECTION
        c_low  = ( 30, 100,  50)
        c_min  = ( 15,  50,  25) # CONNECTION Ölü
        
    if val >= 8: return c_high
    if val >= 6: return c_mid
    if val >= 4: return c_low
    return c_min

def _get_cat_color(category: str) -> tuple[int, int, int]:
    """Minimap ile senkronize kategori renklerini döndürür."""
    # Mapping for normalization
    _MAP = {
        "Mythology & Gods":     (248, 222, 34),
        "Art & Culture":        (240, 60, 110),
        "Nature & Biology":     (60, 255, 80),
        "Nature & Creatures":   (60, 255, 80),
        "Cosmos & Space":       (140, 80, 255),
        "Science & Technology": (3, 190, 240),
        "History & Civilizations": (255, 120, 40),
    }
    # Fallback logic for various naming versions
    if category in _MAP: return _MAP[category]
    
    cat_upper = category.upper()
    if "MYTH" in cat_upper: return (248, 222, 34)
    if "ART" in cat_upper:  return (240, 60, 110)
    if "NATUR" in cat_upper: return (60, 255, 80)
    if "COSMO" in cat_upper: return (140, 80, 255)
    if "SCIEN" in cat_upper: return (3, 190, 240)
    if "HIST" in cat_upper:  return (255, 120, 40)
    
    return (120, 160, 200) # Default Blue-ish
