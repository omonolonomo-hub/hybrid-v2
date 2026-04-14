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

    def set_card(self, card: CardData | None) -> None:
        self._card = card

    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        # ── Arka Plan ──────────────────────────────────────────────────
        pygame.draw.rect(surface, _BG, self.rect, border_radius=8)
        pygame.draw.rect(surface, _BORDER, self.rect, width=1, border_radius=8)

        if self._card is None:
            self._render_placeholder(surface)
            return

        self._render_card(surface, self._card)

    # ------------------------------------------------------------------ #
    def _render_placeholder(self, surface: pygame.Surface) -> None:
        """Kart seçilmemişken gösterilen boş durum."""
        lbl = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h)
        font_cache.render_text(surface, "HOVER A CARD",
                               font_cache.regular(10), _TEXT_DIM,
                               lbl, align="center", v_align="center")

    # ------------------------------------------------------------------ #
    def _render_card(self, surface: pygame.Surface, card: CardData) -> None:
        pad    = 8
        inner  = pygame.Rect(self.rect.x + pad, self.rect.y + pad,
                             self.rect.w - pad * 2, self.rect.h - pad * 2)
        y      = inner.y
        line_h = 16

        # ── 1. Rarity + İsim ───────────────────────────────────────────
        rarity_r = pygame.Rect(inner.x, y, inner.w, line_h)
        font_cache.render_text(surface, card.rarity, font_cache.bold(12), card.rarity_color, rarity_r)
        name_x = inner.x + font_cache.bold(12).size(card.rarity + " ")[0]
        name_r = pygame.Rect(name_x, y, inner.right - name_x, line_h)
        font_cache.render_text(surface, card.name, font_cache.bold(12), card.rarity_color, name_r)
        y += line_h + 2

        # ── 2. Tagler (Kategori + Pasif Tipi + Sinerji/Inpependent) ──
        tag_r = pygame.Rect(inner.x, y, inner.w, 14)
        cat_color = (120, 160, 200)
        passive_color = _PASSIVE_COLORS.get(card.passive_label, (180, 180, 180))
        
        # Sol Etiketler
        font_cache.render_text(surface, f"[{card.category}]", font_cache.bold(9), cat_color, tag_r, align="left")
        
        # Sağ Etiket (Sinerji Grubu)
        if card.synergy_group:
            from v2.constants import Colors
            grp_color = {"MIND": Colors.MIND, "CONNECTION": Colors.CONNECTION, "EXISTENCE": Colors.EXISTENCE}.get(card.synergy_group, _TEXT_DIM)
            font_cache.render_text(surface, f"<{card.synergy_group}>", font_cache.bold(9), grp_color, tag_r, align="right")
        else:
            font_cache.render_text(surface, f"<INDEPENDENT>", font_cache.bold(9), (180, 180, 190), tag_r, align="right")
            
        y += 16
        top_divider_y = y + 2
        pygame.draw.line(surface, _DIVIDER, (self.rect.x + 4, top_divider_y), (self.rect.right - 4, top_divider_y))
        top_y = top_divider_y + 4

        # ── 3. Alt Stat Konumlandırması (Sabit Alt Anchor) ─────────────
        # Statlar 3 satırdan oluşuyor. Her satır 15px.
        stats_h = 45
        stats_start_y = inner.bottom - stats_h
        
        # Alt ayırıcı çizgi
        bottom_divider_y = stats_start_y - 6
        pygame.draw.line(surface, _DIVIDER, (self.rect.x + 4, bottom_divider_y), (self.rect.right - 4, bottom_divider_y))

        # ── 4. Orta Pasif Bölümü (Dinamik Ortalama) ────────────────────
        p_font = font_cache.regular(10)
        lines  = _wrap_text(card.passive_effect, p_font, inner.w)
        lines = lines[:3] # En fazla 3 satır
        
        # İçerik yüksekliği hesapla
        content_h = 14 + (len(lines) * 13) # Başlık 14px + metin satırları 13px
        
        # Top_y ile bottom_divider_y arasındaki boşluğu bul
        avail_h = bottom_divider_y - top_y
        
        # İçeriği dikey olarak ortala (taşmayı önlemek için max sınır ekliyoruz)
        mid_start_y = top_y + max(2, (avail_h - content_h) // 2)
        
        passive_lbl_r = pygame.Rect(inner.x, mid_start_y, inner.w, 14)
        font_cache.render_text(surface, f"Passive: {card.passive_label}", font_cache.bold(11), passive_color, passive_lbl_r)
        
        text_y = mid_start_y + 16
        for line in lines:
            lr = pygame.Rect(inner.x, text_y, inner.w, 13)
            font_cache.render_text(surface, line, p_font, (220, 225, 235), lr)
            text_y += 13

        # ── 5. Stat Verilerini Çizme ───────────────────────────────────
        stats = list(card.stats.items())
        col_w = inner.w // 2
        for i, (stat_name, val) in enumerate(stats[:6]):
            col = i % 2
            sx  = inner.x + col * col_w
            sy  = stats_start_y + (i // 2) * 15
            stat_r = pygame.Rect(sx, sy, col_w, 15)
            
            label  = f"{stat_name[:3].upper()}:"
            font_cache.render_text(surface, label, font_cache.mono(10), (160, 170, 180), stat_r)
            
            val_r = pygame.Rect(sx + 34, sy, col_w - 34, 15)
            val_color = _stat_color(stat_name, val)
            font_cache.render_text(surface, str(val), font_cache.bold(12), val_color, val_r)


def _stat_color(stat_name: str, val: int) -> tuple[int, int, int]:
    """Stat grubuna göre sinerji rengini al ve gücüne göre parlat."""
    from v2.constants import Colors
    
    if stat_name in ("Secret", "Meaning", "Intelligence"):
        c_high = (100, 180, 255) # MIND Neon (Mavi - mora kaymayacak)
        c_mid  = Colors.MIND
        c_low  = ( 40,  80, 160) # MIND Koyu
        c_min  = ( 20,  40, 100)
    elif stat_name in ("Power", "Durability", "Size", "Gravity", "Trace"):
        c_high = (255,  60,  60) # EXISTENCE Neon (kan kırmızısı)
        c_mid  = Colors.EXISTENCE
        c_low  = (140,  50,  50) # EXISTENCE Koyu
        c_min  = ( 80,  30,  30)
    else:
        c_high = ( 80, 255, 120) # CONNECTION Neon (Yeşil - camgöbeği değil)
        c_mid  = Colors.CONNECTION
        c_low  = ( 40, 130,  60) # CONNECTION Koyu
        c_min  = ( 20,  80,  40)
        
    if val >= 8: return c_high
    if val >= 6: return c_mid
    if val >= 4: return c_low
    return c_min
