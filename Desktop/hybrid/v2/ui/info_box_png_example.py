"""
PNG İkon Kullanım Örneği
=========================
info_box_new1.py'deki kategori ikonlarını PNG ile değiştirmek için örnek kod.

KULLANIM:
1. v2/assets/icons/ klasörüne PNG dosyalarını ekleyin:
   - science.png
   - mythology.png
   - art.png
   - nature.png
   - cosmos.png
   - history.png

2. info_box_new1.py'de ilgili bölümü aşağıdaki gibi değiştirin:
"""

import pygame
from v2.ui import icon_loader

# ÖNCEKİ KOD (Font Awesome ile):
"""
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
"""

# YENİ KOD (PNG ile):
"""
# PNG ikon çiz
icon_loader.render_icon(
    surface=surface,
    icon_name=card.category,  # "Science", "Mythology & Gods", vb.
    size=cat_icon_sz,
    pos=(inner.x, icy),
    is_category=True,
    color_tint=None,  # Renk tonu istemiyorsanız None
    shadow=True
)

# Alpha değerini ayarla (gerekirse)
icon_surf = icon_loader.get_icon(card.category, cat_icon_sz, is_category=True)
if icon_surf:
    icon_surf = icon_surf.copy()
    icon_surf.set_alpha(int(255 * self._alpha))
    if shadow:
        shadow_surf = icon_surf.copy()
        shadow_surf.fill((0, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow_surf, (inner.x + 1, icy + 1))
    surface.blit(icon_surf, (inner.x, icy))
"""


# LOBBY PANEL İÇİN ÖRNEK (lobby_panel.py):
"""
# ÖNCEKİ:
icon_char = font_cache.ICONS.get(icon_name, "?")
icon_size_hd = int(avatar_size_hd * 0.32)
icon_font = font_cache.icons(icon_size_hd)
icon_surf = icon_font.render(icon_char, True, rank_col)

# YENİ:
icon_loader.render_icon(
    surface=avatar_hd,
    icon_name=icon_name,  # "CROWN", "MEDAL", "AWARD"
    size=icon_size_hd,
    pos=(center_hd - icon_size_hd // 2, int(center_hd * 0.68) - icon_size_hd // 2),
    is_category=False,
    color_tint=rank_col,
    shadow=False
)
"""
