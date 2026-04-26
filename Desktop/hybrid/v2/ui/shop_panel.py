import logging
import math
from dataclasses import dataclass

import pygame

from v2.constants import Colors, Layout, Screen
from v2.core.exceptions import AutochessException
from v2.core.public_state import ShopViewState
from v2.ui import font_cache
from v2.ui.card_flip import CardFlip

logger = logging.getLogger(__name__)

_FALLBACK_BACK_COLOR = (12, 14, 20)
_FALLBACK_FRONT_COLOR = (20, 60, 100)


@dataclass(frozen=True)
class ShopPanelAction:
    kind: str
    slot_index: int = -1
    card_name: str | None = None


def _make_fallback_surface(color: tuple, w: int, h: h) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    radius = h / 2
    points = [
        (
            cx + radius * math.cos(math.radians(60 * i - 30)),
            cy + radius * math.sin(math.radians(60 * i - 30)),
        )
        for i in range(6)
    ]
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (60, 65, 75), points, 2)
    return surf.convert_alpha()


class ShopPanel:
    def __init__(self):
        self.rect = pygame.Rect(0, Layout.SHOP_PANEL_Y, Screen.W, Layout.SHOP_PANEL_H)

        # ── Golden Ratio Layout ──────────────────────────────────────────────
        # Görünür alanı ikiye bölüyoruz (Altın Oran = 1.618)
        w_vis = Screen.W - Layout.SIDEBAR_LEFT_W
        phi = 1.618034
        
        cards_zone_w = int(w_vis / phi)
        controls_zone_w = w_vis - cards_zone_w
        
        # 1. Cards Placement (Golden Area'nın ortasına hizalı)
        card_w = Layout.SHOP_CARD_W
        card_gap = 24 # Nefes payı 20'den 24'e çıkarıldı
        total_cards_w = (card_w * Layout.SHOP_SLOTS) + (card_gap * (Layout.SHOP_SLOTS - 1))
        
        start_x = Layout.SIDEBAR_LEFT_W + (cards_zone_w - total_cards_w) // 2
        start_y = self.rect.y + (self.rect.h - Layout.SHOP_CARD_H) // 2
        
        self.card_rects: list[pygame.Rect] = []
        for i in range(Layout.SHOP_SLOTS):
            cx = start_x + (card_w + card_gap) * i
            self.card_rects.append(pygame.Rect(cx, start_y, card_w, Layout.SHOP_CARD_H))

        # 2. Controls Placement (Stats -> Buttons -> InfoBox)
        ctrl_start_x = Layout.SIDEBAR_LEFT_W + cards_zone_w
        margin_right = 20
        gap = 16
        info_w = 340
        
        rem_w = controls_zone_w - margin_right - info_w - (gap * 2)
        btn_w = 124
        stats_w = rem_w - btn_w
        
        self.stats_rect = pygame.Rect(ctrl_start_x, start_y, stats_w, Layout.SHOP_CARD_H)
        
        btn_x = self.stats_rect.right + gap
        btn_h = 44
        btn_gap = (Layout.SHOP_CARD_H - (3 * btn_h)) // 2 # Dikeyde tam dengeli
        
        self.reroll_rect = pygame.Rect(btn_x, start_y, btn_w, btn_h)
        self.lock_rect   = pygame.Rect(btn_x, start_y + btn_h + btn_gap, btn_w, btn_h)
        self.ready_rect  = pygame.Rect(btn_x, start_y + 2 * (btn_h + btn_gap), btn_w, btn_h)
        
        info_x = self.reroll_rect.right + gap
        self.info_rect = pygame.Rect(info_x, start_y, info_w, Layout.SHOP_CARD_H)
        # ──────────────────────────────────────────────────────────────────

        self.bg_surface = pygame.Surface((Screen.W, Layout.SHOP_PANEL_H), pygame.SRCALPHA).convert_alpha()
        self.bg_surface.fill((10, 12, 20, 245))
        
        # Alt ayırıcı çizgi (Minimap stili frameless border)
        pygame.draw.line(self.bg_surface, (42, 58, 92, 100), (0, Layout.SHOP_PANEL_H - 1), (Screen.W, Layout.SHOP_PANEL_H - 1), 1)

        self._locked_state = False
        self._gold = 0
        self._phase = "STATE_PREPARATION"
        self._probabilities: dict[str, float] = {"1": 100.0}
        self._card_names: list[str | None] = [None] * Layout.SHOP_SLOTS
        
        # Cache for tier probability text surfaces (invalidated on probability change)
        self._prob_text_cache: dict[tuple[str, float], pygame.Surface] = {}

        from v2.ui.font_cache import mono, render_text as _render_text

        try:
            if not pygame.font.get_init():
                pygame.font.init()
            decal_font = mono(9)
        except AutochessException:
            pygame.font.init()
            decal_font = pygame.font.SysFont("Courier", 9)
        _render_text(
            self.bg_surface,
            "SHOP_BAY // ONLINE",
            decal_font,
            (80, 100, 130, 120),
            pygame.Rect(14, 8, 180, 14),
        )

        # Kart Yuvaları (Premium DCI Hexagon Slots)
        for slot_rect in self.card_rects:
            lx = slot_rect.x - self.rect.x
            ly = slot_rect.y - self.rect.y
            lw, lh = slot_rect.w, slot_rect.h
            cx, cy = lx + lw / 2, ly + lh / 2
            radius = lh / 2
            
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

            # İç Zemin Çukuru (Void / Dark hex)
            pygame.draw.polygon(self.bg_surface, (6, 8, 12, 220), points)
            
            # Hexagon Çerçeve (Mat tactical çizgi)
            pygame.draw.polygon(self.bg_surface, (30, 40, 55, 150), points, width=1)
            
            # Siberpunk Vurgular (Üst ve alt noktalarda veri portu görünümü)
            # points[2] = Bottom Center (90 deg), points[5] = Top Center (270 deg)
            pygame.draw.circle(self.bg_surface, (80, 140, 255, 100), points[2], 2)
            pygame.draw.circle(self.bg_surface, (80, 140, 255, 100), points[5], 2)

        self._flips: list[CardFlip] = []
        self._build_flips()

    def _is_evolved_card(self, card_name: str | None) -> bool:
        if not card_name:
            return False
        try:
            from v2.core.card_database import CardDatabase

            data = CardDatabase.get().lookup(card_name)
            if not data:
                return False
            return getattr(data, "rarity", None) == "E" or getattr(data, "rarity_level", None) == "E"
        except AutochessException:
            return False

    # ------------------------------------------------------------------ #
    # Public Getters (Encapsulation)                                      #
    # ------------------------------------------------------------------ #
    def get_card_name(self, slot_idx: int) -> str | None:
        """Public getter for card name at slot index."""
        if 0 <= slot_idx < len(self._card_names):
            return self._card_names[slot_idx]
        return None
    
    def get_card_names(self) -> list[str | None]:
        """Public getter for all card names."""
        return list(self._card_names)

    def _build_flips(self) -> None:
        self._flips.clear()
        try:
            from v2.assets.loader import AssetLoader

            loader = AssetLoader.get()
            loader_ok = True
        except AutochessException:
            loader_ok = False
            loader = None

        for i, slot_rect in enumerate(self.card_rects):
            w, h = slot_rect.width, slot_rect.height
            name = self._card_names[i]
            evolved = self._is_evolved_card(name)

            if loader_ok and name:
                try:
                    front = pygame.transform.scale(loader.get_card_front(name), (w, h))
                    back = pygame.transform.scale(loader.get_card_back(name), (w, h))
                except FileNotFoundError:
                    front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                    back = _make_fallback_surface(_FALLBACK_BACK_COLOR, w, h)
            else:
                front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                back = _make_fallback_surface(_FALLBACK_BACK_COLOR, w, h)

            flip = CardFlip(back, front, slot_rect, evolved=evolved, evolved_color=Colors.PLATINUM)
            flip.flip_progress = 1.0
            flip._flip_target = 1.0
            self._flips.append(flip)

    def assign_shop(self, card_names: list[str | None]) -> None:
        for i, name in enumerate(card_names[:Layout.SHOP_SLOTS]):
            self._card_names[i] = name
        self._build_flips()

    def apply_view_state(self, shop_state: ShopViewState, *, gold: int, phase: str) -> None:
        self._gold = gold
        self._phase = phase
        self._locked_state = bool(shop_state.is_locked)
        
        # Invalidate probability text cache if probabilities changed
        new_probs = dict(shop_state.rarity_probabilities)
        if new_probs != self._probabilities:
            self._prob_text_cache.clear()
        self._probabilities = new_probs

        new_names = list(shop_state.slots[:Layout.SHOP_SLOTS])
        while len(new_names) < Layout.SHOP_SLOTS:
            new_names.append(None)

        if new_names == self._card_names:
            return

        is_just_purchase = True
        for i in range(Layout.SHOP_SLOTS):
            if new_names[i] != self._card_names[i] and new_names[i] is not None:
                is_just_purchase = False
                break

        if is_just_purchase:
            from v2.ui.card_flip import MockCardBox

            for i in range(Layout.SHOP_SLOTS):
                self._card_names[i] = new_names[i]
                if new_names[i] is None and i < len(self._flips) and not isinstance(self._flips[i], MockCardBox):
                    self._flips[i] = MockCardBox(self.card_rects[i])
        else:
            self.assign_shop(new_names)

    def sync(self, shop_state: ShopViewState = None, *, gold: int = 0, phase: str = "STATE_PREPARATION") -> None:
        if shop_state is not None:
            self.apply_view_state(shop_state, gold=gold, phase=phase)

    def update(self, dt_ms: float) -> None:
        for flip in self._flips:
            flip.update(dt_ms)

    def handle_hover(self, mouse_pos: tuple[int, int]) -> int:
        hovered_idx = -1
        for i, (slot_rect, flip) in enumerate(zip(self.card_rects, self._flips)):
            if slot_rect.collidepoint(mouse_pos):
                flip.hover_start()
                hovered_idx = i
            else:
                flip.hover_end()
        return hovered_idx

    def get_action_for_event(self, event: pygame.event.Event) -> ShopPanelAction | None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.ready_rect.collidepoint(event.pos) and self._phase == "STATE_PREPARATION":
            logger.debug("READY clicked")
            return ShopPanelAction("ready")

        if self.reroll_rect.collidepoint(event.pos):
            logger.debug("REROLL clicked")
            return ShopPanelAction("reroll")

        if self.lock_rect.collidepoint(event.pos):
            logger.debug("LOCK clicked")
            return ShopPanelAction("lock")

        for idx, card_rect in enumerate(self.card_rects):
            if card_rect.collidepoint(event.pos):
                card_name = self._card_names[idx] if idx < len(self._card_names) else None
                logger.debug("BUY slot=%d card='%s'", idx, card_name)
                return ShopPanelAction("buy", slot_index=idx, card_name=card_name)

        return None

    def handle_event(self, event: pygame.event.Event) -> ShopPanelAction | None:
        """Legacy wrapper kept for tests/callers; returns parsed UI intent only."""
        return self.get_action_for_event(event)

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg_surface, self.rect)

        for flip in self._flips:
            flip.render(surface)

        # Query mouse position once for all button renders
        mouse_pos = pygame.mouse.get_pos()

        can_reroll = self._gold >= 2
        # Taktiksel, doygun amber/turuncu
        reroll_color = (240, 160, 40) if can_reroll else (100, 100, 100)
        self._render_dci_button(surface, self.reroll_rect, "REROLL [2G]", reroll_color, can_reroll, mouse_pos, icon_name="SYNC")

        # Kilitsiz: Taktiksel çelik mavisi | Kilitli: Sinyal kırmızısı
        lock_color = (240, 60, 60) if self._locked_state else (120, 140, 160)
        lock_label = "LOCKED" if self._locked_state else "LOCK SHOP"
        self._render_dci_button(surface, self.lock_rect, lock_label, lock_color, True, mouse_pos, icon_name="LOCK")

        if self._phase == "STATE_PREPARATION":
            # Göz yormayan, okunaklı "Emerald" taktik yeşili
            self._render_dci_button(surface, self.ready_rect, "READY PHASE", (40, 190, 100), True, mouse_pos, icon_name="READY")

        probs = dict(self._probabilities)
        # Sadece var olan oranları sayalım (Dikey hizalama için)
        active_tiers = [r for r in ["1", "2", "3", "4", "5"] if probs.get(r, 0.0) > 0 or r in ["1", "2"]]
        row_h = 24
        total_stats_h = len(active_tiers) * row_h
        sy = self.stats_rect.y + (self.stats_rect.h - total_stats_h) // 2 # Dikey merkezleme
        
        prob_font = font_cache.mono(9)
        for i, rarity in enumerate(active_tiers):
            probability = probs.get(rarity, 0.0)
            cache_key = (rarity, probability)
            
            # Check cache first
            if cache_key not in self._prob_text_cache:
                # Render to cache
                text = f"Tier {rarity}: %{probability:.1f}"
                color = (160, 160, 180) if probability > 0 else (60, 65, 80)
                try:
                    self._prob_text_cache[cache_key] = prob_font.render(text, True, color)
                except pygame.error:
                    continue  # Font invalid (test teardown) — skip silently
            
            # Blit cached surface
            text_surf = self._prob_text_cache[cache_key]
            tw, th = text_surf.get_size()
            target_rect = pygame.Rect(self.stats_rect.x, sy + i * row_h, self.stats_rect.w, row_h)
            x = target_rect.x + (target_rect.w - tw) // 2  # center align
            y = target_rect.y + (target_rect.h - th) // 2  # center v_align
            surface.blit(text_surf, (x, y))


    def _render_dci_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: tuple,
        enabled: bool,
        mouse_pos: tuple[int, int],
        icon_name: str = None,
    ):
        is_hover = rect.collidepoint(mouse_pos) and enabled

        cut = 8
        points = [
            (rect.x + cut, rect.y),
            (rect.right - cut, rect.y),
            (rect.right, rect.y + cut),
            (rect.right, rect.bottom - cut),
            (rect.right - cut, rect.bottom),
            (rect.left + cut, rect.bottom),
            (rect.left, rect.bottom - cut),
            (rect.left, rect.y + cut),
        ]

        bg_color = (10, 15, 25, 235) if enabled else (20, 22, 28, 180)
        pygame.draw.polygon(surface, bg_color, points)

        if enabled:
            inner_color = (*color, 45) if is_hover else (*color, 20)
            pygame.draw.polygon(surface, inner_color, points)

        border_color = (
            int(color[0] * 0.2 + 25 * 0.8),
            int(color[1] * 0.2 + 35 * 0.8),
            int(color[2] * 0.2 + 55 * 0.8),
            180,
        ) if enabled else (50, 55, 70, 120)
        pygame.draw.polygon(surface, border_color, points, width=1)

        if enabled:
            pygame.draw.line(surface, (255, 255, 255, 60), (rect.x + cut, rect.y + 1), (rect.right - cut, rect.y + 1), 1)
            if is_hover:
                pygame.draw.polygon(surface, (255, 255, 255, 100), points, width=2)

        label_color = (255, 255, 255) if enabled else (120, 125, 140)
        icon_color = tuple(min(255, int(channel * 1.1)) for channel in color) if enabled else (80, 85, 100)

        text_rect = pygame.Rect(rect)
        if icon_name:
            icon_size = 13
            icon_y = (rect.h - icon_size) // 2
            font_cache.render_icon(surface, icon_name, icon_size, icon_color, (rect.x + 10, rect.y + icon_y), shadow=enabled)
            text_rect.x += 16
            text_rect.w -= 16

        font_cache.render_text(surface, label, font_cache.bold(12), label_color, text_rect, align="center", v_align="center", shadow=enabled)
