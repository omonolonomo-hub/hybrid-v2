import pygame
import math
from v2.constants import Layout
from v2.ui.card_flip import CardFlip

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
    return surf


class HandPanel:
    def __init__(self):
        # ── Ana Panel Rect ──────────────────────────────────────────────
        # Sağda Lobby panelinin altındaki boşluğu doldurmak için width genişletildi
        self.rect = pygame.Rect(
            Layout.CENTER_ORIGIN_X,
            Layout.HAND_PANEL_Y,
            Layout.CENTER_W,
            Layout.HAND_PANEL_H,
        )


        # ── Kart Slotları (Sol Hizalı) ──────────────────────────────────
        self.card_rects: list[pygame.Rect] = []
        start_x = self.rect.x + 30
        start_y = self.rect.y + 10

        for i in range(Layout.HAND_MAX_CARDS):
            cx = start_x + (Layout.HAND_CARD_W + Layout.HAND_CARD_GAP) * i
            self.card_rects.append(pygame.Rect(cx, start_y, Layout.HAND_CARD_W, Layout.HAND_CARD_H))

        # ── Info / Hover Paneli ────────────────────────────────────────
        info_w = Layout.HAND_INFO_W
        info_x = self.rect.right - info_w - 20  # Sağ alt köşeye tam oturacak (test hizasında 20px sağ margini var)

        self.info_rect = pygame.Rect(
            info_x,
            self.rect.y + 10,
            info_w,
            self.rect.h - 20,
        )

        #  AAA Cyberpunk Gradient Arkaplan (LobbyPanel Kalitesi)
        from v2.ui.ui_utils import UIUtils
        self.bg_surface = UIUtils.create_gradient_panel(
            self.rect.w, self.rect.h,
            color_top=(20, 24, 34, 252),
            color_bottom=(10, 12, 18, 255),
            border_radius=8,
            border_color=(42, 58, 92, 255) # Unified soft stroke
        )

        # ── Üst Dekoratif Çizgi (panel sınırı içinde) ─────────────────────
        decal_color = (55, 70, 96, 180)
        pygame.draw.line(self.bg_surface, decal_color, (12, 5), (self.rect.w - 12, 5), 1)

        # Sci-fi Decal Yazısı (subtitle, sag hizalı)
        from v2.ui.font_cache import mono, render_text as _rt
        try:
            decal_fnt = mono(9)
        except Exception:
            pygame.font.init()
            decal_fnt = pygame.font.SysFont("Courier", 9)
        _rt(self.bg_surface, "HAND_TERMINAL // ONLINE", decal_fnt,
            (80, 100, 130, 120),
            pygame.Rect(self.rect.w - 220, 8, 200, 14), align="right")

        # Kart Yuvaları (Sadece içeriye doğru göçük/karanlık insets, sade tasarım)
        for s_rect in self.card_rects:
            lx = s_rect.x - self.rect.x
            ly = s_rect.y - self.rect.y
            lw, lh = s_rect.w, s_rect.h

            # İç Zemin Çukuru (Rounded inset shadow)
            pygame.draw.rect(self.bg_surface, (4, 6, 8, 180), (lx, ly, lw, lh), border_radius=4)
            # İnset derinlik hissi için çerçeve (Optional shading)
            pygame.draw.rect(self.bg_surface, (0, 0, 0, 200), (lx, ly, lw, lh), width=1, border_radius=4)

        # ── Mock kart isimleri ──
        try:
            from v2.core.game_state import GameState
            hand_data = GameState.get().get_hand(player_index=0)
        except Exception:
            hand_data = [None] * Layout.HAND_MAX_CARDS

        self._card_names: list[str | None] = list(hand_data[:Layout.HAND_MAX_CARDS])
        # Eksik slotları None ile doldur
        while len(self._card_names) < Layout.HAND_MAX_CARDS:
            self._card_names.append(None)

        # ── CardFlip Animatörleri (her slot için birer tane) ───────────
        self._flips: list[CardFlip] = []
        self._build_flips()    # _card_names hazır olduğunda çağır

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
        except Exception:
            _loader_available = False

        for i, slot_rect in enumerate(self.card_rects):
            w, h = slot_rect.width, slot_rect.height
            card_name = self._card_names[i] if hasattr(self, "_card_names") else None

            if _loader_available and card_name:
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

            self._flips.append(CardFlip(back, front, slot_rect))

    def assign_card(self, slot_idx: int, card_name: str | None) -> None:
        """Bir slota kart ata (veya None ile boşalt) ve animatörü yenile."""
        if 0 <= slot_idx < len(self._card_names):
            self._card_names[slot_idx] = card_name
            self._rebuild_flip_at(slot_idx)

    def sync(self) -> None:
        """
        GameState'ten güncel el verisini çek ve değişen slotları güncelle.
        Buy olayı sonrasında ShopScene tarafından çağrılır.
        """
        try:
            from v2.core.game_state import GameState
            new_hand = GameState.get().get_hand(player_index=0)
        except Exception:
            return
        for i, new_name in enumerate(new_hand[:len(self._card_names)]):
            if new_name != self._card_names[i]:
                self.assign_card(i, new_name)

    def _rebuild_flip_at(self, idx: int) -> None:
        """Tek bir slotun CardFlip'ini yeniden oluştur."""
        slot_rect  = self.card_rects[idx]
        card_name  = self._card_names[idx]
        w, h = slot_rect.width, slot_rect.height
        try:
            from v2.assets.loader import AssetLoader
            loader = AssetLoader.get()
            if card_name:
                back  = pygame.transform.scale(loader.get_card_back(card_name),  (w, h))
                front = pygame.transform.scale(loader.get_card_front(card_name), (w, h))
            else:
                raise FileNotFoundError
        except Exception:
            back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)
            front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
        self._flips[idx] = CardFlip(back, front, slot_rect)

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
                ghost_layer = pygame.Surface(
                    (surface.get_width(), surface.get_height()), pygame.SRCALPHA
                )
                flip.render(ghost_layer)
                ghost_layer.set_alpha(80)  # Yarı saydam
                surface.blit(ghost_layer, (0, 0))
            else:
                flip.render(surface)

        # 4. InfoBox artık ShopScene tarafından dışarıdan çiziliyor.
        #    Buradaki statik zemin çizimi silindi.
