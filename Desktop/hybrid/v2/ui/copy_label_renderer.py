"""Copy label renderer for displaying card copy counts.

Renders "Copies: N/3" labels on card slots in shop and hand panels.
Maintains a cache of rendered text surfaces for performance.
"""

import pygame
from typing import Optional

from v2.constants import Colors
from v2.ui import font_cache


class CopyLabelRenderer:
    """Renders copy count labels on card slots with caching.
    
    Displays "Copies: N/3" text below card slots, using gold color
    when count reaches 3, otherwise using light blue-gray.
    """
    
    def __init__(self):
        """Initialize the renderer with an empty cache."""
        self._cache: dict[tuple[str, int], pygame.Surface] = {}
    
    def invalidate(self) -> None:
        """Clear the text surface cache.
        
        Should be called when card names change to force re-rendering
        with updated copy counts.
        """
        self._cache.clear()
    
    def render(
        self,
        surface: pygame.Surface,
        rects: list[pygame.Rect],
        names: list[Optional[str]],
        copies_by_name: dict[str, int]
    ) -> None:
        """Render copy labels for a list of card slots.
        
        Args:
            surface: The pygame surface to render onto
            rects: List of card slot rectangles
            names: List of card names (None for empty slots)
            copies_by_name: Dictionary mapping card names to copy counts
        """
        font = font_cache.mono(9)
        
        for slot_rect, name in zip(rects, names):
            if not name:
                continue
            
            count = copies_by_name.get(name, 0)
            cache_key = (name, count)
            
            # Check cache first
            if cache_key not in self._cache:
                # Render to cache
                text = f"Copies: {count}/3"
                color = Colors.GOLD_TEXT if count >= 3 else (200, 205, 230)
                self._cache[cache_key] = font.render(text, True, color)
            
            # Blit cached surface
            text_surf = self._cache[cache_key]
            tw, th = text_surf.get_size()
            x = slot_rect.x + (slot_rect.w - tw) // 2
            y = slot_rect.bottom - 16 + (14 - th) // 2
            surface.blit(text_surf, (x, y))
