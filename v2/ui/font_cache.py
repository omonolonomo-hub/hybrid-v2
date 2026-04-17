"""
FontCache — Merkezi Font Yöneticisi
=====================================
Tüm UI bileşenleri buradan font alır.
AssetLoader başlatılmışsa TTF kullanır, yoksa SysFont ile geri düşer.
(name, size) tuple ile cache'lenir — aynı font iki kez belleğe yüklenmez.
"""

import os
import pygame
from v2.constants import Typography

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
_cache: dict[tuple, pygame.font.Font] = {}


def get(name: str, size: int) -> pygame.font.Font:
    """
    name: Typography.FONT_UI_BOLD gibi TTF dosya adı.
    size: piksel cinsinden boyut.
    """
    key = (name, size)
    if key in _cache:
        return _cache[key]

    path = os.path.join(_FONT_DIR, name)
    if os.path.exists(path):
        font = pygame.font.Font(path, size)
    else:
        # SysFont fallback — hata vermez ama uyarı basar
        base = os.path.splitext(name)[0].lower().replace("-", " ")
        font = pygame.font.SysFont(base, size)

    _cache[key] = font
    return font

def clear_cache() -> None:
    """Testler arası veya sahne geçişlerinde eski font nesnelerini temizle."""
    _cache.clear()


def bold(size: int)   -> pygame.font.Font: return get(Typography.FONT_UI_BOLD,    size)
def regular(size: int)-> pygame.font.Font: return get(Typography.FONT_UI_REGULAR, size)
def mono(size: int)   -> pygame.font.Font: return get(Typography.FONT_MONO,       size)
def icons(size: int)  -> pygame.font.Font: return get(Typography.FONT_ICONS,      size)

# Sık kullanacağımız ikonların Unicode kodları (Font Awesome 7 Free için)
ICONS = {
    "HEART":  "\uf004", # Can (HP)
    "GOLD":   "\uf51e", # Para / Altın
    "SKULL":  "\uf54c", # Ölüm / Leş
    "BOLT":   "\uf0e7", # Enerji / Aksiyon
    "GEAR":   "\uf013", # Ayar / Sistem
    "SWORD":  "\uf71c", # Saldırı
    "SHIELD": "\uf3ed", # Savunma
    "USER":   "\uf007", # Oyuncu
    "FIRE":   "\uf06d", # Sıcaklık / Win-streak
    "LOCK":   "\uf023", # Kilit
    "READY":  "\uf04b", # Hazır / Başlat
    "SYNC":   "\uf01e", # Yenileme
    "SHOP":   "\uf07a", # Alışveriş Sepeti
    "PALETTE":"\uf53f", # Sanat / Palet
    "LEAF":   "\uf06c", # Doğa / Yaprak
    "ATOM":   "\uf5d2", # Bilim / Atom
    "BOOK":   "\uf02d", # Tarih / Kitap
    "STAR":   "\uf005", # Kozmos / Yıldız
    "ANKH":   "\uf669", # Mitoloji / Ankh
    "SEEDLING":"\uf4d8",# Doğa / Filiz
    "PLANET": "\ue0e8", # Kozmos / Satürn
    "LANDMARK":"\uf66f",# Tarih / Anıt
}

def render_icon(
    surface: pygame.Surface,
    icon_name: str,
    size: int,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    shadow: bool = False
) -> None:
    """Belirtilen ikonu istenen boyutta ve renkte çizer."""
    font = icons(size)
    char = ICONS.get(icon_name, "?")
    
    if shadow:
        shadow_surf = font.render(char, True, (0, 0, 0))
        surface.blit(shadow_surf, (pos[0] + 1, pos[1] + 1))
        
    icon_surf = font.render(char, True, color)
    surface.blit(icon_surf, pos)


def render_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    align: str = "left",   # "left" | "center" | "right"
    v_align: str = "top",  # "top"  | "center" | "bottom"
    shadow: bool = False,
    shadow_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    """
    Metni bir rect içine yerleştirip yüzeye çizer.
    align / v_align ile yatay+dikey konumlandırma.
    shadow=True → 1px siyah gölge (okunabilirlik için).
    """
    try:
        text_surf = font.render(text, True, color)
    except pygame.error:
        return   # Font geçersiz (test teardown ortamı) — sessizce devam et
    tw, th    = text_surf.get_size()

    # Yatay
    if align == "center":
        x = rect.x + (rect.w - tw) // 2
    elif align == "right":
        x = rect.right - tw
    else:
        x = rect.x

    # Dikey
    if v_align == "center":
        y = rect.y + (rect.h - th) // 2
    elif v_align == "bottom":
        y = rect.bottom - th
    else:
        y = rect.y

    if shadow:
        shadow_surf = font.render(text, True, shadow_color)
        surface.blit(shadow_surf, (x + 1, y + 1))

    surface.blit(text_surf, (x, y))
