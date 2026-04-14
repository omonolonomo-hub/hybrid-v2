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
