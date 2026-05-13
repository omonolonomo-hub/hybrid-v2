import pygame
import math
from v2.constants import Layout, Colors, Screen
from v2.ui.card_flip import CardFlip
from v2.core.exceptions import AutochessException

# Fallback back surface (AssetLoader yoksa kullanalım)
_FALLBACK_BACK_COLOR  = (38, 42, 62)
_FALLBACK_FRONT_COLOR = (20, 60, 100)

def _make_fallback_surface(color: tuple, w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # Hexagon polygon çiz
    cx, cy = w // 2, h // 2
    radius = h / 2
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (80, 100, 130), points, 2)
    return surf.convert_alpha()


class HandPanel:
    def __init__(self):
        # ── Ana Panel Rect (Full Width Bar -> Cropped for LobbyPanel) ─
        panel_w = Screen.W - Layout.SIDEBAR_RIGHT_W - 20
        self.rect = pygame.Rect(0, Layout.HAND_PANEL_Y, panel_w, Layout.HAND_PANEL_H)

        # Kartların sol hizalarını Shop Panel ile aynı hizada başlatıyoruz:
        start_x = 380
        
        # Kartların dikeyde ortalanması
        start_y = self.rect.y + (self.rect.h - Layout.HAND_CARD_H) // 2
        
        self.card_rects: list[pygame.Rect] = []
        for i in range(Layout.HAND_MAX_CARDS):
            cx = start_x + (Layout.HAND_CARD_W + Layout.HAND_CARD_GAP) * i
            self.card_rects.append(pygame.Rect(cx, start_y, Layout.HAND_CARD_W, Layout.HAND_CARD_H))

        # ── DCI Tactical Shelf (Frameless / Seamless) ──────────────────────
        self.bg_surface = pygame.Surface((panel_w, Layout.HAND_PANEL_H), pygame.SRCALPHA).convert_alpha()
        self.bg_surface.fill((42, 38, 55, 245))  # Açık mor-karbon ton (hex grid ile uyumlu)
        
        # Üst ayırıcı çizgi (Karbon-mor frameless border)
        pygame.draw.line(self.bg_surface, (95, 85, 115, 120), (0, 0), (panel_w, 0), 1)  # Açık mor-karbon

        # Sci-fi Decal Yazısı (subtitle, sag hizalı)
        from v2.ui.font_cache import mono, render_text as _rt
        try:
            decal_fnt = mono(9)
        except AutochessException:
            pygame.font.init()
            decal_fnt = pygame.font.SysFont("Courier", 9)
        _rt(self.bg_surface, "HAND_TERMINAL // ONLINE", decal_fnt,
            (80, 100, 130, 120),
            pygame.Rect(self.rect.w - 220, 15, 200, 14), align="right")

        # Kart Yuvaları (Premium DCI Hexagon Slots)
        for s_rect in self.card_rects:
            lx = s_rect.x - self.rect.x
            ly = s_rect.y - self.rect.y
            lw, lh = s_rect.w, s_rect.h
            cx, cy = lx + lw / 2, ly + lh / 2
            radius = lh / 2
            
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

            # İç Zemin Çukuru (Karbon-mor void)
            pygame.draw.polygon(self.bg_surface, (10, 9, 14, 220), points)
            
            # Hexagon Çerçeve (Karbon-mor tactical çizgi)
            pygame.draw.polygon(self.bg_surface, (95, 85, 115, 170), points, width=1)  # Açık mor-karbon
            
            # Siberpunk Vurgular (Karbon-mor veri portu)
            # points[2] = Bottom Center (90 deg), points[5] = Top Center (270 deg)
            pygame.draw.circle(self.bg_surface, (105, 78, 135, 100), points[2], 2)
            pygame.draw.circle(self.bg_surface, (105, 78, 135, 100), points[5], 2)

        # ── El verisi: ShopScene set_hand() ile iter, burada boş başla ──
        self._card_names: list[str | None] = [None] * Layout.HAND_MAX_CARDS

        # ── CardFlip Animatörleri (her slot için birer tane) ───────────
        self._flips: list[CardFlip] = []
        self._build_flips()    # _card_names hazır olduğunda çağır

        # ── Persistent Ghost Layer (per-frame allocation yerine) ───────
        self._ghost_layer = pygame.Surface((Screen.W, Screen.H), pygame.SRCALPHA).convert_alpha()

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
    
    def get_flip(self, slot_idx: int):
        """Public getter for CardFlip at slot index."""
        if 0 <= slot_idx < len(self._flips):
            return self._flips[slot_idx]
        return None
    
    def get_card_names(self) -> list[str | None]:
        """Public getter for all card names."""
        return list(self._card_names)

    # ------------------------------------------------------------------ #
    # İç Yardımcılar                                                       #
    # ------------------------------------------------------------------ #
    def _build_flips(self) -> None:
        """AssetLoader (varsa) kullanarak her slot için CardFlip oluştur."""
        self._flips.clear()
        try:
            from v2.assets.loader import AssetLoader
            loader = AssetLoader.get()
            _loader_available = True
        except AutochessException:
            _loader_available = False

        for i, slot_rect in enumerate(self.card_rects):
            w, h = slot_rect.width, slot_rect.height
            card_name = self._card_names[i] if hasattr(self, "_card_names") else None
            evolved = self._is_evolved_card(card_name)

            if card_name:
                if _loader_available:
                    try:
                        back_raw  = loader.get_card_back(card_name)
                        front_raw = loader.get_card_front(card_name)
                        back  = pygame.transform.scale(back_raw,  (w, h))
                        front = pygame.transform.scale(front_raw, (w, h))
                    except FileNotFoundError:
                        back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)
                        front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                else:
                    back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)
                    front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                self._flips.append(CardFlip(back, front, slot_rect, evolved=evolved, evolved_color=Colors.PLATINUM))
            else:
                from v2.ui.card_flip import MockCardBox
                self._flips.append(MockCardBox(slot_rect))

    def assign_card(self, slot_idx: int, card_name: str | None) -> None:
        """Bir slota kart ata (veya None ile boşalt) ve animatörü yenile."""
        if 0 <= slot_idx < len(self._card_names):
            self._card_names[slot_idx] = card_name
            self._rebuild_flip_at(slot_idx)

    def set_hand(self, card_names: list[str | None]) -> None:
        """ShopScene tarafından çağrılır. Panel GameState'e dokunmaz.
        Değişen slotları tespit edip yalnızca onları yeniden oluşturur.
        """
        for i, new_name in enumerate(card_names[:len(self._card_names)]):
            if new_name != self._card_names[i]:
                self.assign_card(i, new_name)

    def _rebuild_flip_at(self, idx: int) -> None:
        """Tek bir slotun CardFlip'ini yeniden oluştur."""
        slot_rect  = self.card_rects[idx]
        card_name  = self._card_names[idx]
        w, h = slot_rect.width, slot_rect.height
        evolved = self._is_evolved_card(card_name)
        
        if not card_name:
            from v2.ui.card_flip import MockCardBox
            self._flips[idx] = MockCardBox(slot_rect)
            return

        back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)
        front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
        try:
            from v2.assets.loader import AssetLoader
            loader = AssetLoader.get()
            back  = pygame.transform.scale(loader.get_card_back(card_name),  (w, h))
            front = pygame.transform.scale(loader.get_card_front(card_name), (w, h))
        except (AutochessException, FileNotFoundError):
            pass
        self._flips[idx] = CardFlip(back, front, slot_rect, evolved=evolved,
                                    evolved_color=Colors.PLATINUM)

    # ------------------------------------------------------------------ #
    # Güncelleme                                                           #
    # ------------------------------------------------------------------ #
    def update(self, dt_ms: float) -> None:
        """Her frame çağrılır. dt_ms: milisaniye cinsinden delta time."""
        for flip in self._flips:
            flip.update(dt_ms)

    def handle_hover(self, mouse_pos: tuple[int, int], ghost_index: int = -1) -> int:
        """Mouse pozisyonuna göre hover start/end sinyalle.
        ghost_index: sürüklenen slotun hover'u kilitlenir — fareyle takip gerekmez.
        """
        hovered_idx = -1
        for i, (slot_rect, flip) in enumerate(zip(self.card_rects, self._flips)):
            if i == ghost_index:
                flip.hover_start()  # Drag boyunca hover fizik kilidi
                continue
            if slot_rect.collidepoint(mouse_pos):
                flip.hover_start()
                hovered_idx = i
            else:
                flip.hover_end()
        return hovered_idx

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface, ghost_index: int = -1) -> None:
        """
        Paneli çiz. ghost_index: sürüklenen slotu karartır.
        """
        # 1. Panel zemini ve Oymak Sektörleri (Blit cached bg)
        surface.blit(self.bg_surface, self.rect)

        # Kapasite göstergesi artık LobbyPanel üzerinde sağ tarafta.

        # 2. Her kart slotu
        for i, (slot_rect, flip) in enumerate(zip(self.card_rects, self._flips)):
            if i == ghost_index:
                # Ghost: hover fizik korunarak yarı saydam çiz
                # Persistent surface kullan — per-frame allocation yerine
                self._ghost_layer.fill((0, 0, 0, 0))  # Temizle
                flip.render(self._ghost_layer)
                self._ghost_layer.set_alpha(80)  # Yarı saydam
                surface.blit(self._ghost_layer, (0, 0))
            else:
                flip.render(surface)

        # 4. InfoBox artık ShopScene tarafından dışarıdan çiziliyor.
        #    Buradaki statik zemin çizimi silindi.
