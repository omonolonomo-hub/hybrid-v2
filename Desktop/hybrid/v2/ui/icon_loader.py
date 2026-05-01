"""
IconLoader — PNG İkon Yöneticisi
==================================
Kategori ve diğer ikonları PNG formatında yükler ve cache'ler.
Font Awesome yerine PNG kullanmak için.
"""

import os
import pygame
from typing import Optional

_ICON_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
_cache: dict[tuple[str, int], pygame.Surface] = {}


# Kategori ikon dosya eşlemeleri
CATEGORY_ICONS = {
    "Mythology & Gods": "mythology.png",
    "Art & Culture": "art.png",
    "Nature & Creatures": "nature.png",
    "Cosmos": "cosmos.png",
    "Science": "science.png",
    "History & Civilizations": "history.png",
}

# Genel ikon dosya eşlemeleri
GENERAL_ICONS = {
    "HEART": "heart.png",
    "GOLD": "gold.png",
    "SKULL": "skull.png",
    "BOLT": "stat_speed.png",           # Speed - Hız (BOLT eksikti!)
    "GEAR": "stat_intelligence.png",    # Intelligence - Zeka (GEAR eksikti!)
    "SWORD": "sword.png",
    "SHIELD": "stat_durability.png",    # Durability - Dayanıklılık (SHIELD eksikti!)
    "USER": "user.png",
    "FIRE": "fire.png",
    "LOCK": "stat_secret.png",          # Secret - Sır (LOCK eksikti!)
    "READY": "ready.png",
    "SYNC": "sync.png",
    "SHOP": "shop.png",
    "CROWN": "crown.png",
    "MEDAL": "medal.png",
    "AWARD": "award.png",
    # Stat İkonları (12 adet)
    "FIST": "stat_power.png",           # Power - Güç
    "EXPAND": "stat_size.png",          # Size - Boyut
    "FOOTPRINT": "stat_trace.png",      # Trace - İz
    "MAGNET": "stat_gravity.png",       # Gravity - Çekim
    "MUSIC": "stat_harmony.png",        # Harmony - Uyum
    "BROADCAST": "stat_spread.png",     # Spread - Yayılma
    "GEM": "stat_prestige.png",         # Prestige - Prestij
    "BOOK": "stat_meaning.png",         # Meaning - Anlam
}


def get_icon(icon_name: str, size: int, is_category: bool = False) -> Optional[pygame.Surface]:
    """
    PNG ikon yükler ve istenen boyuta ölçekler.
    
    Args:
        icon_name: İkon adı (kategori adı veya genel ikon anahtarı)
        size: Hedef boyut (piksel)
        is_category: True ise kategori ikonu, False ise genel ikon
    
    Returns:
        Ölçeklenmiş pygame.Surface veya None (dosya bulunamazsa)
    """
    key = (icon_name, size, is_category)
    if key in _cache:
        return _cache[key]
    
    # Dosya adını bul
    if is_category:
        filename = CATEGORY_ICONS.get(icon_name)
    else:
        filename = GENERAL_ICONS.get(icon_name)
    
    if not filename:
        return None
    
    path = os.path.join(_ICON_DIR, filename)
    if not os.path.exists(path):
        return None
    
    try:
        # PNG yükle
        original = pygame.image.load(path).convert_alpha()
        # İstenen boyuta ölçekle (kare olarak)
        scaled = pygame.transform.smoothscale(original, (size, size))
        _cache[key] = scaled
        return scaled
    except pygame.error:
        return None


def render_icon(
    surface: pygame.Surface,
    icon_name: str,
    size: int,
    pos: tuple[int, int],
    is_category: bool = False,
    color_tint: Optional[tuple[int, int, int]] = None,
    shadow: bool = False
) -> None:
    """
    PNG ikonu belirtilen konuma çizer.
    
    Args:
        surface: Hedef yüzey
        icon_name: İkon adı
        size: İkon boyutu (piksel)
        pos: (x, y) konumu
        is_category: Kategori ikonu mu?
        color_tint: Opsiyonel renk tonu (RGB)
        shadow: Gölge ekle
    """
    icon_surf = get_icon(icon_name, size, is_category)
    if not icon_surf:
        # Fallback: Soru işareti çiz
        font = pygame.font.SysFont("Arial", size)
        icon_surf = font.render("?", True, (150, 150, 150))
    
    # Renk tonu uygula (eğer isteniyorsa)
    if color_tint:
        icon_surf = icon_surf.copy()
        icon_surf.fill(color_tint + (0,), special_flags=pygame.BLEND_RGBA_MULT)
    
    # Gölge
    if shadow:
        shadow_surf = icon_surf.copy()
        shadow_surf.fill((0, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow_surf, (pos[0] + 1, pos[1] + 1))
    
    surface.blit(icon_surf, pos)


def clear_cache() -> None:
    """Cache'i temizle."""
    _cache.clear()
