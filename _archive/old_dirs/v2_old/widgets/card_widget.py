"""
card_widget.py
--------------
Tek bir kartı pygame Surface olarak çizen yardımcı.
Hiçbir scene veya state'e bağımlı değil.
Dışarıdan bir kart dict'i alır, pygame Surface döner.

Kullanım:
    surf = CardWidget.render(card, width=120, height=168, selected=False)
    screen.blit(surf, (x, y))
    rect = pygame.Rect(x, y, 120, 168)  # tıklama alanı için
"""

import math
import os
from typing import Dict, Any, Optional, Tuple

import pygame

from core.card_loader import RARITY_COLORS, GROUP_COLORS, STAT_TO_GROUP

# ─── Renk paleti ─────────────────────────────────────────────────────────────
C_BG         = (14, 16, 28)
C_PANEL      = (22, 26, 44)
C_BORDER     = (44, 52, 80)
C_BORDER_SEL = (0, 242, 255)
C_TEXT       = (220, 228, 248)
C_TEXT_DIM   = (100, 110, 140)
C_GOLD       = (255, 200, 50)
C_CYAN       = (0, 242, 255)


class CardWidget:
    """Stateless — tüm metodlar static/classmethod."""

    # Yüklenmiş resimlerin cache'i {path: Surface}
    _img_cache: Dict[str, pygame.Surface] = {}

    @classmethod
    def _load_img(cls, path: Optional[str], w: int, h: int) -> Optional[pygame.Surface]:
        """Resmi cache'den al ya da yükle, boyutlandır."""
        if not path:
            return None
        key = f"{path}_{w}_{h}"
        if key not in cls._img_cache:
            try:
                raw = pygame.image.load(path).convert_alpha()
                cls._img_cache[key] = pygame.transform.smoothscale(raw, (w, h))
            except Exception:
                cls._img_cache[key] = None  # type: ignore
        return cls._img_cache[key]

    @classmethod
    def render(
        cls,
        card: Dict[str, Any],
        width: int = 120,
        height: int = 168,
        selected: bool = False,
        show_back: bool = False,
        font_small: Optional[pygame.font.Font] = None,
        font_tiny: Optional[pygame.font.Font] = None,
    ) -> pygame.Surface:
        """
        Kartı çizer, Surface döner.
        font_small / font_tiny: None ise dahili varsayılan kullanılır.
        """
        surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # ── Arka plan ──
        rarity = card.get("rarity", "1")
        border_col = RARITY_COLORS.get(rarity, C_BORDER)
        sel_col = C_BORDER_SEL if selected else border_col

        # Yuvarlatılmış kart çerçevesi
        pygame.draw.rect(surf, C_PANEL,  (0, 0, width, height), border_radius=10)
        pygame.draw.rect(surf, sel_col,  (0, 0, width, height), 2, border_radius=10)

        # ── Kart resmi ──
        img_h = int(height * 0.52)
        img_path = card.get("back_img_path") if show_back else card.get("card_img_path")
        img = cls._load_img(img_path, width - 4, img_h)
        if img:
            surf.blit(img, (2, 2))
        else:
            # Resim yoksa renk bloğu
            group_col = GROUP_COLORS.get(card.get("dominant_group", "EXISTENCE"), (80, 80, 120))
            pygame.draw.rect(surf, group_col, (2, 2, width - 4, img_h), border_radius=8)

        # ── Rarity şeridi ──
        stripe_y = img_h + 2
        pygame.draw.rect(surf, border_col, (0, stripe_y, width, 4))

        # ── Fontlar ──
        if font_small is None:
            font_small = pygame.font.SysFont("segoeui", max(11, width // 10))
        if font_tiny is None:
            font_tiny = pygame.font.SysFont("segoeui", max(9, width // 13))

        text_y = stripe_y + 6

        # ── Kart adı ──
        name = card.get("name", "?")
        name_surf = font_small.render(name[:16], True, C_TEXT)
        surf.blit(name_surf, (4, text_y))
        text_y += name_surf.get_height() + 2

        # ── Kategori ──
        cat = card.get("category", "")
        cat_surf = font_tiny.render(cat[:18], True, C_TEXT_DIM)
        surf.blit(cat_surf, (4, text_y))
        text_y += cat_surf.get_height() + 4

        # ── Stats (max 6) ──
        stats = card.get("stats", {})
        for stat_name, val in list(stats.items())[:6]:
            group = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            col = GROUP_COLORS.get(group, C_TEXT_DIM)
            # Küçük renkli nokta
            pygame.draw.circle(surf, col, (8, text_y + 4), 3)
            label = font_tiny.render(f"{stat_name[:8]}: {val}", True, C_TEXT)
            surf.blit(label, (14, text_y))
            text_y += label.get_height() + 1
            if text_y > height - 12:
                break

        # ── Altın fiyatı (sağ alt) ──
        cost = card.get("cost", 0)
        cost_surf = font_small.render(f"💰{cost}", True, C_GOLD)
        surf.blit(cost_surf, (width - cost_surf.get_width() - 4, height - cost_surf.get_height() - 4))

        # ── Seçim parıltısı ──
        if selected:
            glow = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*C_BORDER_SEL, 30), (0, 0, width, height), border_radius=10)
            surf.blit(glow, (0, 0))

        return surf

    @classmethod
    def render_mini(
        cls,
        card: Dict[str, Any],
        size: int = 64,
        selected: bool = False,
    ) -> pygame.Surface:
        """
        Küçük hex şeklinde kart (el paneli için).
        size × size kare içine sığdırılmış hex.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        rarity = card.get("rarity", "1")
        border_col = RARITY_COLORS.get(rarity, C_BORDER)
        if selected:
            border_col = C_BORDER_SEL

        # Hex poligon
        cx, cy, r = size // 2, size // 2, size // 2 - 2
        points = [
            (cx + r * math.cos(math.radians(60 * i - 30)),
             cy + r * math.sin(math.radians(60 * i - 30)))
            for i in range(6)
        ]
        pygame.draw.polygon(surf, C_PANEL, points)
        pygame.draw.polygon(surf, border_col, points, 2)

        # Kart resmi hex içine kırpılmış
        img_size = int(r * 1.6)
        img = cls._load_img(card.get("card_img_path"), img_size, img_size)
        if img:
            img_x = cx - img_size // 2
            img_y = cy - img_size // 2
            # Hex maskesi
            mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.polygon(mask_surf, (255, 255, 255, 255), points)
            tmp = pygame.Surface((size, size), pygame.SRCALPHA)
            tmp.blit(img, (img_x, img_y))
            tmp.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(tmp, (0, 0))

        # Grup rengi çerçeve
        group_col = GROUP_COLORS.get(card.get("dominant_group", "EXISTENCE"), border_col)
        pygame.draw.polygon(surf, group_col, points, 2)

        # Seçim iç parlaması
        if selected:
            glow = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (*C_BORDER_SEL, 40), points)
            surf.blit(glow, (0, 0))

        return surf

    @classmethod
    def clear_cache(cls):
        cls._img_cache.clear()
